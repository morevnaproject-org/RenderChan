__author__ = 'Konstantin Dmitriev'

import os, shutil, errno
import random
import time
import threading

def which(program):

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def copytree(src, dst, symlinks=False, hardlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    mkdirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, hardlinks, ignore)
            elif hardlinks:
                os.link(srcname, dstname)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])

    if errors:
        raise shutil.Error(errors)

def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def touch(path, time=None):
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    if not os.path.exists(path):
        with open(path, 'a'):
            os.utime(path, (time, time))
    else:
        os.utime(path, (time, time))

def file_is_older_than(path, seconds):
    return (time.time()-os.path.getmtime(path))>seconds

def float_trunc(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return float(str(f)[:slen])

def sync(profile_output, output, compareTime=None):

    if os.path.exists(profile_output):

        needSync=True

        if compareTime!=None:
            if os.path.exists(profile_output+".sync"):
                if float_trunc(os.path.getmtime(profile_output+".sync"),1) >= compareTime:
                    needSync=False

        if needSync:

            if compareTime!=None:
                output_str=output
                if len(output_str)>60:
                    output_str="..."+output_str[-60:]
                print ". . Syncing profile data for %s" % output_str

            if not os.path.exists(os.path.dirname(output)):
                    mkdirs(os.path.dirname(output))

            if os.path.isdir(profile_output):
                # Copy to temporary path to ensure quick switching
                output_tmp= output+"%08d" % (random.randint(0,99999999))
                copytree(profile_output, output_tmp, hardlinks=True)
                if os.path.exists(output):
                    if os.path.isdir(output):
                        shutil.rmtree(output)
                    else:
                        os.remove(output)
                os.rename(output_tmp, output)
            else:
                if os.path.exists(output):
                    if os.path.isdir(output):
                        shutil.rmtree(output)
                    else:
                        os.remove(output)
                try:
                    os.link(profile_output, output)
                except:
                    print "Error: file already exists"

            # Remember the time of the last sync
            touch(profile_output+".sync", time.time())

    elif os.path.exists(output):
        if os.path.isdir(output):
            shutil.rmtree(output)
        else:
            os.remove(output)

class LockThread(threading.Thread):
    def __init__(self, filename):
        super(LockThread, self).__init__()
        self.filename = filename
        self.active = True
    def run(self):
        while self.active:
            touch(self.filename, time.clock())
            for i in (1,2,3,4,5):
                if self.active:
                    time.sleep(1)
    def unlock(self):
        self.active = False


def switchProfile(project_path, profile):

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


    while True:
        # Check if we are on correct profile
        need_sync = True
        checkfile=os.path.join(project_path,"render","project.conf","profile.conf")
        lockfile=os.path.join(project_path,"render","project.conf","profile.lock")
        prev_profile = ""
        if os.path.exists(checkfile):
            # Read previous profile
            f=open(checkfile)
            prev_profile = f.readlines()[0].strip()
            f.close()
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
                prev_profile = f.readlines()[0].strip()
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
            profilepath=os.path.join(project_path,"render","project.conf",profile)
            renderpath=os.path.join(project_path,"render")
            _sync_path(profilepath, renderpath)

            # Finallym update profile.conf
            f = open(checkfile,'w')
            f.write(profile+"\n")
            f.close()

            return t
        else:
            if os.path.exists(lockfile):
                 f=open(lockfile)
                 prev_profile = f.readlines()[0].strip()
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
                prev_profile = f.readlines()[0].strip()
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

class PlainConfigFileWrapper(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[default]\n'
    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()