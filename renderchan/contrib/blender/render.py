__author__ = 'zelgadis'

import bpy
import sys

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

def find_camera(cameras, base, prefixes, suffixes, side_index = 0):
    for camera in cameras:
        for prefix in prefixes:
            if camera.name.lower().startswith(prefix[side_index]) and camera.name[len(prefix[side_index]):] == base:
                return camera
        for suffix in suffixes:
            if camera.name.lower().endswith(suffix[side_index]) and camera.name[:-len(suffix[side_index])] == base:
                return camera
    return None

def main():

    update = params[UPDATE]

    sce = bpy.context.scene

    sce.frame_current=sce.frame_current+1
    sce.frame_current=sce.frame_current-1

    have_builtin_stereo = "use_multiview" in dir(sce.render)

    if params[STEREO_CAMERA] != "":

        # Search for old camera simulation first
        found=False

        for ob in sce.objects:
            if ob.name == params[STEREO_CAMERA] and ob.type == 'CAMERA':
                sce.camera = ob
                found=True
                break

        if not found:
            separators = ['_', '.', '-', ' ']
            
            side = params[STEREO_CAMERA]
            alt_side = "left" if side == "right" else "right"
            sides = [side, side[0]]
            alt_sides = [alt_side, alt_side[0]]
            
            prefixes = [(sides[side_index] + sep, alt_sides[side_index] + sep) for sep in separators for side_index in range(0, len(sides))]
            prefixes.append((side, alt_side))

            suffixes = [(sep + sides[side_index], sep + alt_sides[side_index]) for sep in separators for side_index in range(0, len(sides))]
            suffixes.append((side, alt_side))

            cameras = [obj for obj in sce.objects if obj.type == "CAMERA"]
            
            if len(cameras) < 1:
                print("Error: Cannot render, no camera in file " + bpy.data.filepath, file=sys.stderr)
                exit(1)
            else:
                selected_camera = find_camera(cameras, sce.camera.name, prefixes, suffixes)
            
                base = None
                if not selected_camera:
                    for prefix in prefixes:
                        if sce.camera.name.lower().startswith(prefix[0]):
                            base = sce.camera.name[len(prefix[0]):]
                            break
                        if sce.camera.name.lower().startswith(prefix[1]):
                            base = sce.camera.name[len(prefix[1]):]
                            break
                    if base:
                        selected_camera = find_camera(cameras, base, prefixes, suffixes)
                if not selected_camera:
                    for suffix in suffixes:
                        if sce.camera.name.lower().endswith(suffix[0]):
                            base = sce.camera.name[:-len(suffix[0])]
                            break
                        if sce.camera.name.lower().endswith(suffix[1]):
                            base = sce.camera.name[:-len(suffix[1])]
                            break
                    if base:
                        selected_camera = find_camera(cameras, base, prefixes, suffixes)
                
                if selected_camera:
                    sce.camera = selected_camera
                    found = True


        if found:
            # We use old method, disable multiview
            if have_builtin_stereo:
                sce.render.use_multiview = False

        else:
            if have_builtin_stereo:
                # Use native blender
                sce.render.use_multiview = True
                sce.render.views_format = 'STEREO_3D'
                side = params[STEREO_CAMERA]
                alt_side = "left" if side == "right" else "right"

                sce.render.views[side].use = True
                sce.render.views[alt_side].use = False
                sce.render.views[side].file_suffix = ""
                sce.render.views[alt_side].file_suffix = "_"+alt_side
                sce.render.views_format == 'INDIVIDUAL'
            else:
                print(prefixes)
                print(suffixes)
                print([c.name for c in cameras])
                print(sce.camera.name)
                print("Error: Could not find " + params[STEREO_CAMERA] + " camera for the stereo render of " + bpy.data.filepath, file=sys.stderr)
                exit(1)


    else:
        if have_builtin_stereo:
            sce.render.use_multiview = False

    rend = sce.render

    rend.resolution_percentage = 100

    #rend.alpha_mode = "PREMUL"

    # Cycles special tweaks
    if sce.render.engine == 'CYCLES':

        # Allow to override smples from .conf file
        if params[CYCLES_SAMPLES]!=None:
            sce.cycles.samples = params[CYCLES_SAMPLES]

        # Allow to set GPU device from RenderChan module settings
        # For information how to identify your GPU device from
        # a cluster console, see http://www.dalaifelinto.com/?p=746
        if params[GPU_DEVICE]==None:
            # That means we have to explicitly force CPU rendering
            sce.cycles.device = 'CPU'
        elif params[GPU_DEVICE]!="":
            print("Cycles: GPU configuration found")
            error=False

            if (bpy.app.version > (2, 78, 0)) or ((bpy.app.version == (2, 78, 0)) and (bpy.app.version_char == 'b')) or ((bpy.app.version == (2, 78, 0)) and (bpy.app.version_char == 'c')):
                if 'CUDA' in bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type:
                    bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
                else:
                    error = True
                    print("ERROR: Cannot activate CUDA.")
                if not error and params[GPU_DEVICE] in bpy.context.user_preferences.addons['cycles'].preferences.devices.keys():
                    # TODO: Allow to use more then one GPU device
                    for device in bpy.context.user_preferences.addons['cycles'].preferences.devices.keys():
                        if device == params[GPU_DEVICE]:
                            bpy.context.user_preferences.addons['cycles'].preferences.devices[device].use = True
                        else:
                            bpy.context.user_preferences.addons['cycles'].preferences.devices[device].use = False
                else:
                    error = True
                    # FIXME: This test probably should go somewhere else (in modules's CheckRequirements?)
                    print("ERROR: Cannot set GPU device (%s) - not found." % params[GPU_DEVICE])
                    print()
                    print("Available devices:")
                    for device in bpy.context.user_preferences.addons['cycles'].preferences.devices.keys():
                        print("   * %s\n" % device)
                    print()
            else:
                if 'CUDA' in bpy.context.user_preferences.system.compute_device_type:
                    bpy.context.user_preferences.system.compute_device_type = 'CUDA'
                else:
                    error = True
                    print("ERROR: Cannot activate CUDA.")
                if not error and params[GPU_DEVICE] in bpy.context.user_preferences.system.bl_rna.properties['compute_device'].enum_items.keys():
                    bpy.context.user_preferences.system.compute_device = params[GPU_DEVICE]
                else:
                    error = True
                    # FIXME: This test probably should go somewhere else (in modules's CheckRequirements?)
                    print("ERROR: Cannot set GPU device (%s) - not found." % params[GPU_DEVICE])
                    print()
                    print("Available devices:")
                    for device in bpy.context.user_preferences.system.bl_rna.properties['compute_device'].enum_items.keys():
                        print("   * %s\n" % device)
                    print()
                
            

            if not error:
                sce.cycles.device = 'GPU'
            else:
                sce.cycles.device = 'CPU'

        # Optimize tiles for speed depending on rendering device
        # See tip #3 at http://www.blenderguru.com/4-easy-ways-to-speed-up-cycles/
        if sce.cycles.device == 'GPU':
            print("Cycles: GPU device used")
            sce.render.tile_x = 256
            sce.render.tile_y = 256
            sce.cycles.debug_use_spatial_splits = False
        else:
            print("Cycles: CPU device used")
            if (bpy.app.version > (2, 78, 0)) or ((bpy.app.version == (2, 78, 0)) and (bpy.app.version_char == 'b')) or ((bpy.app.version == (2, 78, 0)) and (bpy.app.version_char == 'c')):
                bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'NONE'
            else:
                bpy.context.user_preferences.system.compute_device_type = 'NONE'
            sce.render.tile_x = 64
            sce.render.tile_y = 64
            sce.cycles.debug_use_spatial_splits = True
        print()

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
        rend.image_settings.color_mode = 'RGBA'
    elif params[FORMAT] == "avi" or params[FORMAT] == "mp4":
        if bpy.app.version < (2, 79, 0):
            rend.image_settings.file_format = "H264"
            rend.ffmpeg.format = "H264"
            rend.ffmpeg.use_lossless_output=True
            #rend.ffmpeg.audio_codec="AAC"
        else:
            rend.image_settings.color_mode = 'RGB'
            #rend.image_settings.color_depth = '16'
            rend.image_settings.file_format = "FFMPEG"
            if params[FORMAT] == "avi":
                rend.ffmpeg.format = "AVI"
                rend.ffmpeg.audio_codec="PCM"
            elif params[FORMAT] == "mp4":
                rend.ffmpeg.format = "MPEG4"
                rend.ffmpeg.audio_codec="AAC"
            rend.ffmpeg.codec='H264'
            rend.ffmpeg.constant_rate_factor='LOSSLESS'
            rend.ffmpeg.use_lossless_output=True
        
    bpy.ops.sound.bake_animation()

    # Update .blend file if permitted and we have width or height changed
    if update and ( size_x != rend.resolution_x or size_y != rend.resolution_y or fps != rend.fps ):
        bpy.ops.wm.save_mainfile("EXEC_DEFAULT", filepath=bpy.data.filepath)

    # Dump audio track if any
    #audio_found = False
    #for path in bpy.utils.blend_paths(0):
    #    if path.endswith(".wav"):
    #        bpy.ops.sound.mixdown(filepath=params[AUDIOFILE], check_existing=False, container="WAV", codec='PCM', accuracy=32, format='S32')
    #        break

if __name__ == '__main__':
    main()
