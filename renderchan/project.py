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
        self.path=os.path.dirname(confFile)
        self.dependencies=[]

        self.defaults = {
            'width':'480',
            'height':'270',
            'format':'png',
            'audio_rate':'48000',
            'fps':'24',
        }

        self.config={}
        loadRenderConfig(confFile, self.config)

        # Store project configuration - we need that for configuration changes detection

        filename=os.path.join(self.path,"render","project.conf",self.getProfileName(),"core.conf")
        oldconfig={}
        if os.path.exists(filename):
            cp = ConfigParser.SafeConfigParser()
            cp.read(filename)

            for key in cp.options('main'):
                oldconfig[key]=cp.get('main', key)

        newconfig=self.defaults.copy()
        for key in self.config.keys():
            if key in self.defaults.keys():
                newconfig[key]=self.config[key]

        if newconfig!=oldconfig:
            config = ConfigParser.SafeConfigParser()
            config.add_section('main')
            for key in newconfig.keys():
                config.set('main', key, newconfig[key])
            with open(filename, 'wb') as configfile:
                config.write(configfile)

    def registerModule(self, module):
        name=module.getName()
        if name in self.dependencies:
            # Module already registered
            return

        self.dependencies.append(name)

        # Store module configuration - we need that for configuration changes detection
        filename=os.path.join(self.path,"render","project.conf",self.getProfileName(),name+".conf")
        oldconfig={}
        if os.path.exists(filename):
            cp = ConfigParser.SafeConfigParser()
            cp.read(filename)

            for key in cp.options('main'):
                oldconfig[key]=cp.get('main', key)

        newconfig=module.extraParams.copy()
        for key in self.config.keys():
            if key in module.extraParams.keys():
                newconfig[key]=self.config[key]

        if newconfig!=oldconfig:
            if newconfig!=oldconfig:
                config = ConfigParser.SafeConfigParser()
                config.add_section('main')
                for key in newconfig.keys():
                    config.set('main', key, newconfig[key])
                with open(filename, 'wb') as configfile:
                    config.write(configfile)

    def getConfig(self, key):
        if key in self.config.keys():
            return self.config[key]
        elif key in self.defaults.keys():
            return self.defaults[key]
        else:
            print "Warning: No such key (%s)" % (key)
            return ""

    def getProfileName(self):
        return "%sx%s" % (self.config["width"], self.config["height"])