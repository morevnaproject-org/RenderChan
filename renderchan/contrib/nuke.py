__author__ = '036006'

from renderchan.module import RenderChanModule
import subprocess
import os, sys
import re
import random
import tempfile


class RenderChanNukeModule(RenderChanModule):
    """
    RenderChan module for Foundry Nuke (version 15 and newer).
    
    Nuke is a professional compositing software used in the film and 
    television industry for visual effects and motion graphics.
    """
    
    def __init__(self):
        RenderChanModule.__init__(self)
        
        self.conf['binary'] = self.findBinary("nuke")
        self.conf["packetSize"] = 0  # Render all frames in one go
        self.conf["maxNbCores"] = 0  # Use all available cores
        
        # Extra params
        self.extraParams["single"] = "None"
        self.extraParams["write_node"] = ""  # Specific Write node to render
        self.extraParams["proxy"] = "0"  # Use proxy mode
        self.extraParams["disable_gpu"] = "0"  # Disable GPU rendering
        self.extraParams["interactive_mode"] = "1"  # Use -i (interactive license) instead of -t (render license)
    
    def getInputFormats(self):
        return ["nk", "nknc"]  # .nk - Nuke script, .nknc - Nuke Non-Commercial
    
    def getOutputFormats(self):
        return ["exr", "png", "jpg", "tiff", "dpx", "mov", "mp4"]
    
    def _resolve_tcl_expression(self, expr, nk_filename):
        """
        Resolve Nuke TCL expressions to actual file paths.
        
        Common TCL expressions in Nuke:
        - [value root.name] - full path to the .nk file
        - [file tail path] - basename of path
        - [file rootname path] - path without extension
        - [file dirname path] - directory of path
        - [file extension path] - extension of path
        """
        if '[' not in expr:
            return expr
        
        result = expr
        max_iterations = 10  # Prevent infinite loops
        
        for _ in range(max_iterations):
            if '[' not in result:
                break
            
            # Process innermost brackets first
            # Find the innermost [...] expression
            match = re.search(r'\[([^\[\]]+)\]', result)
            if not match:
                break
            
            tcl_expr = match.group(1).strip()
            replacement = None
            
            # [value root.name] - path to .nk file
            if tcl_expr == 'value root.name':
                replacement = nk_filename
            
            # [file tail path] - basename
            elif tcl_expr.startswith('file tail '):
                path = tcl_expr[10:].strip()
                replacement = os.path.basename(path)
            
            # [file rootname path] - remove extension
            elif tcl_expr.startswith('file rootname '):
                path = tcl_expr[14:].strip()
                replacement = os.path.splitext(path)[0]
            
            # [file dirname path] - directory
            elif tcl_expr.startswith('file dirname '):
                path = tcl_expr[13:].strip()
                replacement = os.path.dirname(path)
            
            # [file extension path] - extension
            elif tcl_expr.startswith('file extension '):
                path = tcl_expr[15:].strip()
                replacement = os.path.splitext(path)[1]
            
            # [file join path1 path2 ...] - join paths
            elif tcl_expr.startswith('file join '):
                parts = tcl_expr[10:].strip().split()
                replacement = os.path.join(*parts) if parts else ''
            
            # [getenv VAR] - environment variable
            elif tcl_expr.startswith('getenv '):
                var_name = tcl_expr[7:].strip()
                replacement = os.environ.get(var_name, '')
            
            # [python ...] - skip Python expressions (too complex)
            elif tcl_expr.startswith('python '):
                return None  # Can't resolve Python expressions
            
            if replacement is not None:
                result = result[:match.start()] + replacement + result[match.end():]
            else:
                # Unknown expression - can't resolve
                return None
        
        # Clean up result - remove extra slashes
        result = result.replace('//', '/')
        
        return result
    
    def _extract_node_content(self, content, startPos):
        """
        Extract content inside curly braces, handling nested braces.
        
        Args:
            content: Full file content string
            startPos: Position right after the opening brace
        
        Returns:
            String content between the braces (excluding the braces themselves)
        """
        braceCount = 1
        endPos = startPos
        while braceCount > 0 and endPos < len(content):
            if content[endPos] == '{':
                braceCount += 1
            elif content[endPos] == '}':
                braceCount -= 1
            endPos += 1
        return content[startPos:endPos-1]

    def _expand_sequence_mask(self, filePath):
        """
        Expand %0Nd / %d masks into concrete file list. If nothing matches,
        returns the original masked path.
        """
        percentToken = re.compile(r'%([0-9]*)d')

        if percentToken.search(filePath) is None:
            return [filePath]

        dirPath = os.path.dirname(filePath) or '.'
        baseName = os.path.basename(filePath)
        sequenceFiles = []

        if os.path.isdir(dirPath):
            pattern = re.escape(baseName)

            for _ in percentToken.finditer(baseName):
                width = _.group(1)
                replacement = r"\\d+" if not width else r"\\d{" + width + r"}"
                pattern = percentToken.sub(replacement, pattern, count=1)

            regex = re.compile(r'^' + pattern + r'$')

            for candidate in os.listdir(dirPath):
                if regex.match(candidate):
                    sequenceFiles.append(os.path.join(dirPath, candidate))

        return sorted(sequenceFiles) if sequenceFiles else [filePath]
    
    def analyze(self, filename):
        """
        Analyze a Nuke script to extract dependencies and frame range.
        
        Nuke scripts (.nk) are TCL-based text files that can be parsed
        to find Read nodes (file dependencies) and frame ranges.
        """
        info = {"dependencies": []}
        
        # Regex patterns for parsing Nuke script
        rootNodePattern = re.compile(r'Root\s*\{')
        endFramePattern = re.compile(r'last_frame\s+(\d+)')
        frameRangeNodePattern = re.compile(r'FrameRange\s*\{')
        frameRangeFirstPattern = re.compile(r'first_frame\s+(-?\d+)')
        frameRangeLastPattern = re.compile(r'last_frame\s+(-?\d+)')
        frameRangeDisablePattern = re.compile(r'disable\s+([^\s\}]+)', re.IGNORECASE)
        readNodePattern = re.compile(r'Read\s*\{', re.DOTALL)
        filePathQuotedPattern = re.compile(r'file\s+"([^"]+)"')
        filePathUnquotedPattern = re.compile(r'file\s+(\S+)')

        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except IOError as e:
            print("Error reading Nuke script %s: %s" % (filename, str(e)))
            return info
        
        dirName = os.path.dirname(filename)

        # Parse FrameRange nodes first; take the last enabled one
        frameRangeMatches = list(frameRangeNodePattern.finditer(content))
        startFrame = None
        endFrame = None

        if frameRangeMatches:
            for frMatch in frameRangeMatches:
                frContent = self._extract_node_content(content, frMatch.end())
                frFirstMatch = frameRangeFirstPattern.search(frContent)
                frLastMatch = frameRangeLastPattern.search(frContent)

                if not frFirstMatch or not frLastMatch:
                    continue

                frDisableMatch = frameRangeDisablePattern.search(frContent)
                isDisabled = False
                if frDisableMatch:
                    disableValue = frDisableMatch.group(1).strip().lower()
                    isDisabled = disableValue in ("1", "true", "yes")

                if isDisabled:
                    continue

                startFrame = int(frFirstMatch.group(1).strip())
                endFrame = int(frLastMatch.group(1).strip())

        if startFrame is not None and endFrame is not None:
            info["startFrame"] = startFrame
            info["endFrame"] = endFrame
            print("    Nuke script frame range (FrameRange node): %d to %d" % (startFrame, endFrame))
        
        # Parse Root node for frame range
        if startFrame is None or endFrame is None:
            rootMatch = rootNodePattern.search(content)
            if rootMatch:
                rootContent = self._extract_node_content(content, rootMatch.end())
                endFrameMatch = endFramePattern.search(rootContent)
                if endFrameMatch:
                    info["startFrame"] = 1
                    info["endFrame"] = int(endFrameMatch.group(1).strip())
                    print("    Nuke script frame range (Root node): %d to %d" % (info["startFrame"], info["endFrame"]))

        # Parse Read nodes for dependencies
        readMatches = list(readNodePattern.finditer(content))
        print("    Found %d Read nodes" % len(readMatches))

        for readMatch in readMatches:
            readContent = self._extract_node_content(content, readMatch.end())
            
            # Match file path - handle both quoted and unquoted paths
            fileMatch = filePathQuotedPattern.search(readContent)
            if not fileMatch:
                fileMatch = filePathUnquotedPattern.search(readContent)
            
            if not fileMatch:
                continue
                
            filePath = fileMatch.group(1).strip().strip('"\'')
            
            # Try to resolve TCL expressions
            if '[' in filePath:
                resolvedPath = self._resolve_tcl_expression(filePath, filename)
                if resolvedPath:
                    filePath = resolvedPath
                else:
                    continue
            
            # Clean up path - remove leading ./
            if filePath.startswith('./'):
                filePath = filePath[2:]
            
            # Skip invalid paths
            if not filePath or filePath.startswith('#'):
                continue
            
            # Handle relative paths
            if not os.path.isabs(filePath):
                filePath = os.path.join(dirName, filePath)
            
            # Normalize path
            filePath = os.path.normpath(filePath)

            for depPath in self._expand_sequence_mask(filePath):
                if depPath not in info["dependencies"]:
                    info["dependencies"].append(depPath)
        
        return info
    
    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):
        """
        Render a Nuke script.
        
        Uses Nuke's command-line rendering capabilities with the -x flag
        for executing Write nodes.
        """

        comp = 0.0
        updateCompletion(comp)

        totalFrames = endFrame - startFrame + 1
        # Regex patterns for parsing Nuke's progress output
        frameCompletionPattern = re.compile(r'Frame\s+(\d+)\s+\((\d+)\s+of\s+(\d+)\)') # Frame 1 (1 of 100)
        writeOutputPattern = re.compile(r'Writing\s+(.+)') # Writing /path/to/output.0001.exr
        frameNumberPattern = re.compile(r'\.(\d+)\.') 
        
        # Determine output file path
        # For image sequences, we need to set the pattern with %05d
        # For video formats (mov, mp4), we use the direct path
        if format in RenderChanModule.imageExtensions:
            if extraParams["single"] != "None":
                # Single frame render - output directly to the path
                outputFile = outputPath
            else:
                # Sequence render - Nuke will create the directory automatically
                outputFile = os.path.join(outputPath, "file.%05d." + format)
        else:
            # Video format (mov, mp4) - single file output
            outputFile = outputPath
        
        # Generate a temporary Nuke script that sets output path
        randomString = "%08d" % random.randint(0, 99999999)
        renderScript = os.path.join(
            tempfile.gettempdir(),
            "renderchan-%s-%s.py" % (os.path.basename(filename), randomString)
        )
        
        # Read render script template and substitute parameters
        with open(os.path.join(os.path.dirname(__file__), "nuke", "render.py")) as f:
            scriptContent = f.read()
        
        scriptContent = scriptContent \
            .replace("params[FILENAME]", '"%s"' % filename.replace('\\', '/').replace('"', '\\"')) \
            .replace("params[START_FRAME]", str(startFrame)) \
            .replace("params[END_FRAME]", str(endFrame)) \
            .replace("params[WIDTH]", str(int(extraParams.get("width", 0)))) \
            .replace("params[HEIGHT]", str(int(extraParams.get("height", 0)))) \
            .replace("params[OUTPUT_FILE]", '"%s"' % outputFile.replace('\\', '/').replace('"', '\\"')) \
            .replace("params[FORMAT]", '"%s"' % format) \
            .replace("params[WRITE_NODE]", '"%s"' % extraParams.get("write_node", "")) \
            .replace("params[SINGLE]", '"%s"' % extraParams.get("single", "None"))
        
        with open(renderScript, 'w') as f:
            f.write(scriptContent)

        try:
            # Build command line
            commandline = [self.conf['binary']]
            
            # Choose execution mode:
            # -t = terminal mode (requires render license)
            # -i = interactive mode without GUI (uses interactive license)
            if extraParams.get("interactive_mode", "1") == "1":
                commandline.append("-i")
            else:
                commandline.append("-t")
            
            # Use GPU if available and not disabled
            if extraParams.get("disable_gpu", "0") != "1" and os.environ.get("NUKE_DISABLE_GPU") != "1":
                commandline.append("--gpu")
            else:
                print("================== FORCE DISABLE GPU =====================")
            
            # Proxy mode
            if extraParams.get("proxy", "0") == "1":
                commandline.append("--proxy")
            
            # Execute script and exit
            commandline.append("-x")
            # Execute the Python script
            commandline.append(renderScript)
            
            print('====================================================')
            print('  Nuke Render Command:')
            print('  ' + ' '.join(commandline))
            print('====================================================')
            
            env = os.environ.copy()
            env["PYTHONPATH"] = ""
            
            out = subprocess.Popen(
                commandline,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env
            )
            
            rc = None
            framesWritten = False
            while True:
                line = out.stdout.readline()
                if not line:
                    if rc is not None:
                        break
                
                try:
                    line = line.decode(sys.stdout.encoding or 'utf-8')
                except:
                    line = line.decode('latin-1')
                
                # Skip known harmless warning messages
                lineLower = line.lower()
                if 'no active write operators' in lineLower or 'total render time' in lineLower:
                    continue
                
                print(line, end='')
                sys.stdout.flush()
                
                # Parse progress
                frameMatch = frameCompletionPattern.search(line)
                if frameMatch:
                    currentFrame = int(frameMatch.group(2))
                    total = int(frameMatch.group(3))
                    if total > 0:
                        comp = float(currentFrame) / float(total)
                        updateCompletion(comp)
                
                writeMatch = writeOutputPattern.search(line)
                if writeMatch:
                    # Extract frame number from output filename
                    outputName = writeMatch.group(1)
                    frameNumMatch = frameNumberPattern.search(outputName)
                    if frameNumMatch and totalFrames > 0:
                        frameNum = int(frameNumMatch.group(1))
                        comp = float(frameNum - startFrame + 1) / float(totalFrames)
                        updateCompletion(min(comp, 1.0))
                    # Track that we successfully wrote at least one frame
                    framesWritten = True
                
                rc = out.poll()
            
            print('====================================================')
            if rc == 0 or framesWritten:
                print('  Nuke render completed successfully')
            else:
                print('  Nuke command returns with code %d' % rc)
            print('====================================================')
            
            # Nuke returns code 1 with "no active Write operators" warning even after successful render
            # If we successfully wrote frames, ignore this error
            if rc != 0 and not framesWritten:
                print('  Nuke command failed...')
                raise Exception('Nuke render failed with exit code %d' % rc)
            
            updateCompletion(1.0)
        finally:
            try:
                os.remove(renderScript)
            except:
                pass
