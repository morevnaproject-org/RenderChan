__author__ = 'scribblemaniac'

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
                if len(sequence.elements) > 1:    # If sequence is an image sequence (not a single image)
                    for element in sequence.elements:
                        if os.path.normpath(os.path.normcase(os.path.join(os.path.abspath(bpy.path.abspath(sequence.directory)), element.filename))) == params[OLD_PATH]:
                            # Select and split the image sequence containing a path we want to move
                            bpy.ops.sequencer.select_all(action="DESELECT")
                            sequence.select = True
                            bpy.ops.sequencer.images_separate()

                            # Find all selected sequences (from the split)
                            for subsequence in scene.sequence_editor.sequences_all:
                                if subsequence.select:
                                    # Flag it for smart merging
                                    subsequence["renderchan_smartmerge"] = True

                            # There are new sequences now, so we should just rerun this function
                            main()
                            return
                else:    # If sequence is a single image (not an image sequence)
                    if os.path.normpath(os.path.normcase(os.path.join(os.path.abspath(bpy.path.abspath(sequence.directory)), sequence.elements[0].filename))) == params[OLD_PATH]:
                        sequence.directory = os.path.dirname(params[NEW_PATH])
                        sequence.elements[0].filename = os.path.basename(params[NEW_PATH])
            else:    # Sounds, movies, effects, masks, etc.
                if checkPath(sequence.filepath, old_path_dir):
                    sequence.filepath = params[NEW_PATH]

    # Image Editor links
    for image in bpy.data.images:
        if checkPath(image.filepath, old_path_dir):
            image.filepath = params[NEW_PATH]

    # Text Editor links
    for text in bpy.data.texts:
        if checkPath(text.filepath, old_path_dir):
            text.filepath = params[NEW_PATH]

if __name__ == '__main__':
    main()
