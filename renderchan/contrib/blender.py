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
        self.conf["packetSize"]=10

    def getInputFormats(self):
        return ["blend"]

    def getOutputFormats(self):
        return ["png","exr","avi"]

    def analyze(self, filename):
        info={"dependencies":[]}

        # TODO: get start and end frames

        script=os.path.join(os.path.dirname(__file__),"blender","analyze.py")
        dependencyPattern = re.compile("RenderChan dependency: (.*)$")
        startFramePattern = re.compile("RenderChan start: (.*)$")
        endFramePattern = re.compile("RenderChan end: (.*)$")

        env=os.environ.copy()
        env["PYTHONPATH"]=""
        commandline=[self.conf['binary'], "-b",filename, "-S","Scene", "-P",script]
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

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format, fps, audioRate, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        totalFrames = endFrame - startFrame + 1
        frameCompletionPattern = re.compile("Saved:(.*) Time: .* \(Saving: .*\)")
        frameNumberPattern = re.compile("Fra:(.*) Mem:.*")

        random_string = "%08d" % (random.randint(0,99999999))
        renderscript="/tmp/renderchan"+os.path.basename(filename)+"-"+random_string+".py"
        script=open(os.path.join(os.path.dirname(__file__),"blender","render.py")).read()
        script=script.replace("params[UPDATE]","False")\
           .replace("params[WIDTH]", str(width))\
           .replace("params[HEIGHT]", str(height))\
           .replace("params[CAMERA]", '""')\
           .replace("params[AUDIOFILE]", '"'+os.path.splitext(outputPath)[0]+'.wav"')\
           .replace("params[FORMAT]", '"'+format+'"')
        f = open(renderscript,'w')
        f.write(script)
        f.close()

        if format in RenderChanModule.imageExtensions:
            if extraParams["projectVersion"]<1:
                outputPath=os.path.join(outputPath, "file")+".####"
            else:
                outputPath=os.path.join(outputPath, "file")+".#####"

        print '===================================================='
        print '  Output Path: %s' % outputPath
        print '===================================================='

        env=os.environ.copy()
        env["PYTHONPATH"]=""
        commandline=[self.conf['binary'], "-b",filename, "-S","Scene", "-P",renderscript, "-o",outputPath,
                     "-s",str(startFrame), "-e",str(endFrame), "-a"]
        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        rc = None
        currentFrame = None
        while rc is None:
            line = out.stdout.readline()
            if not line:
                break
            print line,
            sys.stdout.flush()
            fn = frameNumberPattern.search(line)
            if fn:
                currentFrame = float(fn.group(1).strip())
            else:
                fcp = frameCompletionPattern.search(line)
                if fcp and currentFrame is not None:
                    fc = float(currentFrame / 100) / float(totalFrames)
                    updateCompletion(comp + fc)
            rc = out.poll()

        out.communicate()
        rc = out.poll()
        print '===================================================='
        print '  Blender command returns with code %d' % rc
        print '===================================================='
        if rc != 0:
            print '  Blender command failed...'
            raise Exception('  Blender command failed...')

        os.remove(renderscript)