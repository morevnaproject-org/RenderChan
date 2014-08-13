__author__ = 'Konstantin Dmitriev'

import os.path
from renderchan.project import loadRenderConfig
from renderchan.module import RenderChanModule
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
                print ". Analysing file: %s" % os.path.relpath(path)
                info=self.project.cache.getInfo(self.localPath)
                if info and info["timestamp"]>=self.getTime():
                    print ". . Cache found"
                    self.startFrame=int(info["startFrame"])
                    self.endFrame=int(info["endFrame"])
                    self.dependencies=self.project.cache.getDependencies(self.localPath)
                else:
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

                    # Write cache
                    self.project.cache.write(self.localPath, self.getTime(), self.startFrame, self.endFrame, self.dependencies)

                # Rendering params
                if os.path.exists(self.getPath()+".conf"):
                    loadRenderConfig(self.getPath()+".conf", self.config)

                # Format defined by renderpath should take precedence
                if path != self.getPath():
                    ext=os.path.splitext(path)[1][1:]
                    if ext == "lst":
                        if not self.getFormat() in RenderChanModule.imageExtensions:
                            ext=RenderChanModule.imageExtensions[0]
                    self.config["format"]=ext

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

                # cleanup
                while localpath.startswith('/'):
                    localpath=localpath[1:]

                # now, let's have some heuristics...

                # /projectroot/path/file.ext.png ?
                localpath=os.path.splitext(localpath)[0]
                if os.path.exists(os.path.join(self.projectPath,localpath)):
                    return localpath

                # /projectroot/path/file.ext-alpha.png ?
                if localpath.endswith("-alpha"):
                    localpath_alpha=localpath[:-6]
                    if os.path.exists(os.path.join(self.projectPath, localpath_alpha)):
                        return localpath_alpha

                # /projectroot/path/file.ext.png/file-0000x.png ?
                localpath2=os.path.splitext(os.path.dirname(localpath))[0]
                if os.path.exists(os.path.join(self.projectPath,localpath2)) and not os.path.isdir(os.path.join(self.projectPath,localpath2)):
                    return localpath2

                # /projectroot/path/file.ext-alpha.png/file-0000x.png ?
                if localpath2.endswith("-alpha"):
                    localpath_alpha=localpath2[:-6]
                    if os.path.exists(os.path.join(self.projectPath, localpath_alpha)) and not os.path.isdir(os.path.join(self.projectPath,localpath_alpha)):
                        return localpath_alpha

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

        if self.config.has_key("single") and self.config["single"]!="None":
            return 0

        # Let conf files override packet size
        if self.config.has_key("packet_size"):
            size=int(self.config["packet_size"])
        elif self.project.config.has_key(self.module.getName()+".packet_size"):
            size=int(self.project.config[self.module.getName()+".packet_size"])
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
        key="format"
        if self.config.has_key(key):
            format=self.config[key]
        elif self.project:
            if self.module.getName()+"."+key in self.project.config.keys():
                format=self.project.getConfig(self.module.getName()+"."+key)
            else:
                format=self.project.getConfig(key)
        # Check if format is supported by the module
        if not format in self.module.getOutputFormats():
            format=self.module.getOutputFormats()[0]
        return format

    def getParams(self):
        params={}

        # Basic project values
        for key in self.project.defaults.keys():
            if self.config.has_key(key):
                params[key]=self.config[key]
            elif self.project:
                if self.module.getName()+"."+key in self.project.config.keys():
                    params[key]=self.project.getConfig(self.module.getName()+"."+key)
                else:
                    params[key]=self.project.getConfig(key)

        # Module-specific configuration
        for key in self.module.extraParams.keys():
            if key in self.config.keys():
                params[key]=self.config[key]
            elif self.module.getName()+"."+key in self.project.config.keys():
                params[key]=self.project.config[self.module.getName()+"."+key]
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

        return params

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
