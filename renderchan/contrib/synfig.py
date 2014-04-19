__author__ = 'Konstantin Dmitriev'

from renderchan.module import RenderChanModule
import subprocess
import gzip
import os, sys
import re
import errno

class RenderChanSynfigModule(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        self.conf['binary']="synfig"
        self.conf["packetSize"]=100

    def getInputFormats(self):
        return ["sif", "sifz"]

    def getOutputFormats(self):
        return ["png","exr"]

    def analyze(self, filename):

        def _decode_callback(matches):
            id = matches.group(1)
            try:
                return unichr(int(id,16))
            except:
                return id

        info={"dependencies":[]}

        scriptPattern = re.compile(".*<string.*>(.*)</string>.*")
        paramFilenamePattern = re.compile(".*<param name=\"filename\">.*")
        paramFamilyPattern = re.compile(".*<param name=\"family\">.*")
        usePattern = re.compile(".*<param name=\".*\" use=\"(.*)#.*\"/>.*")
        switchLinkOnPattern = re.compile("<switch .*link_on=\"(.*)#:.*\".*>")
        switchSwitchPattern = re.compile("<switch .*switch=\"(.*)#:.*\".*>")

        fpsPattern = re.compile("<canvas .*fps=\"([0-9]+\.[0-9]+)\".*>")
        framePattern = {}
        framePattern["startFrame"] = re.compile("<canvas .*begin-time=\"([0-9.sf\s]+[sf])\".*>")
        framePattern["endFrame"] =  re.compile("<canvas .*end-time=\"([0-9.sf\s]+[sf])\".*>")

        # We need this to make sure that start-end values are read only once
        fps=-1

        if filename.endswith(".sifz"):
            f=gzip.open(filename)
        else:
            f=open(filename)
        prev_line=""
        for line in f.readlines():

            if fps==-1:
                pat=fpsPattern.search(line)
                if pat:
                    fps=float(pat.group(1).strip())

                    for i in ("startFrame","endFrame"):
                        pat=framePattern[i].search(line)
                        if pat:
                            t=pat.group(1).strip()
                            if t.endswith('f'):
                                a=t.split('s ')
                                if len(a)==1:
                                    # "11.000f" case
                                    t=float(a[0][0:-1])
                                else:
                                    # "5s 4.00f" case
                                    t=float(a[0])*fps+float(a[1][0:-1])
                            elif t.endswith('s'):
                                t=float(t[0:-1])*fps
                            info[i]=int(round(t))

            pat=scriptPattern.search(line)
            if pat:
                prev_pat=paramFilenamePattern.search(prev_line)
                if prev_pat:
                    info["dependencies"].append(pat.group(1).strip())
                    continue
                prev_pat=paramFamilyPattern.search(prev_line)
                if prev_pat:
                    info["dependencies"].append(pat.group(1).strip())
                    continue

            pat=usePattern.search(line)
            if pat:
                info["dependencies"].append(pat.group(1).strip())

            pat=switchLinkOnPattern.search(line)
            if pat:
                info["dependencies"].append(pat.group(1).strip())

            pat=switchSwitchPattern.search(line)
            if pat:
                info["dependencies"].append(pat.group(1).strip())

            prev_line=line
        f.close

        dirname=os.path.dirname(filename)
        for i,val in enumerate(info["dependencies"]):
            # Decode unicode characters
            info["dependencies"][i]=re.sub("&#x([a-zA-Z0-9]+)(;|(?=\s))", _decode_callback, info["dependencies"][i])
            info["dependencies"][i]=info["dependencies"][i].replace('%20',' ')

            fullpath=os.path.abspath(os.path.join(dirname,info["dependencies"][i]))
            fallbackpath=os.path.join(dirname,os.path.basename(info["dependencies"][i]))
            if os.path.exists(fullpath):
                info["dependencies"][i]=fullpath
            elif os.path.exists(fallbackpath):
                # Even if path to the file is wrong, synfig looks for the file with the same
                # name in current directory, so we should treat this case.
                info["dependencies"][i]=fallbackpath
            else:
                # Otherwise, just write path to unexisting file as is
                info["dependencies"][i]=fullpath

        return info

    def render(self, filename, outputPath, startFrame, endFrame, width, height, format, fps, audioRate, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        totalFrames = endFrame - startFrame + 1
        #/path/to/file.sifz.png: Line 10 of 100 -- 1m 14s
        frameNumberPattern = re.compile(": Line (.*) of \d+ -- ")

        if format in RenderChanModule.imageExtensions:
            try:
                os.makedirs(outputPath)
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(outputPath):
                    pass
                else: raise
            outputPath=os.path.join(outputPath, "file."+format)


        commandline=[self.conf['binary'], "-t", format, "-o",outputPath, "-w", width, "-h", height,
                     "--start-time",str(startFrame)+"f", "--end-time",str(endFrame)+"f",
                     filename]
        #print " ".join(commandline)
        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        rc = None
        #currentFrame = None
        while rc is None:
            line = out.stdout.readline()
            if not line:
                break
            print line,
            sys.stdout.flush()
            fn = frameNumberPattern.search(line)
            if fn:
                currentFrame = float(fn.group(1).strip())
                fc = float(currentFrame / 100) / float(totalFrames)
                updateCompletion(comp + fc)
            rc = out.poll()

        out.communicate()
        rc = out.poll()
        print '===================================================='
        print '  Synfig command returns with code %d' % rc
        print '===================================================='
        if rc != 0:
            print '  Synfig command failed...'
            raise Exception('  Synfig command failed...')
