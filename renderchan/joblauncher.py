__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from argparse import ArgumentParser
import os
from renderchan.core import RenderChan
from renderchan.file import RenderChanFile
from renderchan import ui
import sys


def process_args():
    parser = ArgumentParser(description=_("%prog [FILE] [options]"),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))

    parser.add_argument("file", metavar="FILE",
            help=_("A path to the file you want to render."))
    
    parser.add_argument("--action", dest="action",
            action="store",
            help=_("Action: render|merge|snapshot."))
    parser.add_argument("--profile", dest="profile",
            action="store",
            help=_("Profile."))
    parser.add_argument("--format", dest="format",
            action="store",
            help=_("Format."))
    parser.add_argument("--start", dest="start",
            action="store", default=None,
            help=_("Start frame."))
    parser.add_argument("--end", dest="end",
            action="store", default=None,
            help=_("End frame."))
    parser.add_argument("--stereo", dest="stereo",
            action="store", default="",
            help=_("Stereo configuration."))
    parser.add_argument("--compare-time", dest="compare_time",
            action="store",
            help=_("Don't render if there is an existing file and it is newer than specified time."))
    parser.add_argument("--target-dir", dest="snapshot_target",
            action="store", default=None,
            help=_("Target directory for snapshots."))
    # This is necessary for correct handling of multi-project rendering.
    # The option specifies which parent project this job been called from.
    # The child projects always inherit settings of parent project.
    # But when job-launcher is called we need to know which project was parent at
    # the moment when job was created. Otherwise we will have different render settings ->
    # which lead to configuration file overwrite -> job will fail reporting that module
    # some files were changed (module configuration file).
    # So, this is why we need --active-project option.
    parser.add_argument("--active-project", dest="active_project",
            action="store", default=None,
            help=_("Active project to inherit options from."))

    #options, args = parser.parse_args()

    # override defaults with settings from file
    #if args:
    #    options.filename=os.path.abspath(args[0])
    #else:
    #    ui.error("Please provide input filename", stderr=True)
    #    exit(1)

    return parser.parse_args()

def updateCompletion(value):
    ui.info("Rendering: %s" % (value*100))
    ui.progress("Rendering", value*100, 100)


def main(argv):
    
    print(argv)
    
    options = process_args()

    ui.set_verbose(True)

    renderchan = RenderChan()
    renderchan.projects.readonly = True

    if options.profile:
        renderchan.setProfile(options.profile)
    if options.stereo in ("left","l"):
        renderchan.setStereoMode("left")
    elif options.stereo in ("right","r"):
        renderchan.setStereoMode("right")

    if options.active_project:
        renderchan.projects.load(options.active_project)

    if options.compare_time:
        compare_time=float(options.compare_time)
    else:
        compare_time=None
    if not ( options.action and options.action in ['render','merge','snapshot'] ):
        options.action = 'render'

    if options.action != 'snapshot':
        taskfile = RenderChanFile(options.file, renderchan.modules, renderchan.projects)
        taskfile.setFormat(options.format)

        if options.action == 'merge' and options.stereo and ( options.stereo[0:1]=="v" or options.stereo[0:1]=="h" ):
            pass
        else:
            (isDirty, tasklist, maxTime)=renderchan.parseDirectDependency(taskfile, compare_time)
            if isDirty:
                ui.error("There are unrendered dependencies for this file!", stderr=True)
                ui.error("       (Project tree changed or job started too early?)", stderr=True)
                ui.error("       Aborting.", stderr=True)
                exit(1)

    if options.action == 'render':
        if options.start and options.end:
            renderchan.job_render(taskfile, taskfile.getFormat(), updateCompletion, int(options.start), int(options.end), compare_time)
        else:
            renderchan.job_render(taskfile, taskfile.getFormat(), updateCompletion, compare_time)
    elif options.action == 'merge':
        if options.stereo and ( options.stereo[0:1]=="v" or options.stereo[0:1]=="h" ):
            renderchan.job_merge_stereo(taskfile, options.stereo)
        else:
            renderchan.job_merge(taskfile, taskfile.getFormat(), renderchan.projects.stereo, compare_time)
    elif options.action == 'snapshot':
        if not options.snapshot_target:
            ui.error("Please specify output filename using --target-dir option.", stderr=True)
        renderchan.job_snapshot(options.file, os.path.abspath(options.snapshot_target))

