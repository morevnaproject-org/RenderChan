

__author__ = 'scribblemaniac'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
import re
import random

class RenderChanInkscapeModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\inkscape\\inkscape.exe")
        else:
            self.conf['binary']="inkscape"
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["svg"]

    def getOutputFormats(self):
        return ["png"]

    def analyze(self, filename):
        #TODO: Consider embeded images dependencies
        return {}


    def checkRequirements(self):
        for key in ['binary']:
            if which(self.conf[key]) == None:
                self.active=False
                print "Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf[key])
                print "    Please install pencil2d package."
                return False
        self.active=True
        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        print(format)
        commandline=[self.conf['binary'], "--file=" + filename, "--without-gui", "--export-png=" + outputPath]
        subprocess.check_call(commandline)

        updateCompletion(1.0)