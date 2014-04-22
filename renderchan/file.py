__author__ = 'Konstantin Dmitriev'

import os.path
from renderchan.project import loadRenderConfig

class RenderChanFile():
    def __init__(self, path, modules, projects):
        self.projectPath = self._findProjectRoot(path)
        self.localPath = self._findLocalPath(path)
        if self.projectPath!='':
            self.project=projects.get(self.projectPath)
        else:
            print "Warning: File %s doesn't belong to any project." % (path)

        self.module = modules.getByExtension(os.path.splitext(path)[1][1:])
        self.dependencies=[]
        self.startFrame=-1
        self.endFrame=-1
        self.params={}

        if self.module:
            info=self.module.analyze(self.getPath())
            if "dependencies" in info.keys():
                self.dependencies=list(set(info["dependencies"]))
            if "startFrame" in info.keys():
                self.startFrame=int(info["startFrame"])
            if "endFrame" in info.keys():
                self.endFrame=int(info["endFrame"])

            # Rendering params
            if os.path.exists(self.getPath()+".conf"):
                loadRenderConfig(self.getPath()+".conf", self.params)
            # Check if format is supported by the module
            if not self.getParam("format") in self.module.getOutputFormats():
                self.params["format"]=self.module.getOutputFormats()[0]


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
            while localpath.startswith('/'):
                localpath=localpath[1:]
            return localpath
        else:
            return path

    def getProjectRoot(self):
        return self.projectPath

    def getPath(self):
        return os.path.join(self.projectPath, self.localPath)

    def getRenderPath(self):
        path=os.path.join(self.projectPath, "render", self.localPath+"."+self.getParam("format") )
        #if self.getOutputFormat() in RenderChanFile.imageExtensions:
        #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
        return path

    def getProfileRenderPath(self):
        profile = self.project.getProfileName()
        path=os.path.join(self.projectPath, "render", "project.conf", profile, self.localPath+"."+self.getParam("format") )
        #if self.getOutputFormat() in RenderChanFile.imageExtensions:
        #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
        return path

    def getParams(self):
        params=self.project.getParams().copy()

        for key in self.params.keys():
            params[key]=self.params[key]

        return params

    def getParam(self, param):
        if self.params.has_key(param):
            return self.params[param]
        elif self.project.getParams().has_key(param):
            return self.project.getParams()[param]
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