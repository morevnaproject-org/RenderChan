__author__ = 'Konstantin Dmitriev'

from gettext import gettext as _
from optparse import OptionParser
import os
from renderchan.core import RenderChan
from renderchan.file import RenderChanFile


def process_args():
    parser = OptionParser(
        usage=_("""
    %prog [options] [FILE]               """))

    parser.add_option("--action", dest="action",
            action="store",
            help=_("Action: render|merge|snapshot."))
    parser.add_option("--profile", dest="profile",
            action="store",
            help=_("Profile."))
    parser.add_option("--format", dest="format",
            action="store",
            help=_("Format."))
    parser.add_option("--start", dest="start",
            action="store", default=None,
            help=_("Start frame."))
    parser.add_option("--end", dest="end",
            action="store", default=None,
            help=_("End frame."))
    parser.add_option("--stereo", dest="stereo",
            action="store", default="",
            help=_("Stereo configuration."))
    parser.add_option("--compare-time", dest="compare_time",
            action="store",
            help=_("Don't render if there is an existing file and it is newer than specified time."))
    parser.add_option("--target-dir", dest="snapshot_target",
            action="store", default=None,
            help=_("Target directory for snapshots."))

    options, args = parser.parse_args()

    # override defaults with settings from file
    if args:
        options.filename=os.path.abspath(args[0])
    else:
        print "ERROR: Please provide input filename"
        exit(1)

    return options, args

def updateCompletion(value):
    print "Rendering: %s" % (value*100)


def main(argv):
    options, args = process_args()

    renderchan = RenderChan()
    renderchan.projects.readonly = True

    if options.profile:
        renderchan.setProfile(options.profile)
    if options.stereo in ("left","l"):
        renderchan.setStereoMode("left")
    elif options.stereo in ("right","r"):
        renderchan.setStereoMode("right")
    if options.compare_time:
        compare_time=float(options.compare_time)
    else:
        compare_time=None
    if not ( options.action and options.action in ['render','merge','snapshot'] ):
        options.action = 'render'

    if options.action != 'snapshot':
        taskfile = RenderChanFile(options.filename, renderchan.modules, renderchan.projects)
        taskfile.setFormat(options.format)

        if options.action == 'merge' and options.stereo and ( options.stereo[0:1]=="v" or options.stereo[0:1]=="h" ):
            pass
        else:
            (isDirty, tasklist, maxTime)=renderchan.parseDirectDependency(taskfile, compare_time)
            if isDirty:
                print "ERROR: There are unrendered dependencies for this file!"
                print "       (Project tree changed or job started too early?)"
                print "       Aborting."
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
            print  "ERROR: Please specify output filename using --target-dir option."
        renderchan.job_snapshot(options.filename, os.path.abspath(options.snapshot_target))

