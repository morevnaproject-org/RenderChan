

__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import which, ffmpeg_has_soxr
from renderchan import ui
import subprocess

class RenderChanMp3Module(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']=self.findBinary("ffmpeg")
        self.conf["packetSize"]=0
        self.soxr=ffmpeg_has_soxr(self.conf['binary'])

    def getInputFormats(self):
        return ["mp3"]

    def getOutputFormats(self):
        return ["wav"]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
            ui.info("Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf['binary']))
            ui.info("    Please install ffmpeg package.")
            return False
        self.active=True
        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        updateCompletion(0.0)

        # TODO: Progress callback

        commandline=[self.conf['binary'], "-y", "-i", filename]
        if self.soxr:
            commandline+=["-af", "aresample=resampler=soxr"]
        commandline+=["-ar", extraParams["audio_rate"], outputPath]
        subprocess.check_call(commandline, **ui.quiet_subprocess())

        updateCompletion(1.0)
