

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random

class RenderChanFfmpegModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']=self.findBinary("ffmpeg")
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["mov", "avi", "mpg", "mp4"]

    def getOutputFormats(self):
        return ["png"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        if not os.path.exists(outputPath):
            os.mkdir(outputPath)

        # TODO: Progress callback

        commandline=[self.conf['binary'], "-i", filename, os.path.join(outputPath,"output_%04d.png")]
        subprocess.check_call(commandline)

        updateCompletion(1.0)
