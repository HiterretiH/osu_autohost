import socket


class OsuIrc:
    def __init__(self, name: str, password: str):
        self.host = "irc.ppy.sh"
        self.port = 6667
        self.name = name
        self.password = password
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.send("PASS " + self.password)
        self.send("NICK " + self.name)
        print("Connected to Bancho")

    def close(self):
        self.sock.close()

    def send(self, text: str):
        self.sock.send((text + '\n').encode(errors="ignore"))

    def receive(self, size=2048):
        return self.sock.recv(size).decode(errors="ignore").lower()
