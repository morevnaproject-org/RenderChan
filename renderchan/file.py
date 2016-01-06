__author__ = 'Konstantin Dmitriev'

import os.path
import configparser
from renderchan.module import RenderChanModule
from renderchan.utils import float_trunc, PlainConfigFileWrapper
from renderchan.metadata import RenderChanMetadata

class RenderChanFile():
    def __init__(self, path, modules, projects):
        path = os.path.abspath(path)
        self.projectPath = self._findProjectRoot(path)
        self.localPath = self._findLocalPath(path)
        self.project=None
        if self.projectPath!='':
            self.project=projects.get(self.projectPath)
        else:
            print("Warning: File %s doesn't belong to any project." % (path))

        # Associated tasks
        self.taskPost=None

        # Shows if we already had attempt to submit this file to the graph and stores the result
        self.isDirty=None
        # Shows if this file is waiting for dirty status resolution
        self.pending=False

        # File modification time
        self.mtime=None

        self.module = modules.getByExtension(os.path.splitext(self.localPath)[1][1:])
        self.dependencies=[]
        #TODO: startFrame and endFrame should go into self.config
        self.startFrame=-1
        self.endFrame=-1

        self.metadata=None

        self.config={}

        if self.module:

            if self.project:
                self.project.registerModule(self.module)

            sourcepath = self.getPath()
            if os.path.exists(sourcepath):

                output_str=os.path.relpath(path)
                if len(output_str)>60:
                    output_str="..."+output_str[-60:]
                print(". Analyzing file: %s" % output_str)

                info=None
                if self.project:
                    info=self.project.cache.getInfo(self.localPath)
                if info and info["timestamp"]>=self.getTime():
                    print(". . Cache found")
                    self.startFrame=int(info["startFrame"])
                    self.endFrame=int(info["endFrame"])
                    self.dependencies=self.project.cache.getDependencies(self.localPath)
                    if info["width"]>0:
                        self.config['width']=str(info["width"])
                    if info["height"]>0:
                        self.config['height']=str(info["height"])
                else:
                    info=self.module.analyze(self.getPath())
                    if "dependencies" in info.keys():
                        self.dependencies=set(info["dependencies"])

                    if "startFrame" in info.keys():
                        self.startFrame=int(info["startFrame"])
                    if "endFrame" in info.keys():
                        self.endFrame=int(info["endFrame"])

                    if "width" in info.keys():
                        self.config['width']=str(info["width"])
                    else:
                        info["width"] = -1

                    if "height" in info.keys():
                        self.config['height']=str(info["height"])
                    else:
                        info["height"] = -1

                    # Write cache
                    if self.project:
                        self.project.cache.write(self.localPath, self.getTime(), self.startFrame, self.endFrame, self.dependencies, info["width"], info["height"])

                # Rendering params
                if os.path.exists(self.getPath()+".conf"):
                    self._loadConfig(self.getPath()+".conf")

                # Format defined by renderpath should take precedence
                if path != self.getPath():
                    ext=os.path.splitext(path)[1][1:]
                    if ext == "lst":
                        if not self.getFormat() in RenderChanModule.imageExtensions:
                            ext=RenderChanModule.imageExtensions[0]
                    self.setFormat(ext)

            else:
                print("Warning: No source file found for %s" % path)

    def _loadConfig(self, filename):

        config = configparser.SafeConfigParser()
        config.readfp(PlainConfigFileWrapper(open(filename)))

        for key in config.options('default'):
            self.config[key]=config.get('default', key)

        return True

    def _findProjectRoot(self, path):
        while True:
            if os.path.exists(os.path.join(path,"project.conf")) and not os.path.isdir(os.path.join(path,"project.conf")):
                return path
            if os.path.exists(os.path.join(path,"remake.conf")) and not os.path.isdir(os.path.join(path,"remake.conf")):
                return path
            if os.path.dirname(path) == path:
                return ""
            path = os.path.dirname(path)

    def _findLocalPath(self, path):
        if self.projectPath!="" and path.startswith(self.projectPath):
            localpath=path[len(self.projectPath):]

            # cleanup
            if os.name=='nt':
                while localpath.startswith('\\'):
                    localpath=localpath[1:]
            else:
                while localpath.startswith('/'):
                    localpath=localpath[1:]

            if localpath.startswith("render") and not localpath.startswith(os.path.join("render","project.conf")):
                localpath=localpath[6:]

                # cleanup
                if os.name=='nt':
                    while localpath.startswith('\\'):
                        localpath=localpath[1:]
                else:
                    while localpath.startswith('/'):
                        localpath=localpath[1:]

                # now, let's have some heuristics...

                # /projectroot/path/file.ext.png ?
                localpath=os.path.splitext(localpath)[0]
                if os.path.exists(os.path.join(self.projectPath,localpath)):
                    return localpath

                # /projectroot/path/file.ext-alpha.png ?
                if localpath.endswith("-alpha"):
                    localpath_alpha=localpath[:-6]
                    if os.path.exists(os.path.join(self.projectPath, localpath_alpha)):
                        return localpath_alpha

                # /projectroot/path/file.ext.png/file-0000x.png ?
                localpath2=os.path.splitext(os.path.dirname(localpath))[0]
                if os.path.exists(os.path.join(self.projectPath,localpath2)) and not os.path.isdir(os.path.join(self.projectPath,localpath2)):
                    return localpath2

                # /projectroot/path/file.ext-alpha.png/file-0000x.png ?
                if localpath2.endswith("-alpha"):
                    localpath_alpha=localpath2[:-6]
                    if os.path.exists(os.path.join(self.projectPath, localpath_alpha)) and not os.path.isdir(os.path.join(self.projectPath,localpath_alpha)):
                        return localpath_alpha

            return localpath

        else:
            return path

    def getTime(self):
        if self.mtime is None:
            self.mtime=float_trunc(os.path.getmtime(self.getPath()),1)
        return self.mtime


    def getProjectRoot(self):
        return self.projectPath

    def getPath(self):
        return os.path.join(self.projectPath, self.localPath)

    def getRenderPath(self):
        if self.project:
            path=os.path.join(self.projectPath, "render", self.localPath+"."+self.getFormat() )
            #if self.getOutputFormat() in RenderChanFile.imageExtensions:
            #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
            return path
        else:
            return None

    def getProfileRenderPath(self, start=None, end=None):
        if 'render_cache_dir' in self.config:
            profiles_path = self.config['render_cache_dir']
        else:
            profiles_path = None
        if start==None or end==None:
            path=os.path.join(self.project.getProfilePath(profiles_path), self.localPath+"."+self.getFormat() )
        else:
            path=os.path.join(self.project.getProfilePath(profiles_path), self.localPath+"-"+str(start)+"-"+str(end)+"."+self.getFormat() )
        #if self.getOutputFormat() in RenderChanFile.imageExtensions:
        #    path=os.path.join(path, "file"+"."+self.getOutputFormat())
        return path

    def getPacketSize(self):

        size=-1

        if "single" in self.config and self.config["single"]!="None":
            return 0

        # Let conf files override packet size
        if "packet_size" in self.config:
            size=int(self.config["packet_size"])
        elif self.module.getName()+".packet_size" in self.project.config:
            size=int(self.project.config[self.module.getName()+".packet_size"])
        elif "packet_size" in self.project.config:
            size=int(self.project.config["packet_size"])

        if size!=-1:

            length = self.endFrame - self.startFrame + 1
            if length<=size:
                # We don't need to split anything
                return 0

            return size
        else:
            return self.module.getPacketSize()

    def setFormat(self, format):
        # Check if format is supported by the module
        if not format in self.module.getOutputFormats():
            return False
        self.config["format"]=format
        return True

    def getFormat(self):
        key="format"
        if key in self.config:
            format=self.config[key]
        elif self.project:
            if self.module.getName()+"."+key in self.project.config.keys():
                format=self.project.getConfig(self.module.getName()+"."+key)
            else:
                format=self.project.getConfig(key)
        # Check if format is supported by the module
        if not format in self.module.getOutputFormats():
            format=self.module.getOutputFormats()[0]
        return format

    def getParams(self):
        params={}

        # Basic project values
        for key in self.project.defaults.keys():
            if self.project:
                if self.module.getName()+"."+key in self.project.config.keys():
                    params[key]=self.project.getConfig(self.module.getName()+"."+key)
                else:
                    params[key]=self.project.getConfig(key)
            if key in self.config:
                if self.config[key].startswith("*"):
                    params[key]=float(self.config[key][1:])*float(params[key])
                else:
                    params[key]=self.config[key]

        # Module-specific configuration
        for key in self.module.extraParams.keys():
            params[key]=self.module.extraParams[key]
            if key in self.project.config.keys():
                params[key]=self.project.config[key]
            if self.module.getName()+"."+key in self.project.config.keys():
                params[key]=self.project.config[self.module.getName()+"."+key]
            if key in self.config.keys():
                if self.config[key].startswith("*"):
                    params[key]=float(self.config[key][1:])*float(params[key])
                else:
                    params[key]=self.config[key]


        # Special routines related with proxies
        if 'use_own_dimensions' in params.keys() and 'proxy_scale' in params.keys():
            if params['use_own_dimensions']!='0' and 'width' in params.keys() and 'height' in params.keys():
                if params['proxy_scale']!='1.0':
                    try:
                        proxy_scale = float(params['proxy_scale'])
                    except:
                        print "WARNING: Wrong value for 'proxy scale' (%s)." % self.getPath()
                        proxy_scale = 1.0
                    width=int(params['width'])
                    height=int(params['height'])
                    if ((width*proxy_scale) % 1) != 0 or ((height*proxy_scale) % 1) != 0:
                        print "WARNING: Can't apply 'proxy scale' for file (%s):" % self.getPath()
                        print "         Dimensions %sx%s give non-integer values when multiplied by factor of %s." % (width, height, proxy_scale)
                    else:
                        params['width'] = str(width*proxy_scale)
                        params['height'] = str(height*proxy_scale)

        # File-specific configuration
        #params["filename"]=self.getPath()
        #params["output"]=self.getRenderPath()
        #params["profile_output"]=self.getProfileRenderPath()
        #params["module"]=self.module.getName()
        #params["packetSize"]=self.getPacketSize()
        #params["start"]=self.getStartFrame()
        #params["end"]=self.getEndFrame()
        params["dependencies"]=self.getDependencies()
        params["projectVersion"]=self.project.version
        #params["profileDir"]=self.project.getProfileDirName()
        #params["projects"] = []

        return params

    def getDependencies(self):
        result = self.dependencies[:]

        if self.module:

            if self.project:
                projectconf=os.path.join(self.project.getProfilePath(),'core.conf')
                if os.path.exists(projectconf):
                    result.append(projectconf)

                moduleconf=os.path.join(self.project.getProfilePath(),self.module.getName()+'.conf')
                if os.path.exists(moduleconf):
                    result.append(moduleconf)

                # This is commented, because it shouldn't influence maxTime
                #profileconf=os.path.join(self.project.path,"render","project.conf","profile.conf")
                #if os.path.exists(profileconf):
                #    result.append(profileconf)

            fileconf=self.getPath()+'.conf'
            if os.path.exists(fileconf):
                result.append(fileconf)

        return result

    def getStartFrame(self):
        return self.startFrame

    def getEndFrame(self):
        return self.endFrame

    def isValid(self):
        if self.projectPath != "":
            return True
        else:
            return False

    def isFrozen(self):
        if self.project:
            return self.project.isFrozen(self.localPath)
        else:
            return False

    def setFrozen(self, value):
        if self.project:
            self.project.setFrozen(self.localPath, value)
        else:
            if value:
                print("ERROR: Cannot freeze file which is not a part of any project.")

    def getMetadata(self):
        if self.metadata==None:
            self.metadata=self._loadMetadata()
        return self.metadata

    def _loadMetadata(self):
        soundExtensions = ['wav','flac','mp3','aiff']
        ext = os.path.splitext(self.localPath)[1][1:]

        # TODO: This is dirty temporary hack, should be properly arranged using metadata modules
        if ext in soundExtensions:
            # Freesound Query
            from renderchan.contrib.metadata.freesound import parse as FreesoundParse
            metadata = FreesoundParse(self.getPath())
        else:
            metadata = RenderChanMetadata()


        # TODO: Here we should query metadata from file modules and merge it
        # ...

        return metadata

