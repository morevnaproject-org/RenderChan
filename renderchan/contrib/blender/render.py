__author__ = 'zelgadis'

import bpy

UPDATE = "update"
WIDTH = "width"
HEIGHT = "height"
CAMERA = "camera"
AUDIOFILE = "audiofile"
FORMAT = "format"

params = {UPDATE: False,
          WIDTH: 480,
          HEIGHT: 270,
          CAMERA: "",
          AUDIOFILE:"/tmp/renderchan-test.wav",
          FORMAT: "png"}


def main():

    update = params[UPDATE]

    sce = bpy.context.scene

    for ob in sce.objects:
        if ob.name == params[CAMERA]:
            sce.camera = ob
            break

    rend = sce.render

    rend.resolution_percentage = 100

    #rend.alpha_mode = "PREMUL"

    #rend.color_mode = "RGBA"

    # Suff for updating file
    size_x = rend.resolution_x
    size_y = rend.resolution_y
    fps = rend.fps

    rend.resolution_x = params[WIDTH]
    rend.resolution_y = params[HEIGHT]
    #rend.fps = $FPS

    # OPENEXR stuff
    #rend.exr_zbuf = False
    #rend.use_exr_half = True
    #rend.exr_preview = False

    rend.use_placeholder = False
    rend.use_overwrite = True

    # TODO: We should force format here
    # rend.file_format = $BLENDERFORMAT

    # Update .blend file if permitted and we have width or height changed
    if update and ( size_x != rend.resolution_x or size_y != rend.resolution_y or fps != rend.fps ):
        bpy.ops.wm.save_mainfile("EXEC_DEFAULT", filepath=bpy.data.filepath)

    # Dump audio track if any
    audio_found = False
    for path in bpy.utils.blend_paths(0):
        if path.endswith(".wav"):
            bpy.ops.sound.mixdown(filepath=params[AUDIOFILE], check_existing=False, container="WAV")
            break

if __name__ == '__main__':
    main()