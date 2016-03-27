

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random

class RenderChanFfmpegModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\ffmpeg\\bin\\ffmpeg.exe")
        else:
            self.conf['binary']="ffmpeg"
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["mov", "avi", "mpg"]

    def getOutputFormats(self):
        return ["png"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        # TODO: Progress callback

        commandline=[self.conf['binary'], "-i", filename, os.path.join(outputPath,"output_%04d.png")]
        subprocess.check_call(commandline)

        updateCompletion(1.0)