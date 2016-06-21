__author__ = 'Ivan Mahonin'

from gettext import gettext as _
from argparse import ArgumentParser
import os
import subprocess
import math


class Thumbnailer:
    def __init__(self):
        self.icons = {}
        self.width = 160
        self.height = 160
        self.icon_size = 80
        self.force = False
        self.clean = False
        
        self.check_executable(["ffmpeg",    "-version"], "FFMpeg")
        self.check_executable(["ffprobe",   "-version"], "FFMpeg")
        self.check_executable(["convert",   "-version"], "ImageMagick")
        self.check_executable(["composite", "-version"], "ImageMagick")
    
    def check_executable(self, command, comment):
        result = False
        try:
            subprocess.check_call(command)
            result = True
        except subprocess.CalledProcessError:
            pass
        print(_("Check %s (%s): %s") % (command[0], comment, ("success" if result else "fail")))
        return result
    
    def build_thumbnails(self, path):
        """
        :param path: Directory of file name to make thumbnail(s)
        :type path: str
        :return:
        """
        
        suffix = ".thumb.png"
        isfile = os.path.isfile(path)
        isdir = os.path.isdir(path)
    
        if not isfile and not isdir:
            print(_("File not found: %s") % path)
            return False

        if isfile and path[-len(suffix):].lower() == suffix:
            if self.clean:
                print(_("Remove thumbnail: %s") % path)
                os.remove(path)
            return True

        if self.clean:
            if isdir:
                for file in sorted(os.listdir(path)):
                    self.build_thumbnails(os.path.join(path, file))
            return True
        
        processed = False
        success = True
        if isfile and path[-4:].lower() == ".png":
            processed, success = self.build_thumbnail_png(path, path[0:-4] + suffix, self.find_icon(path[0:-4]))
        elif isdir and path[-4:].lower() == ".png":
            processed, success = self.build_thumbnail_png_sequence(path, path[0:-4] + suffix, self.find_icon(path[0:-4]))
        elif isfile and path[-4:].lower() == ".avi":
            processed, success = self.build_thumbnail_avi(path, path[0:-4] + suffix, self.find_icon(path[0:-4]))
        elif not processed and isdir:
            for file in sorted(os.listdir(path)):
                self.build_thumbnails(os.path.join(path, file))

        if not success:
            print(_("Failed to create thumbnail(s) for: %s") % path)
        elif processed:
            print(_("Created thumbnail(s) for: %s") % path)
        return success
    
    def command_thumbnail(self, src = None, dest = None):
        if not src: src = "png:-"
        if not dest: dest = "png:-"
        size = str(self.width) + "x" + str(self.height)
        return ["convert", str(src), "-thumbnail", size+"^", "-gravity", "center", "-extent", size, str(dest)]

    def command_icon(self, icon, src = None, dest = None):
        if not src: src = "png:-"
        if not dest: dest = "png:-"
        size = str(self.icon_size) + "x" + str(self.icon_size)
        return ["composite", "-gravity", "SouthEast", "-geometry", size+"+0+0", icon, str(src), str(dest)]

    def command_video_frame(self, seek, src = None, dest = None):
        if not src: src = "-"
        if not dest: dest = "-"
        return ["ffmpeg", "-ss", '%.4f' % seek, "-i", str(src), "-frames", "1", "-f", "image2", "-c", "png", str(dest), "-y"]

    def run_pipe(self, commands):
        success = True
        
        processes = []
        stdin = None
        stdout = subprocess.PIPE
        for command in commands:
            if len(processes) == len(commands)-1:
                stdout = None
            process = subprocess.Popen(command, stdin=stdin, stdout=stdout)
            processes.append(process)
            if stdin: stdin.close()
            stdin = process.stdout
            
        for process in processes:
            try:
                if process.wait(30):
                    print(_("Command complete with errors: %s") % str(process.args))
                    success = False
            except subprocess.TimeoutExpired:
                print(_("Timeout expired for: %s") % str(process.args))
                success = False
        return success
    
    def extract_duration(self, src):
        command = ["ffprobe", "-i",  str(src), "-show_entries",  "format=duration", "-of", "csv=p=0"]
        try:
            return float(subprocess.check_output(command).decode("utf-8"))
        except subprocess.CalledProcessError:
            print(_("Command complete with errors: %s") % str(command))
            return -1

    def find_icon(self, path):
        for key in self.icons:
            if path[-len(key):].lower() == key:
                return self.icons[key]
        return
    
    def check_date(self, src, dest, icon):
        if self.force:
            return True
        if not os.path.isfile(dest):
            return True
        if os.path.getmtime(src) >= os.path.getmtime(dest):
            return True
        if icon and os.path.getmtime(icon) >= os.path.getmtime(dest):
            return True
        return False 
    
    def build_thumbnail_png(self, src, dest, icon):
        if not self.check_date(src, dest, icon):
            return False, True
        if icon:
            return True, self.run_pipe([
                self.command_thumbnail(src = src),
                self.command_icon(dest = dest, icon = icon) ])
        return True, self.run_pipe([
            self.command_thumbnail(src = src, dest = dest) ])
    
    def build_thumbnail_png_sequence(self, src, dest, icon):
        files = []
        for f in sorted(os.listdir(src)):
            if f[-4:].lower() == ".png":
                files.append(f)
        if len(files) == 0:
            print(_("Empty sequence: %s") % src)
            return True, False
        return self.build_thumbnail_png(os.path.join(src, files[math.floor(len(files)/2)]), dest, icon)
    
    def build_thumbnail_avi(self, src, dest, icon):
        if not self.check_date(src, dest, icon):
            return False, True
        duration = self.extract_duration(src)
        if duration < 0:
            return True, False
        if icon:
            return True, self.run_pipe([
                self.command_video_frame(src = src, seek = 0.5*duration),
                self.command_thumbnail(),
                self.command_icon(dest = dest, icon = icon) ])
        return True, self.run_pipe([
            self.command_video_frame(src = src, seek = 0.5*duration),
            self.command_thumbnail(dest = dest) ])


