

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import run_ffmpeg_progress
import os

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

        commandline=[self.conf['binary'], "-i", filename, os.path.join(outputPath,"output_%04d.png")]
        run_ffmpeg_progress(commandline, lambda c, t: updateCompletion(min(float(c)/t, 1.0)), endFrame-startFrame+1)

        updateCompletion(1.0)
