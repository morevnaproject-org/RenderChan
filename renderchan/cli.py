__author__ = 'Konstantin Dmitriev'

import os
import sys

from gettext import gettext as _
from optparse import OptionParser

from renderchan.core import RenderChan


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

    app = RenderChan()