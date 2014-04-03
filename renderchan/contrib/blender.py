__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from subprocess import check_call

class RenderChanBlenderModule(RenderChanModule):
    def __init__(self):
        pass

    def checkRequirements(self):
        return True

    def getInputFormats(self):
        return ["blend"]

    def getOutputFormats(self):
        return []

    def getDependencies(self, filename):
        return []

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format):
        renderscript="/tmp/script.py"
        commandline=["blender", "-b",filename, "-S","Scene", "-P",renderscript, "-a"]
        check_call(commandline)