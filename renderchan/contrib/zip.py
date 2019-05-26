__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which
import subprocess
import os
from zipfile import ZipFile
import random

class RenderChanZipModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["zip"]

    def getOutputFormats(self):
        return ["dir"]

    def checkRequirements(self):
        self.active=True
        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        os.mkdir(outputPath)
        with ZipFile(filename) as zip:
            for member in zip.namelist():
                zip.extract(member, outputPath)

        updateCompletion(1.0)
