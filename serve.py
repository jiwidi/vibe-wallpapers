#!/usr/bin/env python3
"""Serve the local Nocturne gallery and native composition API."""
from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import sys
import traceback
from urllib.parse import parse_qs, unquote, urlsplit

from compositions import CompositionService, CompositionError, CompositionBusy, Options, ROOT


class GalleryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, service, **kwargs):
        self.service = service
        super().__init__(*args, directory=str(service.root), **kwargs)

    def _json(self, code, body, retry=None):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if retry is not None:
            self.send_header('Retry-After', str(retry))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def _local_host(self):
        host = self.headers.get('Host', '').split(':', 1)[0].lower()
        if host == 'localhost':
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def do_GET(self):
        if not self._local_host():
            self._json(403, {'error': 'this server accepts localhost requests only'})
            return
        parsed = urlsplit(self.path)
        if parsed.path == '/api/health':
            self._json(200, {'composition': True})
            return
        if parsed.path == '/api/compose':
            self._compose(parsed.query)
            return
        if parsed.path.startswith('/api/'):
            self._json(404, {'error': 'unknown API endpoint'})
            return
        if not self._static_allowed(parsed.path):
            self.send_error(404, 'File not found')
            return
        super().do_GET()

    def do_HEAD(self):
        if not self._local_host():
            self._json(403, {'error': 'this server accepts localhost requests only'})
            return
        path = urlsplit(self.path).path
        if path == '/api/health':
            self._json(200, {'composition': True})
        elif path.startswith('/api/'):
            self._json(405, {'error': 'use GET for composition rendering'})
        elif self._static_allowed(path):
            super().do_HEAD()
        else:
            self.send_error(404, 'File not found')

    def _static_allowed(self, raw_path):
        decoded = unquote(raw_path)
        parts = Path(decoded.lstrip('/')).parts
        if any(part.startswith('.') for part in parts):
            return False
        path = (self.service.root / decoded.lstrip('/')).resolve()
        if not path.is_relative_to(self.service.root):
            return False
        if not parts:
            return True
        # Keep repository internals private while serving all gallery media.
        return (parts[0] in ('gallery', 'wallpapers', 'assets')
                or (parts[0] == 'research' and path.suffix == '.md')
                or (len(parts) == 1 and parts[0] in ('index.html', 'favicon.ico', 'README.md')))

    def list_directory(self, path):
        self.send_error(404, 'Directory listing is disabled')
        return None

    def _compose(self, query):
        try:
            if len(query) > 1024:
                raise CompositionError('query is too long')
            values = parse_qs(query, keep_blank_values=True, max_num_fields=12)
            allowed = {'id', 'layout', 'width', 'height', 'density', 'seed', 'download'}
            if values.keys() - allowed or any(len(v) != 1 for v in values.values()):
                raise CompositionError('unknown or repeated query parameter')
            def text(name, default):
                return values.get(name, [default])[0]
            def integer(name, default):
                value = text(name, str(default))
                if not re.fullmatch(r'[0-9]{1,5}', value):
                    raise CompositionError(name + ' must be an integer')
                return int(value)
            download = text('download', '0')
            if download not in ('0', '1'):
                raise CompositionError('download must be 0 or 1')
            options = Options(text('id', ''), text('layout', 'fill'), integer('width', 1280),
                              integer('height', 540), integer('density', 3), integer('seed', 0))
            result = self.service.render(options)
            # Open before headers, so a concurrent cache prune cannot break delivery.
            with result.path.open('rb') as source:
                size = os.fstat(source.fileno()).st_size
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(size))
                self.send_header('X-Composition-Cache', 'hit' if result.cache_hit else 'miss')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('X-Content-Type-Options', 'nosniff')
                if download == '1':
                    filename = f'{options.id}-{options.layout}-{options.width}x{options.height}.png'
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                shutil.copyfileobj(source, self.wfile)
        except CompositionBusy as error:
            self._json(503, {'error': str(error)}, retry=2)
        except (CompositionError, ValueError) as error:
            self._json(400, {'error': str(error)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc(file=sys.stderr)
            self._json(500, {'error': 'composition rendering failed; see the local server log'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--bind', default='127.0.0.1')
    args = parser.parse_args()
    if args.bind != 'localhost':
        try:
            if not ipaddress.ip_address(args.bind).is_loopback or ':' in args.bind:
                parser.error('--bind must be localhost or an IPv4 loopback address')
        except ValueError:
            parser.error('--bind must be localhost or an IPv4 loopback address')
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    service = CompositionService(ROOT)
    def handler(*handler_args, **handler_kwargs):
        return GalleryHandler(*handler_args, service=service, **handler_kwargs)
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    server.daemon_threads = True
    print(f'Nocturne: http://{args.bind}:{args.port} — composition API ready', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
