__author__ = '036006'

from renderchan.contrib.blender import RenderChanBlenderModule


class RenderChanAnimeforgeModule(RenderChanBlenderModule):
    def __init__(self):
        RenderChanBlenderModule.__init__(self)
        self.conf["binary"] = self.findBinary("animeforge")

    def getInputFormats(self):
        return ["af"]