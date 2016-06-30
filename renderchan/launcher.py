__author__ = 'Ivan Mahonin'

from gettext import gettext as _
from argparse import ArgumentParser
import os
import subprocess
import datetime
import pwd


class Launcher:
    def __init__(self):
        self.pidFile = ""
        self.logFile = "-"
        self.outputFile = "-"
        self.sourceDir = ""
        self.renderDir = ""
        self.mountDir = ""
        self.user = ""
        self.projectCommands = []
        
        self.commands = []
        self.dryRun = False

        self.createdDirs = {}
        self.mountedDirs = []
        self.mountedSources = []
        self.projects = []
   
    def file_append(self, file, line):
        if file == "-":
            print(line)
        elif file:
            f = open(file, 'a')
            print(str(line), file=f)
            f.close()

    def now(self):
        return datetime.datetime.utcnow().isoformat()

    def try_file_append(self, files, line, fileType, timeStamp):
        lines = [str(line)]
        if timeStamp:
            lines[0] = self.now() + " " + lines[0]
        
        tried = {}
        for file in files:
            if file in tried:
                continue
            tried[file] = True
            try:
                for l in lines:
                    self.file_append(file, l)
                break
            except Exception as e:
                lines.insert(0, _("Cannot write to file (%s, %s), error: %s") % (fileType, file, str(e)))
                if timeStamp:
                    lines[0] = self.now() + " " + lines[0]

    def log(self, line):
        self.try_file_append([self.logFile, self.outputFile, "-"], line, "log", True)

    def info(self, line):
        self.log(_("Info: ") + line)
        
    def warning(self, line):
        self.log(_("Warning: ") + line)
        
    def error(self, line):
        self.log(_("Error: ") + line)

    def output(self, line):
        self.try_file_append([self.logFile, self.outputFile, "-"], line, "output", False)

    def outHeader(self, line):
        self.output("-----------------------------------------------")
        self.output("-- " + _("Begin"))
        self.output("-- " + self.now())
        self.output("-- " + str(line))
        self.output("-----------------------------------------------")

    def outFooter(self, line):
        self.output("")
        self.output("-----------------------------------------------")
        self.output("-- " + _("End"))
        self.output("-- " + self.now())
        self.output("-----------------------------------------------")
        self.output("")
    
    def check_executable(self, command, comment):
        result = False
        try:
            subprocess.check_call(command)
            result = True
        except subprocess.CalledProcessError:
            pass
        print(_("Check %s (%s): %s") % (command[0], comment, ("success" if result else "fail")))
        return result
    
    def setPidFile(self, pidFile):
        if self.pidFile == pidFile:
            return
        if self.pidFile and os.path.isfile(pidFile):
            os.remove(self.pidFile)

        if pidFile and os.path.isfile(pidFile):
            f = open(pidFile, 'r')
            pid = int(f.read())
            f.close()
            try:
                os.kill(pid, 0)
                self.error(_("Another instance already launched"))
                return False
            except:
                pass
            try:
                os.remove(pidFile)
            except:
                pass
        self.pidFile = pidFile

        if self.pidFile:
            f = open(self.pidFile, 'w')
            f.write(str(os.getpid()))
            f.close()
        return True
    
    def run(self):
        self.info(_("Launch"))
        try:
            for command in self.commands:
                self.info(_("Process: ") + command[0] + " " + command[1])
                if command[0] == "pid":
                    if not self.setPidFile(os.path.abspath(command[1])):
                        break
                elif command[0] == "log":
                    prev = self.logFile
                    self.logFile = os.path.abspath(command[1]) if command[1] != "-" else "-"
                    if self.logFile != prev:
                        self.info(_("Start log"))
                elif command[0] == "out":
                    self.outputFile = os.path.abspath(command[1]) if command[1] != "-" else "-"
                elif command[0] == "src":
                    self.sourceDir = os.path.abspath(command[1])
                elif command[0] == "render":
                    self.renderDir = os.path.abspath(command[1])
                elif command[0] == "mount":
                    self.mountDir = os.path.abspath(command[1])
                elif command[0] == "user":
                    self.user = command[1]
                elif command[0] == "prj-cmd":
                    self.projectCommands.append(command[1])
                elif command[0] == "prj-clear":
                    self.projectCommands = []
                elif command[0] == "run":
                    self.runProjects()
                else:
                    self.error(_("Unknown key: ") + command[0])
        except:
            self.error(_("Unhandled exception"))
        self.umountAll()
        self.setPidFile("")
        self.info(_("Done"))
    
    def runProjects(self):
        self.info(_("Process projects in: ") + self.sourceDir)
        if not self.sourceDir:
            self.error(_("Source directory is not set"))
            return
        if not self.mountDir:
            self.error(_("Mount directory is not set"))
            return
        if not self.renderDir:
            self.error(_("Render directory is not set"))
            return

        self.umountAll()

        self.info(_("Search projects in: ") + self.sourceDir)
        self.projects = []
        self.scan()
        projects = self.projects
        self.projects = []
        
        if len(projects) == 0:
            self.warning(_("No projects found"))
            return
        
        try:        
            self.createDirectory(self.mountDir)
            self.mount(self.mountDir, self.sourceDir)
        except Exception as e:
            self.error(_("Cannot mount source directory %s, error: %s") % (self.sourceDir, str(e)))
            
        prepared = []
        for project in projects:
            self.info(_("Prepare project: ") + project)
            try:
                projectLocal = project[len(self.sourceDir):]
                while len(projectLocal) and projectLocal[0] == os.path.sep:
                    projectLocal = projectLocal[1:]
                
                renderDir = os.path.join(self.renderDir, projectLocal)
                mountDir = os.path.join(self.mountDir, projectLocal)
                
                self.createDirectory(renderDir)
                self.createDirectory(os.path.join(mountDir, "render"))
                self.mount(os.path.join(mountDir, "render"), renderDir)
            
                prepared.append(mountDir)
            except Exception as e:
                self.error(_("Cannot prepare project %s, error: %s") % (project, str(e)))
        self.projects = []

        for project in prepared:
            self.info(_("Run project: ") + project)
            for command in self.projectCommands:
                self.runCommand(command, self.user, project)
        
        self.umountAll()
    
    def scan(self, sourceDir = None, level = 0):
        if level >= 256:
            self.error(_("Max recurse level reached (%s): %s") % ("scan", str(level)))
            return
        
        if not sourceDir:
            sourceDir = self.sourceDir
        
        if os.path.isfile(os.path.join(sourceDir, "project.conf")):
            self.info(_("Project found: ") + sourceDir)
            self.projects.append(sourceDir)
        
        try:
            for file in sorted(os.listdir(sourceDir)):
                if os.path.isdir(os.path.join(sourceDir, file)):
                    self.scan(os.path.join(sourceDir, file), level + 1)
        except Exception as e:
            self.error(_("Cannot scan directory %s, error: %s") % (sourceDir, str(e)))
            
    def runCommand(self, command, user = None, workDir = None, raiseException = False):
        self.info(_("Run command: ") + str(command))
        if self.dryRun:
            return
        
        if user:
            if not isinstance(command, str):
                command = subprocess.list2cmdline(command)
            command = ["sudo", "-u", self.user, "/bin/bash", "-c", command]
        
        self.outHeader(str(command))
        exception = None
        try:
            f = open(self.outputFile, 'ab') if self.outputFile != "-" else None
            subprocess.check_call(command, stdout = f, stderr = f, cwd = workDir)
        except Exception as e:
            exception = e
        finally:
            if f:
                f.close()
        self.outFooter(str(command))
        
        if exception:
            if raiseException:
                raise exception
            else:
                self.error(_("Run command failed (%s), error: %s") % (str(command), str(exception)))            

    def isDirectory(self, path, level = 0):
        if level >= 10:
            self.error(_("Max recurse level reached (%s): %s") % ("isDirectory", str(level)))
            return False
        
        if self.dryRun:
            for i in range(len(self.mountedDirs)):
                t = self.mountedDirs[i]
                s = self.mountedSources[i]
                if len(t) and len(s):
                    if t[-1] != os.path.sep:
                        t = t + os.path.sep
                    if s[-1] != os.path.sep:
                        s = s + os.path.sep
                    if path[0:len(t)] == t and self.isDirectory(s + path[len(t):], level + 1):
                        return True
        if os.path.isdir(path):
            return True
                        
    def createDirectory(self, path):
        if not self.isDirectory(path) and not path in self.createdDirs:
            self.createDirectory(os.path.dirname(path))
            self.info(_("Create directory: %s") % path)
            if self.dryRun:
                self.createdDirs[path] = True
            else:
                os.mkdir(path)
                if self.user:
                    pw = pwd.getpwnam(self.user)
                    os.chown(path, pw.pw_uid, pw.pw_gid)

    def mount(self, targetDir, sourceDir):
        self.info(_("Mount directory '%s' to '%s'") % (sourceDir, targetDir))
        self.runCommand(["mount", "--bind", sourceDir, targetDir], raiseException = True)
        self.mountedDirs.insert(0, targetDir)
        self.mountedSources.insert(0, sourceDir)

    def umount(self, targetDir):
        self.info(_("Unmount directory: ") + targetDir)
        self.runCommand(["umount", targetDir], raiseException = True)
        self.mountedSources.remove( self.mountedSources[self.mountedDirs.index(targetDir)] )
        self.mountedDirs.remove(targetDir)

    def umountAll(self):
        self.info(_("Unmount all"))
        while len(self.mountedDirs):
            try:
                self.umount(self.mountedDirs[0])
            except Exception as e:
                self.error(_("Cannot unmount directory (%s), error %s") % (self.mountedDirs[0], str(e)))
                self.mountedSources.remove(self.mountedSources[0])
                self.mountedDirs.remove(self.mountedDirs[0])


