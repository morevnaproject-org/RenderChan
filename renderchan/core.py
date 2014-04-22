__author__ = 'Konstantin Dmitriev'

import sys
from renderchan.file import RenderChanFile
from renderchan.project import RenderChanProjectManager
from renderchan.module import RenderChanModuleManager
from renderchan.utils import mkdirs
from puliclient import Task, Graph
import os

class RenderChan():
    def __init__(self):

        self.puliServer = ""
        self.puliPort = 8004

        print "RenderChan initialized."
        self.projects = RenderChanProjectManager()
        self.modules = RenderChanModuleManager()
        self.modules.loadAll()

    def setHost(self, host):
        self.puliServer=host

    def setPort(self, port):
        self.puliPort=port

    def submit(self, taskfile, useDispatcher=True):

        """

        :type taskfile: RenderChanFile
        """
        deps = taskfile.getDependencies()

        for path in deps:
            dependency = RenderChanFile(path, self.modules, self.projects)
            if path != dependency.getPath():
                # We have a new task to render
                self.submit(dependency)

        # Puli part here

        # First we create a graph
        graph = Graph( 'RenderChan graph', poolName="default" )
        name = taskfile.getPath()
        runner = "renderchan.puli.RenderChanRunner"
        decomposer = "renderchan.puli.RenderChanDecomposer"

        params = taskfile.getParams()
        params["filename"]=taskfile.getPath()
        params["output"]=taskfile.getRenderPath()
        params["profile_output"]=taskfile.getProfileRenderPath()
        params["module"]=taskfile.module.getName()
        params["packetSize"]=taskfile.module.getPacketSize()
        params["start"]=taskfile.getStartFrame()
        params["end"]=taskfile.getEndFrame()
        params["dependencies"]=taskfile.getDependencies()
        params["projectVersion"]=taskfile.project.version

        # Make sure we have all directories created
        mkdirs(os.path.dirname(params["profile_output"]))
        mkdirs(os.path.dirname(params["output"]))

        # Add rendering task to the graph
        taskRender=graph.addNewTask( name="Render: "+name, runner=runner, arguments=params, decomposer=decomposer )


        # Now we will add a task which composes results and places it into valid destination

        # Add rendering task to the graph
        runner = "renderchan.puli.RenderChanPostRunner"
        decomposer = "renderchan.puli.RenderChanPostDecomposer"
        taskPost=graph.addNewTask( name="Post: "+name, runner=runner, arguments=params, decomposer=decomposer,
                                   maxNbCores=taskfile.module.conf["maxNbCores"] )

        graph.addEdges( [
            (taskRender, taskPost)
            ] )

        # Finally submit the graph to Puli

        if self.puliServer=="":
            server="127.0.0.1"
            # TODO: If no server address given, then try to run our own dispatcher
            # ...
        else:
            server=self.puliServer

        if useDispatcher:
            # Submit to dispatcher host
            graph.submit(server, self.puliPort)
        else:
            # Local rendering
            graph.execute()

