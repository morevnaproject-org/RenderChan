__author__ = 'Konstantin Dmitriev'

import os.path
import ConfigParser
from renderchan.utils import mkdirs
from renderchan.cache import RenderChanCache

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
        self.confPath=confFile
        self.cache=RenderChanCache(os.path.join(self.path, "render", "cache.sqlite"))
        # List of modules used in the project
        self.dependencies=[]

        self.defaults = {
            'width':'480',
            'height':'270',
            'format':'png',
            'audio_rate':'48000',
            'fps':'24',
        }


        # Project configuration

        self.config={}
        loadRenderConfig(confFile, self.config)

        # Store project configuration - we need that to track configuration changes

        if not os.path.isdir(os.path.join(self.path,"render","project.conf",self.getProfileName())):
            mkdirs(os.path.join(self.path,"render","project.conf",self.getProfileName()))

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

        # Store current profile
        filename=os.path.join(self.path,"render","project.conf","profile.conf")
        prev_profile = ""
        if os.path.exists(filename):
            # Read previous profile
            f=open(filename)
            prev_profile = f.readlines()[0].strip()
            f.close()
        if prev_profile!=self.getProfileName():
            f = open(filename,'w')
            f.write(self.getProfileName()+"\n")
            f.close()


        # Load list of frozen files
        self.frozenPaths=[]
        self.loadFrozenPaths()

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

        newconfig={}
        for key in module.extraParams:
            if self.config.has_key(module.getName()+"."+key):
                newconfig[key]=self.config[module.getName()+"."+key]
            elif self.config.has_key(key):
                newconfig[key]=self.config[key]
            else:
                newconfig[key]=module.extraParams[key]

        if newconfig!=oldconfig:
            config = ConfigParser.SafeConfigParser()
            config.add_section('main')
            for key in newconfig.keys():
                if newconfig[key]!=None:
                    config.set('main', key, str(newconfig[key]))
            with open(filename, 'wb') as configfile:
                config.write(configfile)

    def getConfig(self, key):
        if key in self.config.keys():
            return self.config[key]
        elif key in self.defaults.keys():
            return self.defaults[key]
        else:
            return None

    def getProfileName(self):
        return "%sx%s" % (self.config["width"], self.config["height"])

    def loadFrozenPaths(self):
        filename=os.path.join(self.path,"render","project.conf","frozen.list")
        if os.path.exists(filename):
            f=open(filename)
            for line in f.readlines():
                line = line.strip()
                if not line in self.frozenPaths:
                    self.frozenPaths.append(line)
            f.close()

    def saveFrozenPaths(self):
        filename=os.path.join(self.path,"render","project.conf","frozen.list")
        f = open(filename, 'w')
        for line in self.frozenPaths:
            f.write(line+"\n")
        f.close()

    def isFrozen(self, path):
        for frozenPath in self.frozenPaths:
            if ("/"+path).startswith(frozenPath):
                return True
        return False

    def setFrozen(self, path, value):

        # FIXME: In fact, we have to use a more complex algorithm for recursive paths

        if os.path.isdir(os.path.join(self.path, path)) and not path.endswith('/'):
            path = path+'/'
        path="/"+path
        if value==True:
            if not path in self.frozenPaths:
                self.frozenPaths.append(path)
        else:
            if path in self.frozenPaths:
                self.frozenPaths.remove(path)