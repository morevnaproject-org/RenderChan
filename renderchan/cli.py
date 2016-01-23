__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from optparse import OptionParser
import os.path
import sys

from renderchan.core import RenderChan
from renderchan.file import RenderChanFile


def process_args():
    parser = OptionParser(
        usage=_("""
    %prog [FILE]               """))

    parser.add_option("--profile", dest="profile",
            action="store",
            help=_("Set rendering profile."))
    parser.add_option("--stereo", dest="stereo",
            action="store",
            help=_("Enable stereo-3D rendering. Possible values for STEREO:\n\n"
                   "'vertical' or 'v', "
                   "'vertical-cross' or 'vc', "
                   "'horizontal' or 'h', "
                   "'horizontal-cross' or 'hc', "
                   "'left' or 'l', "
                   "'right' or 'r'. "
                    ))

    # TODO: Not implemented
    parser.add_option("--width", dest="width",
            action="store",
            help=_("Output width."))
    # TODO: Not implemented
    parser.add_option("--height", dest="height",
            action="store",
            help=_("Output height."))

    parser.add_option("--renderfarm", dest="renderfarmType",
            action="store",
            help=_("Set renderfarm engine type."))
    parser.add_option("--host", dest="host",
            action="store",
            help=_("Set renderfarm server host (Puli renderfarm)."))
    parser.add_option("--port", dest="port",
            action="store",
            help=_("Set renderfarm server port (Puli renderfarm)."))
    parser.add_option("--cgru-location", dest="cgru_location",
            action="store",
            help=_("Set cgru directory (Afanasy renderfarm)."))

    parser.add_option("--deps", dest="dependenciesOnly",
            action="store_true",
            default=False,
            help=_("Render dependencies, but not file itself."))
    parser.add_option("--allocate", dest="allocateOnly",
            action="store_true",
            default=False,
            help=_("Don't do the actual render, just allocate a placeholder for file."))
    parser.add_option("--snapshot-to", dest="snapshot_to",
            action="store",
            help=_("Write a snapshot into specified directory."))

    options, args = parser.parse_args()

    return options, args


def main(datadir, argv):
    options, args = process_args()

    if len(args)<1:
        print("Please specify filename for rendering.")
        sys.exit(0)

    filename = os.path.abspath(args[0])

    renderchan = RenderChan()

    renderchan.datadir = datadir

    if options.profile:
        renderchan.setProfile(options.profile)

    if options.renderfarmType and options.renderfarmType in renderchan.available_renderfarm_engines:
        renderchan.renderfarm_engine = options.renderfarmType

        if options.host:
            if renderchan.renderfarm_engine in ("puli"):
                renderchan.setHost(options.host)
            else:
                print("WARNING: The --host parameter cannot be set for this type of renderfarm.")
        if options.port:
            if renderchan.renderfarm_engine in ("puli"):
                renderchan.setPort(options.port)
            else:
                print("WARNING: The --port parameter cannot be set for this type of renderfarm.")

        if options.cgru_location:
            renderchan.cgru_location = options.cgru_location
    else:
        if options.host:
            print("WARNING: No renderfarm type given. Ignoring --host parameter.")
        if options.port:
            print("WARNING: No renderfarm type given. Ignoring --port parameter.")

    if options.snapshot_to:
        renderchan.snapshot_path = options.snapshot_to

    taskfile = RenderChanFile(filename, renderchan.modules, renderchan.projects)
    return renderchan.submit(taskfile, options.dependenciesOnly, options.allocateOnly, options.stereo)
