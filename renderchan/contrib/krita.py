__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import subprocess
import random
import os
import shutil
from renderchan.utils import mkdirs

class RenderChanKritaModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\zip\\bin\\unzip.exe")
        else:
            self.conf['binary']="unzip"
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["kra"]

    def getOutputFormats(self):
        return ["png"]

    def analyze(self, filename):
        #TODO: Consider file layers as dependencies
        return {}

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        random_string = "%08d" % (random.randint(0,99999999))
        tmpPath=outputPath+"."+random_string
        mkdirs(tmpPath)

        commandline=[self.conf['binary'], "-j", "-d", tmpPath, filename, "mergedimage.png"]
        subprocess.check_call(commandline)

        os.rename(os.path.join(tmpPath,"mergedimage.png"), outputPath)

        shutil.rmtree(tmpPath)

        updateCompletion(1)
