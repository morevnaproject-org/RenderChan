__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import os
from zipfile import ZipFile

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
            members = zip.namelist()
            total = len(members)
            for i, member in enumerate(members):
                zip.extract(member, outputPath)
                updateCompletion(float(i+1)/total if total else 1.0)

        updateCompletion(1.0)
