import socket
import argparse
import threading
import sys
import time

running = True

def reader(sock, binary_mode=False):
    global running
    buf = b""
    while running:
        try:
            if binary_mode:
                while len(buf) < 4:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                
                if len(buf) < 4:
                    print("Server closed connection")
                    break
                
                length = struct.unpack(">I", buf[:4])[0]
                buf = buf[4:]
                
                while len(buf) < length:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    
                if len(buf) < length:
                    print("Server closed connection")
                    break
                    
                raw = buf[:length]
                buf = buf[length:]
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    print(line)
            else:
                chunk = sock.recv(4096)
            if not chunk:
                print("Server closed connection")
                break
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.rstrip(b"\r").decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                print(line)
        except OSError:
                break
    running = False
def main():
    global running
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--nick")
    parser.add_argument("--binary", action="store_true") # binary framing
    args = parser.parse_args()
 
    try:
        sock = socket.create_connection((args.host, args.port), timeout=5)
    except OSError as e:
        print("cannot connect to {}:{} - {}".format(args.host, args.port, e))
        sys.exit(1)
    sock.settimeout(None)
 
    t = threading.Thread(target=reader, args=(sock, args.binary))
    t.daemon = True
    t.start()
 
    def send_cmd(text):
        payload = text.encode("utf-8")
        if args.binary:
            sock.sendall(struct.pack(">I", len(payload)) + payload)
        else:
            sock.sendall(payload + b"\n")

    if args.nick:
         send_cmd("NICK " + args.nick)
 
    try:
        while running:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                continue
            sock.sendall((line + "\n").encode())
            if line.strip().upper() == "QUIT":
                time.sleep(0.3)   # let the reader thread print the final reply
                break
    except KeyboardInterrupt:
        try:
            send_cmd("QUIT")
        except OSError:
            pass
    finally:
        running = False
        try:
            sock.close()
        except OSError:
            pass
        print("disconnected")
 
 
if __name__ == "__main__":
    main()
 
