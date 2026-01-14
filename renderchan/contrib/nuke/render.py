__author__ = '036006'

"""
Nuke render script for RenderChan.

This script is executed inside Nuke's Python environment to configure
and render the scene. Parameters are substituted by RenderChan before execution.
"""

import nuke

# Supported format mapping for Nuke Write node
FORMAT_MAP = {
    "exr": "exr",
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "tiff": "tiff",
    "tif": "tiff",
    "dpx": "dpx",
    "mov": "mov",
    "mp4": "mov",
}

# Parameters (will be replaced by RenderChan)
FILENAME = params[FILENAME]
START_FRAME = params[START_FRAME]
END_FRAME = params[END_FRAME]
WIDTH = params[WIDTH]
HEIGHT = params[HEIGHT]
OUTPUT_FILE = params[OUTPUT_FILE]
FORMAT = params[FORMAT]
WRITE_NODE = params[WRITE_NODE]
SINGLE = params[SINGLE]
PROXY = params[PROXY]

# Load the script
nuke.scriptOpen(FILENAME)

# Force proxy mode according to RenderChan settings (default off)
try:
    proxy_enabled = bool(int(PROXY))
except Exception:
    proxy_enabled = False
nuke.root()["proxy"].setValue(proxy_enabled)

# Set frame range
if START_FRAME > 0 and END_FRAME > 0:
    nuke.root()["first_frame"].setValue(START_FRAME)
    nuke.root()["last_frame"].setValue(END_FRAME)

# Set format/resolution if specified
# if WIDTH > 0 and HEIGHT > 0:
#     fmt = nuke.addFormat("%d %d RenderChan" % (WIDTH, HEIGHT))
#     nuke.root()["format"].setValue(fmt)

# Find Write nodes and select the best one
write_nodes = [n for n in nuke.allNodes("Write")]
target_write = None

if WRITE_NODE:
    # User specified a specific Write node
    for w in write_nodes:
        if w.name() == WRITE_NODE:
            target_write = w
            break
    if not target_write:
        print("Warning: Write node '%s' not found" % WRITE_NODE)

if not target_write and write_nodes:
    # Priority 1: Find enabled Write node named "Write1" (Nuke default)
    for w in write_nodes:
        if w.name() == "Write1" and not w["disable"].value():
            target_write = w
            break
    
    # Priority 2: Find first enabled Write node
    if not target_write:
        for w in write_nodes:
            if not w["disable"].value():
                target_write = w
                break
    
    # Priority 3: Use first Write node (even if disabled)
    if not target_write:
        target_write = write_nodes[0]
        print("Warning: All Write nodes are disabled, using '%s'" % target_write.name())

if not target_write:
    # No Write nodes exist - create one connected to output
    print("No Write nodes found, creating one...")
    
    # Find the output node (last node in the tree)
    output_node = None
    
    # First, look for Output node
    for n in nuke.allNodes("Output"):
        output_node = n.input(0) if n.input(0) else n
        break
    
    # Otherwise, find a node with no dependent nodes (end of tree)
    if not output_node:
        for n in nuke.allNodes():
            if n.Class() not in ("Viewer", "Write", "BackdropNode"):
                dependents = n.dependent()
                if not dependents or all(d.Class() in ("Viewer", "Write") for d in dependents):
                    output_node = n
                    break
    
    if output_node:
        target_write = nuke.createNode("Write", inpanel=False)
        target_write.setInput(0, output_node)
        print("Created Write node connected to '%s'" % output_node.name())
    else:
        raise Exception("Cannot find suitable node to connect Write node")

if target_write:
    target_write["file"].setValue(OUTPUT_FILE)
    
    # Set file type based on format
    file_type = FORMAT_MAP.get(FORMAT, "exr")
    target_write["file_type"].setValue(file_type)
    
    # Ensure Write node is enabled
    target_write["disable"].setValue(False)
    
    # Get frame range - use provided values or from script
    start = START_FRAME if START_FRAME > 0 else int(nuke.root()["first_frame"].value())
    end = END_FRAME if END_FRAME > 0 else int(nuke.root()["last_frame"].value())
    
    print("Rendering frames %d to %d" % (start, end))
    print("Output: %s" % target_write["file"].value())
    
    # Render
    if SINGLE != "None":
        nuke.execute(target_write, int(SINGLE), int(SINGLE))
    else:
        nuke.execute(target_write, start, end)

nuke.scriptClose()
