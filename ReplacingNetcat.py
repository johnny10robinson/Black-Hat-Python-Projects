import sys
import socket
import getopt
import threading
import subprocess

# Initialize global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

# Print usage information and exit
def usage():
    print("Netcat Replacement")
    print()
    print("Usage: ReplacingNetcat.py -t target_host -p port")
    print(
        "-l --listen                - listen on [host]:[port] for incoming "
        "connections")
    print(
        "-e --execute=file_to_run   - execute the given file upon receiving "
        "a connection")
    print("-c --command               - initialize a command shell")
    print(
        "-u --upload=destination    - upon receiving connection upload a file "
        "and write to [destination]")
    print()
    print("Examples: ")
    print("ReplacingNetcat.py -t 192.168.0.1 -p 5555 -l -c")
    print("ReplacingNetcat.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("ReplacingNetcat.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./ReplacingNetcat.py -t 192.168.11.12 -p 135")
    sys.exit(0)

# This function runs a command and returns the output
def run_command(cmd):
    cmd = cmd.rstrip()  # Trim the newline
    try:
        # Run the command and get the output
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        output = e.output  # Capture errors
    return output

# This function handles incoming client connections
def client_handler(client_socket):
    global upload
    global execute
    global command

    print("[*] Client handler started")

    # Check if upload destination is specified
    if len(upload_destination):
        file_buffer = b""  # Buffer to store file data
        while True:
            data = client_socket.recv(1024)  # Receive data from the client
            if not data:
                break  # End if no more data
            else:
                file_buffer += data  # Append received data to buffer

        try:
            # Write the received data to a file
            with open(upload_destination, "wb") as file_descriptor:
                file_descriptor.write(file_buffer)
            client_socket.send(f"Successfully saved file to {upload_destination}\r\n".encode('utf-8'))
        except OSError:
            client_socket.send(f"Failed to save file to {upload_destination}\r\n".encode('utf-8'))

    # Check if a command needs to be executed
    if len(execute):
        output = run_command(execute)  # Execute the command
        client_socket.send(output)  # Send the output to the client

    # If command shell is requested, go into a loop to receive commands
    if command:
        while True:
            try:
                client_socket.send("<BHP:#> ".encode('utf-8'))  # Prompt for input
                cmd_buffer = b""
                while b"\n" not in cmd_buffer:
                    data = client_socket.recv(1024)  # Receive command from client
                    if not data:
                        break  # Break if no more data
                    cmd_buffer += data
                if cmd_buffer:
                    response = run_command(cmd_buffer.decode())
                    client_socket.send(response.encode('utf-8'))  # Send back the command output
            except Exception as e:
                print(f"[*] Exception: {e}")
                client_socket.close()
                break

def server_loop():
    global target
    global port

    # If no target is defined, listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))  # Bind to the target and port
    server.listen(5)  # Start listening with a backlog of 5

    print(f"[*] Listening on {target}:{port}")

    while True:
        client_socket, addr = server.accept()  # Accept incoming connection
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        # Start a new thread to handle the client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))  # Connect to the target

        if len(buffer):
            client.send(buffer.encode('utf-8'))

        while True:
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode('utf-8')

                if recv_len < 4096:
                    break
            print(response, end='')

            buffer = input("")
            buffer += "\n"

            client.send(buffer.encode('utf-8'))

    except socket.error as exc:
        print("[*] Exception! Exiting.")
        print(f"[*] Caught exception socket.error: {exc}")

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port", "command", "upload"])

        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-l", "--listen"):
                listen = True
            elif o in ("-e", "--execute"):
                execute = a
            elif o in ("-c", "--command"):
                command = True
            elif o in ("-u", "--upload"):
                upload_destination = a
            elif o in ("-t", "--target"):
                target = a
            elif o in ("-p", "--port"):
                port = int(a)
            else:
                assert False, "Unhandled Option"

    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # Are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()

if __name__ == "__main__":
    main()
