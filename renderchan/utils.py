__author__ = 'Konstantin Dmitriev'

import os, shutil, errno
import random
import time
import threading
import io
import shutil
from renderchan import ui

if os.name == 'nt':
    import ctypes
    kdll = ctypes.windll.LoadLibrary("kernel32.dll")

def which(program):
    def is_exe(fpath):
        if os.name=='nt':
            return os.path.isfile(fpath) or os.path.isfile(fpath+".exe") or os.path.isfile(fpath+".bat")
        else:
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        program=os.path.realpath(program)
        if is_exe(program):
            return program
    else:
        path = shutil.which(program)
        if path:
            return os.path.realpath(path)

    return None

_hardlinks_broken = False

def copy_file(src, dst):
    """shutil.copy2, tolerant to filesystems without chmod/utime (GVFS-FUSE, CIFS)."""
    shutil.copyfile(src, dst)
    try:
        shutil.copystat(src, dst)
    except OSError:
        pass

def link_or_copy(src, dst):
    """Hardlink src to dst, falling back to a real copy.

    On CIFS mounts a fresh hardlink can be unreadable for a second or two
    (attribute cache) or broken entirely, while os.link() itself reports
    success - so the link is verified by actually reading it."""
    global _hardlinks_broken
    if not _hardlinks_broken:
        try:
            os.link(src, dst)
        except OSError:
            _hardlinks_broken = True
        else:
            for _ in range(10):  # up to ~3 s for the link to become readable
                try:
                    with open(dst, 'rb') as f:
                        f.read(1)
                    return
                except OSError:
                    time.sleep(0.3)
            os.remove(dst)
            _hardlinks_broken = True
    copy_file(src, dst)

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
                link_or_copy(srcname, dstname)
            else:
                copy_file(srcname, dstname)
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

def touch(path, timevalue=None):
    if timevalue==None:
        timevalue=time.time()
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    if not os.path.exists(path):
        with open(path, 'a'):
            os.utime(path, (timevalue, timevalue))
    else:
        os.utime(path, (timevalue, timevalue))

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
            if os.path.exists(profile_output+".sync") and os.path.exists(output):
                if float_trunc(os.path.getmtime(profile_output+".sync"),1) >= compareTime:
                    needSync=False

        if needSync:

            if compareTime!=None:
                output_str=output
                if len(output_str)>60:
                    output_str="..."+output_str[-60:]
                ui.info(". . Syncing profile data for %s" % output_str)

            if not os.path.exists(os.path.dirname(output)):
                    mkdirs(os.path.dirname(output))

            if os.path.isdir(profile_output):
                # Copy to temporary path to ensure quick switching
                output_tmp= output+"%08d" % (random.randint(0,99999999))
                copytree(profile_output, output_tmp, hardlinks=True)
                while os.path.exists(output):
                    try:
                        if os.path.isdir(output):
                            shutil.rmtree(output)
                        else:
                            os.remove(output)
                    except:
                        ui.warn("Failed to remove %s... Trying again..." % output)
                        pass
                rename_success=False
                while not rename_success:
                    try:
                        os.rename(output_tmp, output)
                        rename_success=True
                    except:
                        ui.warn("Failed to rename %s -> %s... Trying again..." % (output_tmp, output))
                        pass
            else:
                if os.path.exists(output):
                    try:
                        if os.path.isdir(output):
                            shutil.rmtree(output)
                        else:
                            os.remove(output)
                    except:
                        pass
                
                if os.name == 'nt':
                    try:
                        shutil.copyfile(profile_output, output)
                    except:
                            raise Exception('ERROR: Cannot sync profile data.')
                else:
                    try:
                        link_or_copy(profile_output, output)
                    except:
                            raise Exception('ERROR: Cannot sync profile data.')

            if not os.path.exists(output):
                raise Exception('ERROR: Failed to sync profile data.')

            # Remember the time of the last sync
            touch(profile_output + ".sync", time.time())

    elif os.path.exists(output):
        if os.path.isdir(output):
            shutil.rmtree(output)
        else:
            os.remove(output)

class LockThread(threading.Thread):
    def __init__(self, filename, interval=5):
        super(LockThread, self).__init__()
        self.daemon = True
        self.filename = filename
        self.interval = interval
        self._stop_event = threading.Event()
    def run(self):
        while not self._stop_event.is_set():
            touch(self.filename, time.time())
            self._stop_event.wait(self.interval)
    def unlock(self):
        self._stop_event.set()

def ini_wrapper(filename):
    with open(filename, 'r') as f:
        ini_str = '[default]\n' + f.read()
    return io.StringIO(ini_str)

def is_true_string(string):
    string = string.lower()
    return string == "1" or string == "true" or string == "yes"


def sanitize_path(path):
    assert isinstance(path, str)
    if os.name == 'nt':
        path = path.replace('/', os.sep)
    else:
        path = path.replace('\\', os.sep)
    return path
