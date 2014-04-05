__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from subprocess import check_call
import os

class RenderChanBlenderModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']="blender"

    def getInputFormats(self):
        return ["blend"]

    def getOutputFormats(self):
        return []

    def getDependencies(self, filename):
        return []

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format, updateCompletion):
        renderscript="/tmp/script.py"
        env=os.environ.copy()
        env["PYTHONPATH"]=""
        commandline=["blender", "-b",filename, "-S","Scene", "-P",renderscript, "-o",outputPath, "-a"]
        commandline=["blender", "-b",filename, "-S","Scene", "-o",outputPath, "-a"]
        check_call(commandline, env=env)