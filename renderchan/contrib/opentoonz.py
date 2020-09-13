

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random

class RenderChanOpentoonzModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']=self.findBinary("tcomposer")
        self.conf["packetSize"]=0


    def getInputFormats(self):
        return ["tnz"]

    def getOutputFormats(self):
        return ["tiff" , "png"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        if not os.path.exists(outputPath):
            os.mkdir(outputPath)

        # TODO: Progress callback

        commandline=[self.conf['binary'], "-nthreads", "all", filename, "-o", os.path.join(outputPath, "image."+format)]
        subprocess.check_call(commandline)

        updateCompletion(1.0)
