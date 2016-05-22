__author__ = 'zelgadis'

import bpy
import sys

OLD_PATH = "old_path"
NEW_PATH = "new_path"

params = {OLD_PATH: "",
          NEW_PATH: ""}

def main():
    old_path_dir = os.path.dirname(old_path)
    for path in bpy.utils.blend_paths(absolute=False, packed=True, local=True):
        # Blender 2.58 treats paths starting with "///" well,
        # but bpy.path.abspath() converts such path to absolute.
        # We need to avoid that.
        path = re.sub('^//+', '//', path)
        path = os.path.abspath(bpy.path.abspath(path))
        if not os.path.isabs(params[OLD_PATH]):
            path = os.path.relpath(path, old_path)
        
        if os.path.normpath(os.path.normcase(path)) == params[OLD_PATH]:
            # TODO Change this path to the new path
            pass

if __name__ == '__main__':
    main()