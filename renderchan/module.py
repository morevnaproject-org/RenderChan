__author__ = 'Konstantin Dmitriev'

from importlib import import_module
from renderchan.utils import which
import os, sys
import inspect
import configparser

class RenderChanModuleManager():
    def __init__(self):
        self.list = {}
        self.loadAll()

    def load(self, name):
        try:
            #module = __import__(moduleName, fromlist=[cls])
            module = import_module("renderchan.contrib."+name)
        except ImportError as error:
            raise ImportError("No module '%s' on PYTHONPATH:\n%s. (%s)" % (name, "\n".join(sys.path), error))

        cls = name.capitalize()
        try:
            moduleClass = getattr(module, "RenderChan"+cls+"Module")
        except AttributeError:
            raise ImportError("No such job type '%s' defined in module '%s'." % (cls, name))

        motherClass = RenderChanModule
        if not issubclass(moduleClass, motherClass):
            motherClassName = "%s.%s" % (motherClass.__module__, motherClass.__name__)
            raise ImportError("%s (loaded as '%s') is not a valid %s." % (moduleClass, name, motherClassName))

        module = moduleClass()
        module.loadConfiguration()
        if not module.checkRequirements():
            print("Warning: Unable load module - %s." % (name))
        self.list[name]=module

    def loadAll(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        modulesdir = os.path.join(dir, "contrib")
        files = [ f for f in os.listdir(modulesdir) if os.path.isfile(os.path.join(modulesdir,f)) ]
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext==".py" and filename!='__init__':
                self.load(filename)

    def get(self, name):
        if name not in self.list:
            self.load(name)

        return self.list[name]

    def getByExtension(self, ext):
        for key,item in list(self.list.items()):
            if ext in item.getInputFormats():
                if item.active:
                    return item
        return None

class RenderChanModule():
    imageExtensions = ['png','exr']
    def __init__(self):
        self.conf = {}
        self.conf['binary']=""
        #TODO: "packetSize" should be renamed to "extra_params" and merged with self.extraParams?
        self.conf["packetSize"]=20
        self.conf["compatVersion"]=1
        self.conf["maxNbCores"]=0

        # Extra params - additional rendering parameters. supplied through the project.conf and
        # file-specific .conf files.
        #TODO: ExtraParams should be registered in a special way
        #TODO:    So, if a module registers its own extra param we should now it isn't already registered as global extraParam.
        self.extraParams={}
        #   'use_own_dimensions' - Don't use project dimensions, use image dimensions defined it the source file
        #   'proxy_scale' - Apply scale factor to resulting image. Valid only if 'use_own_dimensions' == 1.
        #  Those options are applied in RenderChanFile.getParams() - file.py.
        self.extraParams['use_own_dimensions']='0'
        self.extraParams['proxy_scale']='1.0'

        self.active=False

    def getName(self):
        return os.path.splitext(os.path.basename(inspect.getfile(self.__class__)))[0]

    def loadConfiguration(self):

        filename = os.path.join(os.path.expanduser("~"), ".config", "renderchan", "modules.conf")

        if os.path.exists(filename):

            config = configparser.ConfigParser()
            config.read(filename)

            if config.has_section(self.getName()):
                for key in self.conf:
                    if config.has_option(self.getName(),key):
                        self.conf[key]=config.get(self.getName(),key)

    def getConfiguration(self):
        return self.conf

    def setConfiguration(self, conf):
        for key,value in list(conf.items()):
            if key not in self.conf:
                print("Module %s doesn't accept configuration key '%s': No such entry." % (self.__class__.__name__, key))
                continue
            if not type(self.conf[key]).__name__ == type(conf[key]).__name__:
                print("Module %s doesn't accept configuration value for key '%s': Wrong type." % (self.__class__.__name__, key))
                continue
            self.conf[key] = conf[key]

    def checkRequirements(self):
        if self.conf['binary']:
            binary_path = which(self.conf['binary'])
            if binary_path == None:
                self.active=False
                print("Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf["binary"]))
                print("    Please install %s package." % (self.getName()))
            else:
                # Workaround because some applications (gimp) cannot be executed via symlink
                self.conf['binary'] = binary_path
                self.active=True
        else:
            self.active=False
        return self.active

    def getInputFormats(self):
        return []

    def getOutputFormats(self):
        return []

    def analyze(self, filename):
        #TODO: Return a special structure object (RenderChanFileInfo) instead of ordinary dictionary
        #TODO:     RenderChanFileInfo = {'dependencies': [], 'start': -1, 'end': -1, 'width':-1, 'height':-1}
        return {}

    def getPacketSize(self):
        return self.conf["packetSize"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):
        pass