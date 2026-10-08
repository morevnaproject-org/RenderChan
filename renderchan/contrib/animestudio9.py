__author__ = '036006'

from renderchan.module import RenderChanModule
from renderchan.utils import is_true_string
from renderchan import ui
import subprocess
import os, sys
import threading
import errno
import re
import locale
import platform

FPS_PATTERN = re.compile(r"^fps\s+(\d+)")

class RenderChanAnimestudio9Module(RenderChanModule):
    def __init__(self):
        RenderChanModule.__init__(self)
        
        self.conf["binary"]=self.findBinary("animestudio9")
        self.conf["packetSize"]=0
        self.conf["maxNbCores"]=1

        # Extra params
        self.extraParams["layer_composition"]="1"
        #self.extraParams['use_own_dimensions']='1'
        self.extraParams["half_size"]="0"
        

    def getInputFormats(self):
        return ["anme"]

    def getOutputFormats(self):
        return ["png"]

    def analyze(self, filename):
        info={ "dependencies":[], "width": 0, "height": 0 }

        try:
            lines = self._read_file_lines(filename)
        except IOError as e:
            ui.error("Error reading AnimeStudio9 file %s: %s" % (filename, str(e)))
            return info

        frame_pattern = re.compile(r"^frame_range\s+(\d+)\s+(\d+)")
        dimensions_pattern = re.compile(r"^dimensions\s+(\d+)\s+(\d+)")
        dependency_pattern = re.compile(r"^(image|audio_file|soundtrack)\s+\"(.*)\"")

        base_dir = os.path.dirname(os.path.abspath(filename))
        dependencies = []
        seen_dependencies = set()

        for line in lines:
            stripped = line.strip()
            match = frame_pattern.match(stripped)
            if match:
                # Temporarily disabled: generating .lst files for compositions breaks
                # packet merging, and the .lst files themselves fail to merge properly.
                # A robust solution requires moving composition .lst generation to
                # core.py, which is currently deferred.
                # info["startFrame"] = int(match.group(1))
                # info["endFrame"] = int(match.group(2))
                # print("    AnimeStudio9 frame range: %d to %d" % (info["startFrame"], info["endFrame"]))
                continue

            match = FPS_PATTERN.match(stripped)
            if match:
                info["fps"] = int(match.group(1))
                ui.info("    AnimeStudio9 fps: %d" % info["fps"])
                continue

            match = dimensions_pattern.match(stripped)
            if match:
                info["width"] = int(match.group(1))
                info["height"] = int(match.group(2))
                continue

            match = dependency_pattern.match(stripped)
            if match:
                dep_path = match.group(2).strip()
                resolved = self._resolve_dependency_path(base_dir, dep_path)
                if resolved and resolved not in seen_dependencies:
                    seen_dependencies.add(resolved)
                    dependencies.append(resolved)

        if len(dependencies) > 0:
            ui.info("    AnimeStudio9 dependencies: %d" % len(dependencies))
            info["dependencies"] = dependencies
        return info

    def render(self, filename, outputPath, startFrame, endFrame, format, updateCompletion, extraParams={}):

        comp = 0.0
        updateCompletion(comp)

        render_tasks = []
        temp_files = []
        comp_names = []

        try:
            file_lines = self._read_file_lines(filename)
        except IOError as e:
            ui.error("Error reading AnimeStudio9 file %s: %s" % (filename, str(e)))
            raise Exception("AnimeStudio9 render failed: unable to read %s" % filename)

        fps_value = self._extract_fps(file_lines)
        if fps_value is None:
            ui.error("AnimeStudio9 fps not found in %s" % filename)
            raise Exception("AnimeStudio9 render failed: fps not found in %s" % filename)

        layer_comp_value = extraParams.get("layer_composition", "1")
        layer_comp_enabled = is_true_string(layer_comp_value) or layer_comp_value.upper() == "ALL"

        if layer_comp_enabled:
            ui.info('====================================================')
            ui.info('  AnimeStudio9 layer_composition: enabled (%s)' % layer_comp_value)
            compositions = self._parse_layer_compositions(file_lines)
            target_folder = outputPath

            comp_names = [name for name, _ in compositions]
            ui.info('====================================================')
            ui.info('  AnimeStudio9 compositions: %d' % len(comp_names))
            if comp_names:
                ui.info('   ' + ', '.join(comp_names))
            else:
                ui.info('   (no compositions found)')
            ui.info('====================================================')

            if compositions:
                for comp_name, layer_ids in compositions:
                    temp_path = self._create_composition_file(filename, file_lines, comp_name, layer_ids)
                    temp_files.append(temp_path)
                    render_tasks.append((temp_path, target_folder))
            else:
                render_tasks.append((filename, target_folder))
        else:
            ui.info('====================================================')
            ui.info('  AnimeStudio9 layer_composition: DISABLED')
            ui.info('====================================================')
            render_tasks.append((filename, outputPath))

        total_tasks = float(len(render_tasks))
        completed = 0.0

        try:
            grand = 0.0
            task_frames = []
            for target_file, target_output in render_tasks:
                frames = self._frame_range(target_file)
                task_frames.append(frames)
                grand += frames
            if grand <= 0:
                grand = 1.0
            done_frames = 0.0
            for i, (target_file, target_output) in enumerate(render_tasks):
                if i < len(comp_names):
                    ui.progress_label("Rendering " + comp_names[i])
                cb = (lambda base=done_frames, tf=task_frames[i]: (
                    lambda produced: updateCompletion((base + produced) / grand)))()
                self._render_single(target_file, target_output, extraParams, fps_value, startFrame, endFrame, progress_cb=cb)
                done_frames += task_frames[i]
                updateCompletion(done_frames / grand)

            if not render_tasks:
                updateCompletion(1)
        finally:
            for temp_path in temp_files:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _frame_range(self, path):
        try:
            with open(path, 'rb') as f:
                text = f.read().decode('utf-8', errors='replace')
        except (IOError, OSError):
            return 0
        m = re.search(r"frame_range\s+(\d+)\s+(\d+)", text)
        if m:
            return int(m.group(2)) - int(m.group(1)) + 1
        return 0

    def _poll_frames(self, outputPath, existing_pngs, total_frames, progress_cb, stop):
        last = -1
        while not stop.is_set():
            try:
                count = len([f for f in os.listdir(outputPath) if f.endswith(".png")]) - len(existing_pngs)
            except OSError:
                count = last
            if count != last and count >= 0:
                last = count
                progress_cb(min(count, total_frames))
            stop.wait(0.5)

    def _render_single(self, filename, outputPath, extraParams, fps_value, startFrame=None, endFrame=None, progress_cb=None):

        existing_pngs = set()
        if os.path.isdir(outputPath):
            for f in os.listdir(outputPath):
                if f.endswith(".png"):
                    existing_pngs.add(f)

        try:
            os.makedirs(outputPath)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(outputPath):
                pass
            else: raise

        # Remove path conversion for now
        # if (platform.system()=="Linux"):
        #     # Workaround for Wine
        #     filename_cli=filename.replace("/", "\\")
        #     outputPath_cli=outputPath.replace("/", "\\")
        # else:
        filename_cli=filename
        outputPath_cli=outputPath
        
        commandline=[self.conf['binary'], "-r", filename_cli, "-v", "-f", "png", "-outfolder", outputPath_cli]

        # Temporarily disabled: generating .lst files for compositions breaks
        # packet merging, and the .lst files themselves fail to merge properly.
        # A robust solution requires moving composition .lst generation to
        # core.py, which is currently deferred.
        # if startFrame is not None:
        #     commandline.extend(["-start", str(int(startFrame))])
        # if endFrame is not None:
        #     commandline.extend(["-end", str(int(endFrame))])

        if platform.system()=="Linux" and self.conf['binary'].lower().endswith(".exe"):
            commandline = ["wine"] + commandline
        
        if is_true_string(extraParams["half_size"]):
            commandline.append("-halfsize")
            commandline.append("yes")

        ui.info('====================================================')
        ui.info('  AnimeStudio9 Render Command:')
        ui.info('  ' + ' '.join(commandline))
        ui.info('====================================================')

        out = subprocess.Popen(commandline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        total_frames = self._frame_range(filename)
        if total_frames <= 0 and startFrame is not None and endFrame is not None:
            total_frames = endFrame - startFrame + 1
        stop_polling = threading.Event()
        poller = None
        if progress_cb and total_frames > 0:
            poller = threading.Thread(target=self._poll_frames,
                                      args=(outputPath, existing_pngs, total_frames, progress_cb, stop_polling),
                                      daemon=True)
            poller.start()
        try:
            rc = None
            while True:
                    line = out.stdout.readline()
                    if not line:
                            if rc is not None:
                                    break
                    try:
                        line_decoded = line.decode(locale.getpreferredencoding() or 'utf-8')
                    except:
                        line_decoded = line.decode('latin-1')

                    if "send_buffer Failed to get a sample" in line_decoded:
                        rc = out.poll()
                        continue

                    ui.info(line_decoded.rstrip())
                    sys.stdout.flush()

                    rc = out.poll()
        finally:
            stop_polling.set()
            if poller is not None:
                poller.join(timeout=1)

        ui.info('====================================================')
        if rc == 0:
            ui.info('  AnimeStudio9 render completed successfully')
        else:
            ui.info('  AnimeStudio9 command returns with code %d' % rc)
        ui.info('====================================================')

        if rc != 0:
            raise Exception('AnimeStudio9 render failed with exit code %d' % rc)
        
        directory = os.fsencode(outputPath)
    
        for file in sorted(os.listdir(directory)):
             filename = os.fsdecode(file)
             if filename.endswith(".png") and filename not in existing_pngs:
                 lstfile=os.path.join(outputPath, filename[:-10]+".lst")
                 if not os.path.exists(lstfile):
                    with open(lstfile, "w") as text_file:
                        text_file.write(f"FPS {fps_value}\n")
                 with open(lstfile, "a") as text_file:
                    text_file.write(filename+"\n")

    def _read_file_lines(self, filename):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()

    def _extract_fps(self, lines):
        for line in lines:
            match = FPS_PATTERN.match(line.strip())
            if match:
                return int(match.group(1))
        return None

    def _resolve_dependency_path(self, base_dir, raw_path):
        cleaned = raw_path.strip()
        if not cleaned:
            return None

        normalized = os.path.expanduser(cleaned.replace("\\", os.sep))

        if re.match(r"^[A-Za-z]:[\\/]", cleaned):
            return os.path.normpath(normalized)

        if normalized.startswith("//") or normalized.startswith("\\\\"):
            return os.path.normpath(normalized)

        if os.path.isabs(normalized):
            return os.path.normpath(normalized)

        return os.path.normpath(os.path.join(base_dir, normalized))

    def _parse_layer_compositions(self, lines):
        compositions = []
        idx = 0
        while idx < len(lines):
            if lines[idx].strip() == "layercomp":
                name = None
                layer_ids = []

                search_idx = idx + 1
                while search_idx < len(lines):
                    current = lines[search_idx].strip()
                    if current.startswith("name"):
                        name = self._extract_quoted(current)
                    if current.startswith("{"):
                        search_idx += 1
                        break
                    search_idx += 1

                while search_idx < len(lines):
                    current = lines[search_idx].strip()
                    if current.startswith("layer_id"):
                        layer_ids.append(self._extract_quoted(current))
                    elif current.startswith("}"):
                        break
                    search_idx += 1

                if name:
                    compositions.append((name, layer_ids))
                idx = search_idx
            else:
                idx += 1
        return compositions

    def _extract_quoted(self, line):
        match = re.search(r'"(.*)"', line)
        if match:
            return match.group(1)
        return ""

    def _create_composition_file(self, original_path, lines, comp_name, allowed_ids):
        modified_content = self._apply_layer_visibility(lines, set(allowed_ids))
        dir_path = os.path.dirname(original_path)
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        comp_suffix = self._sanitize_comp_name(comp_name)

        candidate = os.path.join(dir_path, f"{base_name}-{comp_suffix}.anme")
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(dir_path, f"{base_name}-{comp_suffix}-{counter}.anme")
            counter += 1

        with open(candidate, "w", encoding="utf-8") as temp_file:
            temp_file.write(modified_content)
        return candidate

    def _apply_layer_visibility(self, lines, allowed_ids):
        new_lines = []
        in_layer = False
        layer_opened = False
        brace_depth = 0
        current_uuid = None

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("layer_type "):
                in_layer = True
                current_uuid = None
                layer_opened = False

            opens = line.count("{")
            closes = line.count("}")

            if in_layer and opens:
                layer_opened = True

            brace_depth += opens

            if in_layer and stripped.startswith("uuid "):
                current_uuid = self._extract_quoted(stripped)

            if in_layer and stripped.startswith("visible") and current_uuid:
                leading = line[:line.find("visible")]
                is_visible = current_uuid in allowed_ids
                line = f"{leading}visible {'true' if is_visible else 'false'}\n"

            brace_depth -= closes

            if in_layer and layer_opened and brace_depth == 0:
                in_layer = False
                current_uuid = None
                layer_opened = False

            new_lines.append(line)

        return "".join(new_lines)

    def _sanitize_comp_name(self, name):
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
        return safe or "comp"
