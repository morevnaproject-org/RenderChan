__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import subprocess
import random
import os
import shutil
import re
from renderchan.utils import which
from renderchan.utils import mkdirs

class RenderChanKritaModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['zip_binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\zip\\bin\\unzip.exe")
            self.conf['convert_binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\imagemagick\\bin\\convert.exe")
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\krita\\bin\\krita.exe")
        else:
            #TODO: Additional bunaries should be separate modules
            self.conf['zip_binary']="unzip"
            self.conf['convert_binary']="convert"
            self.conf['binary']="krita"

        self.conf["packetSize"]=0

        self.extraParams['use_own_dimensions']='1'
        self.extraParams['proxy_scale']='1.0'

    def getInputFormats(self):
        return ["kra"]

    def getOutputFormats(self):
        return ["png"]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf['binary']))
            print("    Please install krita package.")
            return False
        if which(self.conf['zip_binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable!" % (self.getName(), self.conf['zip_binary']))
            print("    Please install unzip package.")
            return False
        if which(self.conf['convert_binary']) == None:
            self.active=False
            print("Module warning (%s): Cannot find '%s' executable!" % (self.getName(), self.conf['convert_binary']))
            print("    Please install ImageMagick package.")
            return False
        self.active=True
        return True

    def analyze(self, filename):
        info={'dependencies':[], 'width':0, 'height':0}

        random_string = "%08d" % (random.randint(0,99999999))
        #TODO: fix temporary directory path for Windows case!
        tmpPath=os.path.join("/tmp","renderchan-krita-module-info-"+random_string)
        mkdirs(tmpPath)

        commandline=[self.conf['zip_binary'], "-j", "-d", tmpPath, filename, "maindoc.xml"]
        subprocess.check_call(commandline)

        f=open(os.path.join(tmpPath,"maindoc.xml"))

        #TODO: Consider file layers as dependencies
        #...

        # Extracting width/height
        imagePattern = re.compile(".*<IMAGE .*>.*")

        for line in f.readlines():
            pat=imagePattern.search(line)
            if pat:
                widthPattern = re.compile(".*width=\"(.*?)\".*")
                pat=widthPattern.search(line)
                if pat:
                    info["width"]=int(pat.group(1).strip())
                heightPattern = re.compile(".*height=\"(.*?)\".*")
                pat=heightPattern.search(line)
                if pat:
                    info["height"]=int(pat.group(1).strip())
                break
        f.close

        shutil.rmtree(tmpPath)

        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        deps_count=0
        for item in extraParams["dependencies"]:
            if not item.endswith(".conf"):
                deps_count+=1
                break

        random_string = "%08d" % (random.randint(0,99999999))
        outputPathTmp = outputPath + "-" + random_string + "." + format

        if deps_count==0:

            random_string = "%08d" % (random.randint(0,99999999))
            tmpPath=outputPath+"."+random_string
            mkdirs(tmpPath)

            commandline=[self.conf['zip_binary'], "-j", "-d", tmpPath, filename, "mergedimage.png"]
            subprocess.check_call(commandline)

            #TODO: Compress image?
            os.rename(os.path.join(tmpPath,"mergedimage.png"), outputPathTmp)

            shutil.rmtree(tmpPath)

        else:
            #TODO: PNG transperency settings at ~/.kde/share/config/kritarc ? use KDEHOME env ?
            commandline=[self.conf['binary'], "--export", filename, "--export-filename", outputPathTmp]
            subprocess.check_call(commandline)

        dimensions = extraParams["width"]+"x"+extraParams["height"]
        commandline=[self.conf['convert_binary'], outputPathTmp, "-resize", dimensions, outputPath]
        subprocess.check_call(commandline)

        os.remove(outputPathTmp)

        updateCompletion(1)
