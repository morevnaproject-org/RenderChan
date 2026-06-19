__author__ = 'scribblemaniac'

import bpy

# Combines a series of sequential sequences into a single image sequence (say that ten times fast!)
def merge_sequence(sequence):
    if len(sequence) <= 1:
        return

    # Get the filenames (base names) of all elements in sequence except for the first element
    filenames = [frame.elements[0].filename for frame in sequence[1:]]

    # Delete all elements in sequence except for the first element
    bpy.ops.sequencer.select_all(action="DESELECT")
    for frame in sequence[1:]:
        frame.select = True
     bpy.ops.sequencer.delete()

     # Add all of the files to the end of the first sequence
     for filename in filenames:
         sequence[0].elements.append(filename)

def main():
    for scene in bpy.data.scenes:
        if not scene.sequence_editor:
            continue

        to_merge = {}
        for sequence in scene.sequence_editor.sequences_all:
            try:
                if sequence["renderchan_smartmerge"]:
                    try:
                        to_merge[sequence.channel]
                    except KeyError as e:
                        to_merge[sequence.channel] = {}
                    to_merge[sequence.channel][sequence.frame_start] = sequence
                    del sequence["renderchan_smartmerge"]
            except KeyError as e:
                pass # Wasn't flagged for merging, ignore

        for channel in to_merge:
            to_merge[channel].sort()
            sequence = []
            for frame in to_merge[channel]:
                if not sequence:
                    sequence.append(frame)
                    continue
                if sequence[-1].frame_start + 1 != frame.frame_start or sequence[-1].directory != frame.directory:
                    merge_sequence(sequence)
                    sequence = []
                sequence.append(frame)
            merge_sequence(sequence)

if __name__ == '__main__':
    main()
