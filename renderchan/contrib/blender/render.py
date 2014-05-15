__author__ = 'zelgadis'

import bpy

UPDATE = "update"
WIDTH = "width"
HEIGHT = "height"
STEREO_CAMERA = "camera"
AUDIOFILE = "audiofile"
FORMAT = "format"
CYCLES_SAMPLES = "cycles_samples"
PRERENDER_COUNT = "prerender_count"
GPU_DEVICE = "gpu_device"

params = {UPDATE: False,
          WIDTH: 480,
          HEIGHT: 270,
          STEREO_CAMERA: "",
          AUDIOFILE:"/tmp/renderchan-test.wav",
          FORMAT: "png",
          CYCLES_SAMPLES: None,
          PRERENDER_COUNT: 0,
          GPU_DEVICE: ""}


def main():

    update = params[UPDATE]

    sce = bpy.context.scene

    sce.frame_current=sce.frame_current+1
    sce.frame_current=sce.frame_current-1

    if params[STEREO_CAMERA]!="":
        found=False

        for ob in sce.objects:
            if ob.name == params[STEREO_CAMERA]:
                sce.camera = ob
                found=True
                break

        if not found:
            basename = sce.camera.name
            for ob in sce.objects:
                if ob.name == basename+"."+params[STEREO_CAMERA]:
                    sce.camera = ob
                    break

    rend = sce.render

    rend.resolution_percentage = 100

    #rend.alpha_mode = "PREMUL"

    #rend.color_mode = "RGBA"

    # Cycles special tweaks
    if sce.render.engine == 'CYCLES':

        # Allow to override smples from .conf file
        if params[CYCLES_SAMPLES]!=0:
            sce.cycles.samples = params[CYCLES_SAMPLES]

        # Allow to set GPU device from RenderChan module settings
        # For information how to identify your GPU device from
        # a cluster console, see http://www.dalaifelinto.com/?p=746
        if params[GPU_DEVICE]!="":
            print("Cycles: GPU configuration found")
            bpy.context.user_preferences.system.compute_device_type = 'CUDA'
            if params[GPU_DEVICE] in bpy.context.user_preferences.system.bl_rna.properties['compute_device'].enum_items.keys():
                bpy.context.user_preferences.system.compute_device = params[GPU_DEVICE]
            else:
                # FIXME: This test probably should go somewhere else (in modules's CheckRequirements?)
                print("")
                print("ERROR: Cannot set GPU device (%s) - not found." % params[GPU_DEVICE])
                print("")
                print("Available devices:")
                for device in bpy.context.user_preferences.system.bl_rna.properties['compute_device'].enum_items.keys():
                    print("   * %s\n" % device)
                print("")

            sce.cycles.device = 'GPU'

        # Optimize tiles for speed depending on rendering device
        # See tip #3 at http://www.blenderguru.com/4-easy-ways-to-speed-up-cycles/
        if sce.cycles.device == 'GPU':
            print("Cycles: GPU device used")
            sce.render.tile_x = 256
            sce.render.tile_y = 256
            sce.cycles.debug_use_spatial_splits = False
        else:
            print("Cycles: CPU device used")
            sce.render.tile_x = 64
            sce.render.tile_y = 64
            sce.cycles.debug_use_spatial_splits = True

        #sce.cycles.use_cache = True   # Cache BVH
        sce.cycles.debug_bvh_type = 'STATIC_BVH'
        #sce.render.use_persistent_data = True   # Persistent Images


    # Suff for updating file
    size_x = rend.resolution_x
    size_y = rend.resolution_y
    fps = rend.fps

    # This is a dirty hack to make  objects initialized properly.
    # Sometimes (especially when using linked groups with armatures and complex expressions)
    # the objects are not properly initialized and appear correctly only on second-third render.
    # With the trick below you can instruct blender to make some count of pre-renders to
    # ensure that all objects are properly initialized.
    # Just put a relevant option for .conf file, like this:
    #      blender_prerender_count=1
    for _ in range(params[PRERENDER_COUNT]):
        rend.resolution_x = 32
        rend.resolution_y = 32
        bpy.ops.render.render()

    rend.resolution_x = params[WIDTH]
    rend.resolution_y = params[HEIGHT]
    #rend.fps = $FPS



    # OPENEXR stuff
    #rend.exr_zbuf = False
    #rend.use_exr_half = True
    #rend.exr_preview = False

    rend.use_placeholder = False
    rend.use_overwrite = True

    # Force format here
    if params[FORMAT] == "png":
        rend.image_settings.file_format = "PNG"
    elif params[FORMAT] == "avi":
        rend.image_settings.file_format = "H264"
        rend.ffmpeg.format = "H264"
        rend.ffmpeg.use_lossless_output=True
        rend.ffmpeg.audio_codec="AAC"

    # Update .blend file if permitted and we have width or height changed
    if update and ( size_x != rend.resolution_x or size_y != rend.resolution_y or fps != rend.fps ):
        bpy.ops.wm.save_mainfile("EXEC_DEFAULT", filepath=bpy.data.filepath)

    # Dump audio track if any
    #audio_found = False
    #for path in bpy.utils.blend_paths(0):
    #    if path.endswith(".wav"):
    #        bpy.ops.sound.mixdown(filepath=params[AUDIOFILE], check_existing=False, container="WAV")
    #        break

if __name__ == '__main__':
    main()