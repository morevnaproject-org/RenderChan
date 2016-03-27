

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import re
import random

class RenderChanPencil2dModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\pencil\\pencil2d.exe")
        else:
            self.conf['binary']="pencil2d"
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["pcl"]

    def getOutputFormats(self):
        return ["png"]

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        output = os.path.join(outputPath,"file")
        commandline=[self.conf['binary'], filename, "--export-sequence", output]
        subprocess.check_call(commandline)

        updateCompletion(1.0)