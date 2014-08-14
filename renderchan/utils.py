__author__ = 'Konstantin Dmitriev'

import os, shutil, errno
import random
import time

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