__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import subprocess
import os, sys
import re
import random


class RenderChanBlenderModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']="blender"
        self.conf["packetSize"]=40
        self.conf["gpu_device"]=""
        self.conf["disable_gpu"]=False
        # Extra params
        self.extraParams["cycles_samples"]="0"
        self.extraParams["prerender_count"]="0"
        self.extraParams["single"]="None"

    def getInputFormats(self):
        return ["blend"]

    def getOutputFormats(self):
        return ["png","exr","avi"]

    def analyze(self, filename):
        info={"dependencies":[]}

        script=os.path.join(os.path.dirname(__file__),"blender","analyze.py")
        dependencyPattern = re.compile("RenderChan dependency: (.*)$")
        startFramePattern = re.compile("RenderChan start: (.*)$")
        endFramePattern = re.compile("RenderChan end: (.*)$")

        env=os.environ.copy()
        env["PYTHONPATH"]=""
        commandline=[self.conf['binary'], "-b",filename, "-P",script]
        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        rc = None
        while rc is None:
            line = out.stdout.readline()
            if not line:
                break
            #print line,
            sys.stdout.flush()

            dep = dependencyPattern.search(line)
            if dep:
                info["dependencies"].append(dep.group(1).strip())

            start=startFramePattern.search(line)
            if start:
                info["startFrame"]=start.group(1).strip()

            end=endFramePattern.search(line)
            if end:
                info["endFrame"]=end.group(1).strip()


            rc = out.poll()

        out.communicate()
        rc = out.poll()

        if rc != 0:
            print '  Blender command failed...'

        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        totalFrames = endFrame - startFrame + 1
        frameCompletionPattern = re.compile("Saved:(\d+) Time: .* \(Saving: .*\)")
        frameCompletionPattern2 = re.compile("Append frame (\d+) Time: .* \(Saving: .*\)")
        frameNumberPattern = re.compile("Fra:(\d+) Mem:.*")

        stereo_camera = ""
        if extraParams["stereo"]=="left":
            stereo_camera = "Left"
        elif extraParams["stereo"]=="right":
            stereo_camera = "Right"

        if self.conf["disable_gpu"] or 'BLENDER_DISABLE_GPU' in os.environ:
            print "================= FORCE DISABLE GPU ===================="
            gpu_device='None'
        else:
            print "==================== GPU ENABLED ======================="
            gpu_device='"'+self.conf["gpu_device"]+'"'

        random_string = "%08d" % (random.randint(0,99999999))
        renderscript="/tmp/renderchan-"+os.path.basename(filename)+"-"+random_string+".py"
        script=open(os.path.join(os.path.dirname(__file__),"blender","render.py")).read()
        script=script.replace("params[UPDATE]","False")\
           .replace("params[WIDTH]", str(extraParams["width"]))\
           .replace("params[HEIGHT]", str(extraParams["height"]))\
           .replace("params[STEREO_CAMERA]", '"'+stereo_camera+'"')\
           .replace("params[AUDIOFILE]", '"'+os.path.splitext(outputPath)[0]+'.wav"')\
           .replace("params[FORMAT]", '"'+format+'"')\
           .replace("params[CYCLES_SAMPLES]",str(int(extraParams["cycles_samples"])))\
           .replace("params[PRERENDER_COUNT]",str(int(extraParams["prerender_count"])))\
           .replace("params[GPU_DEVICE]",gpu_device)
        f = open(renderscript,'w')
        f.write(script)
        f.close()

        if format in RenderChanModule.imageExtensions:
            if extraParams["single"]!="None":
                outputPath=outputPath+"-######"
            elif extraParams["projectVersion"]<1:
                outputPath=os.path.join(outputPath, "file")+".####"
            else:
                outputPath=os.path.join(outputPath, "file")+".#####"

        print '===================================================='
        print '  Output Path: %s' % outputPath
        print '===================================================='

        env=os.environ.copy()
        env["PYTHONPATH"]=""

        commandline=[self.conf['binary'], "-b",filename, "-S","Scene", "-P",renderscript, "-o",outputPath]
        if extraParams["single"]=="None":
            commandline.append("-x")
            commandline.append("1")
            commandline.append("-s")
            commandline.append(str(startFrame))
            commandline.append("-e")
            commandline.append(str(endFrame))
            commandline.append("-a")
        else:
            commandline.append("-x")
            commandline.append("0")
            commandline.append("-f")
            commandline.append(extraParams["single"])

        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        rc = None
        currentFrame = None
        while rc is None:
            line = out.stdout.readline()
            if not line:
                break
            print line,
            sys.stdout.flush()

            if line.startswith("CUDA error: Out of memory"):
                raise Exception('  Blender command failed...')

            fn = frameNumberPattern.search(line)
            if fn:
                currentFrame = float(fn.group(1).strip())
            elif currentFrame is not None:
                fcp = frameCompletionPattern.search(line)
                if fcp :
                    fc = float(currentFrame / 100) / float(totalFrames)
                    updateCompletion(comp + fc)
                else:
                    fcp = frameCompletionPattern2.search(line)
                    if fcp:
                        fc = float(currentFrame / 100) / float(totalFrames)
                        updateCompletion(comp + fc)
            rc = out.poll()

        out.communicate()
        rc = out.poll()
        print '===================================================='
        print '  Blender command returns with code %d' % rc
        print '===================================================='

        if format in RenderChanModule.imageExtensions and extraParams["single"]!="None":
            outputPath=outputPath[:-7]
            tmp=outputPath+"-%06d" % int(extraParams["single"])
            os.rename(tmp, outputPath)

        if rc != 0:
            print '  Blender command failed...'
            raise Exception('  Blender command failed...')

        os.remove(renderscript)