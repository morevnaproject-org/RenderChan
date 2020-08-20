

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random

class RenderChanVorbisModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']=self.findBinary("oggdec")
        self.conf['sox_binary']=self.findBinary("sox")
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["ogg"]

    def getOutputFormats(self):
        return ["wav"]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable!" % (self.getName(), self.conf['binary']))
            print("    Please install vorbis-tools package.")
            return False
        if which(self.conf['sox_binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable!" % (self.getName(), self.conf['sox_binary']))
            print("    Please install sox package.")
            return False
        self.active=True
        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        random_string = "%08d" % (random.randint(0,99999999))
        tmpfile=outputPath+"."+random_string

        # TODO: Progress callback

        commandline=[self.conf['binary'], filename, "-o",tmpfile]
        subprocess.check_call(commandline)

        commandline=[self.conf['sox_binary'], tmpfile, outputPath, "rate", "-v", extraParams["audio_rate"]]
        subprocess.check_call(commandline)

        os.remove(tmpfile)

        updateCompletion(1.0)
