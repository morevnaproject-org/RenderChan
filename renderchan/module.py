__author__ = 'Konstantin Dmitriev'

from importlib import import_module

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
        pass

    def checkRequirements(self):
        return True

    def getInputFormats(self):
        return []

    def getOutputFormats(self):
        return []

    def getDependencies(self, filename):
        return []

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format):
        pass