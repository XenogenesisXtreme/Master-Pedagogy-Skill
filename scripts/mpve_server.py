#!/usr/bin/env python3
"""Run the local MPVE HTTP API.

Endpoints:
  POST /videos
  GET  /videos/{job_id}
  GET  /videos/{job_id}/result
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.mpve_engine import JobStore, MPVEEngine


class MPVEHandler(BaseHTTPRequestHandler):
    engine: MPVEEngine

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/videos":
            self._send(404, {"error": "not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
            job, duplicate = self.engine.submit(payload)
            self._send(200 if duplicate else 202, {"job": job, "duplicate": duplicate})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def do_GET(self) -> None:
        path = urlparse(self.path).path.strip("/").split("/")
        if len(path) not in (2, 3) or path[0] != "videos":
            self._send(404, {"error": "not found"})
            return
        job_id = path[1]
        try:
            job = self.engine.status(job_id)
            if len(path) == 3 and path[2] == "result":
                if job["state"] != "completed":
                    self._send(409, {"error": f"job is {job['state']}; result is not available", "job": job})
                    return
                self._send(200, {"job": job, "result": job["result"]})
            else:
                self._send(200, {"job": job})
        except KeyError:
            self._send(404, {"error": "job not found", "job_id": job_id})
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def log_message(self, format: str, *args) -> None:
        return


def serve(
    host: str = "127.0.0.1",
    port: int = 8787,
    output_root: str | None = None,
    *,
    data_dir: str | None = None,
    workers: int = 1,
) -> None:
    if output_root:
        jobs_root = Path(output_root)
        persistent_root = jobs_root.parent
    else:
        persistent_root = Path(data_dir or os.environ.get("MPVE_DATA_DIR", "build/mpve"))
        jobs_root = persistent_root / "jobs"
    persistent_root.mkdir(parents=True, exist_ok=True)
    jobs_root.mkdir(parents=True, exist_ok=True)
    store = JobStore(jobs_root, db_path=persistent_root / "mpve.sqlite3")
    engine = MPVEEngine(jobs_root, store=store, worker_count=workers)

    class Handler(MPVEHandler):
        pass

    Handler.engine = engine
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"MPVE listening on http://{host}:{port} (data_dir={persistent_root}, workers={workers})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        engine.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data-dir", default=os.environ.get("MPVE_DATA_DIR", "build/mpve"), help="Persistent directory for the SQLite database and video jobs")
    parser.add_argument("--output-root", help="Legacy override for the jobs directory; database is stored in its parent")
    parser.add_argument("--workers", type=int, default=int(os.environ.get("MPVE_WORKERS", "1")))
    args = parser.parse_args()
    serve(args.host, args.port, args.output_root, data_dir=args.data_dir, workers=args.workers)
