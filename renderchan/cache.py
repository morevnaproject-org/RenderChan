__author__ = 'Konstantin Dmitriev'

import os, sys
import sqlite3

class RenderChanCache():
    def __init__(self, path):

        self.path=path
        self.connection=None

        try:
            self.connection=sqlite3.connect(path)
            cur=self.connection.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS Paths(Id INTEGER PRIMARY KEY, Path TEXT, Timestamp REAL, Start INTEGER, End INTEGER);")
            cur.execute("CREATE TABLE IF NOT EXISTS Dependencies(Id INTEGER, Dependency TEXT);")
            self.connection.commit()

        except sqlite3.Error, e:

            print "Error %s:" % e.args[0]
            sys.exit(1)

    def __del__(self):
        self.connection.commit()
        self.connection.close()
        print "Cache closed."

    def getInfo(self, path):
        cur=self.connection.cursor()
        cur.execute("SELECT * FROM Paths WHERE Path='%s'" % (path))
        row = cur.fetchone()
        if row:
            info={}
            info['timestamp']=row[2]
            info['startFrame']=row[3]
            info['endFrame']=row[4]
            return info
        else:
            return None

    def getDependencies(self, path):
        cur=self.connection.cursor()
        cur.execute("SELECT Id FROM Paths WHERE Path='%s'" % (path))
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

    def write(self, path, timestamp, start, end, dependencies):

        cur=self.connection.cursor()

        # First, delete all records for given path if present
        cur.execute("SELECT Id FROM Paths WHERE Path='%s'" % (path))
        rows = cur.fetchall()
        for row in rows:
            cur.execute("DELETE FROM Paths WHERE Id=%s" % (row[0]))
            cur.execute("DELETE FROM Dependencies WHERE Id=%s" % (row[0]))
        self.connection.commit()

        # Now, write the data
        cur.execute("INSERT INTO Paths(Path, Timestamp, Start, End) VALUES('%s', %f, %s, %s)" % (path, timestamp, start, end))
        id = cur.lastrowid
        for dep in dependencies:
            relpath=os.path.relpath(os.path.realpath(dep), os.path.realpath(os.path.dirname(os.path.dirname(self.path))))
            cur.execute("INSERT INTO Dependencies(Id, Dependency) VALUES(%s, '%s')" % (id, relpath))
        self.connection.commit()
