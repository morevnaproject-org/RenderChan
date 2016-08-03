__author__ = 'Ivan Mahonin'

from gettext import gettext as _
from argparse import ArgumentParser
from renderchan.core import RenderChan
import os
import subprocess
import math


class Thumbnailer:
    def __init__(self):
        self.srcdir = os.path.abspath(".")
        self.renderdir = os.path.join(self.srcdir, "render")
        self.thumbdir = self.renderdir
        self.coreDatadir = ""
        self.icons = {}
        self.width = 160
        self.height = 160
        self.icon_size = 80
        self.force = False
        self.dry_run = False
        self.suffix = ".thumb.png"
        
        self.created_dirs = {}
        self.removed_dirs = {}

        self.dep_trees = {}
        self.dep_tree_roots = []
        
        self.check_executable(["ffmpeg",    "-version"], "FFMpeg")
        self.check_executable(["ffprobe",   "-version"], "FFMpeg")
        self.check_executable(["convert",   "-version"], "ImageMagick")
        self.check_executable(["composite", "-version"], "ImageMagick")
    
    def build_tree(self, rootdir, project_file):
        renderchan = RenderChan()
        renderchan.datadir = self.coreDatadir
        renderchan.dry_run = True
        renderchan.force = True
        renderchan.track = True
            
        renderDir = os.path.join(rootdir, "render") + os.path.sep
        formats = renderchan.modules.getAllInputFormats()
    
        dirs = [rootdir]
        files = []
        while len(dirs):
            d = dirs.pop(0)
            for f in sorted(os.listdir(d)):
                file = os.path.join(d, f)
                if f[0] == '.' or file[0:len(renderDir)] == renderDir:
                    continue
                if os.path.isfile(file):
                    if os.path.splitext(file)[1][1:] in formats:
                        files.append(file)
                if os.path.isdir(file):
                    dirs.append(file)
                    
        for file in files:
            try:
                renderchan.submit('render', file, False, False, False)
            except:
                while renderchan.trackedFilesStack:
                    renderchan.trackFileEnd()
        
        tree = {}
        for key, value in renderchan.trackedFiles.items():
            newValue = {}
            newValue["source"] = os.path.join(rootdir, value["source"])
            newValue["deps"] = []
            newValue["backDeps"] = []
            for file in value["deps"]:
                newValue["deps"].append( os.path.join(rootdir, file) )
            for file in value["backDeps"]:
                newValue["backDeps"].append( os.path.join(rootdir, file) )
            tree[os.path.join(rootdir, key)] = newValue

        return tree
    
    def build_full_deps(self, tree_key, key, depsKey, fullDepsKey):
        if ( tree_key in self.dep_trees
             and key in self.dep_trees[tree_key]
             and fullDepsKey not in self.dep_trees[tree_key][key] ):
            self.dep_trees[tree_key][key][fullDepsKey] = []
            for dep in self.dep_trees[tree_key][key][depsKey]:
                if dep not in self.dep_trees[tree_key][key][fullDepsKey]:
                    self.dep_trees[tree_key][key][fullDepsKey].append(dep)
                    if dep in self.dep_trees[tree_key]:
                        self.build_full_deps(tree_key, dep, depsKey, fullDepsKey)
                        for dd in self.dep_trees[tree_key][dep][fullDepsKey]:
                            if dd not in self.dep_trees[tree_key][key][fullDepsKey]:
                                self.dep_trees[tree_key][key][fullDepsKey].append(dd)

    def get_dep_tree(self, filename):
        if filename not in self.dep_trees:
            project_file = os.path.join(filename, "project.conf")
            if os.path.isfile(project_file):
                self.dep_tree_roots.append(filename)
                self.dep_trees[filename] = self.build_tree(filename, project_file)
                for k in self.dep_trees[filename]:
                    self.build_full_deps(filename, k, "deps", "fullDeps")
                    self.build_full_deps(filename, k, "backDeps", "fullBackDeps")
            elif filename == "" or filename == os.path.sep:
                self.dep_trees[filename] = {}
            else:
                self.dep_trees[filename] = self.get_dep_tree(os.path.dirname(filename))
        return self.dep_trees[filename]
    
    def check_executable(self, command, comment):
        result = False
        try:
            subprocess.check_call(command)
            result = True
        except subprocess.CalledProcessError:
            pass
        print(_("Check %s (%s): %s") % (command[0], comment, ("success" if result else "fail")))
        return result
    
    def clean_thumbnails(self, path = ""):
        src = os.path.join(self.thumbdir, path) if path != "" else self.thumbdir
        if os.path.isfile(src):
            if src[-len(self.suffix):].lower() == self.suffix:
                print(_("Remove thumbnail: %s") % src)
                if self.dry_run:
                    self.removed_dirs[os.path.dirname(src)] = self.removed_dirs.get(os.path.dirname(src), 0) - 1
                else:
                    os.remove(src)
        elif os.path.isdir(src):
            for file in sorted(os.listdir(src)):
                self.clean_thumbnails(os.path.join(path, file))
            if len(os.listdir(src)) + self.removed_dirs.get(src, 0) <= 0:
                print(_("Remove directory: %s") % src)
                if self.dry_run:
                    self.removed_dirs[os.path.dirname(src)] = self.removed_dirs.get(os.path.dirname(src), 0) - 1
                else:
                    os.rmdir(src)

    def build_thumbnails(self, path = ""):
        src = os.path.join(self.srcdir, path) if path != "" else self.srcdir
        
        if not os.path.isfile(src) and not os.path.isdir(src):
            print(_("File not found: %s") % src)
            return False
        if os.path.isfile(src) and path[-len(self.suffix):].lower() == self.suffix:
            return True
        if src == self.renderdir and path != "":
            return True
        if src == self.thumbdir and path != "":
            return True
        
        render = os.path.join(self.renderdir, path) if path != "" else self.renderdir
        dest = os.path.join(self.thumbdir, path + self.suffix) if path != "" else self.thumbdir + self.suffix
        icon = self.find_icon(src)

        if os.path.isdir(src):
            for file in sorted(os.listdir(src)):
                self.build_thumbnails(os.path.join(path, file))

        processed, success = self.build_thumbnail_any(src, render, dest, icon)

        if not success:
            print(_("Failed to create thumbnail(s) for: %s") % src)
        elif processed:
            print(_("Created thumbnail(s) for: %s") % src)
        return success

    def build_thumbnail_any(self, src, render, dest, icon):
        found = False
        processed = False
        success = True
        if not found:
            found, processed, success = self.build_thumbnail(src, dest, icon)
        if not found:
            found, processed, success = self.build_thumbnail(render + ".png", dest, icon)
        if not found:
            found, processed, success = self.build_thumbnail(render + ".avi", dest, icon)
        if not found and src != self.srcdir and os.path.isdir(src):
            found, processed, success = (True,) + self.build_thumbnail_directory(src, dest, icon)
        return processed, success

    def build_thumbnail(self, src, dest, icon):
        if os.path.isfile(src) and src[-4:].lower() == ".png":
            return (True,) + self.build_thumbnail_png(src, dest, icon)
        elif os.path.isdir(src) and src[-4:].lower() == ".png":
            return (True,) + self.build_thumbnail_png_sequence(src, dest, icon)
        elif os.path.isfile(src) and src[-4:].lower() == ".avi":
            return (True,) + self.build_thumbnail_avi(src, dest, icon)
        return False, False, True
    
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
        if not self.dry_run:
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

    def create_directory(self, path):
        if not os.path.isdir(path) and path not in self.created_dirs:
            self.create_directory(os.path.dirname(path))
            print(_("Create directory: %s") % path)
            if self.dry_run:
                self.created_dirs[path] = True
            else:
                os.mkdir(path)

    def create_directory_for_file(self, path):
        self.create_directory(os.path.dirname(path))

    def find_icon(self, path):
        if os.path.isdir(path) and ".directory" in self.icons:
            return self.icons[".directory"]
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
        self.create_directory_for_file(dest)
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
        self.create_directory_for_file(dest)
        if icon:
            return True, self.run_pipe([
                self.command_video_frame(src = src, seek = 0.5*duration),
                self.command_thumbnail(),
                self.command_icon(dest = dest, icon = icon) ])
        return True, self.run_pipe([
            self.command_video_frame(src = src, seek = 0.5*duration),
            self.command_thumbnail(dest = dest) ])

    def build_thumbnail_directory(self, src, dest, icon):
        srcPrefix = src + os.path.sep
        destPath = self.thumbdir + src[len(self.srcdir):]
        renderPath = self.renderdir + src[len(self.srcdir):]
        
        tree = self.get_dep_tree(src)
        root = src in self.dep_tree_roots
        
        bestFileSrc = None
        bestFileRender = None
        bestDepsCount = 0
        bestBackDepsExists = False
        
        doAppend = True
        files = []
        for f in sorted(os.listdir(src)):
            if doAppend:
                files.append(f)
            else:
                files.insert(0, f)
            doAppend = not doAppend 
        
        for f in files:
            fileSrc = os.path.join(src, f)
            fileDest = os.path.join(destPath, f + self.suffix)
            fileRender = os.path.join(renderPath, f)
            if os.path.isfile(fileDest):
                depsCount = 0
                backDepsExists = root
                if fileSrc in tree:
                    for dep in tree[fileSrc]["fullDeps"]:
                        if dep[0:len(srcPrefix)] == srcPrefix or dep[0:len(renderPath)] == renderPath:
                            depsCount += 1
                    for dep in tree[fileSrc]["backDeps"]:
                        if dep[0:len(srcPrefix)] != srcPrefix and dep[0:len(renderPath)] != renderPath:
                            backDepsExists = True
                if ( not bestFileSrc
                     or (bestFileSrc and bestBackDepsExists < backDepsExists)
                     or (bestFileSrc and bestBackDepsExists == backDepsExists and bestDepsCount < depsCount) ):
                    bestFileSrc = fileSrc
                    bestFileRender = fileRender
                    bestDepsCount = depsCount
                    bestBackDepsExists = backDepsExists
                    
        if bestFileSrc:
            #print(_("Main file for '%s' is '%s', deps %s, back-deps %s") % (src, bestFileSrc[len(src):], bestDepsCount, bestBackDepsExists))
            return self.build_thumbnail_any(bestFileSrc, bestFileRender, dest, icon)
        else:
            return False, True 


