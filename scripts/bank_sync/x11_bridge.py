#!/usr/bin/env python3
"""Bridge TCP port 6000 to the local X11 unix socket.

Docker Desktop on Linux cannot bind-mount /tmp/.X11-unix unless the user
adds it under Settings -> Resources -> File Sharing. This script exposes
the display over TCP on all interfaces so containers can connect via
``DISPLAY=host.docker.internal:0`` without a socket mount.

Run on the host before starting the automation service with the X11 overlay:

    xhost +local:
    python3 scripts/bank_sync/x11_bridge.py

Leave it running in a terminal while you use headed bank sign-in.
"""

from __future__ import annotations

import argparse
import os
import select
import socket
import sys
from pathlib import Path


def _resolve_socket(display: str) -> Path:
    if display.startswith(":"):
        return Path("/tmp/.X11-unix") / f"X{display[1:]}"
    raise ValueError(f"Unsupported DISPLAY value {display!r}; expected :N")


def _relay(a: socket.socket, b: socket.socket) -> None:
    try:
        while True:
            readable, _, _ = select.select([a, b], [], [])
            if a in readable:
                chunk = a.recv(65536)
                if not chunk:
                    break
                b.sendall(chunk)
            if b in readable:
                chunk = b.recv(65536)
                if not chunk:
                    break
                a.sendall(chunk)
    finally:
        a.close()
        b.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--display",
        default=os.environ.get("DISPLAY", ":0"),
        help="X display to bridge (default: $DISPLAY or :0)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="TCP listen address (default: 0.0.0.0 for Docker Desktop)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6000,
        help="TCP listen port (default: 6000 for display :0)",
    )
    args = parser.parse_args()

    x_socket = _resolve_socket(args.display)
    if not x_socket.exists():
        print(f"X11 socket not found: {x_socket}", file=sys.stderr)
        return 1

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(32)
    print(
        f"X11 bridge listening on {args.host}:{args.port} -> {x_socket}",
        flush=True,
    )

    try:
        while True:
            client, addr = server.accept()
            unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            unix.connect(str(x_socket))
            print(f"Accepted X11 client from {addr[0]}:{addr[1]}", flush=True)
            _relay(client, unix)
    except KeyboardInterrupt:
        print("\nStopping X11 bridge", flush=True)
    finally:
        server.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
