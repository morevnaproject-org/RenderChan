__author__ = 'Konstantin Dmitriev'

import os.path
import time
import ConfigParser
import shutil
from renderchan.utils import mkdirs, sync, file_is_older_than, PlainConfigFileWrapper, LockThread
from renderchan.cache import RenderChanCache

class RenderChanProjectManager():
    def __init__(self):

        self.list = {}

        # Active project. All other projects inherit render settings of active one.
        self.active = None

        # Active profile to apply. If value is None, then use default (defined by the project).
        self.profile = None

        # Stereo mode to apply
        self.stereo = ""

        # Determines if projects should be loaded readonly
        self.readonly = False

    def load(self, path):

        self.list[path]=RenderChanProject(path, self.readonly)

        # All projects should inherit render configuration of active project
        if self.getActive()==None:
            self.setActive(self.list[path])
            if not self.profile:
                self.profile = self.active.activeProfile
            self.active.config["stereo"]=self.stereo
            self.active.loadRenderConfig(self.profile)
        else:
            self.list[path].config=self.active.config.copy()
            self.list[path].activeProfile=self.active.activeProfile

    def get(self, path):
        if not self.list.has_key(path):
            self.load(path)

        return self.list[path]

    def setActive(self, project):
        """

        :type project: RenderChanProject
        """
        self.active = project
        self.updateChildProjects()

    def getActive(self):
        return self.active

    def updateChildProjects(self):
        for key in self.list.keys():
            self.list[key].config=self.active.config.copy()
            self.list[key].activeProfile=self.active.activeProfile
            self.list[key].loadRenderConfig(self.profile)