def process_args():
    parser = ArgumentParser(description=_("Run RenderChan thumbnails generator."),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))
    parser.add_argument("--root", dest="root",
            action="store",
            default=".",
            help=_("Set root directory."))
    parser.add_argument("--width", dest="width",
            type=int,
            action="store",
            help=_("Thumbnail width."))
    parser.add_argument("--height", dest="height",
            type=int,
            action="store",
            help=_("Thumbnail height."))
    parser.add_argument("--icon-size", dest="icon_size",
            type=int,
            action="store",
            help=_("Size of file type icon at thumbnail."))
    parser.add_argument("--icon-percent", dest="icon_percent",
            type=float,
            action="store",
            help=_("Size of file type icon at thumbnail as percent of minimum from width and height."))
    parser.add_argument("--force", "-f", dest="force",
            action="store_true",
            default=False,
            help=_("Rebuild thumbniles for all files."))
    parser.add_argument("--clean", dest="clean",
            action="store_true",
            default=False,
            help=_("Remove all *.thumb.png files."))
    return parser.parse_args()


def main(datadir, argv):
    args = process_args()
    root = os.path.abspath(args.root)
    
    if datadir:
        datadir = os.path.abspath(datadir)
    else:
        datadir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "thumbicons")
    
    thumbnailer = Thumbnailer()
    
    width        = args.width        if args.width        and args.width        > 0 else 0
    height       = args.height       if args.height       and args.height       > 0 else 0
    icon_size    = args.icon_size    if args.icon_size    and args.icon_size    > 0 else 0
    icon_percent = args.icon_percent if args.icon_percent and args.icon_percent > 0 else 0
    force        = True if args.force else False
    clean        = True if args.clean else False
    
    if clean:
        if width:        print(_("Ignore %s argument, because %s was set") % ("--width",        "--clean"))
        if height:       print(_("Ignore %s argument, because %s was set") % ("--height",       "--clean"))
        if icon_size:    print(_("Ignore %s argument, because %s was set") % ("--icon-size",    "--clean"))
        if icon_percent: print(_("Ignore %s argument, because %s was set") % ("--icon-percent", "--clean"))
        if force:        print(_("Ignore %s argument, because %s was set") % ("--force",        "--clean"))
    elif icon_size:
        if icon_percent: print(_("Ignore %s argument, because %s was set") % ("--icon-percent", "--icon-size"))
    
    if not width and not height:
        width  = thumbnailer.width
        height = thumbnailer.height
    elif not width:
        width = math.ceil(thumbnailer.width*height/thumbnailer.height)
    elif not height:
        height = math.ceil(thumbnailer.height*width/thumbnailer.width)
        
    if not icon_size and not icon_percent:
        icon_size = math.ceil(min(width, height)*thumbnailer.icon_size/min(thumbnailer.width, thumbnailer.height))
    if not icon_size:
        icon_size = math.ceil(min(width, height)*0.01*icon_percent)
    
    thumbnailer.width     = width
    thumbnailer.height    = height
    thumbnailer.icon_size = icon_size
    thumbnailer.force     = force
    thumbnailer.clean     = clean
    for f in os.listdir(datadir):
        if f[-4:].lower() == ".png":
            thumbnailer.icons["." + f[0:-4].lower()] = os.path.join(datadir, f)

    if thumbnailer.clean:
        print(_("Remove thumbnails for: %s") % root)
    else:
        print(_("Generate thumbnails for: %s") % root)
        print(_("Width: %d")     % thumbnailer.width)
        print(_("Height: %d")    % thumbnailer.height)
        print(_("Icon size: %d") % thumbnailer.icon_size)
        if thumbnailer.force:
            print(_("Force"))
    
    thumbnailer.build_thumbnails(root)
