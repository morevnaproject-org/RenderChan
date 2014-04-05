# coding: utf-8
__author__ = 'Konstantin Dmitriev'

from puliclient.jobs import TaskDecomposer, CommandRunner, StringParameter
from renderchan.module import RenderChanModuleManager

class RenderChanDecomposer(TaskDecomposer):
   def __init__(self, task):
       self.task = task
       self.task.runner = "renderchan.puli.RenderChanRunner"

       # The decompose method will split the task from start to end in packet_size and call the addCommand method below for each chunk
       self.decompose(task.arguments["start"], task.arguments["end"],
                                    task.arguments["packetSize"], self)

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
                        callback.addCommand(start, end)
                    else:
                        for i in range(fullPacketCount):
                            packetStart = start + i * packetSize
                            packetEnd = packetStart + packetSize - 1
                            callback.addCommand(packetStart, packetEnd)
                        if lastPacketCount:
                            packetStart = start + (i + 1) * packetSize
                            callback.addCommand(packetStart, end)
                else:
                    callback.addCommand(int(frame), int(frame))
        else:
            start = int(start)
            end = int(end)

            length = end - start + 1
            fullPacketCount, lastPacketCount = divmod(length, packetSize)

            if length < packetSize:
                callback.addCommand(start, end)
            else:
                for i in range(fullPacketCount):
                    packetStart = start + i * packetSize
                    packetEnd = packetStart + packetSize - 1
                    callback.addCommand(packetStart, packetEnd)
                if lastPacketCount:
                    packetStart = start + (i + 1) * packetSize
                    callback.addCommand(packetStart, end)

   def addCommand(self, packetStart, packetEnd):
       # get all arguments from the Task
       args = self.task.arguments.copy()

       # change values of start and end
       args["start"] = packetStart
       args["end"] = packetEnd
       args["output"] = args["profile_output"]
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
                      arguments["start"],
                      arguments["end"],
                      arguments["width"],
                      arguments["height"],
                      arguments["format"],
                      updateCompletion)

        updateCompletion(1)