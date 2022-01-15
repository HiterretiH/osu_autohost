import osu
import config
from time import time
import collections


def get_new_line(irc):
    prev = ""
    while True:
        lines = (prev + irc.receive()).split("\n")
        for i in range(len(lines)-1):
            yield lines[i].strip()
        prev = lines[-1]


def set_host(irc, room, name):
    irc.send(f"PRIVMSG {room} :!mp host {name}")
    print(name, "became host")


def discard_settings(irc, room):
    irc.send(f"PRIVMSG {room} :!mp name {config.lobby_name}")
    irc.send(f"PRIVMSG {room} :!mp password {config.lobby_password}")
    irc.send(f"PRIVMSG {room} :!mp mods freemod")
    irc.send(f"PRIVMSG {room} :!mp size 16")


config.osuirc_name = config.osuirc_name.replace(' ', '_').lower()

osubot = osu.OsuIrc(config.osuirc_name, config.osuirc_password)
osubot.connect()

osubot.send(f"PRIVMSG BanchoBot :mp make {config.lobby_name}")
queue = collections.deque()
room = ""
commands_time = {"!queue": 0, "!info": 0}
names = []
receiving_names = False

try:
    for line in get_new_line(osubot):
        if line == "ping cho.ppy.sh":
            osubot.send("PONG cho.ppy.sh")
            if room and not receiving_names and len(queue) > 0:  # check if next host is still here
                osubot.send(f"NAMES {room}")
                names = []
                receiving_names = True
            continue

        if room:
            if line == f":{config.osuirc_name}!cho@ppy.sh part :{room}":
                print("Old room is closed. Creating new one...")
                osubot.send(f"PRIVMSG BanchoBot :mp make {config.lobby_name}")
                queue = collections.deque()
                room = ""
                names = []
                receiving_names = False
                continue

            if receiving_names:
                if f"{config.osuirc_name} = {room}" in line:
                    msg = line[line.find(sep) + len(sep):]
                    for user in msg.split(' '):
                        if user[0] != '+' and user != "@banchobot":
                            names.append(user)
                            if user not in queue:
                                queue.append(user)
                if line.endswith("end of /names list."):
                    receiving_names = False
                    if len(queue) > 0 and queue[0] not in names:
                        while len(queue) > 0 and queue[0] not in names:
                            queue.popleft()
                        if len(queue) > 0:
                            set_host(osubot, room, queue[0])
                    print("Current players:", *names)

            if "privmsg " + room in line:
                name = line[1: line.find("!")]
                msg = line[line.find(sep) + len(sep):]

                if name == "banchobot":
                    if "joined in slot" in msg:
                        player = msg[:msg.find("joined in slot")-1].replace(' ', '_')
                        queue.append(player)
                        print(player, "joined the game")
                        if len(queue) == 1:
                            set_host(osubot, room, queue[0])
                    elif "left the game" in msg:
                        player = msg[:msg.find("left the game")-1].replace(' ', '_')
                        if len(queue) > 1 and player == queue[0]:
                            set_host(osubot, room, queue[1])
                        if player in queue:
                            queue.remove(player)
                        print(player, "left the game")
                        if len(queue) == 0:
                            discard_settings(osubot, room)
                            print("The room is empty. Settings discarded")
                    elif "the match has started!" == msg:
                        print("Match started")
                        if len(queue) > 1:
                            queue.rotate(-1)
                    elif "the match has finished!" == msg:
                        print("Match finished")
                        if len(queue) > 0:
                            set_host(osubot, room, queue[0])
                            osubot.send(f"NAMES {room}")
                            names = []
                            receiving_names = True

                else:
                    if msg in ("!info", "!queue"):
                        print(f"{name}: {msg}")
                        t = time()
                        if t >= commands_time[msg]:
                            commands_time[msg] = t + config.commands_timeout
                            if msg == "!info":
                                osubot.send(f"PRIVMSG {room} :{config.help_msg}")
                            elif msg == "!queue":
                                osubot.send(f"PRIVMSG {room} :Host queue: {' => '.join(queue)}")

        else:
            if line.startswith(f":{config.osuirc_name}!cho@ppy.sh join :#"):
                room = line[line.rfind('#'):]
                sep = room + " :"
                discard_settings(osubot, room)
                print("Created room:", room)

except KeyboardInterrupt:
    if room:
        osubot.send(f"PRIVMSG {room} :!mp close")
        print("Room closed")
    osubot.close()
