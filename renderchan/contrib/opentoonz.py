

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
        #TO DO: create dictionary manually
        
        self.conf['binary']=self.findBinary("tcomposer") #method works but variable pointer is buggy/ has wrong parameters

        self.conf["packetSize"]=0
        # Extra params
        self.extraParams["range"]="1"
        self.extraParams["step"]="1"
        self.extraParams["shrink"]="1"
        self.extraParams["multimedia"]="0"
        self.extraParams["maxtilesize"]="none"
        self.extraParams["nthreads"]="all"
        self.os : str = os.name

    def getInputFormats(self):
        return ["tnz"]

    def getOutputFormats(self):
        return ["png", "tiff", "avi"]

    def render(self, 
               filename : str, 
               outputPath : str, 
               startFrame : float, 
               endFrame : float, 
               format: str, 
               updateCompletion, 
               extraParams={}
               ):

        updateCompletion(0.0)
        
        if format == "avi":
            img_format="tiff"
            img_outputPath=outputPath+"."+img_format
        else:
            img_format=format
            img_outputPath=outputPath
        
        # Make Output folder
        if os.path.exists(img_outputPath):
            print("Output: ",img_outputPath)
            shutil.rmtree(img_outputPath)
        os.mkdir(img_outputPath)

        # TODO: Progress callback



        # craete Empty List
        commandline: list = []

        if self.os == 'posix': # Unix-like
            commandline=[self.findBinary("tcomposer"),'--appimage-exec', 'tcomposer', filename, "-o", os.path.join(img_outputPath, "image."+img_format), "-nthreads",extraParams['nthreads'], "-step", extraParams['step'], "-shrink", extraParams['shrink'], "-multimedia", extraParams['multimedia']]
        
        elif self.os == "nt":
            # Windows specofic code
            os.chdir(os.path.dirname(self.conf['binary']))
            commandline=[self.conf['binary'], filename, "-o", os.path.join(img_outputPath, "image."+img_format), "-nthreads", extraParams['nthreads'], "-step", extraParams['step'], "-shrink", extraParams['shrink'], "-multimedia", extraParams['multimedia']]
  

        # Error Catcher
        try:        
            subprocess.check_output(commandline)

        except subprocess.CalledProcessError as e:
            print(e)



        if format == "avi":
            #TODO: Detect frame rate!
            commandline=[self.findBinary("ffmpeg"), "-r", "24", "-f", "image2", "-i", os.path.join(img_outputPath, "image.%04d."+img_format), "-c:v", "libx264", outputPath]
            
            try:
                subprocess.check_call(commandline)
                shutil.rmtree(img_outputPath)
            except subprocess.CalledProcessError as e:
                print(e)
                exit

        updateCompletion(1.0)
