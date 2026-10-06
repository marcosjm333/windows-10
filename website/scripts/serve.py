"""Serve the Pages base path on loopback without copying or exposing the repo."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import functools
import argparse

DIST = Path(__file__).resolve().parents[1] / 'dist'
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if not urlsplit(self.path).path.startswith('/windows-10/'):
            self.send_response(302)
            self.send_header('Location', '/windows-10/')
            self.end_headers()
            return
        self.path = self.path[len('/windows-10'):]
        super().do_GET()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), functools.partial(Handler, directory=str(DIST)))
    print(f'Novere preview: http://127.0.0.1:{args.port}/windows-10/', flush=True)
    server.serve_forever()