class ConfigParser:
    def __init__(self, file = None, text = None):
        self.commands = []
        self.index = 0
        self.text = ""
        
        if file:
            f = open(file, "r")
            self.text = f.read()
        elif text:
            self.text = text
            
        self.parse()
                
    def parse(self):
        while(self.index < len(self.text)):
            self.parseLine()

    def parseLine(self):
        line = ""
        
        while True:
            begin = self.index
            comment = -1
            nlscreen = -1
            nl = len(self.text)
            quotes = ""

            for i in range(begin, len(self.text)):
                screened = i > 0 and self.text[i-1] == '\\' and (i < 2 or self.text[i-2] != '\\')
                
                rprev = i > 0 and self.text[i-1] == '\r'
                nprev = i > 0 and self.text[i-1] == '\n'
                rcurr = self.text[i] == '\r'
                ncurr = self.text[i] == '\n'
                rnext = i+1 < len(self.text) and self.text[i+1] == '\r'
                nnext = i+1 < len(self.text) and self.text[i+1] == '\n'
                if (rcurr and (nprev or not nnext)) or (ncurr and (rprev or not rnext)):
                    nl = i+1
                    break
                
                if comment < 0 and nlscreen >= 0 and not self.text[i].isspace():
                    nlscreen = -1
    
                if comment < 0 and not screened and (self.text[i] == '"' or self.text[i] == '\''):
                    if quotes and self.text[i] == quotes[-1]:
                        quotes = quotes[0:-1]
                    else: 
                        quotes = quotes + self.text[i]
                    continue
                if comment < 0 and not quotes and nlscreen < 0 and not screened and self.text[i] == '\\':
                    nlscreen = i
                    continue
                if comment < 0 and not quotes and not screened and self.text[i] == '#':
                    comment = i
                    continue

            if nlscreen >= 0:
                line = line + self.text[begin:nlscreen]
            elif comment >= 0:
                line = line + self.text[begin:comment]
            else:
                line = line + self.text[begin:nl]
            
            self.index = nl
            if nlscreen < 0:
                break
        
        command = parseCommand(line)
        if command:
            self.commands.append(command)


