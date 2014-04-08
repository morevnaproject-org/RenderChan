# coding: utf-8
__author__ = 'Konstantin Dmitriev'

from puliclient.jobs import TaskDecomposer, CommandRunner, StringParameter
from renderchan.module import RenderChanModuleManager
import os, shutil
import subprocess

def copytree(src, dst, symlinks=False, hardlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    os.makedirs(dst)
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

class RenderChanDecomposer(TaskDecomposer):
   def __init__(self, task):
       self.task = task
       self.task.runner = "renderchan.puli.RenderChanRunner"

       # The decompose method will split the task from start to end in packet_size and call the addCommand method below for each chunk
       self.decompose(task.arguments["start"], task.arguments["end"],
                                    task.arguments["packetSize"], self.addCommand)


   def decompose(self, start, end, packetSize, callback, framesList=""):
        # FIXME: This actually should be moved to TaskDecomposer class (Puli upstream)
        packetSize = int(packetSize)
        if len(framesList) != 0:
            frames = framesList.split(",")
            for frame in frames:
                if "-" in frame:
                    frameList = frame.split("-")
                    start = int(frameList[0])
                    end = int(frameList[1])

                    length = end - start + 1
                    fullPacketCount, lastPacketCount = divmod(length, packetSize)

                    if length < packetSize:
                        callback(start, end)
                    else:
                        for i in range(fullPacketCount):
                            packetStart = start + i * packetSize
                            packetEnd = packetStart + packetSize - 1
                            callback(packetStart, packetEnd)
                        if lastPacketCount:
                            packetStart = start + (i + 1) * packetSize
                            callback(packetStart, end)
                else:
                    callback(int(frame), int(frame))
        else:
            start = int(start)
            end = int(end)

            length = end - start + 1
            fullPacketCount, lastPacketCount = divmod(length, packetSize)

            if length < packetSize:
                callback(start, end)
            else:
                for i in range(fullPacketCount):
                    packetStart = start + i * packetSize
                    packetEnd = packetStart + packetSize - 1
                    callback(packetStart, packetEnd)
                if lastPacketCount:
                    packetStart = start + (i + 1) * packetSize
                    callback(packetStart, end)

   def addCommand(self, packetStart, packetEnd):
       # get all arguments from the Task
       args = self.task.arguments.copy()

       # change values of start and end
       args["start"] = packetStart
       args["end"] = packetEnd
       args["output"] = args["profile_output"]
       if args["format"]=="avi":
            # For avi files we need to give each packet different name
            args["output"] = os.path.splitext(args["output"])[0]+"-"+str(packetStart)+"-"+str(packetEnd)+".avi"
            # And also keep track of created files wihin a special list
            output_list = os.path.splitext(args["profile_output"])[0]+".txt"
            f = open(output_list,'a')
            f.write("file '%s'\n" % (args["output"]))
            f.close()

       cmdName = "%s_%s_%s" % (self.task.name, str(packetStart), str(packetEnd))

       # Add the command to the Task
       self.task.addCommand(cmdName, args)

class RenderChanRunner(CommandRunner):

    def execute(self, arguments, updateCompletion, updateMessage, updateStats ):

        print 'Running module "%s"' % arguments["module"]
        updateCompletion(0.0)

        moduleManager = RenderChanModuleManager()

        module = moduleManager.get(arguments["module"])
        module.render(arguments["filename"],
                      arguments["output"],
                      int(arguments["start"]),
                      int(arguments["end"]),
                      arguments["width"],
                      arguments["height"],
                      arguments["format"],
                      module.conf["compatVersion"],
                      updateCompletion)

        updateCompletion(1)


class RenderChanPostDecomposer(TaskDecomposer):
   def __init__(self, task):
       self.task = task
       self.task.runner = "renderchan.puli.RenderChanPostRunner"
       #self.ranges=[]

       # The decompose method will split the task from start to end in packet_size and call the addCommand method below for each chunk
       #self.decompose(task.arguments["start"], task.arguments["end"],
       #                             task.arguments["packetSize"], self.addRange)

       # get all arguments from the Task
       args = self.task.arguments.copy()

       # change values of start and end
       #args["ranges"] = self.ranges
       cmdName = "%s_%s" % (self.task.name, "post")

       # Add the command to the Task
       self.task.addCommand(cmdName, args)


class RenderChanPostRunner(CommandRunner):

    def execute(self, arguments, updateCompletion, updateMessage, updateStats ):

        updateCompletion(0.0)

        output=arguments["output"]
        profile_output=arguments["profile_output"]
        profile_output_list=os.path.splitext(profile_output)[0]+".txt"

        if arguments["format"]=="avi":
            # We need to merge the rendered files into single one
            subprocess.check_call(["ffmpeg", "-y", "-f", "concat", "-i", profile_output_list, "-c", "copy", profile_output])
            os.remove(profile_output_list)
            updateCompletion(0.5)

        if not os.path.exists(os.path.dirname(output)):
            os.mkdir(os.path.dirname(output))

        if os.path.isdir(profile_output):
            copytree(profile_output, output, hardlinks=True)
        else:
            os.link(profile_output, output)

        updateCompletion(1)
