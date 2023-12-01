

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import random
import shutil

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
        return ["png", "tiff", "avi"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)
        
        if format == "avi":
            img_format="tiff"
            img_outputPath=outputPath+"."+img_format
        else:
            img_format=format
            img_outputPath=outputPath
        
        if os.path.exists(img_outputPath):
            shutil.rmtree(img_outputPath)
        os.mkdir(img_outputPath)

        # TODO: Progress callback

        os.chdir(os.path.dirname(self.conf['binary']))
        
        commandline=[self.conf['binary'], filename, "-o", os.path.join(img_outputPath, "image."+img_format), "-nthreads", extraParams['nthreads'], "-step", extraParams['step'], "-shrink", extraParams['shrink'], "-multimedia", extraParams['multimedia']]
        subprocess.check_call(commandline)
        
        if format == "avi":
            #TODO: Detect frame rate!
            commandline=[self.findBinary("ffmpeg"), "-r", "24", "-f", "image2", "-i", os.path.join(img_outputPath, "image.%04d."+img_format), "-c:v", "libx264", outputPath]
            subprocess.check_call(commandline)
            shutil.rmtree(img_outputPath)

        updateCompletion(1.0)
