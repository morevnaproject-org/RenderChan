__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from argparse import ArgumentParser
from argparse import Action
from argparse import SUPPRESS
import os
import sys

from renderchan.core import RenderChan, __version__

class FormatsAction(Action):
    def __init__(self,
                 option_strings,
                 datadir=None,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help_message="show supported formats and exit"):
        super(FormatsAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help_message)
        self.datadir = datadir

    def __call__(self, parser, namespace, values, option_string=None):
        actualstdout = sys.stdout
        sys.stdout = open(os.devnull,'w')

        renderchan = RenderChan()
        if self.datadir:
            renderchan.datadir = self.datadir

        s = ""
        for f in sorted(renderchan.modules.getAllInputFormats()):
            s = s + "," + f if s else f
        print(s, file=actualstdout)

        parser.exit()

def process_args(datadir):
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
    parser.add_argument("--post-script", metavar=_("SCRIPT_PATH"),
            action="store",
            help=_("Execute script after successful completion. Rendering result is passed as first argument to the script."))
    parser.add_argument("--force", "-f",
            action="store_true",
            default=False,
            help=_("Forces the file and all of its dependencies to be rerendered."))
    parser.add_argument("--force-proxy", dest="forceProxy",
            action="store_true",
            default=False,
            help=_("Allow to change aspect ratio while scaling (see proxy_scale config option)"))
    parser.add_argument("--dry-run", dest="dryRun",
            action="store_true",
            default=False,
            help=_("Parse files, but don't render anything."))
    parser.add_argument("--recursive", dest="recursive",
            action="store_true",
            default=False,
            help=_("Render all files in directory"))
    parser.add_argument("--pack", dest="pack",
            action="store_true",
            default=False,
            help=_("Pack the file and all its dependencies into zip file (saved in the current working directory)."))
    parser.add_argument("--print", dest="print",
            action="store_true",
            default=False,
            help=_("Print all dependencies for given file."))

    parser.add_argument("--version", "-v", action='version', version=_("RenderChan version %s") % __version__)
    parser.add_argument("--formats", action=FormatsAction, datadir=datadir)

    return parser.parse_args()


def main(datadir, argv):
    args = process_args(datadir)

    filename = os.path.abspath(args.file)

    renderchan = RenderChan()

    renderchan.datadir = datadir
    renderchan.dry_run = args.dryRun
    
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
            renderchan.cgru_location = args.cgru_location
    else:
        if args.host:
            print("WARNING: No renderfarm type given. Ignoring --host parameter.")
        if args.port:
            print("WARNING: No renderfarm type given. Ignoring --port parameter.")

    if args.snapshot_to:
        renderchan.snapshot_path = args.snapshot_to
        
    if args.post_script:
        renderchan.post_script = args.post_script
    
    renderchan.force = args.force

    if args.pack:
        renderchan.dry_run = True
        #renderchan.force = True
        renderchan.track = True
        renderchan.action = "pack"
    elif args.print:
        renderchan.dry_run = True
        #renderchan.force = True
        renderchan.track = True
        renderchan.action = "print"

    if args.forceProxy:
        renderchan.force_proxy = args.forceProxy
        
    if args.recursive:
        if not os.path.isdir(filename):
            print("ERROR: --recursive expects a directory, got a file: %s" % filename, file=sys.stderr)
            return 1

        success = True
        renderDir = os.path.join(filename, "render") + os.path.sep
        formats = renderchan.modules.getAllInputFormats()

        dirs = [filename]
        files = []
        while len(dirs):
            d = dirs.pop(0)
            for f in sorted(os.listdir(d)):
                file = os.path.join(d, f)
                # Skip hidden entries, like .git, .svn, .DS_Store, etc.
                if f[0] == '.':
                    continue
                # Skip symlinks
                if os.path.islink(file):
                    continue
                try:
                    rel_parts = os.path.relpath(file, filename).split(os.sep)
                except ValueError:
                    # Happens on Windows when crossing drive letters; skip to avoid crashing
                    continue
                # Skip anything under render/ directory
                if 'render' in (part.lower() for part in rel_parts):
                    continue
                if os.path.isfile(file):
                    ext = os.path.splitext(file)[1][1:].lower()
                    if ext in formats:
                        files.append(file)
                if os.path.isdir(file):
                    dirs.append(file)
                    
        for file in files:
            try:
                print(_("Process file: %s") % (file))
                renderchan.submit(file, args.dependenciesOnly, args.allocateOnly, args.stereo)
            except:
                while renderchan.trackedFilesStack:
                    renderchan.trackFileEnd()
                print(_("Rendering failed for file: %s") % (file))
                success = False
        return 0 if success else 1

    return renderchan.submit(filename, args.dependenciesOnly, args.allocateOnly, args.stereo)
