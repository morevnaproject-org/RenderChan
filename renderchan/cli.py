__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from argparse import ArgumentParser
import os.path
import sys

from renderchan.core import RenderChan, __version__
from renderchan.file import RenderChanFile


def process_args():
    parser = ArgumentParser(description=_("Render a file in a RenderChan project."),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))

    parser.add_argument("file", metavar="FILE",
            help=_("A path to the file you want to render."))

    parser.add_argument("--profile", metavar=_("PROFILE"),
            action="store",
            help=_("Set rendering profile."))
    parser.add_argument("--stereo",
            choices=["vertical", "v", "vertical-cross", "vc", "horizontal", "h", "horizontal-cross", "hc", "left", "l", "right", "r"],
            action="store",
            help=_("Enable stereo-3D rendering."))

    # TODO: Not implemented
    parser.add_argument("--width", metavar=_("WIDTH"),
            type=int,
            action="store",
            help=_("Output width."))
    # TODO: Not implemented
    parser.add_argument("--height", metavar=_("HEIGHT"),
            type=int,
            action="store",
            help=_("Output height."))

    parser.add_argument("--renderfarm", dest="renderfarmType",
            choices=["puli","afanasy"],
            action="store",
            help=_("Set renderfarm engine type."))
    parser.add_argument("--host", metavar=_("HOST"),
            action="store",
            help=_("Set renderfarm server host (Puli renderfarm)."))
    parser.add_argument("--port", metavar=_("PORT"),
            type=int,
            action="store",
            help=_("Set renderfarm server port (Puli renderfarm)."))
    parser.add_argument("--cgru-location", dest="cgru_location", metavar=_("CGRU_LOCATION"),
            action="store",
            help=_("Set cgru directory (Afanasy renderfarm)."))

    parser.add_argument("--deps", dest="dependenciesOnly",
            action="store_true",
            default=False,
            help=_("Render dependencies, but not file itself."))
    parser.add_argument("--allocate", dest="allocateOnly",
            action="store_true",
            default=False,
            help=_("Don't do the actual render, just allocate a placeholder for file."))
    parser.add_argument("--snapshot-to", metavar=_("SNAPSHOT_TO"),
            action="store",
            help=_("Write a snapshot into specified directory."))

    parser.add_argument("--version", "-v", action='version', version=_("RenderChan version %s") % __version__)

    return parser.parse_args()


def main(datadir, argv):
    args = process_args()

    filename = os.path.abspath(args.file)

    renderchan = RenderChan()

    renderchan.datadir = datadir

    if args.profile:
        renderchan.setProfile(args.profile)

    if args.renderfarmType and args.renderfarmType in renderchan.available_renderfarm_engines:
        renderchan.renderfarm_engine = args.renderfarmType

        if args.host:
            if args.renderfarm_engine in ("puli"):
                renderchan.setHost(args.host)
            else:
                print("WARNING: The --host parameter cannot be set for this type of renderfarm.")
        if args.port:
            if renderchan.renderfarm_engine in ("puli"):
                renderchan.setPort(args.port)
            else:
                print("WARNING: The --port parameter cannot be set for this type of renderfarm.")

        if args.cgru_location:
            args.cgru_location = options.cgru_location
    else:
        if args.host:
            print("WARNING: No renderfarm type given. Ignoring --host parameter.")
        if args.port:
            print("WARNING: No renderfarm type given. Ignoring --port parameter.")

    if args.snapshot_to:
        renderchan.snapshot_path = args.snapshot_to

    return renderchan.submit('render', filename, args.dependenciesOnly, args.allocateOnly, args.stereo)
