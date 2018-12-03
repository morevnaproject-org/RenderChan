__author__ = 'Konstantin Dmitriev'

import os, sys
import sqlite3
import random
import shutil
import tempfile
from renderchan.utils import mkdirs

class RenderChanCache():
    def __init__(self, path, readonly=False):

        self.connection=None
        self.closed = True
        self.readonly=readonly

        if not os.path.exists(os.path.dirname(path)):
            mkdirs(os.path.dirname(path))

        if self.readonly:
            random_num = "%08d" % (random.randint(0,99999999))
            tmp_path="renderchan-cache-"+random_num+".sqlite"
            tmp_path=os.path.join(tempfile.gettempdir(),tmp_path)
            if os.path.exists(path):
                shutil.copy(path,tmp_path)
            self.path=tmp_path
        else:
            self.path=path



        try:



            self.connection=sqlite3.connect(path)
            self.connection.text_factory = str
            cur=self.connection.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS Paths(Id INTEGER PRIMARY KEY, Path TEXT, Timestamp REAL, Start INTEGER, End INTEGER, Width INTEGER, Height INTEGER);")
            cur.execute("CREATE TABLE IF NOT EXISTS Dependencies(Id INTEGER, Dependency TEXT);")
            self.connection.commit()

            self.closed = False

        except sqlite3.Error as e:

            print("SQLite error: %s" % e.args[0], file=sys.stderr)
            sys.exit(1)

    def __del__(self):
        if not self.closed:
            self.close()

    def close(self):
        self.connection.commit()
        self.connection.close()
        self.closed = True

        if self.readonly:
            try:
                if os.path.exists(self.path):
                    os.remove(self.path)
            except:
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
            print("ERROR: Cannot read from database.", file=sys.stderr)
            return None

    def write(self, path, timestamp, start, end, dependencies, width, height):
        if self.closed:
            print("ERROR: Database is closed. Writing isn't possible.", file=sys.stderr)
            return None
        try:
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
                relpath=os.path.relpath(os.path.realpath(dep), os.path.realpath(os.path.dirname(os.path.dirname(self.path))))
                cur.execute("INSERT INTO Dependencies(Id, Dependency) VALUES(?, ?)", (id, relpath))
            self.connection.commit()
        except:
            print("ERROR: Cannot write into database.", file=sys.stderr)
