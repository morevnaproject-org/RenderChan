# coding: utf-8
__author__ = 'Konstantin Dmitriev'

from puliclient.jobs import TaskDecomposer, CommandRunner, StringParameter
from renderchan.module import RenderChanModuleManager
from renderchan.utils import touch
from renderchan.utils import sync
from renderchan.utils import float_trunc
from renderchan.utils import copytree
import os
import subprocess
import shutil


class RenderChanDecomposer(TaskDecomposer):
    def __init__(self, task):
        self.task = task
        self.task.runner = "renderchan.puli.RenderChanRunner"

        if os.path.exists(os.path.splitext(task.arguments["profile_output"])[0] + ".txt"):
            os.remove(os.path.splitext(task.arguments["profile_output"])[0] + ".txt")
        if os.path.exists(os.path.splitext(task.arguments["profile_output"])[0] + "-alpha.txt"):
            os.remove(os.path.splitext(task.arguments["profile_output"])[0] + "-alpha.txt")

        if task.arguments["packetSize"] != 0:
            # The decompose method will split the task from start to end in packet_size and call the addCommand method below for each chunk
            self.decompose(task.arguments["start"], task.arguments["end"],
                           task.arguments["packetSize"], self.addCommand)
        else:
            self.addCommand(task.arguments["start"], task.arguments["end"])


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
        if args["packetSize"] != 0:
            # We need to give each packet different name
            args["output"] = os.path.splitext(args["output"])[0] + "-" + str(packetStart) + "-" + str(packetEnd) + "." + \
                             args["format"]
            # And also keep track of created files within a special list
            output_list = os.path.splitext(args["profile_output"])[0] + ".txt"
            f = open(output_list, 'a')
            f.write("file '%s'\n" % (args["output"]))
            f.close()
            if args.has_key("extract_alpha") and args["extract_alpha"] == "1":
                output_list = os.path.splitext(args["profile_output"])[0] + "-alpha.txt"
                f = open(output_list, 'a')
                alpha_output = os.path.splitext(args["output"])[0] + "-alpha" + os.path.splitext(args["output"])[1]
                f.write("file '%s'\n" % (alpha_output))
                f.close()

        cmdName = "%s_%s_%s" % (self.task.name, str(packetStart), str(packetEnd))

        # Add the command to the Task
        self.task.addCommand(cmdName, args)


class RenderChanRunner(CommandRunner):
    def execute(self, arguments, updateCompletion, updateMessage, updateStats):
        print 'Running module "%s"' % arguments["module"]
        updateCompletion(0.0)

        if not os.path.exists(os.path.dirname(arguments["output"])):
            os.makedirs(os.path.dirname(arguments["output"]))

        moduleManager = RenderChanModuleManager()

        module = moduleManager.get(arguments["module"])
        module.execute(arguments["filename"],
                       arguments["output"],
                       int(arguments["start"]),
                       int(arguments["end"]),
                       arguments["width"],
                       arguments["height"],
                       arguments["format"],
                       arguments["fps"],
                       arguments["audio_rate"],
                       updateCompletion,
                       arguments)

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
    def execute(self, arguments, updateCompletion, updateMessage, updateStats):

        updateCompletion(0.0)

        jobs = [(arguments["output"], arguments["profile_output"])]
        if arguments.has_key("extract_alpha") and arguments["extract_alpha"] == "1":
            alpha_job = []
            alpha_job.append(
                os.path.splitext(arguments["output"])[0] + "-alpha" + os.path.splitext(arguments["output"])[1])
            alpha_job.append(os.path.splitext(arguments["profile_output"])[0] + "-alpha" +
                             os.path.splitext(arguments["profile_output"])[1])
            jobs.append(alpha_job)

        for job in jobs:
            output = job[0]
            profile_output = job[1]
            profile_output_list = os.path.splitext(profile_output)[0] + ".txt"

            if arguments["packetSize"] > 0:

                # We need to merge the rendered files into single one

                print "Merging: %s" % profile_output

                # But first let's check if we really need to do that
                uptodate = False
                if os.path.exists(profile_output):
                    if os.path.exists(profile_output + ".done") and \
                                    float_trunc(os.path.getmtime(profile_output + ".done"), 1) >= arguments["maxTime"]:
                        # Hurray! No need to merge that piece.
                        uptodate = True
                    else:
                        if os.path.isdir(profile_output):
                            shutil.rmtree(profile_output)
                        else:
                            os.remove(profile_output)

                if not uptodate:
                    if arguments["format"] == "avi":
                        subprocess.check_call(
                            ["ffmpeg", "-y", "-f", "concat", "-i", profile_output_list, "-c", "copy", profile_output])
                    else:
                        # Merge all sequences into single directory
                        f = open(profile_output_list, 'r')
                        for line in f.readlines():
                            line = line.strip()
                            line = line[6:-1]
                            print line
                            copytree(line, profile_output, hardlinks=True)
                        f.close()
                        # Add LST file
                        lst_path = os.path.splitext(profile_output)[0] + ".lst"
                        f = open(lst_path, 'w')
                        f.write("FPS %s\n" % arguments["fps"])
                        for filename in sorted(os.listdir(profile_output)):
                            if filename.endswith(arguments["format"]):
                                f.write("%s/%s\n" % ( os.path.basename(profile_output), filename ))
                        f.close()
                        # Compatibility
                        if arguments["projectVersion"] < 1:
                            f = open(os.path.join(profile_output, "file.lst"), 'w')
                            f.write("FPS %s\n" % arguments["fps"])
                            for filename in sorted(os.listdir(profile_output)):
                                if filename.endswith(arguments["format"]):
                                    f.write("%s\n" % filename)
                            f.close()
                    os.remove(profile_output_list)
                    touch(profile_output + ".done", arguments["maxTime"])
                else:
                    print "  This chunk is already merged. Skipping."
                updateCompletion(0.5)

            sync(profile_output, output)

            #touch(output+".done",arguments["maxTime"])
            touch(output, arguments["maxTime"])

        updateCompletion(1)
