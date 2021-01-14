__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import subprocess
import os, sys
from distutils.version import StrictVersion
from xml.etree import ElementTree

class RenderChanOliveModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        
        self.conf["binary"]=self.findBinary("olive-editor")
        self.conf["packetSize"]=0

        self.version = StrictVersion('0.1.0')  # default value

    def getInputFormats(self):
        return ["ove"]

    def getOutputFormats(self):
        return ["mp4","png","avi"]

    def checkRequirements(self):
        RenderChanModule.checkRequirements(self)
        if self.active:
            # The CLI features depend on the version
            proc = subprocess.Popen([self.conf['binary'], "-v"], stdout=subprocess.PIPE)
            try:
                outs, errs = proc.communicate(timeout=5)
            except TimeoutExpired:
                proc.kill()
                outs, errs = proc.communicate()
            rc = proc.poll()
            if rc == 0:
                line = outs.decode("utf-8")
                if line.startswith("Olive "):
                    self.version = StrictVersion("0.1.0")
                else:
                    # Get the version from stdout. An example of the output: "0.2.0-19eabf28\n"
                    self.version = line.rstrip().split("-")[0]
                    self.version = StrictVersion(self.version)
                    print("WARNING: Olive version >= 0.2.0 not supported yet.")
                    self.active = False
            else:
                self.active = False

            if self.active == False:
                print("WARNING: Failed to initialize Olive module.")

        return self.active

    def analyze(self, filename):

        def _decode_callback(matches):
            id = matches.group(1)
            try:
                return chr(int(id,16))
            except:
                return id
        
        def time_to_frames(time, fps):
            if time == None:
                result = 0
            else:
                fps = float(fps)
                split = time.split(' ')
                framesCount = 0
                multiplier_map = { 'f': 1, 's': fps, 'm': fps*60, 'h': fps*60*60 }
                for field in split:
                    framesCount += float(field[0:-1]) * float(multiplier_map[field[-1]])
                result = int(round(framesCount))
            return result

        info = {"dependencies": []}

        f=open(filename, 'rb')
        
        tree = ElementTree.parse(f)
        root = tree.getroot()
        
        # Parse dependencies
        dependencies=[]

        # TODO: Detect if file version is compatible with installed version of Olive

        if self.version < StrictVersion('0.2.0'):
            media_tag = root.find(".//media")
            if media_tag:
                for footage_tag in media_tag.iter('footage'):
                    dependencies.append(footage_tag.get('url'))
        else:
            #TODO: Add support for parsing Olive 0.2.0 format
            pass
        
        f.close()

        # Eliminate empty entries
        for i,val in enumerate(dependencies):
            if dependencies[i]!=None:
                info["dependencies"].append(dependencies[i])

        dirname = os.path.dirname(filename)
        for i, val in enumerate(info["dependencies"]):
            fullpath = os.path.abspath(os.path.join(dirname, info["dependencies"][i]))
            info["dependencies"][i] = fullpath

        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        #if self.version < StrictVersion('0.2.0'):
            print()
            print("ERROR: Commandline rendering not implemented for Olive. Aborting.", file=sys.stderr)
            print()
            exit(1)

