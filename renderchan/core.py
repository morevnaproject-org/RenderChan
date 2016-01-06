__author__ = 'Konstantin Dmitriev'

import sys
from renderchan.file import RenderChanFile
from renderchan.project import RenderChanProjectManager
from renderchan.module import RenderChanModuleManager, RenderChanModule
from renderchan.utils import mkdirs
from renderchan.utils import float_trunc
from renderchan.utils import sync
from renderchan.utils import touch
from renderchan.utils import copytree
from renderchan.utils import which
import os, time
import shutil
import subprocess

class RenderChan():
    def __init__(self):

        self.datadir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")

        self.available_renderfarm_engines = ("puli","afanasy")
        self.renderfarm_engine = ""
        self.renderfarm_host = "127.0.0.1"
        self.renderfarm_port = 8004

        print("RenderChan initialized.")
        self.start_time = time.time()
        self.projects = RenderChanProjectManager()
        self.modules = RenderChanModuleManager()

        self.loadedFiles = {}

        self.graph = None  # used by renderfarm
        # == taskgroups bug / commented ==
        # The following are the special taskgroups used for managing stereo rendering
        #self.taskgroupLeft = None
        #self.taskgroupRight = None

        # FIXME: The childTask is a dirty workaround, which we need because of broken taskgroups functionality (search for "taskgroups bug" string to get the commented code)
        self.childTask = None

        self.AfanasyBlockClass=None
        self.cgru_location = "/opt/cgru"

        self.snapshot_path = None

        self.ffmpeg_binary = ''
        if os.name == 'nt':
            ffmpeg_path = os.path.join(os.path.dirname(__file__),"..\\..\\ffmpeg\\bin\\ffmpeg.exe")
            avconv_path = os.path.join(os.path.dirname(__file__),"..\\..\\avconv\\bin\\avconv.exe")
        else:
            ffmpeg_path = 'ffmpeg'
            avconv_path = 'avconv'
        if which(ffmpeg_path) != None:
            self.ffmpeg_binary = ffmpeg_path
        elif which(avconv_path) != None:
            self.ffmpeg_binary = avconv_path
        if self.ffmpeg_binary == '':
            raise Exception('ERROR: No ffmpeg binary found. Please install ffmpeg.')

    def __del__(self):
        if self.renderfarm_engine == "":
            t = time.time()-self.start_time
            hours = int(t/3600)
            t = t - hours*3600
            minutes = int(t/60)
            t = t - minutes*60
            seconds = int(t)
            print()
            print()
            print("Execution time: %02d:%02d:%02d " % ( hours, minutes, seconds ))
            print()

    def setHost(self, host):
        self.renderfarm_host=host

    def setPort(self, port):
        self.renderfarm_port=port

    def setStereoMode(self, mode):
        self.setProfile(self.projects.profile, mode)

    def setProfile(self, profile, stereo=None):
        """

        :type profile: str
        """

        if stereo == None:
            stereo=self.projects.stereo

        if self.projects.active:

            # Update root project
            self.projects.active.config["stereo"]=stereo
            self.projects.active.loadRenderConfig(profile)

            # Update child projects
            for key in self.projects.list.keys():
                project = self.projects.list[key]
                project.config=self.projects.active.config.copy()
                project.loadRenderConfig(self.projects.profile)
                # Reload module configuration
                loaded_modules = project.dependencies[:]
                project.dependencies = []
                for module_name in loaded_modules:
                    module = self.modules.get(module_name)
                    project.registerModule(module)

        self.projects.profile=profile
        self.projects.stereo=stereo

    def submit(self, taskfile, dependenciesOnly=False, allocateOnly=False, stereo=""):

        """

        :type taskfile: RenderChanFile
        """

        if taskfile.project == None:
            print()
            print("ERROR: Can't render a file which is not a part of renderchan project.")
            print()
            return 1

        if self.renderfarm_engine=="afanasy":

            os.environ["CGRU_LOCATION"]=self.cgru_location
            os.environ["AF_ROOT"]=os.path.join(self.cgru_location,"afanasy")
            sys.path.insert(0, os.path.join(self.cgru_location,"lib","python"))
            sys.path.insert(0, os.path.join(self.cgru_location,"afanasy","python"))

            from af import Job as AfanasyJob
            from af import Block as AfanasyBlock
            self.AfanasyBlockClass=AfanasyBlock
            self.graph = AfanasyJob('RenderChan - %s - %s' % (taskfile.localPath, taskfile.projectPath))

        elif self.renderfarm_engine=="puli":
            from puliclient import Graph
            self.graph = Graph( 'RenderChan graph', poolName="default" )

        last_task = None

        if stereo in ("vertical","v","horizontal","h"):

            # Left eye graph
            self.setStereoMode("left")
            self.addToGraph(taskfile, dependenciesOnly, allocateOnly)

            if self.renderfarm_engine!="":
                self.childTask = taskfile.taskPost

            # Right eye graph
            self.setStereoMode("right")
            self.addToGraph(taskfile, dependenciesOnly, allocateOnly)

            # Stitching altogether
            if self.renderfarm_engine=="":
                self.job_merge_stereo(taskfile, stereo)
            elif self.renderfarm_engine=="afanasy":

                name = "StereoPost - %f" % ( time.time() )
                block = self.AfanasyBlockClass(name, 'generic')
                block.setCommand("renderchan-job-launcher %s --action merge --profile %s --stereo %s --compare-time %f" % ( taskfile.getPath(), self.projects.profile, stereo, time.time() ))
                if taskfile.taskPost!=None:
                    block.setDependMask(taskfile.taskPost)
                block.setNumeric(1,1,100)
                block.setCapacity(100)

                self.graph.blocks.append(block)

                last_task = name

            elif self.renderfarm_engine=="puli":

                runner = "puliclient.contrib.commandlinerunner.CommandLineRunner"

                # Add parent task which composes results and places it into valid destination
                command = "renderchan-job-launcher %s --action merge --profile %s --stereo %s --compare-time %f" % ( taskfile.getPath(), self.projects.profile, stereo, time.time() )
                stereoTask = self.graph.addNewTask( name="StereoPost: "+taskfile.localPath, runner=runner, arguments={ "args": command} )

                # Dummy task
                #decomposer = "puliclient.contrib.generic.GenericDecomposer"
                #params={ "cmd":"echo", "start":1, "end":1, "packetSize":1, "prod":"test", "shot":"test" }
                #dummyTask = self.graph.addNewTask( name="StereoDummy", arguments=params, decomposer=decomposer )

                # == taskgroups bug / commented ==
                #self.graph.addEdges( [(self.taskgroupLeft, self.taskgroupRight)] )
                #self.graph.addEdges( [(self.taskgroupRight, stereoTask)] )
                #self.graph.addChain( [self.taskgroupLeft, dummyTask, self.taskgroupRight, stereoTask] )
                if taskfile.taskPost!=None:
                    self.graph.addEdges( [(taskfile.taskPost, stereoTask)] )

                last_task = stereoTask

        else:
            if stereo in ("left","l"):
                self.setStereoMode("left")
            elif stereo in ("right","r"):
                self.setStereoMode("right")
            self.addToGraph(taskfile, dependenciesOnly, allocateOnly)

            last_task = taskfile.taskPost

        # Snapshot
        if self.snapshot_path:
            if stereo in ("vertical","v","horizontal","h"):
                snapshot_source = os.path.splitext(taskfile.getRenderPath())[0]+"-stereo-"+stereo[0:1]+os.path.splitext(taskfile.getRenderPath())[1]
            else:
                snapshot_source = taskfile.getProfileRenderPath()


            if self.renderfarm_engine=="":

                self.job_snapshot(snapshot_source, self.snapshot_path)

            elif self.renderfarm_engine=="afanasy":

                name = "Snapshot - %f" % ( time.time() )
                block = self.AfanasyBlockClass(name, 'generic')
                block.setCommand("renderchan-job-launcher %s --action snapshot --target-dir %s" % ( snapshot_source,  self.snapshot_path))
                if last_task!=None:
                    block.setDependMask(last_task)
                block.setNumeric(1,1,100)
                block.setCapacity(50)

                self.graph.blocks.append(block)

            elif self.renderfarm_engine=="puli":

                runner = "puliclient.contrib.commandlinerunner.CommandLineRunner"

                # Add parent task which composes results and places it into valid destination
                command = "renderchan-job-launcher %s --action snapshot --target-dir %s" % ( snapshot_source, self.snapshot_path)
                snapshotTask = self.graph.addNewTask( name="Snapshot: "+taskfile.localPath, runner=runner, arguments={ "args": command} )

                if last_task!=None:
                    self.graph.addEdges( [(last_task, snapshotTask)] )


        # Make sure to close cache before submitting job to renderfarm
        for path in self.projects.list.keys():
            self.projects.list[path].cache.close()

        # Submit job to renderfarm
        if self.renderfarm_engine=="afanasy":

            # Wait a moment to make sure cache is closed properly
            # (this allows to avoid issues with shared nfs drives)
            time.sleep(1)

            self.graph.output(True)
            self.graph.send()

        elif self.renderfarm_engine=="puli":
            self.graph.submit(self.renderfarm_host, self.renderfarm_port)

    def addToGraph(self, taskfile, dependenciesOnly=False, allocateOnly=False):
        """

        :type taskfile: RenderChanFile
        """

        for path in self.loadedFiles.keys():
            self.loadedFiles[path].isDirty=None
        #self.loadedFiles={}

        # == taskgroups bug / commented ==
        # Prepare taskgroups if we do stereo rendering
        #if self.projects.active.getConfig("stereo")=="left":
        #    self.taskgroupLeft = self.graph.addNewTaskGroup( name="TG Left: "+taskfile.getPath() )
        #elif self.projects.active.getConfig("stereo")=="right":
        #    self.taskgroupRight = self.graph.addNewTaskGroup( name="TG Right: "+taskfile.getPath() )


        if allocateOnly and dependenciesOnly:

            if os.path.exists(taskfile.getRenderPath()):
                self.parseDirectDependency(taskfile, None)
            else:
                taskfile.endFrame = taskfile.startFrame + 2
                self.parseRenderDependency(taskfile, allocateOnly)

        elif dependenciesOnly:

            self.parseDirectDependency(taskfile, None)

        elif allocateOnly:

            if os.path.exists(taskfile.getRenderPath()):
                print("File is already allocated.")
                sys.exit(0)
            taskfile.dependencies=[]
            taskfile.endFrame = taskfile.startFrame + 2
            self.parseRenderDependency(taskfile, allocateOnly)

        else:

            self.parseRenderDependency(taskfile, allocateOnly)


        self.childTask = None


    def parseRenderDependency(self, taskfile, allocateOnly):
        """

        :type taskfile: RenderChanFile
        """

        # TODO: Re-implement this function in the same way as __not_used__syncProfileData() ?

        isDirty = False

        # First, let's ensure, that we are in sync with profile data

        t=taskfile.project.switchProfile(taskfile.project.getProfileDirName())

        checkTime=None
        if os.path.exists(taskfile.getProfileRenderPath()+".sync"):
            checkFile=os.path.join(taskfile.getProjectRoot(),"render","project.conf","profile.conf")
            checkTime=float_trunc(os.path.getmtime(checkFile),1)
        if os.path.exists(taskfile.getProfileRenderPath()):

            source=taskfile.getProfileRenderPath()
            dest=taskfile.getRenderPath()
            sync(source,dest,checkTime)

            source=os.path.splitext(taskfile.getProfileRenderPath())[0]+"-alpha."+taskfile.getFormat()
            dest=os.path.splitext(taskfile.getRenderPath())[0]+"-alpha."+taskfile.getFormat()
            sync(source,dest,checkTime)

        else:
            isDirty = True

        t.unlock()


        if not os.path.exists(taskfile.getProfileRenderPath()):
            # If no rendering exists, then obviously rendering is required
            isDirty = True
            compareTime = None
            if os.environ.get('DEBUG'):
                print("DEBUG: Dirty = 1 (no rendering exists)")
        else:
            # Otherwise we have to check against the time of the last rendering
            compareTime = float_trunc(os.path.getmtime(taskfile.getProfileRenderPath()),1)

        # Get "dirty" status for the target file and all dependent tasks, submitted as dependencies
        (isDirtyValue, tasklist, maxTime)=self.parseDirectDependency(taskfile, compareTime)

        if isDirtyValue:
            isDirty = True

        # If rendering is requested
        if isDirty:

            # Make sure we have all directories created
            mkdirs(os.path.dirname(taskfile.getProfileRenderPath()))
            mkdirs(os.path.dirname(taskfile.getRenderPath()))

            params = taskfile.getParams()

            # Keep track of created files to allow merging them later
            output_list = os.path.splitext( taskfile.getProfileRenderPath() )[0] + ".txt"
            output_list_alpha = os.path.splitext( taskfile.getProfileRenderPath() )[0] + "-alpha.txt"
            if os.path.exists(output_list):
                os.remove(output_list)
            if os.path.exists(output_list_alpha):
                os.remove(output_list_alpha)
            if taskfile.getPacketSize() > 0:
                segments = self.decompose(taskfile.getStartFrame(), taskfile.getEndFrame(), taskfile.getPacketSize())
                for range in segments:
                    start=range[0]
                    end=range[1]
                    chunk_name = taskfile.getProfileRenderPath(start,end)
                    f = open(output_list, 'a')
                    f.write("file '%s'\n" % (chunk_name))
                    f.close()
                    if "extract_alpha" in params and params["extract_alpha"] == "1":

                        f = open(output_list_alpha, 'a')
                        alpha_output = os.path.splitext(chunk_name)[0] + "-alpha" + os.path.splitext(chunk_name)[1]
                        f.write("file '%s'\n" % (alpha_output))
                        f.close()
            else:
                segments=[ (None,None) ]


            if allocateOnly:
                # Make sure this file will be re-rendered next time
                compare_time=taskfile.mtime-1000
            else:
                compare_time=maxTime

            if self.renderfarm_engine=="":

                for range in segments:
                    start=range[0]
                    end=range[1]
                    self.job_render(taskfile, taskfile.getFormat(), self.updateCompletion, start, end, compare_time)

                self.job_merge(taskfile, taskfile.getFormat(), taskfile.project.getConfig("stereo"), compare_time)

            elif self.renderfarm_engine=="afanasy":

                # Render block

                command = "renderchan-job-launcher %s --action render --format %s --profile %s --compare-time %s" % ( taskfile.getPath(), taskfile.getFormat(), self.projects.profile, compare_time )
                if self.projects.stereo!="":
                    command += " --stereo %s" % (self.projects.stereo)
                if taskfile.getPacketSize()>0:
                    command += " --start @#@ --end @#@"

                if taskfile.project.path == self.projects.active.path:
                    name = "%s - %f" % ( taskfile.localPath, time.time() )
                else:
                    name = "%s - %s - %f" % ( taskfile.localPath, taskfile.projectPath, time.time() )

                if taskfile.module.getName() in ("blender"):
                    blocktype=taskfile.module.getName()
                else:
                    blocktype="generic"


                block = self.AfanasyBlockClass(name, blocktype)
                block.setCommand(command.decode('utf-8'))
                block.setErrorsTaskSameHost(-2)
                if taskfile.getPacketSize()>0:
                    block.setNumeric(taskfile.getStartFrame(),taskfile.getEndFrame(),taskfile.getPacketSize())
                else:
                    block.setNumeric(1,1,100)

                if taskfile.module.getName() in ("flac","mp3","vorbis"):
                    block.setCapacity(50)
                elif taskfile.module.getName() in ("synfig"):
                    block.setCapacity(500)

                depend_mask=[]
                for dep_task in tasklist:
                    depend_mask.append(dep_task)

                if self.childTask!=None:
                    depend_mask.append(self.childTask)
                block.setDependMask("|".join(depend_mask))



                command = "renderchan-job-launcher %s --action merge --format %s --profile %s --compare-time %s" % ( taskfile.getPath(), taskfile.getFormat(), self.projects.profile, compare_time )
                if self.projects.stereo!="":
                    command += " --stereo %s" % (self.projects.stereo)

                self.graph.blocks.append(block)

                # Post block

                if taskfile.project.path == self.projects.active.path:
                    name_post = "Post %s - %f" % ( taskfile.localPath, time.time() )
                else:
                    name_post = "Post %s - %s - %f" % ( taskfile.localPath, taskfile.projectPath, time.time() )
                taskfile.taskPost = name_post
                block = self.AfanasyBlockClass(name_post, "generic")
                block.setNumeric(1,1,100)
                block.setCommand(command.decode('utf-8'))
                block.setDependMask(name)
                block.setErrorsTaskSameHost(-2)
                block.setCapacity(50)


                self.graph.blocks.append(block)

            elif self.renderfarm_engine=="puli":

                # Puli part here

                graph_destination = self.graph
                # == taskgroups bug / commented ==
                #if self.projects.active.getConfig("stereo")=="left":
                #    graph_destination = self.taskgroupLeft
                #    name+=" (L)"
                #elif self.projects.active.getConfig("stereo")=="right":
                #    graph_destination = self.taskgroupRight
                #    name+=" (R)"
                #else:
                #    graph_destination = self.graph

                runner = "puliclient.contrib.commandlinerunner.CommandLineRunner"

                # Add parent task which composes results and places it into valid destination
                command = "renderchan-job-launcher %s --action merge --format %s --profile %s --compare-time %s" % ( taskfile.getPath(), taskfile.getFormat(), self.projects.profile, compare_time )
                if self.projects.stereo!="":
                    command += " --stereo %s" % (self.projects.stereo)
                taskfile.taskPost=graph_destination.addNewTask( name="Post: "+taskfile.localPath, runner=runner, arguments={ "args": command} )

                # Add rendering segments
                for range in segments:
                    start=range[0]
                    end=range[1]
                    if start!=None and end!=None:
                        segment_name = "Render: %s (%s-%s)" % (taskfile.localPath, start, end)
                        command = "renderchan-job-launcher %s --action render --format %s --profile %s --start %s --end %s --compare-time %s" % ( taskfile.getPath(), taskfile.getFormat(), self.projects.profile, start, end, compare_time )
                    else:
                        segment_name = "Render: %s" % (taskfile.localPath)
                        command = "renderchan-job-launcher %s --action render --format %s --profile %s --compare-time %s" % ( taskfile.getPath(), taskfile.getFormat(), self.projects.profile, compare_time )
                    if self.projects.stereo!="":
                        command += " --stereo %s" % (self.projects.stereo)

                    task=graph_destination.addNewTask( name=segment_name, runner=runner, arguments={ "args": command} )
                    self.graph.addEdges( [(task, taskfile.taskPost)] )

                    # Add edges for dependent tasks
                    for dep_task in tasklist:
                        self.graph.addEdges( [(dep_task, task)] )

                    if self.childTask!=None:
                        self.graph.addEdges( [(self.childTask, task)] )

        # Mark this file as already parsed and thus its "dirty" value is known
        taskfile.isDirty=isDirty

        return isDirty


    def parseDirectDependency(self, taskfile, compareTime):
        """

        :type taskfile: RenderChanFile
        """

        tasklist=[]

        if taskfile.isFrozen():
            return (False, [], 0)

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
            path = os.path.abspath(path)
            if path in self.loadedFiles.keys():
                dependency = self.loadedFiles[path]
                if dependency.pending:
                    # Avoid circular dependencies
                    print("Warning: Circular dependency detected for %s. Skipping." % (path))
                    continue
            else:
                dependency = RenderChanFile(path, self.modules, self.projects)
                if not os.path.exists(dependency.getPath()):
                    # TODO: Add an option to specify how to deal with missing files: create empty placeholder (default), create warning placeholder, none (most likely throw an erros) or raise exception.
                    if ( not os.path.exists(path) ) and ( dependency.projectPath!='' ):
                        # Let's look if we have a placeholder template
                        ext = os.path.splitext(path)[1]
                        placeholder = os.path.join(self.datadir, "missing", "empty" + ext)
                        if os.path.exists(placeholder):
                            print("   Creating an empty placeholder for %s..." % path)
                            mkdirs(os.path.dirname(path))
                            shutil.copy(placeholder, path)
                            t = time.mktime(time.strptime('01.01.1960 00:00:00', '%d.%m.%Y %H:%M:%S'))
                            os.utime(path,(t,t))
                        else:
                            print("   Skipping file %s..." % path)
                    else:
                        print("   Skipping file %s..." % path)
                    continue
                self.loadedFiles[dependency.getPath()]=dependency
                if dependency.project!=None and dependency.module!=None:
                    self.loadedFiles[dependency.getRenderPath()]=dependency
                    # Alpha
                    renderpath_alpha=os.path.splitext(dependency.getRenderPath())[0]+"-alpha."+dependency.getFormat()
                    self.loadedFiles[renderpath_alpha]=dependency

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
                    timestamp=float_trunc(os.path.getmtime(dependency.getProfileRenderPath()),1)

                    if compareTime is None:
                        isDirty = True
                        if os.environ.get('DEBUG'):
                            print("DEBUG: %s:" % taskfile.localPath)
                            print("DEBUG: Dirty = 1 (no compare time)")
                            print()
                    elif timestamp > compareTime:
                        isDirty = True
                        if os.environ.get('DEBUG'):
                            print("DEBUG: %s:" % taskfile.localPath)
                            print("DEBUG: Dirty = 1 (dependency timestamp is higher)")
                            print("DEBUG:            compareTime     = %f" % (compareTime))
                            print("DEBUG:            dependency time = %f" % (timestamp))
                            print()
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
                if os.environ.get('DEBUG'):
                    print("DEBUG: %s:" % taskfile.localPath)
                    print("DEBUG: Dirty = 1 (no compare time)")
                    print()
                isDirty = True
            elif timestamp > compareTime:
                isDirty = True
                if os.environ.get('DEBUG'):
                    print("DEBUG: %s:" % taskfile.localPath)
                    print("DEBUG: Dirty = 1 (source timestamp is higher)")
                    print("DEBUG:            compareTime     = %f" % (compareTime))
                    print("DEBUG:            source time = %f" % (timestamp))
                    print()
            if timestamp>maxTime:
                maxTime=timestamp

        taskfile.pending=False

        return (isDirty, list(tasklist), maxTime)

    def updateCompletion(self, value):
        print("Rendering: %s" % (value*100))

    def __not_used__syncProfileData(self, renderpath):

        if renderpath in self.loadedFiles.keys():
            taskfile = self.loadedFiles[renderpath]
            if taskfile.pending:
                # Avoid circular dependencies
                print("Warning: Circular dependency detected for %s. Skipping." % (renderpath))
                return
        else:
            taskfile = RenderChanFile(renderpath, self.modules, self.projects)
            if not os.path.exists(taskfile.getPath()):
                print("   No source file for %s. Skipping." % renderpath)
                return
            self.loadedFiles[taskfile.getPath()]=taskfile
            taskfile.pending=True  # we need this to avoid circular dependencies
            if taskfile.project!=None and taskfile.module!=None:
                self.loadedFiles[taskfile.getRenderPath()]=taskfile

        deps = taskfile.getDependencies()
        for path in deps:
            self.syncProfileData(path)

        if renderpath != taskfile.getPath():
            # TODO: Change parseRenderDependency() in the same way?
            checkFile=os.path.join(taskfile.getProjectRoot(),"render","project.conf","profile.conf")
            checkTime=float_trunc(os.path.getmtime(checkFile),1)

            source=taskfile.getProfileRenderPath()
            dest=taskfile.getRenderPath()
            sync(source,dest,checkTime)

            source=os.path.splitext(taskfile.getProfileRenderPath())[0]+"-alpha."+taskfile.getFormat()
            dest=os.path.splitext(taskfile.getRenderPath())[0]+"-alpha."+taskfile.getFormat()
            sync(source,dest,checkTime)

        taskfile.pending=False

    def job_render(self, taskfile, format, updateCompletion, start=None, end=None, compare_time=None):
        """

        :type taskfile: RenderChanFile
        """

        if start==None or end==None:
            output = taskfile.getProfileRenderPath(0,0)
            start=taskfile.getStartFrame()
            end=taskfile.getEndFrame()
        else:
            output = taskfile.getProfileRenderPath(start,end)

        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        # Check if we really need to re-render
        uptodate=False
        if compare_time:
            if os.path.exists(output+".done") and os.path.exists(output):
                if float_trunc(os.path.getmtime(output+".done"),1) >= compare_time:
                    # Hurray! No need to re-render that piece.
                    uptodate=True

        if not uptodate:

            # PROJECT LOCK
            # Make sure our rendertree is in sync with current profile
            locks=[]
            for project in self.projects.list.values():
                t=project.switchProfile(taskfile.project.getProfileDirName())
                locks.append(t)

            try:
                if os.path.isdir(output):
                    shutil.rmtree(output)

                if os.path.exists(output+".done"):
                    os.remove(output+".done")

                # TODO: Create file lock here

                params = taskfile.getParams()
                taskfile.module.render(taskfile.getPath(),
                               output,
                               int(start),
                               int(end),
                               format,
                               updateCompletion,
                               params)
                touch(output+".done",compare_time)
                if "extract_alpha" in params and params["extract_alpha"] == "1":
                    alpha_output = os.path.splitext(output)[0] + "-alpha" + os.path.splitext(output)[1]
                    touch(alpha_output+".done",compare_time)

                # TODO: Release file lock here

            except:
                for lock in locks:
                    lock.unlock()
                exit(1)

            # Releasing PROJECT LOCK
            for lock in locks:
                lock.unlock()

        else:
            print("  This chunk is already up to date. Skipping.")

        updateCompletion(1.0)

    def job_merge(self, taskfile, format, stereo, compare_time=None):
        """

        :type taskfile: RenderChanFile
        """

        # PROJECT LOCK
        # Make sure our rendertree is in sync with current profile
        locks=[]
        for project in self.projects.list.values():
            t=project.switchProfile(taskfile.project.getProfileDirName())
            locks.append(t)

        try:

            params = taskfile.getParams()

            suffix_list = [""]
            if "extract_alpha" in params and params["extract_alpha"] == "1":
                suffix_list.append("-alpha")

            for suffix in suffix_list:

                output = os.path.splitext(taskfile.getRenderPath())[0] + suffix + "." + format
                profile_output = os.path.splitext( taskfile.getProfileRenderPath() )[0] + suffix + "." + format
                profile_output_list = os.path.splitext(profile_output)[0] + ".txt"

                # We need to merge the rendered files into single one

                print("Merging: %s" % profile_output)

                # But first let's check if we really need to do that
                uptodate = False
                if os.path.exists(profile_output):
                    if os.path.exists(profile_output + ".done") and \
                                    float_trunc(os.path.getmtime(profile_output + ".done"), 1) >= compare_time:
                        # Hurray! No need to merge that piece.
                        uptodate = True
                    else:
                        if os.path.isdir(profile_output):
                            shutil.rmtree(profile_output)
                        else:
                            os.remove(profile_output)
                        if os.path.exists(profile_output + ".done"):
                            os.remove(profile_output + ".done")

                if not uptodate:

                    if taskfile.getPacketSize() > 0:

                        if os.path.exists(profile_output_list):

                            # Check if we really have all segments rendered correctly

                            f = open(profile_output_list, 'r')
                            segments=f.readlines()
                            f.close()
                            for i in range(len(segments)):
                                segments[i] = segments[i].strip()
                                segments[i] = segments[i][6:-1]

                                segment = segments[i]

                                if os.path.exists(segment+".done") and os.path.exists(segment):
                                    continue
                                print("ERROR: Not all segments were rendered. Aborting.")
                                exit(1)

                            if format == "avi":
                                subprocess.check_call(
                                    [self.ffmpeg_binary, "-y", "-f", "concat", "-i", profile_output_list, "-c", "copy", profile_output])
                            else:
                                # Merge all sequences into single directory
                                for line in segments:
                                    print(line)
                                    copytree(line, profile_output, hardlinks=True)

                            os.remove(profile_output_list)
                            touch(profile_output + ".done", float(compare_time))
                        else:
                            print("  This chunk is already merged. Skipping.")
                        #updateCompletion(0.5)

                    else:
                        segment = os.path.splitext( taskfile.getProfileRenderPath(0,0) )[0] + suffix + "." + format
                        if os.path.exists(segment+".done") and os.path.exists(segment):
                                os.rename(segment, profile_output)
                                touch(profile_output + ".done", float(compare_time))
                        else:
                                print("ERROR: Not all segments were rendered. Aborting.")
                                exit(1)

                # Add LST file
                if format in RenderChanModule.imageExtensions and os.path.isdir(profile_output):
                    lst_profile_path = os.path.splitext(profile_output)[0] + ".lst"
                    lst_path = os.path.splitext(output)[0] + ".lst"
                    f = open(lst_profile_path, 'w')
                    f.write("FPS %s\n" % params["fps"])
                    for filename in sorted(os.listdir(profile_output)):
                        if filename.endswith(format):
                            f.write("%s/%s\n" % ( os.path.basename(profile_output), filename ))
                    f.close()
                    sync(lst_profile_path, lst_path)
                    # Compatibility
                    if taskfile.project.version < 1:
                        lst_profile_path = os.path.join(profile_output, "file.lst")
                        lst_path = os.path.join(output, "file.lst")
                        f = open(lst_profile_path, 'w')
                        f.write("FPS %s\n" % params["fps"])
                        for filename in sorted(os.listdir(profile_output)):
                            if filename.endswith(format):
                                f.write("%s\n" % filename)
                        f.close()
                        sync(lst_profile_path, lst_path)

                sync(profile_output, output)

                #touch(output+".done",arguments["maxTime"])
                touch(output, float(compare_time))

        except:
            for lock in locks:
                lock.unlock()
            exit(1)

        # Releasing PROJECT LOCK
        for lock in locks:
            lock.unlock()

        #updateCompletion(1)

    def job_merge_stereo(self, taskfile, mode, format="mp4"):

        output = os.path.splitext(taskfile.getRenderPath())[0]+"-stereo-"+mode[0:1]+"."+format

        prev_mode = self.projects.stereo
        self.setStereoMode("left")
        input_left = taskfile.getProfileRenderPath()
        self.setStereoMode("right")
        input_right = taskfile.getProfileRenderPath()
        self.setStereoMode(prev_mode)

        print("Merging: %s" % output)

        # But first let's check if we really need to do that
        uptodate = False
        if os.path.exists(output):
            if os.path.exists(output + ".done") and \
                os.path.exists(input_left) and \
                os.path.exists(input_right) and \
                float_trunc(os.path.getmtime(output + ".done"), 1) >= float_trunc(os.path.getmtime(input_left), 1) and \
                float_trunc(os.path.getmtime(output + ".done"), 1) >= float_trunc(os.path.getmtime(input_right), 1):
                    # Hurray! No need to merge that piece.
                    uptodate = True
            else:
                if os.path.isdir(output):
                    shutil.rmtree(output)
                else:
                    os.remove(output)
                if os.path.exists(output + ".done"):
                    os.remove(output + ".done")

        if not uptodate:
            if mode[0:1]=='v':
                subprocess.check_call(
                        ["ffmpeg", "-y", "-i", input_left, "-i", input_right,
                         "-filter_complex", "[0:v]setpts=PTS-STARTPTS, pad=iw:ih*2[bg]; [1:v]setpts=PTS-STARTPTS[fg]; [bg][fg]overlay=0:h",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "1",
                         "-c:a", "libmp3lame", "-qscale:a", "0",
                         "-f", "mp4",
                         output])
            else:
                subprocess.check_call(
                        ["ffmpeg", "-y", "-i", input_left, "-i", input_right,
                         "-filter_complex", "[0:v]setpts=PTS-STARTPTS, pad=iw*2:ih[bg]; [1:v]setpts=PTS-STARTPTS[fg]; [bg][fg]overlay=w",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "1",
                         "-c:a", "libmp3lame", "-qscale:a", "0",
                         "-f", "mp4",
                         output])
            touch(output + ".done", os.path.getmtime(output))
        else:
            print("  This chunk is already merged. Skipping.")


    def job_snapshot(self, renderpath, snapshot_dir):

        if not os.path.exists(snapshot_dir):
            mkdirs(snapshot_dir)

        time_string = "%s" % ( time.strftime("%Y%m%d-%H%M%S") )
        filename = os.path.splitext(os.path.basename(renderpath))[0] + "-" + time_string + os.path.splitext(renderpath)[1]
        snapshot_path = os.path.join(snapshot_dir, filename)

        print()
        print("Creating snapshot to %s ..." % (filename))
        print()

        if os.path.isdir(snapshot_path):
            try:
                copytree(renderpath, snapshot_dir, hardlinks=True)
            except:
                copytree(renderpath, snapshot_dir, hardlinks=False)
        else:
            try:
                os.link(renderpath, snapshot_path)
            except:
                shutil.copy2(renderpath, snapshot_path)


    def decompose(self, start, end, packetSize, framesList=""):
        packetSize = int(packetSize)
        result=[]
        if len(framesList) != 0:
            frames = framesList.split(",")
            for frame in frames:
                if "-" in frame:
                    frameList = frame.split("-")
                    start = int(frameList[0])
                    end = int(frameList[1])

                    length = end - start + 1
                    fullPacketCount, lastPacketCount = divmod(length, packetSize)

                    if length < packetSize:
                        result.append((start, end))
                    else:
                        for i in range(fullPacketCount):
                            packetStart = start + i * packetSize
                            packetEnd = packetStart + packetSize - 1
                            result.append((packetStart, packetEnd))
                        if lastPacketCount:
                            packetStart = start + (i + 1) * packetSize
                            result.append((packetStart, end))
                else:
                    result.append((int(frame), int(frame)))
        else:
            start = int(start)
            end = int(end)

            length = end - start + 1
            fullPacketCount, lastPacketCount = divmod(length, packetSize)

            if length < packetSize:
                result.append((start, end))
            else:
                for i in range(fullPacketCount):
                    packetStart = start + i * packetSize
                    packetEnd = packetStart + packetSize - 1
                    result.append((packetStart, packetEnd))
                if lastPacketCount:
                    packetStart = start + (i + 1) * packetSize
                    result.append((packetStart, end))

        return result

    def loadFile(self, filename):
        return RenderChanFile(filename, self.modules, self.projects)

