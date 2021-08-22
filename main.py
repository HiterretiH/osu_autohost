import osu
import config
from time import time

config.osuirc_name = config.osuirc_name.replace(' ', '_').lower()

osubot = osu.OsuIrc(config.osuirc_name, config.osuirc_password)
osubot.connect()

osubot.send(f"PRIVMSG BanchoBot :mp make {config.lobby_name}")
queue = []
room = ""
commands_time = {"!queue": 0, "!info": 0}
names = []
receiving_names = False

try:
    while True:
        for line in osubot.receive().split('\n'):
            line = line.strip()

            if line == "ping cho.ppy.sh":
                osubot.send("PONG cho.ppy.sh")
                continue

            if room:
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
                        if queue[0] not in names:
                            while len(queue) > 0 and queue[0] not in names:
                                queue.pop(0)
                            if len(queue) > 0:
                                osubot.send(f"PRIVMSG {room} :!mp host {queue[0]}")
                        print("Current players:", *names)

                if "privmsg " + room in line:
                    name = line[1: line.find("!")]
                    msg = line[line.find(sep) + len(sep):]

                    if name == "banchobot":
                        if "joined in slot" in msg:
                            player = msg[:msg.find("joined in slot")-1].replace(' ', '_')
                            queue.append(player)
                            if len(queue) == 1:
                                osubot.send(f"PRIVMSG {room} :!mp host {queue[0]}")
                            print(player, "joined the game")
                        elif "left the game" in msg:
                            player = msg[:msg.find("left the game")-1].replace(' ', '_')
                            if player == queue[0] and len(queue) > 1:
                                osubot.send(f"PRIVMSG {room} :!mp host {queue[1]}")
                            if player in queue:
                                queue.remove(player)
                            print(player, "left the game")
                        elif "the match has started!" == msg:
                            print("Match started")
                            if len(queue) > 1:
                                el = queue.pop(0)
                                queue.append(el)
                        elif "the match has finished!" == msg:
                            print("Match finished")
                            if len(queue) > 0:
                                osubot.send(f"PRIVMSG {room} :!mp host {queue[0]}")
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
                    osubot.send(f"PRIVMSG {room} :!mp password {config.lobby_password}")
                    osubot.send(f"PRIVMSG {room} :!mp mods freemod")
                    osubot.send(f"PRIVMSG {room} :!mp size 16")
                    print("Created room:", room)

except KeyboardInterrupt:
    if room:
        osubot.send(f"PRIVMSG {room} :!mp close")
        print("Room closed")
    osubot.close()
