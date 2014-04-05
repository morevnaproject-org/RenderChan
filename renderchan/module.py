__author__ = 'Konstantin Dmitriev'

from importlib import import_module
import os

class RenderChanModuleManager():
    def __init__(self):
        self.list = {}

    def load(self, name):
        try:
            #module = __import__(moduleName, fromlist=[cls])
            module = import_module("renderchan.contrib."+name)
        except ImportError, error:
            traceback.print_exc()
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

    def get(self, name):
        if not self.list.has_key(name):
            self.load(name)

        return self.list[name]

class RenderChanModule():
    def __init__(self):
        self.conf = {}
        self.conf['binary']="foo"

        self.active=False

        self.checkRequirements()

    def __is_exe(self, fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    def __which(self, program):
        fpath, fname = os.path.split(program)
        if fpath:
            if self.__is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if self.__is_exe(exe_file):
                    return exe_file

        return None

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
        if self.__which(self.conf['binary']) == None:
            self.active=False
        else:
            self.active=True
        return self.active

    def getInputFormats(self):
        return []

    def getOutputFormats(self):
        return []

    def getDependencies(self, filename):
        return []

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format):
        pass