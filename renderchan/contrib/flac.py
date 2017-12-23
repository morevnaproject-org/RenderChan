

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random

class RenderChanFlacModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\packages\\flac\\win32\\flac.exe")
            self.conf['sox_binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\packages\\sox\\sox.exe")
        else:
            self.conf['binary']="flac"
            self.conf['sox_binary']="sox"
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["flac"]

    def getOutputFormats(self):
        return ["wav"]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf['binary']))
            print("    Please install flac package.")
            return False
        if which(self.conf['sox_binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable!" % (self.getName(), self.conf['sox_binary']))
            print("    Please install sox package.")
            return False
        self.active=True
        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        random_string = "%08d" % (random.randint(0,99999999))
        tmpfile=outputPath+"."+random_string

        # TODO: Progress callback

        commandline=[self.conf['binary'], "-d", filename, "-o", tmpfile]
        subprocess.check_call(commandline)

        commandline=[self.conf['sox_binary'], tmpfile, outputPath, "rate", "-v", extraParams["audio_rate"]]
        subprocess.check_call(commandline)

        os.remove(tmpfile)

        updateCompletion(1.0)
