__author__ = 'zelgadis'

import bpy
import sys

OLD_PATH = "old_path"
NEW_PATH = "new_path"

params = {OLD_PATH: "",
          NEW_PATH: ""}

def checkPath(path, old_path_dir):
    # Blender 2.58 treats paths starting with "///" well,
    # but bpy.path.abspath() converts such path to absolute.
    # We need to avoid that.
    clean_path = re.sub('^//+', '//', path)
    clean_path = os.path.abspath(bpy.path.abspath(clean_path))
    if not os.path.isabs(params[OLD_PATH]):
        clean_path = os.path.relpath(clean_path, old_path_dir)
    
    return os.path.normpath(os.path.normcase(clean_path)) == params[OLD_PATH]

def main():
    old_path_dir = os.path.dirname(params[OLD_PATH])
    
    # Video Sequence Editor links
    for scene in bpy.data.scenes:
        if not scene.sequence_editor:
            continue
        for sequence in scene.sequence_editor.sequences_all:
            if sequence.type == "IMAGE":
                if not sequence.elements:
                    continue
                if len(sequence.elements) > 1:
                    for element in sequence.elements:
                        if os.path.normpath(os.path.normcase(os.path.join(os.path.abspath(bpy.path.abspath(sequence.directory)), element.filename))) == params[OLD_PATH]:
                            print("Warning: Moving image sequences not currently supported")
                    continue
                
                if os.path.normpath(os.path.normcase(os.path.join(os.path.abspath(bpy.path.abspath(sequence.directory)), sequence.elements[0].filename))) == params[OLD_PATH]:
                    sequence.directory = os.path.dirname(params[NEW_PATH])
                    sequence.elements[0].filename = os.path.basename(params[NEW_PATH])
                
                """ Old code (for reference)
                if checkPath(os.path.join(sequence.directory, element.filename)):
                    new_dir = os.path.dirname(params[NEW_PATH])
                    for dest_sequence in reversed(scene.sequence_editor.sequences_all):
                        if (bpy.path.abspath(seq.directory) == seq.directory) != os.path.isabs(params[NEW_PATH]):
                            continue
                        if os.path.abspath(bpy.path.abspath(seq.directory)) == os.path.abspath(params[NEW_PATH]):
                            
                            break
                """
            else:
                if checkPath(sequence.filepath):
                    sequence.filepath = params[NEW_PATH]
    
    # Image Editor links
    for image in bpy.data.images:
        if checkPath(image.filepath):
            image.filepath = params[NEW_PATH]
    
    # Text Editor links
    for text in bpy.data.texts:
        if checkPath(text.filepath):
            text.filepath = params[NEW_PATH]

if __name__ == '__main__':
    main()