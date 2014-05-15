__author__ = 'Konstantin Dmitriev'

import sys
from renderchan.file import RenderChanFile
from renderchan.project import RenderChanProjectManager
from renderchan.module import RenderChanModuleManager
from renderchan.utils import mkdirs
from renderchan.utils import float_trunc
from renderchan.utils import sync
from puliclient import Task, Graph
import os, time

class RenderChan():
    def __init__(self):

        self.puliServer = ""
        self.puliPort = 8004

        print "RenderChan initialized."
        self.projects = RenderChanProjectManager()
        self.modules = RenderChanModuleManager()
        self.modules.loadAll()

        self.loadedFiles = {}

        self.graph = Graph( 'RenderChan graph', poolName="default" )

    def setHost(self, host):
        self.puliServer=host

    def setPort(self, port):
        self.puliPort=port

    def submit(self, taskfile, useDispatcher=True, dependenciesOnly=False, allocateOnly=False):

        """

        :type taskfile: RenderChanFile
        """

        if allocateOnly and dependenciesOnly:

            if os.path.exists(taskfile.getRenderPath()):
                self.parseDirectDependency(taskfile, None)
            else:
                taskfile.endFrame = taskfile.startFrame + 1
                self.parseRenderDependency(taskfile, allocateOnly)

        elif dependenciesOnly:

            self.parseDirectDependency(taskfile, None)

        else:

            if allocateOnly:
                if os.path.exists(taskfile.getRenderPath()):
                    print "File is already allocated."
                    sys.exit(0)
                taskfile.dependencies=[]
                taskfile.endFrame = taskfile.startFrame + 1

            self.parseRenderDependency(taskfile, allocateOnly)

        # Finally submit the graph to Puli

        if self.puliServer=="":
            server="127.0.0.1"
            # TODO: If no server address given, then try to run our own dispatcher
            # ...
        else:
            server=self.puliServer

        if useDispatcher:
            # Submit to dispatcher host
            self.graph.submit(server, self.puliPort)
        else:
            # Local rendering
            self.graph.execute()

    def parseRenderDependency(self, taskfile, allocateOnly):
        """

        :type taskfile: RenderChanFile
        """

        isDirty = False

        # First, let's ensure, that we are in sync with profile data
        checkTime=None
        if os.path.exists(taskfile.getProfileRenderPath()+".sync"):
            checkFile=os.path.join(taskfile.getProjectRoot(),"render","project.conf","profile.conf")
            checkTime=float_trunc(os.path.getmtime(checkFile),1)
        if os.path.exists(taskfile.getProfileRenderPath()):
            sync(taskfile.getProfileRenderPath(),taskfile.getRenderPath(),checkTime)
        else:
            isDirty = True


        if not os.path.exists(taskfile.getRenderPath()):
            # If no rendering exists, then obviously rendering is required
            isDirty = True
            compareTime = None
        else:
            # Otherwise we have to check against the time of the last rendering
            compareTime = float_trunc(os.path.getmtime(taskfile.getRenderPath()),1)

        # Get "dirty" status for the target file and all dependent tasks, submitted as dependencies
        (isDirtyValue,tasklist, maxTime)=self.parseDirectDependency(taskfile, compareTime)

        if isDirtyValue:
            isDirty = True

        # If rendering is requested
        if isDirty:

            # Puli part here

            name = taskfile.getPath()
            runner = "renderchan.puli.RenderChanRunner"
            decomposer = "renderchan.puli.RenderChanDecomposer"

            params = taskfile.getParams()
            # Max time is a
            if allocateOnly:
                # Make sure this file will be re-rendered next time
                params["maxTime"]=taskfile.mtime-1000
            else:
                params["maxTime"]=maxTime

            # Make sure we have all directories created
            mkdirs(os.path.dirname(params["profile_output"]))
            mkdirs(os.path.dirname(params["output"]))

            # Add rendering task to the graph
            taskfile.taskRender=self.graph.addNewTask( name="Render: "+name, runner=runner, arguments=params, decomposer=decomposer )


            # Now we will add a task which composes results and places it into valid destination

            # Add rendering task to the graph
            runner = "renderchan.puli.RenderChanPostRunner"
            decomposer = "renderchan.puli.RenderChanPostDecomposer"
            taskfile.taskPost=self.graph.addNewTask( name="Post: "+name, runner=runner, arguments=params, decomposer=decomposer,
                                       maxNbCores=taskfile.module.conf["maxNbCores"] )

            self.graph.addEdges( [(taskfile.taskRender, taskfile.taskPost)] )

            # Add edges for dependent tasks
            for task in tasklist:
                self.graph.addEdges( [(task, taskfile.taskRender)] )

        # Mark this file as already parsed and thus its "dirty" value is known
        taskfile.isDirty=isDirty

        return isDirty


    def parseDirectDependency(self, taskfile, compareTime):
        """

        :type taskfile: RenderChanFile
        """

        tasklist=[]

        self.loadedFiles[taskfile.getPath()]=taskfile
        if taskfile.project!=None and taskfile.module!=None:
            self.loadedFiles[taskfile.getRenderPath()]=taskfile

        deps = taskfile.getDependencies()

        # maxTime is the maximum of modification times for all direct dependencies.
        # It allows to compare with already rendered pieces and continue rendering
        # if they are rendered AFTER the maxTime.
        #
        # But, if we have at least one INDIRECT dependency (i.e. render task) and it is submitted
        # for rendering, then we can't compare with maxTime (because dependency will be rendered
        # and thus rendering should take place no matter what).
        maxTime = taskfile.getTime()

        taskfile.pending=True  # we need this to avoid circular dependencies

        isDirty=False
        for path in deps:
            if path in self.loadedFiles.keys():
                dependency = self.loadedFiles[path]
                if dependency.pending:
                    # Avoid circular dependencies
                    print "Warning: Circular dependency detected for %s. Skipping." % (path)
                    continue
            else:
                print ". loading file: %s" % path
                dependency = RenderChanFile(path, self.modules, self.projects)
                if not os.path.exists(dependency.getPath()):
                    print "   Skipping file %s..." % path
                    continue

            # Check if this is a rendering dependency
            if path != dependency.getPath():
                # We have a new task to render
                if dependency.isDirty==None:
                    if dependency.module!=None:
                        dep_isDirty = self.parseRenderDependency(dependency, allocateOnly=False)
                    else:
                        raise Exception("No module to render file")
                else:
                    # The dependency was already submitted to graph
                    dep_isDirty = dependency.isDirty

                if dep_isDirty:
                    # Let's return submitted task into tasklist
                    if not dependency.taskPost in tasklist:
                        tasklist.append(dependency.taskPost)
                    # Increase maxTime, because re-rendering of dependency will take place
                    maxTime=time.time()
                    isDirty = True
                else:
                    # If no rendering requested, we still have to check if rendering result
                    # is newer than compareTime

                    #if os.path.exists(dependency.getRenderPath()):  -- file is obviously exists, because isDirty==0
                    timestamp=float_trunc(os.path.getmtime(dependency.getRenderPath()),1)

                    if compareTime is None:
                        isDirty = True
                    elif timestamp > compareTime:
                        isDirty = True
                    if timestamp>maxTime:
                        maxTime=timestamp

            else:
                # No, this is an ordinary dependency
                    (dep_isDirty, dep_tasklist, dep_maxTime) = self.parseDirectDependency(dependency, compareTime)
                    if dep_isDirty:
                        isDirty=True
                    if dep_maxTime>maxTime:
                        maxTime=dep_maxTime
                    for task in dep_tasklist:
                        if not task in tasklist:
                            tasklist.append(task)

        if not isDirty:
            timestamp = float_trunc(taskfile.getTime(), 1)
            if compareTime is None:
                isDirty = True
            elif timestamp > compareTime:
                isDirty = True
            if timestamp>maxTime:
                maxTime=timestamp

        taskfile.pending=False

        return (isDirty, list(tasklist), maxTime)
