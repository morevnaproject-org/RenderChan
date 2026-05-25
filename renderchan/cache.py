__author__ = 'Konstantin Dmitriev'

import os, sys
import sqlite3
import random
import shutil
import socket
import tempfile
import time
from renderchan.utils import mkdirs, LockThread

LOCK_STALE_TIMEOUT = 300      # seconds; lock not updated for this long is assumed stale
LOCK_HEARTBEAT_INTERVAL = 60  # seconds between lockfile mtime updates

class RenderChanCache():
    def __init__(self, path, readonly=False):

        self.connection=None
        self.closed = True
        self.readonly=readonly
        self.path=path
        self.lockfile=path+".lock"
        self._lock_heartbeat=None

        if not os.path.exists(os.path.dirname(path)):
            mkdirs(os.path.dirname(path))

        if not self.readonly:
            if not self._acquire_lock():
                sys.exit(1)

        random_num = "%08d" % (random.randint(0,99999999))
        self.local_path="renderchan-cache-"+random_num+".sqlite"
        self.local_path=os.path.join(tempfile.gettempdir(),self.local_path)
        if os.path.exists(path):
            shutil.copy(path,self.local_path)

        try:
            self.connection=sqlite3.connect(self.local_path)
            self.connection.text_factory = str
            cur=self.connection.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS Paths(Id INTEGER PRIMARY KEY, Path TEXT, Timestamp REAL, Start INTEGER, End INTEGER, Width INTEGER, Height INTEGER);")
            cur.execute("CREATE TABLE IF NOT EXISTS Dependencies(Id INTEGER, Dependency TEXT);")
            self.connection.commit()

            self.closed = False

        except sqlite3.Error as e:
            print("ERROR: Cannot initialize cache database.")
            print("SQLite error: %s" % e.args[0])
            print("Cache file path: %s" % self.local_path)
            if not self.readonly:
                self._release_lock()

    def _acquire_lock(self):
        if os.path.exists(self.lockfile):
            lock_mtime = os.path.getmtime(self.lockfile)
            lock_age = time.time() - lock_mtime
            if lock_age >= LOCK_STALE_TIMEOUT:
                lock_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lock_mtime))
                print("WARNING: Cache lock is stale (last updated %s), removing: %s" % (lock_time_str, self.lockfile))
                try:
                    os.remove(self.lockfile)
                except Exception:
                    print("ERROR: Cannot remove stale lock file: %s" % self.lockfile)
                    return False
            else:
                try:
                    with open(self.lockfile, 'r') as f:
                        locked_by = f.read().strip()
                except Exception:
                    locked_by = "(unknown)"
                print("ERROR: Cache is locked by '%s' (%.0f s ago)." % (locked_by, lock_age))
                print("If the lock is stale, delete the lock file:")
                print("  %s" % self.lockfile)
                return False
        try:
            with open(self.lockfile, 'w') as f:
                f.write("%s:%d\n" % (socket.gethostname(), os.getpid()))
        except Exception:
            print("ERROR: Cannot create lock file: %s" % self.lockfile)
            return False
        self._lock_heartbeat = LockThread(self.lockfile, interval=LOCK_HEARTBEAT_INTERVAL)
        self._lock_heartbeat.start()
        return True

    def _release_lock(self):
        if self._lock_heartbeat is not None:
            self._lock_heartbeat.unlock()
            self._lock_heartbeat = None
        try:
            if os.path.exists(self.lockfile):
                os.remove(self.lockfile)
        except Exception as e:
            print("WARNING: Cannot remove lock file '%s': %s" % (self.lockfile, e))

    def __del__(self):
        if not self.closed:
            self.close()

    def close(self):
        self.connection.commit()
        self.connection.close()
        self.closed = True

        if not self.readonly:
            try:
                shutil.copy(self.local_path, self.path)
            except Exception as e:
                print("ERROR: Cannot save cache to '%s': %s" % (self.path, e))
            self._release_lock()

        try:
            if os.path.exists(self.local_path):
                os.remove(self.local_path)
        except Exception:
            pass

        print("Cache closed.")

    def getInfo(self, path):
        if self.closed:
            return None
        try:
            cur=self.connection.cursor()
            cur.execute("SELECT * FROM Paths WHERE Path = ? ", (path,))
            row = cur.fetchone()
            if row:
                info={}
                info['timestamp']=row[2]
                info['startFrame']=row[3]
                info['endFrame']=row[4]
                info['width']=row[5]
                info['height']=row[6]
                return info
            else:
                return None
        except:
            print("ERROR: Cannot read from database.", file=sys.stderr)
            return None

    def getDependencies(self, path):
        if self.closed:
            return None
        try:
            cur=self.connection.cursor()
            cur.execute("SELECT Id FROM Paths WHERE Path = ?", (path,))
            result = cur.fetchone()
            if result:
                id=result[0]
                dependencies=[]
                projectroot=os.path.dirname(os.path.dirname(self.path))
                cur.execute("SELECT * FROM Dependencies WHERE Id=%s" % (id))
                rows = cur.fetchall()
                for row in rows:
                    dependencies.append(os.path.join(projectroot, row[1]))
                return dependencies
            else:
                return None
        except:
            print("ERROR: Cannot read from database.")
            return None

    def write(self, path, timestamp, start, end, dependencies, width, height):
        if self.closed:
            print("ERROR: Database is closed. Writing isn't possible.")
            return None
        
        cur=self.connection.cursor()

        # First, delete all records for given path if present
        cur.execute("SELECT Id FROM Paths WHERE Path = ?", (path,))
        rows = cur.fetchall()
        for row in rows:
            cur.execute("DELETE FROM Paths WHERE Id=%s" % (row[0]))
            cur.execute("DELETE FROM Dependencies WHERE Id=%s" % (row[0]))
        self.connection.commit()

        # Now, write the data
        cur.execute("INSERT INTO Paths(Path, Timestamp, Start, End, Width, Height) VALUES(?, ?, ?, ?, ?, ?)", (path, timestamp, start, end, width, height))
        id = cur.lastrowid

        # Again, make sure we have no associated data in dependency table
        cur.execute("DELETE FROM Dependencies WHERE Id=%s" % (id))

        # Write a list of dependencies
        for dep in dependencies:
            relpath=""
            try:
                relpath=os.path.relpath(os.path.realpath(dep), os.path.realpath(os.path.dirname(os.path.dirname(self.path))))
            except:
                # Workaround for Windows, which gives wrong paths in some cases (returns path on different drive)
                relpath=os.path.realpath(dep)
            cur.execute("INSERT INTO Dependencies(Id, Dependency) VALUES(?, ?)", (id, relpath))
        try:
            self.connection.commit()
        except:
            print("ERROR: Cannot write into database.")
