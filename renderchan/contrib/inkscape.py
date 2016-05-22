

__author__ = 'scribblemaniac'

from renderchan.module import RenderChanModule
import subprocess
import gzip
import os
import os.path
from xml.etree import ElementTree

class RenderChanInkscapeModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        if os.name == 'nt':
            self.conf['binary']=os.path.join(os.path.dirname(__file__),"..\\..\\..\\inkscape\\inkscape.exe")
        else:
            self.conf['binary']="inkscape"
        self.conf["packetSize"]=0
        
        self.extraParams['use_own_dimensions']='1'
        self.extraParams['proxy_scale']='1.0'

    def getInputFormats(self):
        return ["svg", "svgz", "ai", "cdr", "vsd"]

    def getOutputFormats(self):
        return ["png", "ps", "eps", "pdf", "emf", "wmf"]

    def analyze(self, filename):
        info={ "dependencies":[], 'width': 0, 'height': 0 }

        if filename.endswith(".svgz"):
            f=gzip.open(filename, 'rb')
        else:
            f=open(filename, 'rb')
        
        tree = ElementTree.parse(f)
        root = tree.getroot()
        
        info["width"] = root.get("width")
        info["height"] = root.get("height")

        for element in root.iter("{http://www.w3.org/2000/svg}image"):
            fullpath = os.path.join(os.path.dirname(filename), element.get("{http://www.w3.org/1999/xlink}href"))
            fallbackpath = element.get("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref")
            if not os.path.exists(fullpath) and os.path.exists(fallbackpath):
                info["dependencies"].append(fallbackpath)
            else:
                info["dependencies"].append(fullpath)
        
        f.close()

        return info
    
    def replace(self, filename, oldPath, newPath):
        oldPath = os.path.normpath(os.path.normcase(oldPath))
        
        if filename.endswith(".svgz"):
            f=gzip.open(filename, 'rb')
        else:
            f=open(filename, 'rb')
        
        try:
            tree = ElementTree.parse(f)
        finally:
            f.close()
        
        root = tree.getroot()
        
        for element in root.iter("{http://www.w3.org/2000/svg}image"):
           if os.path.normpath(os.path.normcase(element.get("{http://www.w3.org/1999/xlink}href"))) == oldPath:
               element.set("{http://www.w3.org/1999/xlink}href", newPath)
           if os.path.normpath(os.path.normcase(element.get("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref"))) == oldPath:
               element.set("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}absref", os.path.normpath(os.path.join(os.path.dirname(filename), newPath)))
        
        tree.write(filename)

        return True

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        commandline=[self.conf['binary'], "--file=" + filename, "--without-gui", "--export-width=" + extraParams["width"], "--export-height=" + extraParams["height"], "--export-%s=%s" % (format, outputPath)]
        subprocess.check_call(commandline)

        updateCompletion(1.0)
