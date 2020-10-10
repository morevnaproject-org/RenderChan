

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
        # Extra params
        self.extraParams["range"]="1"
        self.extraParams["step"]="1"
        self.extraParams["shrink"]="1"
        self.extraParams["multimedia"]="0"
        self.extraParams["maxtilesize"]="none"
        self.extraParams["nthreads"]="all"

    def getInputFormats(self):
        return ["tnz"]

    def getOutputFormats(self):
        return ["tiff" , "png"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        if not os.path.exists(outputPath):
            os.mkdir(outputPath)

        # TODO: Progress callback

        os.chdir(os.path.dirname(self.conf['binary']))
        commandline=[self.conf['binary'], filename, "-o", os.path.join(outputPath, "image."+format), "-nthreads", extraParams['nthreads'], "-step", extraParams['step'], "-shrink", extraParams['shrink'], "-multimedia", extraParams['multimedia']]
        subprocess.check_call(commandline)

        updateCompletion(1.0)
