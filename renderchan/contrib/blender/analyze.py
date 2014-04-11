#!python

import os


def get_project_root(path):
    if os.path.exists(os.path.join(path, "project.conf")) or os.path.exists(os.path.join(path, "remake.conf")):
        return path
    else:
        if os.path.dirname(path) == path:
            return ""
        else:
            return get_project_root(os.path.dirname(path))


# blender 2.5x stuff
import bpy
import os.path
import re

# blender 2.56 & 2.57 crashes when using "bpy.utils.blend_paths(1)",
# so we forced to fallback to relative paths:
paths = bpy.utils.blend_paths(0)
outputlist = []
projectroots = []

#projectroot = os.environ['PROJECTROOT']
#if projectroot == '':
#	Print("No PROJECTROOT variable defined!")
#	sys.exit(1)
#renderdir=os.path.join(projectroot,'render')

for f in paths:
    if f != "":

        # Blender 2.58 treats paths starting with "///" well,
        # but bpy.path.abspath() converts such path to absolute.
        # We need to avoid that.
        f = re.sub('^//+', '//', f)

        f = os.path.abspath(bpy.path.abspath(f))

        projectroot = ""
        for r in projectroots:
            if f.startswith(os.path.join(r, "render")):
                projectroot = r
                break
        if projectroot == "":
            projectroot = get_project_root(os.path.dirname(f))
            if projectroot != "":
                projectroots.append(projectroot)

        if projectroot != "" and f.startswith(os.path.join(projectroot, "render")):

            renderdir = os.path.join(projectroot, "render")

            # f = /projectroot/render/path.ext.png/file000x.png
            # or
            # f = /projectroot/render/path.ext.png

            f2 = f.replace(renderdir, '', 1)[1:]
            # f2 = path.ext.png/file000x.png
            # or
            # f2 = path.ext.png

            f2 = os.path.splitext(f2)[0]
            f2 = os.path.join(projectroot, f2)

            # f2 = /projectroot/path.ext.png/file000x
            # or
            # f2 = /projectroot/path.ext

            if not os.path.exists(f2):
                # f2 = /projectroot/path.ext.png/file000x

                f = os.path.dirname(f)
                # f = /projectroot/render/path.ext.png

                if not f in outputlist:
                    outputlist.append(f)

            else:
                # f2 = /projectroot/path.ext

                if not f in outputlist:
                    outputlist.append(f)

        else:
            if not f in outputlist:
                outputlist.append(f)

for f in outputlist:
    print("RenderChan dependency: %s" % f)
