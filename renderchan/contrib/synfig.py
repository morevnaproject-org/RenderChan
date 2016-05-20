__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
from renderchan.utils import is_true_string
import subprocess
import gzip
import os, sys
import errno
import re
from xml.etree import ElementTree

class RenderChanSynfigModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\synfig\\bin\\synfig.exe")
        else:
            self.conf['binary']="synfig"
        self.conf["packetSize"]=100
        self.conf["maxNbCores"]=1

        # Extra params
        self.extraParams["single"]="None"
        self.extraParams["extract_alpha"]="0"

    def getInputFormats(self):
        return ["sif", "sifz"]

    def getOutputFormats(self):
        return ["png","exr", "avi"]

    def analyze(self, filename):

        def _decode_callback(matches):
            id = matches.group(1)
            try:
                return chr(int(id,16))
            except:
                return id
        
        def time_to_frames(time, fps):
            split = time.split(' ')
            framesCount = 0
            multiplier_map = { 'f': 1, 's': fps, 'm': fps*60, 'h': fps*60*60 }
            for field in split:
                framesCount += float(field[0:-1]) * multiplier_map[field[-1]]
            return int(round(framesCount))

        info={ "dependencies":[], "width": 0, "height": 0 }

        if filename.endswith(".sifz"):
            f=gzip.open(filename, 'rb')
        else:
            f=open(filename, 'rb')
        
        tree = ElementTree.parse(f)
        root = tree.getroot()
        
        info["width"] = root.get("width")
        info["height"] = root.get("height")
        
        fps = root.get("fps")
        
        info["startFrame"] = time_to_frames(root.get("begin-time"), fps)
        info["endFrame"] = time_to_frames(root.get("end-time"), fps)
        
        # Parse dependencies
        
        # <param name="filename"><string>(dependency)</string></param
        info["dependencies"].extend(element.text for element in root.findall(".//param[@name='filename']/string"))
        # <param name="family"><string>(dependency)</string></param>
        info["dependencies"].extend(element.text for element in root.findall(".//param[@name='family']/string"))
        # <param name="*" use="(dependency)">
        info["dependencies"].extend(element.get("use") for element in root.findall(".//param[@name][@use]"))
        # <switch link_on="(dependency)">
        info["dependencies"].extend(element.get("link_on").rsplit("#:")[0] for element in root.findall(".//switch[@link_on]"))
        # <switch switch="(dependency)">
        info["dependencies"].extend(element.get("switch").rsplit("#:")[0] for element in root.findall(".//switch[@switch]"))
        
        f.close()

        dirname=os.path.dirname(filename)
        for i,val in enumerate(info["dependencies"]):
            # Decode unicode characters
            info["dependencies"][i]=re.sub("&#x([a-zA-Z0-9]+)(;|(?=\s))", _decode_callback, info["dependencies"][i])
            info["dependencies"][i]=info["dependencies"][i].replace('%20',' ')

            fullpath=os.path.abspath(os.path.join(dirname,info["dependencies"][i]))
            fallbackpath=os.path.join(dirname,os.path.basename(info["dependencies"][i]))
            if not os.path.exists(fullpath) and os.path.exists(fallbackpath):
                # Even if path to the file is wrong, synfig looks for the file with the same
                # name in current directory, so we should treat this case.
                info["dependencies"][i]=fallbackpath
            else:
                # This is a path to a nonexistent file if fullpath and fallbackpath are both nonexistent 
                info["dependencies"][i]=fullpath

        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        totalFrames = endFrame - startFrame + 1
        #/path/to/file.sifz.png: Line 10 of 100 -- 1m 14s
        frameNumberPattern = re.compile(": Line (\d+) of \d+ -- ")

        if format in RenderChanModule.imageExtensions and extraParams["single"]=="None":
            try:
                os.makedirs(outputPath)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(outputPath):
                    pass
                else: raise
            outputPath=os.path.join(outputPath, "file."+format)


        commandline=[self.conf['binary'], "-o",outputPath, "-w", str(int(extraParams["width"])), "-h", str(int(extraParams["height"]))]
        commandline.append("--sequence-separator")
        commandline.append(".")

        if format == "avi":
            commandline.append("-t")
            commandline.append("ffmpeg")
            commandline.append("--video-codec")
            commandline.append("libx264-lossless")
            commandline.append("--video-bitrate")
            commandline.append("2000")
        else:
            commandline.append("-t")
            commandline.append("png")

        if extraParams["single"]=="None":
            commandline.append("--start-time")
            commandline.append(str(startFrame)+"f")
            commandline.append("--end-time")
            commandline.append(str(endFrame)+"f")
        else:
            commandline.append("--time")
            commandline.append(extraParams["single"]+"f")

        if is_true_string(extraParams["extract_alpha"]):
            commandline.append("-x")

        commandline.append(filename)

        #print " ".join(commandline)
        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        rc = None
        #currentFrame = None
        while rc is None:
            line = out.stdout.readline().decode("utf-8")
            if not line:
                break
            print(line, end=' ')
            sys.stdout.flush()
            fn = frameNumberPattern.search(line)
            if fn:
                currentFrame = float(fn.group(1).strip())
                fc = float(currentFrame / 100) / float(totalFrames)
                updateCompletion(comp + fc)
            rc = out.poll()

        out.communicate()
        rc = out.poll()
        print('====================================================')
        print('  Synfig command returns with code %d' % rc)
        print('====================================================')
        if rc != 0:
            if os.name == 'nt' and rc == -1073741819:
                pass
            else:
                print('  Synfig command failed...')
                raise Exception('  Synfig command failed...')
        updateCompletion(1)
