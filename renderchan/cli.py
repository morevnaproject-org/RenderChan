__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from argparse import ArgumentParser
from argparse import Action
from argparse import SUPPRESS
import os
import sys
import stat
import time

from renderchan.core import RenderChan, __version__
from renderchan import ui


def _is_hidden(path, name):
    """Detect hidden entries on both Unix (dotfiles) and Windows (hidden/system attributes)."""
    if name.startswith('.'):
        return True
    if os.name == 'nt':
        try:
            attrs = os.stat(path, follow_symlinks=False).st_file_attributes
        except OSError as e:
            ui.warn("Cannot stat %s: %s" % (path, e))
            return False
        return bool(attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM))
    return False

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
    parser.add_argument("--verbose", dest="verbose",
            action="store_true",
            default=False,
            help=_("Verbose output (the historical plain-text format)."))
    parser.add_argument("--recursive", dest="recursive",
            action="store_true",
            default=False,
            help=_("Render all files in directory"))
    parser.add_argument("--pack", dest="pack",
            action="store_true",
            default=False,
            help=_("Pack the file and all its dependencies into zip file (saved in the current working directory)."))
    parser.add_argument("--pack-to-dir", dest="pack_to_dir",
            metavar="PATH",
            default=None,
            help=_("Copy the file and all its dependencies into specified directory (instead of making zip file)."))
    parser.add_argument("--print", dest="print",
            action="store_true",
            default=False,
            help=_("Print all dependencies for given file."))

    parser.add_argument("--version", "-v", action='version', version=_("RenderChan version %s") % __version__)
    parser.add_argument("--formats", action=FormatsAction, datadir=datadir)

    return parser.parse_args()


def main(datadir, argv):
    args = process_args(datadir)

    ui.set_verbose(args.verbose)
    ui.quiet_blank()
    ui.intro("RenderChan v%s" % __version__, animate=True)

    filename = os.path.abspath(args.file)

    if not args.recursive:
        ui.rail_blank()
        ui.log_info(os.path.basename(filename))
        ui.rail_blank()

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
                ui.warn("The --host parameter cannot be set for this type of renderfarm.")
        if args.port:
            if renderchan.renderfarm_engine in ("puli"):
                renderchan.setPort(args.port)
            else:
                ui.warn("The --port parameter cannot be set for this type of renderfarm.")

        if args.cgru_location:
            renderchan.cgru_location = args.cgru_location
    else:
        if args.host:
            ui.warn("No renderfarm type given. Ignoring --host parameter.")
        if args.port:
            ui.warn("No renderfarm type given. Ignoring --port parameter.")

    if args.snapshot_to:
        renderchan.snapshot_path = args.snapshot_to
        
    if args.post_script:
        renderchan.post_script = args.post_script
    
    renderchan.force = args.force

    if args.pack_to_dir:
        renderchan.dry_run = True
        #renderchan.force = True
        renderchan.track = True
        renderchan.action = "pack"
        renderchan.pack_to_dir = os.path.abspath(args.pack_to_dir)
    elif args.pack:
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
            ui.error("--recursive expects a directory, got a file: %s" % filename, stderr=True)
            return 1

        success = True
        renderDir = os.path.join(filename, "render") + os.path.sep
        formats = renderchan.modules.getAllInputFormats()

        dirs = [filename]
        files = []
        while len(dirs):
            d = dirs.pop(0)
            try:
                entries = sorted(os.listdir(d))
            except OSError as e:
                ui.warn("Cannot list directory %s: %s" % (d, e))
                continue
            for f in entries:
                file = os.path.join(d, f)
                # Skip hidden entries, like .git, .svn, .DS_Store, etc.
                if _is_hidden(file, f):
                    continue
                try:
                    rel_parts = os.path.relpath(file, filename).split(os.sep)
                except ValueError as e:
                    # Happens on Windows when crossing drive letters; skip to avoid crashing
                    ui.warn("Cannot build relative path for %s: %s" % (file, e))
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
                ui.info(_("Process file: %s") % (file))
                ui.log_info(file)
                renderchan.submit(file, args.dependenciesOnly, args.allocateOnly, args.stereo)
            except:
                while renderchan.trackedFilesStack:
                    renderchan.trackFileEnd()
                ui.error(_("Rendering failed for file: %s") % (file))
                success = False
        result = 0 if success else 1
    else:
        result = renderchan.submit(filename, args.dependenciesOnly, args.allocateOnly, args.stereo)

    ui.progress_stop()
    if result in (0, None):
        ui.outro(_("Completed in %s") % ui.format_duration(time.time() - renderchan.start_time))
    else:
        ui.outro(_("Failed"))
    return result
