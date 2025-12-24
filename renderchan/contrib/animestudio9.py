__author__ = '036006'

from renderchan.module import RenderChanModule
from renderchan.utils import is_true_string
import subprocess
import gzip
import os, sys
import errno
import re
import locale
import platform
from xml.etree import ElementTree

class RenderChanMohoModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        
        self.conf["binary"]=self.findBinary("moho")
        self.conf["packetSize"]=100
        self.conf["maxNbCores"]=1

        # Extra params
        self.extraParams["layer_composition"]=""
        #self.extraParams['use_own_dimensions']='1'
        self.extraParams["half_size"]="0"
        

    def getInputFormats(self):
        return ["anme", "moho"]

    def getOutputFormats(self):
        return ["png"]

    def analyze(self, filename):

        info={ "dependencies":[], "width": 0, "height": 0 }

        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        if format in RenderChanModule.imageExtensions:
            try:
                os.makedirs(outputPath)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(outputPath):
                    pass
                else: raise
            #outputPath=os.path.join(outputPath, "file."+format)

        if (platform.system()=="Linux"):
            # Workaround for Wine
            filename_cli=filename.replace("/", "\\")
            outputPath_cli=outputPath.replace("/", "\\")
        else:
            filename_cli=filename
            outputPath_cli=outputPath
        
        commandline=[self.conf['binary'], "-r", filename_cli, "-v", "-f", "png", "-outfolder", outputPath_cli]
        
        if extraParams["layer_composition"]:
            commandline.append("-layercomp")
            commandline.append(extraParams["layer_composition"])

        if is_true_string(extraParams["half_size"]):
            commandline.append("-halfsize")
            commandline.append("yes")

        #print(" ".join(commandline))
        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc = None
        while True:
                line = out.stdout.readline()
                if not line:
                        if rc is not None:
                                break
                line = line.decode(locale.getpreferredencoding())
                #print(line)
                sys.stdout.flush()

                rc = out.poll()
        
        directory = os.fsencode(outputPath)
    
        for file in sorted(os.listdir(directory)):
             filename = os.fsdecode(file)
             if filename.endswith(".png"): 
                 lstfile=os.path.join(outputPath, filename[:-10]+".lst")
                 if not os.path.exists(lstfile):
                    #print(lstfile)
                    with open(lstfile, "w") as text_file:
                        text_file.write("FPS 24\n")
                 with open(lstfile, "a") as text_file:
                    text_file.write(filename+"\n")
                 #print(filename)
                 continue
             else:
                 continue
        
        updateCompletion(1)
