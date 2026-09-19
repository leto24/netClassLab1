import socket
 
HOST = "127.0.0.1"
PORT = 5050
 
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.settimeout(1.0)
srv.bind((HOST, PORT))
srv.listen(5)
print("echo server listening on", PORT)
try: 
    while True:
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue          
        print("connected:", addr)
        with conn:
            while True:
                buffer = b"" 
                while True:
                    try:
                        data = conn.recv(1024)
                    except socket.timeout:
                         continue
                    if not data:
                        break
                    buffer += data
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        conn.sendall(line.upper() + b'\n')
                    
        print("disconnected:", addr)
except KeyboardInterrupt:
    print("KeyboardInterrupt, Stopping server")
finally:
    srv.close()