class RenderChanProject():
    def __init__(self, path, readonly=False):

        self.path=path

        self.confPath = os.path.join(path,"project.conf")
        if not os.path.exists(self.confPath):
            # Look for remake.conf
            self.confPath = os.path.join(path,"remake.conf")
        if not os.path.exists(self.confPath):
            raise Exception

        if os.path.basename(self.confPath) == "remake.conf":
            self.version = 0
        else:
            self.version = 1

        self.activeProfile=None


        # PROJECT CACHE

        # Check for cache version
        self.cache_version = 1
        cachepath = os.path.join(self.path, "render", "cache.sqlite")
        if not readonly:
            if os.path.exists(os.path.join(self.path, "render", "cache.version")):
                existing_cache_version=0
                f=open(os.path.join(self.path, "render", "cache.version"))
                content=f.readlines()
                f.close()
                if len(content)>0:
                    try:
                        existing_cache_version=int(content[0].strip())
                    except:
                        pass
                if existing_cache_version!=self.cache_version:
                    os.remove(cachepath)
            else:
                if os.path.exists(cachepath):
                    # There is unversioned cache, remove it
                    os.remove(cachepath)

        # Load cache
        self.cache=RenderChanCache(cachepath, readonly)

        # Save cache version
        f = open(os.path.join(self.path, "render", "cache.version"),'w')
        f.write(str(self.cache_version)+"\n")
        f.close()


        # List of modules used in the project
        self.dependencies=[]

        self.defaults = {
            'width':'480',
            'height':'270',
            'format':'png',
            'audio_rate':'48000',
            'fps':'24',
            'stereo':'',
        }

        # Check the consistency of localization
        localedir = "locale"
        self.language=self.getLanguage()
        # render dir
        needCleanup=True
        if os.path.exists(os.path.join(self.path,'render',localedir,'lang.conf')):
            with open(os.path.join(self.path,'render',localedir,'lang.conf'), 'r') as f:
                current_language = f.readline().strip()
            if self.language == current_language:
                needCleanup=False
        if needCleanup and os.path.exists(os.path.join(self.path,'render',localedir)):
            print "The language data is inconsistent in %s. Cleaning..." % os.path.join(self.path,'render',localedir)
            shutil.rmtree(os.path.join(self.path,'render',localedir))
            mkdirs(os.path.join(self.path,'render',localedir))
            shutil.copy2(os.path.join(self.path,localedir,'lang.conf'),os.path.join(self.path,'render',localedir,'lang.conf'))

        # Project configuration

        self.config={}
        self.loadRenderConfig()

        # Load list of frozen files
        self.frozenPaths=[]
        self.loadFrozenPaths()


    def loadRenderConfig(self, profile=None):

        """
        :type profile: str
        """
        if self.version==0 and profile!=None:

            print("Warning: Profiles are not supported with old project format. No profile loaded.")
            return False

        elif self.version==0:

            # Old project format, used by Remake

            config = ConfigParser.SafeConfigParser()
            config.readfp(PlainConfigFileWrapper(open(self.confPath)))

            for key in config.options('default'):
                self.config[key]=config.get('default', key)
        else:

            # Native RenderChan project format

            config = ConfigParser.SafeConfigParser()
            config.readfp(open(self.confPath))

            # sanity check
            for section in config.sections():
                if "." in section:
                    print "Warning: Incorrect profile name found (%s) - dots are not allowed." % (section)

            if profile==None:
                if config.has_option("main", "active_profile"):
                    profile=config.get("main", "active_profile")
                else:
                    if len(config.sections())!=0:
                        profile = config.sections()[0]
                    else:
                        return False

            profile=profile.replace(".","")

            for key in config.options(profile):
                self.config[key]=config.get(profile, key)

            # check for correct values
            if self.getConfig("stereo")!="left" and self.getConfig("stereo")!="right":
                self.config["stereo"]=""

            self.activeProfile=profile



        # Store project configuration - we need that to track configuration changes
        profilepath = self.getProfilePath()
        if not os.path.isdir(profilepath):
            mkdirs(profilepath)

        filename=os.path.join(profilepath,"core.conf")
        oldconfig={}
        if os.path.exists(filename):
            cp = ConfigParser.SafeConfigParser()
            cp.read(filename)

            for key in cp.options('main'):
                oldconfig[key]=cp.get('main', key)

        newconfig=self.defaults.copy()
        for key in self.config.keys():
            if key in self.defaults.keys():
                newconfig[key]=self.config[key]

        if newconfig!=oldconfig:
            config = ConfigParser.SafeConfigParser()
            config.add_section('main')
            for key in newconfig.keys():
                config.set('main', key, newconfig[key])
            with open(filename, 'wb') as configfile:
                config.write(configfile)

        # Store current profile
        #filename=os.path.join(self.path,"render","project.conf","profile.conf")
        #prev_profile = ""
        #if os.path.exists(filename):
        #    # Read previous profile
        #    f=open(filename)
        #    prev_profile = f.readlines()[0].strip()
        #    f.close()
        #if prev_profile!=self.getProfileDirName():
        #    f = open(filename,'w')
        #    f.write(self.getProfileDirName()+"\n")
        #    f.close()

        return True

    def registerModule(self, module):
        name=module.getName()
        if name in self.dependencies:
            # Module already registered
            return

        self.dependencies.append(name)

        # Store module configuration - we need that for configuration changes detection
        filename=os.path.join(self.getProfilePath(),name+".conf")
        oldconfig={}
        if os.path.exists(filename):
            cp = ConfigParser.SafeConfigParser()
            cp.read(filename)

            for key in cp.options('main'):
                oldconfig[key]=cp.get('main', key)

        newconfig={}
        for key in module.extraParams:
            if self.config.has_key(module.getName()+"."+key):
                newconfig[key]=self.config[module.getName()+"."+key]
            elif self.config.has_key(key):
                newconfig[key]=self.config[key]
            else:
                newconfig[key]=module.extraParams[key]

        if newconfig!=oldconfig:
            config = ConfigParser.SafeConfigParser()
            config.add_section('main')
            for key in newconfig.keys():
                if newconfig[key]!=None:
                    config.set('main', key, str(newconfig[key]))
            with open(filename, 'wb') as configfile:
                config.write(configfile)

    def getConfig(self, key):
        if key in self.config.keys():
            return self.config[key]
        elif key in self.defaults.keys():
            return self.defaults[key]
        else:
            return None

    def getProfilePath(self):
        return os.path.join(self.path,'render','project.conf','profiles',self.getProfileDirName())

    def getProfileDirName(self):
        if self.version == 0:
            result="%sx%s" % (self.getConfig("width"), self.getConfig("height"))
        else:
            result="%sx%s.%s"  % (self.getConfig("width"), self.getConfig("height"), self.activeProfile)
        if self.language!='':
            result=result+'.'+self.language
        if self.getConfig("stereo")!='':
            result=result+"."+self.getConfig("stereo")
        return result

    def loadFrozenPaths(self):
        filename=os.path.join(self.path,"render","project.conf","frozen.list")
        if os.path.exists(filename):
            f=open(filename)
            for line in f.readlines():
                line = line.strip()
                if not line in self.frozenPaths:
                    self.frozenPaths.append(line)
            f.close()

    def saveFrozenPaths(self):
        filename=os.path.join(self.path,"render","project.conf","frozen.list")
        f = open(filename, 'w')
        for line in self.frozenPaths:
            f.write(line+"\n")
        f.close()

    def isFrozen(self, path):
        for frozenPath in self.frozenPaths:
            if ("/"+path).startswith(frozenPath):
                return True
        return False

    def setFrozen(self, path, value):

        # FIXME: In fact, we have to use a more complex algorithm for recursive paths

        if os.path.isdir(os.path.join(self.path, path)) and not path.endswith('/'):
            path = path+'/'
        path="/"+path
        if value==True:
            if not path in self.frozenPaths:
                self.frozenPaths.append(path)
        else:
            if path in self.frozenPaths:
                self.frozenPaths.remove(path)

    def getLanguage(self):

        localedir = "locale"
        localedirpath = os.path.join(self.path, localedir)
        current_language = ''
        if not os.path.exists(os.path.join(localedirpath,'lang.conf')):
            print("Warning: The \"locale\" directory isn't configured for localization.")
        else:
            with open(os.path.join(localedirpath,'lang.conf'), 'r') as f:
                current_language = f.readline().strip()
        return current_language

    def switchLanguage(self, language):

        localedir = "locale"
        localedirpath = os.path.join(self.path, localedir)

        current_language=self.getLanguage()

        if not current_language:
            return False

        if language==current_language:
            print("This language is already active.")
            return True

        if not os.path.exists(localedirpath+"."+language):
            print("Error: No such language (%s)." % language)
            return False
        else:
            # do directory switch
            os.rename(localedirpath, localedirpath+"."+current_language)
            os.remove(os.path.join(localedirpath+"."+current_language, "lang.conf"))
            os.rename(localedirpath+"."+language, localedirpath)
            f = open(os.path.join(localedirpath,'lang.conf'), 'w')
            f.write(language+"\n")
            f.close()

            # cleanup renderings
            if os.path.exists(os.path.join(self.path,'render',localedir)):
                shutil.rmtree(os.path.join(self.path,'render',localedir))
                mkdirs(os.path.join(self.path,'render',localedir))
                shutil.copy2(os.path.join(localedirpath,'lang.conf'),os.path.join(self.path,'render',localedir,'lang.conf'))




    def switchProfile(self, profile):

        def _sync_path(src, dest):
            names = os.listdir(src)
            for name in names:
                path = os.path.join(src, name)
                if os.path.isdir(path):
                    _sync_path(path, os.path.join(dest,name))
                else:
                    if name.endswith(".sync"):
                        name = name[:-5]
                        sync( os.path.join(src,name), os.path.join(dest,name) )


        if not os.path.isdir(self.getProfilePath()):
            mkdirs(self.getProfilePath())

        msg=""
        while True:
            if msg!="":
                print msg
            msg="The rendertree is locked by other process. Waiting..."
            # Check if we are on correct profile
            need_sync = True
            checkfile=os.path.join(self.path,"render","project.conf","profile.conf")
            lockfile=os.path.join(self.path,"render","project.conf","profile.lock")
            #prev_profile = ""
            if os.path.exists(checkfile):
                # Read previous profile
                f=open(checkfile)
                fcontent=f.readlines()
                f.close()
                if len(fcontent)>0:
                    prev_profile = fcontent[0].strip()
                    if prev_profile==profile:
                        need_sync = False

            if need_sync:
                if os.path.exists(lockfile):
                    if not(file_is_older_than(lockfile, 6.0)):
                         # the profile is locked, we can't switch it now
                         time.sleep(5)
                         continue

                # the lockfile is old enough

                f = open(lockfile,'w')
                f.write(profile+"\n")
                f.close()

                # let's wait to make sure the lock is ours
                time.sleep(1)

                # Sanity check
                if os.path.exists(lockfile):
                    f=open(lockfile)
                    fcontent=f.readlines()
                    if len(fcontent)>0:
                        prev_profile = fcontent[0].strip()
                    else:
                         prev_profile = None
                    f.close()
                    if not (prev_profile==profile):
                        # someone have modified the file in the meantime, let's wait and try again
                        time.sleep(5)
                        continue
                else:
                    # something is wrong, because file is vanished
                    time.sleep(5)
                    continue

                # Start update thread
                t = LockThread(lockfile)
                t.start()

                # Switch the profile
                renderpath=os.path.join(self.path,"render")
                _sync_path(self.getProfilePath(), renderpath)

                # Finally update profile.conf
                f = open(checkfile,'w')
                f.write(profile+"\n")
                f.close()

                return t
            else:
                if os.path.exists(lockfile):
                     f=open(lockfile)
                     fcontent=f.readlines()
                     if len(fcontent)>0:
                         prev_profile = fcontent[0].strip()
                     else:
                         prev_profile = None
                     f.close()
                     if not(prev_profile==profile or file_is_older_than(lockfile, 6.0)):
                         # someone tries to switch profile right now, let's wait and try again
                         time.sleep(5)
                         continue

                f = open(lockfile,'w')
                f.write(profile+"\n")
                f.close()

                # Sanity check
                if os.path.exists(lockfile):
                    f=open(lockfile)
                    fcontent=f.readlines()
                    if len(fcontent)>0:
                        prev_profile = fcontent[0].strip()
                    else:
                         prev_profile = None
                    f.close()
                    if not (prev_profile==profile):
                        # someone have modified the file in the meantime, let's wait and try again
                        time.sleep(5)
                        continue
                else:
                    # something is wrong, because file is vanished
                    time.sleep(5)
                    continue

                # Start update thread
                t = LockThread(lockfile)
                t.start()

                return t