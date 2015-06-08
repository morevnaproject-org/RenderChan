__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from optparse import OptionParser
import os.path

from renderchan.core import RenderChan
from renderchan.file import RenderChanFile
from renderchan.project import RenderChanProject


def process_args():
    parser = OptionParser(
        usage=_("""
    %prog               """))

    parser.add_option("--freeze", dest="freezeList",
            action="append",
            help=_("Freeze path."))
    parser.add_option("--unfreeze", dest="unfreezeList",
            action="append",
            help=_("Un-freeze path."))
    parser.add_option("--lang", dest="setLanguage",
            action="store", nargs=1,
            help=_("Switch project language."))

    options, args = parser.parse_args()

    return options, args


def main(argv):
    options, args = process_args()

    renderchan = RenderChan()

    # Parse frozen parameters
    if options.freezeList or options.unfreezeList:
        if not options.freezeList:
            options.freezeList=[]
        if not options.unfreezeList:
            options.unfreezeList=[]
        frozenListChanged=False
        for filename in options.freezeList:
            filename=os.path.abspath(filename)
            if not filename in options.unfreezeList:
                taskfile = RenderChanFile(filename, renderchan.modules, renderchan.projects)
                taskfile.setFrozen(True)
                frozenListChanged=True
        for filename in options.unfreezeList:
            filename=os.path.abspath(filename)
            if not filename in options.freezeList:
                taskfile = RenderChanFile(filename, renderchan.modules, renderchan.projects)
                taskfile.setFrozen(False)
                frozenListChanged=True
        if frozenListChanged:
            taskfile.project.saveFrozenPaths()

    if options.setLanguage:
        project = RenderChanProject(os.getcwd())
        project.switchLanguage(options.setLanguage)