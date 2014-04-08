__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from optparse import OptionParser

from renderchan.module import RenderChanModuleManager


def process_args():
    parser = OptionParser(
        usage=_("""
    %prog [options] [FILE]               """))

    parser.add_option("--width", dest="width",
            action="store",
            help=_("Output width."))
    parser.add_option("--height", dest="height",
            action="store",
            help=_("Output height."))
    parser.add_option("--from", dest="startFrame",
            action="store",
            help=_("Start frame."))
    parser.add_option("--to", dest="endFrame",
            action="store",
            help=_("End frame."))
    parser.add_option("--output", dest="outputPath",
            action="store",
            help=_("Output path."))
    parser.add_option("--module", dest="moduleName",
            action="store",
            help=_("Choose module to use."))
    options, args = parser.parse_args()

    # override defaults with settings from file
    if args:
        options.filename=args[0]
    else:
        print "ERROR: Please provide input filename"
        exit(1)

    return options, args

def updateCompletion(value):
    print "Rendering: %s" % (value*100)


def main(argv):
    options, args = process_args()

    # TODO: Get commandline from modules
    moduleManager = RenderChanModuleManager()

    options.moduleName = "blender"
    module = moduleManager.get(options.moduleName)
    module.render(options.filename, options.outputPath,
                  int(options.startFrame),
                  int(options.endFrame),
                  int(options.width),
                  int(options.height),
                  "png",
                  module.conf["compatVersion"],
                  updateCompletion)