def parseCommand(line):
    line = line.strip()
    space = len(line)
    for i in range(len(line)):
        if line[i].isspace():
            space = i
            break
    if space > 0:
        return [line[0:space].strip(), line[space:].strip()]
    return None


def makeArgsParser():
    parser = ArgumentParser(description=_("Run RenderChan launcher."),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))
    parser.add_argument("commands", nargs = '*',
            action="append",
            help=_("Configuration commands"))
    parser.add_argument("--config", dest="config",
            action="store",
            default="",
            help=_("Path to configuration file."))
    parser.add_argument("--dry-run", dest="dryRun",
            action="store_true",
            default=False,
            help=_("Simulate activity."))
    return parser

def main(argv):
    argsParser = makeArgsParser()
    args = argsParser.parse_args(argv)
    
    launcher = Launcher()
    
    if args.dryRun:
        launcher.dryRun = True
    if args.commands and len(args.commands):
        args.commands.remove(args.commands[0])
    
    if args.config:
        launcher.commands = ConfigParser(file = args.config).commands
        if args.commands and len(args.commands): 
            print(_("Ignore command argumens, because %s was set") % ("--config"))
    elif args.commands and len(args.commands):
        for command in args.commands:
            parsed = parseCommand(str(command))
            if parsed:
                launcher.commands.append(parsed)
    else:
        argsParser.print_usage()
        return
    
    launcher.run()
    