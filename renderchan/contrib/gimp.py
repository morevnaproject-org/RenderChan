

__author__ = 'scribblemaniac'

from renderchan.module import RenderChanModule
from renderchan.utils import which
from distutils.spawn import find_executable
import subprocess
import os
import re
import random

class RenderChanGimpModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\gimp\\gimp.exe")
        else:
            binaryPath=find_executable("gimp")
            # Workaround because the gimp binary cannot be executed via symlink
            if os.path.islink(binaryPath):
                binaryPath=os.path.abspath(os.readlink(binaryPath))
            self.conf['binary']=binaryPath
        self.conf["packetSize"]=0

    def getInputFormats(self):
        return ["xcf", "fli", "flc", "dds", "dcm", "dicom", "eps", "fit", "fits", "g3", "xjt", "cel", "wmf", "ico", "pnm", "ppm", "pgm", "pbm", "psp", "psd", "pdf", "ps", "tiff", "bmp", "xbm", "xwd", "pcx", "pcc"]

    def getOutputFormats(self):
        return ["png", "jpg", "jpeg", "pdf", "psd", "tif", "tiff", "bmp", "ico", "txt", "html", "gif", "mng"]

    def checkRequirements(self):
        if which(self.conf['binary']) == None:
            self.active=False
            print "Module warning (%s): Cannot find '%s' executable." % (self.getName(), self.conf["binary"])
            print "    Please install GIMP package."
        else:
            self.active=True
        return self.active

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp=0.0
        updateCompletion(comp)
        
        # Determines drawable (depending on layer support)
        if format in ("gif", "ico", "mng", "psd"):
            drawable="gimp-image-get-active-drawable image"
        else:
            drawable="gimp-image-merge-visible-layers image CLIP-TO-IMAGE"
        
        # Preprocessing procedures
        if format == "gif":
            preprocedure="(gimp-image-convert-indexed image 0 0 255 0 0 \"\")"
        else:
            preprocedure=""
        
        # Determine procedure name
        if format in ("png", "tiff"):
            saveProcedure="file-%s-save2" % format
        elif format in ("txt", "html"):
            saveProcedure="file-aa-save"
        elif format == "jpg":
            saveProcedure="file-jpeg-save"
        elif format == "tif":
            saveProcedure="file-tiff-save2"
        elif format in ("jpeg", "pdf", "psd", "gif", "mng"):
            saveProcedure="file-%s-save" % format
        else:
            saveProcedure="gimp-file-save"
        
        # Determine paramters
        if format == "png":
            # PNG get special treatment because default parameters can be fetched from GIMP
            saveParameters=" ".join(subprocess.check_output([self.conf['binary'], "-i", "-b", "(let ((str \"\") (defaults (file-png-get-defaults))) (gimp-message (do ((i 0 (+ i 1))) ((= i 9) str) (set! str (string-append str (number->string (nth i defaults)))))))", "-b", "(gimp-quit 0)"], stderr=subprocess.STDOUT)[19:28])
            #saveParameters="0 9 0 0 0 1 0 0 0"
        elif format in ("jpg", "jpeg"):
            saveParameters=".9 0 0 0 \" \" 0 1 0 1"
        elif format == "pdf":
            saveParameters="0 1 1"
        elif format == "psd":
            saveParameters="1 1"
        elif format in ("tif", "tiff"):
            saveParameters="1 0"
        elif format == "txt":
            saveParameters="\"Text file\""
        elif format == "html":
            saveParameters="\"Pure html\""
        elif format == "gif":
            saveParameters="0 1 100 2"
        elif format == "mng":
            saveParameters="0 9 .9 0 1 100 2 1 0 0 1 0"
        else:
            saveParameters=""

        # See docs for readable script-fu code
        commandline=[self.conf['binary'], "-i", "-b", "(let*  ((filename \"%s\") (outpath \"%s\") (image (car (gimp-file-load RUN-NONINTERACTIVE filename filename))) (drawable (car (%s)))) %s (gimp-image-scale image %s %s) (%s RUN-NONINTERACTIVE image drawable outpath outpath %s) (gimp-image-delete image))" % (filename, outputPath, drawable, preprocedure, extraParams['width'], extraParams['height'], saveProcedure, saveParameters), "-b", "(gimp-quit 0)"]

        subprocess.check_call(commandline)

        updateCompletion(1.0)
