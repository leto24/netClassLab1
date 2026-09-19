#!/usr/bin/env python3
"""
TuskChat starter -- hand this to students at the start of M2.

The accept loop and the line-buffering loop are written for you, because those
are the two places where a beginner gets stuck for four hours with nothing to
show. Everything marked TODO is yours.

Run:  python server.py --host 127.0.0.1--port 5050
Test: telnet 127.0.0.1 5050
"""

import argparse
import socket
import threading
import struct

MAX_LINE = 512

# Shared state. Every thread touches this, so every access needs the lock.
clients = {}                       # nickname -> connection object
clients_lock = threading.Lock()
ERRORS = {
    100: "unknown command",
    101: "bad arguments",
    102: "nickname taken",
    103: "not registered",
    104: "no such user",
    105: "line too long",
}





class Client:
    def __init__(self, conn, addr, binary_framing=False):
        self.conn = conn
        self.addr = addr
        self.nick = None
        self.send_lock = threading.Lock()
        self.binary_framing = binary_framing

    def error(self, code):
        self.send_line("ERR {} {}".format(code, ERRORS[code]))

    def broadcast(self, text):
        with clients_lock:
            targets = [c for c in clients.values() if c is not self]
        for c in targets:
            c.send_line(text)

    def send_line(self, text):
        """Always send through here. sendall() loops over partial writes."""
        with self.send_lock:
            try:
                payload = text.encode("utf-8")
                if self.binary_framing:
                    # Send the length of the message as a 4-byte big-endian integer
                    length_prefix = struct.pack('>I', len(payload))
                    self.conn.sendall(length_prefix + payload)
                else:
                    self.conn.sendall((payload + b"\n"))
            except OSError:
                pass


def handle_line(cli, line):
    """
    Handle one complete command line from one client.

    Return "close" to hang up on this client, or None to keep going.

    TODO (M2): NICK, MSG, WHO, QUIT and the ERR codes from the spec.
    TODO (M3): PM, broadcast to everyone but the sender, INFO notices.
    """
    parts = line.split(" ", 1)
    verb = parts[0].upper()
    rest = parts[1] if len(parts) > 1 else ""

    if verb == "NICK":
        # TODO: validate the nickname, reject duplicates (ERR 102),
        #       register it under clients_lock, reply OK, notify others.
        success = False
        with clients_lock:
            if rest not in clients and rest.strip(): # nickname is not taken and not empty
                if cli.nick in clients:
                    old_nick = cli.nick
                    clients.pop(cli.nick) # clears old nickname if changing
                clients.update({rest:cli})
                success = True
        if success:
            cli.nick = rest
            cli.send_line("Nickname validated!")
            try: 
                cli.broadcast("INFO {} has changed nickname to {}".format(old_nick, rest))
                cli.send_line("Nickname changed!")
            except UnboundLocalError: # if no old_nick, then this is a new user
                cli.broadcast("INFO {} has joined the chat".format(cli.nick))
        elif not rest.strip():
            cli.error(101)
        else: 
            cli.error(102)
    elif verb == "MSG":
        if cli.nick is None:
            return cli.error(103)
        if not rest:
            return cli.error(101)
        cli.send_line("OK")
        cli.broadcast("MSG {} {}".format(cli.nick, rest))
    elif verb == "QUIT":
        cli.send_line("OK bye")
        return "close"
    elif verb == "WHO":
        if cli.nick is None:
            return cli.error(103)
        with clients_lock:
            targets = [c for c in clients.values()]
        cli.send_line("WHO " + " ".join([c.nick for c in targets]))
    elif verb == "PM":
        if cli.nick is None:
            return cli.error(103)
        if not rest:
            return cli.error(101)
        try:
            target_nick, message = rest.split(" ", 1)
        except ValueError:
            return cli.error(101)
        with clients_lock:
            target_client = clients.get(target_nick)
        if target_client is None:
            return cli.error(104)
        target_client.send_line("PM {} {}".format(cli.nick, message))
        cli.send_line("OK")
    else:
        cli.error(100)

    return None


def serve_client(conn, addr, binary_mode):
    """
    One thread per client. The buffering loop below is the part students
    most often get wrong, so it is provided -- read it until you can explain
    why the `while b"\\n" in buf` loop is a `while` and not an `if`.
    """
    conn.settimeout(120.0) # drop idle clients after 2 minutes
    cli = Client(conn, addr, binary_framing=binary_mode)
    buf = b""
    try:
        while True:
            if binary_mode:
               # 1. Accumulate exactly 4 bytes for the length prefix
                while len(buf) < 4:
                    chunk = conn.recv(4096)
                    if not chunk:
                        return
                    buf += chunk
                length_prefix = buf[:4]
                buf = buf[4:]
                message_length = struct.unpack('>I', length_prefix)[0]
                if message_length > MAX_LINE:
                    cli.error(105)
                    return
                # 2. Accumulate exactly `message_length` bytes for the payload
                while len(buf) < message_length:
                    chunk = conn.recv(4096)
                    if not chunk:
                        return
                    buf += chunk
                raw = buf[:message_length]
                buf = buf[message_length:]
                try:
                    line = raw.decode("utf-8", errors="strict").strip()
                except UnicodeDecodeError:
                    cli.error(101)
                    continue   
                if not line:
                    continue     
                if handle_line(cli, line) == "close":
                    return
            else:
                chunk = conn.recv(4096)
            if not chunk:                       # empty result == peer closed
                break
            buf += chunk

            while b"\n" in buf:                 # may be several lines at once
                raw, buf = buf.split(b"\n", 1)
                if len(raw) > MAX_LINE:
                    cli.error(105)
                    return "close"
                try:
                    line = raw.rstrip(b"\r").decode("utf-8", errors="strict").strip()
                except UnicodeDecodeError:
                    cli.error(101)
                    continue
                if not line:
                    continue
                if handle_line(cli, line) == "close":
                    return

            if len(buf) > MAX_LINE:             # a line that never ends
                cli.error(105)
                buf = b""
    except socket.timeout:
        cli.error(103)
    except OSError:
        pass
    finally:
        # TODO (M3): remove this client from the roster and send an INFO notice.
        with clients_lock:
            if cli.nick in clients:
                clients.pop(cli.nick)
        if cli.nick is not None: # if no nickname was set, don't broadcast
            cli.broadcast("INFO {} has left the chat".format(cli.nick))
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--binary", action="store_true") # binary framing
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # do not delete
    srv.bind((args.host, args.port))
    srv.listen(16)
    srv.settimeout(1.0)
    print(f"listening on {args.host}:{args.port}")

    try:
        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=serve_client, args=(conn, addr, args.binary),
                             daemon=True).start()
    except KeyboardInterrupt:
       print("KeywordInterrupt, Stopping Server")
    finally:
        srv.close()


if __name__ == "__main__":
    main()
