from builtins import int
__author__ = 'Ivan Mahonin'

from gettext import gettext as _
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlparse
import io
import os.path
import json

from renderchan.core import RenderChan


class RenderChanHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        args = parse_qs(parsed_url.query)
        for key in args.keys():
            args[key] = args[key][-1]
        
        filename = os.path.abspath(self.server.renderchan_rootdir + os.path.sep + unquote(parsed_url.path))
        
        renderchan = RenderChan()
        renderchan.datadir = self.server.renderchan_datadir
        
        renderchan.track = True
        renderchan.dry_run = True
        
        if "dryRun" in args:
            renderchan.dry_run = bool(args["dryRun"])
        
        if "profile" in args:
            renderchan.setProfile(str(args["profile"]))
        
        if "renderfarmType" in args and str(args["renderfarmType"]) in renderchan.available_renderfarm_engines:
            renderchan.renderfarm_engine = str(args["renderfarmType"])
            if "host" in args:
                if renderchan.renderfarm_engine in ("puli"):
                    renderchan.setHost(str(args["host"]))
                else:
                    print("WARNING: The --host parameter cannot be set for this type of renderfarm.")
            if "port" in args:
                if renderchan.renderfarm_engine in ("puli"):
                    renderchan.setPort(int(args["port"]))
                else:
                    print("WARNING: The --port parameter cannot be set for this type of renderfarm.")
            if "cgru_location" in args:
                renderchan.cgru_location = str(args["cgru_location"])
    
        if "snapshot_to" in args:
            renderchan.snapshot_path = str(args["snapshot_to"])
        
        if "force" in args:
            renderchan.force = bool(args["force"])
    
        error = renderchan.submit('render', filename, bool(args.get("dependenciesOnly")), bool(args.get("allocateOnly")), str(args.get("stereo")))

        reply = {}
        if error:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            reply["error"] = error
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            reply["files"] = renderchan.trackedFiles
        self.wfile.write(bytes(json.dumps(reply, self.wfile), "UTF-8"))

def process_args():
    parser = ArgumentParser(description=_("Run RenderChan HTTP-server."),
            epilog=_("For more information about RenderChan, visit https://morevnaproject.org/renderchan/"))

    parser.add_argument("--host", dest="host",
            action="store",
            default="",
            help=_("Set HTTP-server host."))
    parser.add_argument("--port", dest="port",
            type=int,
            action="store",
            default=80,
            help=_("Set HTTP-server port."))
    parser.add_argument("--root", dest="root",
            action="store",
            default=".",
            help=_("Set HTTP-server root directory."))

    return parser.parse_args()

def main(datadir, argv):
    args = process_args()

    server = HTTPServer((args.host, args.port), RenderChanHTTPRequestHandler)
    server.renderchan_datadir = datadir
    server.renderchan_rootdir = os.path.abspath(args.root)
    server.serve_forever()
