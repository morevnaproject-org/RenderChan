__author__ = 'Konstantin Dmitriev'

import os.path
from renderchan.project import loadRenderConfig
from renderchan.utils import float_trunc

class RenderChanFile():
    globalParams=["width","height","fps",]
    def __init__(self, path, modules, projects):
        self.projectPath = self._findProjectRoot(path)
        self.localPath = self._findLocalPath(path)
        self.project=None
        if self.projectPath!='':
            self.project=projects.get(self.projectPath)
        else:
            print "Warning: File %s doesn't belong to any project." % (path)

        # Associated tasks
        self.taskRender=None
        self.taskPost=None

        # Shows if we already had attempt to submit this file to the graph and stores the result
        self.isDirty=None
        # Shows if this file is waiting for dirty status resolution
        self.pending=False

        # File modification time
        self.mtime=None

        self.module = modules.getByExtension(os.path.splitext(self.localPath)[1][1:])
        self.dependencies=[]
        self.startFrame=-1
        self.endFrame=-1

        self.config={}

        if self.module:

            if self.project:
                self.project.registerModule(self.module)

            if os.path.exists(self.getPath()):
                info=self.module.analyze(self.getPath())
                if "dependencies" in info.keys():

                    projectconf=os.path.join(self.project.path,'render','project.conf',self.project.getProfileName(),'core.conf')
                    if os.path.exists(projectconf):
                        info["dependencies"].append(projectconf)

                    moduleconf=os.path.join(self.project.path,'render','project.conf',self.project.getProfileName(),self.module.getName()+'.conf')
                    if os.path.exists(moduleconf):
                        info["dependencies"].append(moduleconf)

                    # This is commented, because it shouldn't influence maxTime
                    #profileconf=os.path.join(self.project.path,"render","project.conf","profile.conf")
                    #if os.path.exists(profileconf):
                    #    info["dependencies"].append(profileconf)

                    fileconf=self.getPath()+'.conf'
                    if os.path.exists(fileconf):
                        info["dependencies"].append(fileconf)

                    self.dependencies=list(set(info["dependencies"]))

                if "startFrame" in info.keys():
                    self.startFrame=int(info["startFrame"])
                if "endFrame" in info.keys():
                    self.endFrame=int(info["endFrame"])

                # Rendering params
                if os.path.exists(self.getPath()+".conf"):
                    loadRenderConfig(self.getPath()+".conf", self.config)
            else:
                print "Warning: No source file found for %s" % path


    def _findProjectRoot(self, path):
        while True:
            if os.path.exists(os.path.join(path,"project.conf")) and not os.path.isdir(os.path.join(path,"project.conf")):
                return path
            if os.path.exists(os.path.join(path,"remake.conf")) and not os.path.isdir(os.path.join(path,"remake.conf")):
                return path
            if os.path.dirname(path) == path:
                return ""
            path = os.path.dirname(path)

    def _findLocalPath(self, path):
        if self.projectPath!="" and path.startswith(self.projectPath):
            localpath=path[len(self.projectPath):]

            # cleanup
            while localpath.startswith('/'):
                localpath=localpath[1:]

            if localpath.startswith("render") and not localpath.startswith(os.path.join("render","project.conf")):
                localpath=localpath[6:]
                localpath=os.path.splitext(localpath)[0]

            # cleanup
            while localpath.startswith('/'):
                localpath=localpath[1:]

            return localpath
        else:
            return path

    def getTime(self):
        if self.mtime is None:
            self.mtime=float_trunc(os.path.getmtime(self.getPath()),1)
        return self.mtime


    def getProjectRoot(self):
        return self.projectPath

    def getPath(self):
        return os.path.join(self.projectPath, self.localPath)

    def getRenderPath(self):
        if self.project:
            path=os.path.join(self.projectPath, "render", self.localPath+"."+self.getFormat() )
            #if self.getOutputFormat() in RenderChanFile.imageExtensions:
            #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
            return path
        else:
            return None

    def getProfileRenderPath(self):
        profile = self.project.getProfileName()
        path=os.path.join(self.projectPath, "render", "project.conf", profile, self.localPath+"."+self.getFormat() )
        #if self.getOutputFormat() in RenderChanFile.imageExtensions:
        #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
        return path

    def getPacketSize(self):

        size=-1

        if self.config.has_key("single") and self.config["single"]!=None:
            return 0

        # Let conf files override packet size
        if self.config.has_key(self.module.getName()+"_packet_size"):
            size=int(self.config[self.module.getName()+"_packet_size"])
        elif self.config.has_key("packet_size"):
            size=int(self.config["packet_size"])
        elif self.project.config.has_key(self.module.getName()+"_packet_size"):
            size=int(self.project.config[self.module.getName()+"_packet_size"])
        elif self.project.config.has_key("packet_size"):
            size=int(self.project.config["packet_size"])

        if size!=-1:

            length = self.endFrame - self.startFrame + 1
            if length<=size:
                # We don't need to split anything
                return 0

            return size
        else:
            return self.module.getPacketSize()

    def getFormat(self):
        # Check if format is supported by the module
        format=self.getConfig("format")
        if not format in self.module.getOutputFormats():
            format=self.module.getOutputFormats()[0]
        return format

    def getParams(self):
        params={}

        # Basic project values
        for key in self.project.defaults.keys():
            params[key]=self.getConfig(key)

        # Module-specific configuration
        for key in self.module.extraParams.keys():
            if key in self.config.keys():
                params[key]=self.config[key]
            elif key in self.project.config.keys():
                params[key]=self.project.config[key]
            else:
                params[key]=self.module.extraParams[key]

        # File-specific configuration
        params["filename"]=self.getPath()
        params["output"]=self.getRenderPath()
        params["profile_output"]=self.getProfileRenderPath()
        params["module"]=self.module.getName()
        params["packetSize"]=self.getPacketSize()
        params["start"]=self.getStartFrame()
        params["end"]=self.getEndFrame()
        #params["dependencies"]=self.getDependencies()
        params["projectVersion"]=self.project.version
        params["format"]=self.getFormat()

        return params

    def getConfig(self, key):
        if self.config.has_key(key):
            return self.config[key]
        elif self.project:
            return self.project.getConfig(key)
        else:
            return None

    def getDependencies(self):
        return self.dependencies

    def getStartFrame(self):
        return self.startFrame

    def getEndFrame(self):
        return self.endFrame

    def isValid(self):
        if self.projectPath != "":
            return True
        else:
            return False

    def isFrozen(self):
        if self.project:
            return self.project.isFrozen(self.localPath)
        else:
            return False

    def setFrozen(self, value):
        if self.project:
            self.project.setFrozen(self.localPath, value)
        else:
            if value:
                print "ERROR: Cannot freeze file which is not a part of any project."
