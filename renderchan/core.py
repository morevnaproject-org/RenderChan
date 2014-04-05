__author__ = 'Konstantin Dmitriev'

import sys
from renderchan.file import RenderChanFile
from renderchan.project import RenderChanProjectManager
from renderchan.module import RenderChanModuleManager
from puliclient import Task, Graph

class RenderChan():
    def __init__(self):

        self.puliServer = "127.0.0.1"
        self.puliPort = 8004

        print "RenderChan initialized."
        self.projects = RenderChanProjectManager()
        self.modules = RenderChanModuleManager()

    def submit(self, taskfile):

        """

        :type taskfile: RenderChanFile
        """
        deps = taskfile.getDependencies()

        for path in deps:
            dependency = RenderChanFile(path)
            if path != dependency.getPath():
                # We have a new task to render
                self.submit(dependency)

        # Puli part here

        # First we create a graph
        graph = Graph( 'RenderChan graph', poolName="default" )
        name = taskfile.getPath()
        #runner = "puliclient.contrib.commandlinerunner.CommandLineRunner"
        #arguments = {"args": "synfigstudio"}
        #runner  = "puliclient.contrib.generic.GenericRunner"
        #arguments = {"cmd": "blender"}
        runner = "renderchan.puli.RenderChanRunner"
        decomposer = "renderchan.puli.RenderChanDecomposer"

        arguments = {}
        arguments["filename"]=taskfile.getPath()
        arguments["output"]=taskfile.getRenderPath()
        arguments["profile_output"]=taskfile.getProfileRenderPath()
        arguments["format"]=taskfile.getOutputFormat()

        # FIXME: Options below should be detected
        arguments["module"]="blender"
        arguments["start"]=0
        arguments["end"]=15
        arguments["width"]=480
        arguments["height"]=270

        # FIXME: Packet size should be defined by module
        arguments["packetSize"]=10

        # Then add a new task to the graph
        graph.addNewTask( name, runner=runner, arguments=arguments, decomposer=decomposer )
        # Finally submit the graph to the server
        graph.submit(self.puliServer, self.puliPort)

