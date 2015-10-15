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
            self.conf['zip_binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\zip\\bin\\unzip.exe")
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\krita\\bin\\krita.exe")
        else:
            self.conf['zip_binary']="unzip"
            self.conf['binary']="krita"

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

        deps_count=0
        for item in extraParams["dependencies"]:
            if not item.endswith(".conf"):
                deps_count+=1
                break

        if deps_count==0:

            random_string = "%08d" % (random.randint(0,99999999))
            tmpPath=outputPath+"."+random_string
            mkdirs(tmpPath)

            commandline=[self.conf['zip_binary'], "-j", "-d", tmpPath, filename, "mergedimage.png"]
            subprocess.check_call(commandline)

            #TODO: Compress image?
            os.rename(os.path.join(tmpPath,"mergedimage.png"), outputPath)

            shutil.rmtree(tmpPath)

        else:
            #TODO: PNG transperency settings at ~/.kde/share/config/kritarc ? use KDEHOME env ?
            commandline=[self.conf['binary'], "--export", filename, "--export-filename", outputPath]
            subprocess.check_call(commandline)

        updateCompletion(1)