class Attribution():
    def __init__(self, filename, moduleManager=None, projectManager=None):
        self.modules = moduleManager
        if self.modules==None:
            self.modules = RenderChanModuleManager()

        self.projects = projectManager
        if self.projects==None:
            self.projects = RenderChanProjectManager()

        self.licenses = {}
        self.freesound_items = {}  # author:[title1,title2,...]

        taskfile = RenderChanFile(filename, self.modules, self.projects)
        self.parse(taskfile)

    def parse(self, taskfile):

        for dep in taskfile.getDependencies():
            t = RenderChanFile(dep, self.modules, self.projects)
            metadata = t.getMetadata()
            if "freesound" in metadata.sources:
                for author in metadata.authors:
                    if author not in self.freesound_items:
                        self.freesound_items[author]=[]
                    if not metadata.title in self.freesound_items[author]:
                        self.freesound_items[author].append(metadata.title)
            if not metadata.license == None:
                if metadata.license not in self.licenses:
                    self.licenses[metadata.license]=[]
                self.licenses[metadata.license].append(t.getPath())

            self.parse(t)

    def output(self):
        print()
        print("== Sound FX ==")
        print("This video uses these sounds from freesound:")
        print()
        for author in self.freesound_items.keys():
            print('"'+'", "'.join(self.freesound_items[author])+'" by '+author)
        print()
        print("== Licenses ==")
        print(", ".join(self.licenses.keys()))
        print()



