__author__ = 'Konstantin Dmitriev'

import os.path

class RenderChanFile():
    def __init__(self, path):
        self.targetFormat = ""
        self.projectPath = self._findProjectRoot(path)
        #self.project = projects.get(self.projectPath)
        self.localPath = self._findSourcePath(path)
        self.moduleName = ""

        # Load Module


    def _findProjectRoot(self, path):
        while True:
            if os.path.exists(os.path.join(path,"project.conf")) or os.path.exists(os.path.join(path,"remake.conf")):
                return path
            if os.path.dirname(path) == path:
                return ""
            path = os.path.dirname(path)

    def _findSourcePath(self, path):
        return ""

    def getProjectRoot(self):
        return self.projectPath

    def getPath(self):
        return os.path.join(self.projectPath, self.localPath)

    def getRenderPath(self):
        return os.path.join(self.projectPath, "render", self.localPath+"."+self.targetFormat )

    def getProfileRenderPath(self):
        profile = "480x270"
        return os.path.join(self.projectPath, "render", "project.conf", profile, self.localPath+"."+self.targetFormat )

    def getDependencies(self):
        return []

    def isValid(self):
        if self.projectPath != "":
            return True
        else:
            return False