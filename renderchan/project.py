__author__ = 'Konstantin Dmitriev'

import os.path
import ConfigParser

def loadRenderConfig(filename, targetDict):

    config = ConfigParser.SafeConfigParser()
    config.readfp(FakeSecHead(open(filename)))

    for key in config.options('default'):
        targetDict[key]=config.get('default', key)

    return True

class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[default]\n'
    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()

class RenderChanProjectManager():
    def __init__(self):
        self.list = {}

    def load(self, path):
        confFile = os.path.join(path,"project.conf")
        if not os.path.exists(confFile):
            # Look for remake.conf
            confFile = os.path.join(path,"remake.conf")
        if not os.path.exists(confFile):
            raise Exception

        # TODO: Load project cache here
        # ...

        self.list[path]=RenderChanProject(confFile)

    def get(self, path):
        if not self.list.has_key(path):
            self.load(path)

        return self.list[path]

class RenderChanProject():
    def __init__(self, confFile):
        if os.path.basename(confFile) == "remake.conf":
            self.version = 0
        else:
            self.version = 1

        self.params = {
            'width':'480',
            'height':'270',
            'format':'png',
            'audio_rate':'48000',
            'fps':'24',
        }
        loadRenderConfig(confFile, self.params)
        pass

    def getFormat(self):
        return self.params["format"]

    def getParams(self):
        return self.params

    def getProfileName(self):
        return "%sx%s" % (self.params["width"], self.params["height"])