def process_args():
    parser = ArgumentParser(description=_("Run RenderChan thumbnails generator."),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))
    parser.add_argument("srcdir",
            help=_("A path to the source files."))
    parser.add_argument("--renderdir", dest="renderdir",
            action="store",
            default="",
            help=_("A path to the rendered files."))
    parser.add_argument("--thumbdir", dest="thumbdir",
            action="store",
            default="",
            help=_("A path to the thumbnails."))
    parser.add_argument("--suffix", dest="suffix",
            action="store",
            default=".thumb.png",
            help=_("Suffix of thumbnail file"))
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
    parser.add_argument("--dry-run", dest="dry_run",
            action="store_true",
            default=False,
            help=_("Simulate activity."))
    parser.add_argument("--clean", dest="clean",
            action="store_true",
            default=False,
            help=_("Remove all *.thumb.png files."))
    return parser.parse_args()


def main(datadir, argv):
    args = process_args()
    
    if datadir:
        datadir = os.path.abspath(datadir)
    else:
        datadir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "thumbicons")
    
    thumbnailer = Thumbnailer()
    
    srcdir       = os.path.abspath(args.srcdir)    if args.srcdir    else thumbnailer.srcdir
    renderdir    = os.path.abspath(args.renderdir) if args.renderdir else os.path.join(srcdir, "render") 
    thumbdir     = os.path.abspath(args.thumbdir)  if args.thumbdir  else renderdir
    
    suffix       = args.suffix if args.suffix else thumbnailer.suffix
    
    width        = args.width        if args.width        and args.width        > 0 else 0
    height       = args.height       if args.height       and args.height       > 0 else 0
    icon_size    = args.icon_size    if args.icon_size    and args.icon_size    > 0 else 0
    icon_percent = args.icon_percent if args.icon_percent and args.icon_percent > 0 else 0
    force        = True if args.force   else False
    dry_run      = True if args.dry_run else False
    clean        = True if args.clean   else False
    
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
    
    thumbnailer.srcdir    = srcdir
    thumbnailer.renderdir = renderdir
    thumbnailer.thumbdir  = thumbdir
    thumbnailer.suffix    = suffix
    thumbnailer.width     = width
    thumbnailer.height    = height
    thumbnailer.icon_size = icon_size
    thumbnailer.force     = force
    thumbnailer.dry_run   = dry_run
    thumbnailer.clean     = clean
    for f in os.listdir(datadir):
        if f[-4:].lower() == ".png":
            thumbnailer.icons["." + f[0:-4].lower()] = os.path.join(datadir, f)

    if thumbnailer.clean:
        print(_("Remove thumbnails"))
        print(_("Thumbnails path: %s") % thumbnailer.thumbdir)
        if thumbnailer.dry_run:
            print(_("Dry run - actually do nothing"))
        thumbnailer.clean_thumbnails()
    else:
        print(_("Generate thumbnails"))
        print(_("Source path:     %s") % thumbnailer.srcdir)
        print(_("Render path:     %s") % thumbnailer.renderdir)
        print(_("Thumbnails path: %s") % thumbnailer.thumbdir)
        print(_("Width: %d")           % thumbnailer.width)
        print(_("Height: %d")          % thumbnailer.height)
        print(_("Icon size: %d")       % thumbnailer.icon_size)
        if thumbnailer.force:
            print(_("Force"))
        if thumbnailer.dry_run:
            print(_("Dry run - actually do nothing"))
        thumbnailer.build_thumbnails()
    
