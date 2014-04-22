__author__ = 'Konstantin Dmitriev'

from importlib import import_module
from renderchan.utils import which
import os
import inspect

class RenderChanModuleManager():
    def __init__(self):
        self.list = {}

    def load(self, name):
        try:
            #module = __import__(moduleName, fromlist=[cls])
            module = import_module("renderchan.contrib."+name)
        except ImportError, error:
            raise ImportError("No module '%s' on PYTHONPATH:\n%s. (%s)" % (moduleName, "\n".join(sys.path), error))

        cls = name.capitalize()
        try:
            moduleClass = getattr(module, "RenderChan"+cls+"Module")
        except AttributeError:
            raise ImportError("No such job type '%s' defined in module '%s'." % (cls, name))

        motherClass = RenderChanModule
        if not issubclass(moduleClass, motherClass):
            motherClassName = "%s.%s" % (motherClass.__module__, motherClass.__name__)
            raise ImportError("%s (loaded as '%s') is not a valid %s." % (moduleClass, name, motherClassName))

        self.list[name] = moduleClass()
        self.list[name].checkRequirements()

    def loadAll(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        modulesdir = os.path.join(dir, "contrib")
        files = [ f for f in os.listdir(modulesdir) if os.path.isfile(os.path.join(modulesdir,f)) ]
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext==".py" and filename!='__init__':
                self.load(filename)

    def get(self, name):
        if not self.list.has_key(name):
            self.load(name)

        return self.list[name]

    def getByExtension(self, ext):
        for key,item in self.list.items():
            if ext in item.getInputFormats():
                if item.active:
                    return item
        return None

class RenderChanModule():
    imageExtensions = ['png','exr']
    def __init__(self):
        self.conf = {}
        self.conf['binary']="foo"
        self.conf["packetSize"]=20
        self.conf["compatVersion"]=1
        self.conf["maxNbCores"]=0

        # Extra params - additional rendering parameters. supplied through the project.conf and
        # file-specific .conf files.
        self.extra_params={}

        self.active=False

    def getName(self):
        return os.path.splitext(os.path.basename(inspect.getfile(self.__class__)))[0]

    def getConfiguration(self):
        return self.conf

    def setConfiguration(self, conf):
        for key,value in conf.items():
            if not self.conf.has_key(key):
                print "Module %s doesn't accept configuration key '%s': No such entry." % (self.__class__.__name__, key)
                continue
            if not type(self.conf[key]).__name__ == type(conf[key]).__name__:
                print "Module %s doesn't accept configuration value for key '%s': Wrong type." % (self.__class__.__name__, key)
                continue
            self.conf[key] = conf[key]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
        else:
            self.active=True
        return self.active

    def getInputFormats(self):
        return []

    def getOutputFormats(self):
        return []

    def analyze(self, filename):
        return {}

    def getPacketSize(self):
        return self.conf["packetSize"]

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format, fps, audioRate, updateCompletion, extraParams={}):
        pass