__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from optparse import OptionParser

from renderchan.core import RenderChan
from renderchan.file import RenderChanFile


def process_args():
    parser = OptionParser(
        usage=_("""
    %prog [FILE]               """))

    parser.add_option("--width", dest="width",
            action="store",
            help=_("Output width."))
    parser.add_option("--height", dest="height",
            action="store",
            help=_("Output height."))
    options, args = parser.parse_args()

    return options, args


def main(argv):
    options, args = process_args()

    renderchan = RenderChan()

    # FIXME: Hardcoded sample file path
    taskfile = RenderChanFile("/home/zelgadis/projects/renderchan/1-professions/020/scene-2.blend")
    renderchan.submit(taskfile)