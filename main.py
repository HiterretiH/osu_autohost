import osu
import config
from time import time
import collections
import ConfigReaderWriter
import threading


def get_new_line(irc):
    prev = ""
    while True:
        lines = (prev + irc.receive()).split("\n")
        for i in range(len(lines)-1):
            yield lines[i].strip()
        prev = lines[-1]


def set_host(irc, room: dict, name: str):
    irc.send(f"PRIVMSG {room['id']} :!mp host {name}")
    print(f"(#{room['num']}) {name} became host")


def discard_settings(irc, room: dict):
    irc.send(f"PRIVMSG {room['id']} :!mp name {room['name']}")
    irc.send(f"PRIVMSG {room['id']} :!mp password {room['password']}")
    irc.send(f"PRIVMSG {room['id']} :!mp mods freemod")
    irc.send(f"PRIVMSG {room['id']} :!mp size 16")


def create_room(irc, room: dict):
    irc.send(f"PRIVMSG BanchoBot :mp make {room['name']}")


def set_dicts(num, queue, commands_time, names, receiving_names):
    queue.update( {num: collections.deque()} )
    commands_time.update( {num: {"!queue": 0, "!info": 0}} )
    names.update( {num: []} )
    receiving_names.update( {num: False} )


def check_rooms(irc, queue, commands_time, names, receiving_names):
    """
    This function checks related to room dicts, adds missing keys, and removes redundant ones.
    Also, creates room if it does not exist
    """

    for room in rooms:
        if room['num'] not in queue.keys():
            set_dicts(room['num'], queue, commands_time, names, receiving_names)
            if not room['id']:
                create_room(irc, room)
            else:
                irc.send(f"JOIN {room['id']}")
                irc.send(f"NAMES {room['id']}")
                receiving_names[room['num']] = True
                print(f"Joining in {room['id']}")

    if len(queue.keys()) != len(rooms):
        nums = [room['num'] for room in rooms]
        for key in queue.keys().copy():
            if key not in nums:
                queue.pop(key)
                commands_time.pop(key)
                names.pop(key)
                receiving_names.pop(key)


config.osuirc_name = config.osuirc_name.replace(' ', '_').lower()

osubot = osu.OsuIrc(config.osuirc_name, config.osuirc_password)
osubot.connect()

rooms = []

lock = threading.Lock()
config_reader = ConfigReaderWriter.ConfigReaderWriter(lock, rooms, "rooms.yaml", 120)
config_reader.start()

queue = {}
commands_time = {}
names = {}
receiving_names = {}

try:
    for line in get_new_line(osubot):
        if line == "ping cho.ppy.sh":
            osubot.send("PONG cho.ppy.sh")
            with lock:
                for room in rooms:
                    num = room['num']
                    if room['id'] and not receiving_names[num] and len(queue[num]) > 0:
                        osubot.send(f"NAMES {room['id']}")
                        names[num] = []
                        receiving_names[num] = True
            continue

        if line.startswith(f":{config.osuirc_name}!cho@ppy.sh join :#"):
            with lock:
                for room in rooms:
                    if not room['id']:
                        room['id'] = line[line.rfind('#'):]
                        room['old_id'] = '1'
                        discard_settings(osubot, room)
                        print(f"(#{room['num']}) Created room: {room['id']}")
                        break
            continue

        lock.acquire()
        check_rooms(osubot, queue, commands_time, names, receiving_names)
        for room in rooms:
            if room['id']:
                mp_id = room['id']
                num = room['num']
                sep = room['id'] + " :"

                if line == f":{config.osuirc_name}!cho@ppy.sh part :{mp_id}":
                    print(f"(#{num}) {mp_id} is closed")

                    room['old_id'] = room['id']
                    room['id'] = ""

                    if room["recreate when closed"]:
                        print(f"Creating new room with name {room['name']}")
                        create_room(osubot, room)
                        set_dicts(num, queue, commands_time, names, receiving_names)
                    continue

                if receiving_names[num]:
                    if f"{config.osuirc_name} = {mp_id}" in line:
                        msg = line[line.find(sep) + len(sep):]
                        for user in msg.split(' '):
                            if user[0] != '+' and user != "@banchobot":
                                names[num].append(user)
                                if user not in queue[num]:
                                    queue[num].append(user)
                                    if len(queue) == 1:
                                        set_host(osubot, room, user)
                    if line.endswith(sep + "end of /names list."):
                        receiving_names[num] = False
                        if len(queue[num]) > 0 and queue[num][0] not in names[num]:
                            while len(queue[num]) > 0 and queue[num][0] not in names[num]:
                                queue[num].popleft()
                            if len(queue[num]) > 0:
                                set_host(osubot, room, queue[num][0])
                        print(f"(#{num}) Current players:", *names[num])

                if "privmsg " + mp_id in line:
                    name = line[1: line.find("!")]
                    msg = line[line.find(sep) + len(sep):]

                    if name == "banchobot":
                        if "joined in slot" in msg:
                            player = msg[:msg.find("joined in slot")-1].replace(' ', '_')
                            queue[num].append(player)
                            print(f"(#{num}) {player} joined the game")
                            if len(queue[num]) == 1:
                                set_host(osubot, room, queue[num][0])
                        elif "left the game" in msg:
                            player = msg[:msg.find("left the game")-1].replace(' ', '_')
                            if len(queue[num]) > 1 and player == queue[num][0]:
                                set_host(osubot, room, queue[num][1])
                            if player in queue[num]:
                                queue[num].remove(player)
                            print(f"(#{num}) {player} left the game")
                            if room['discard when empty'] and len(queue[num]) == 0:
                                discard_settings(osubot, room)
                                print(f"(#{num}) Room is empty. Settings discarded")
                        elif "the match has started!" == msg:
                            print(f"(#{num}) Match started")
                            if len(queue[num]) > 1:
                                queue[num].rotate(-1)
                        elif "the match has finished!" == msg:
                            print(f"(#{num}) Match finished")
                            if len(queue[num]) > 0:
                                set_host(osubot, room, queue[num][0])
                                osubot.send(f"NAMES {mp_id}")
                                names[num] = []
                                receiving_names[num] = True

                    else:
                        if msg in ("!info", "!queue"):
                            print(f"(#{num}) {name}: {msg}")
                            t = time()
                            if t >= commands_time[num][msg]:
                                commands_time[num][msg] = t + config.commands_timeout
                                if msg == "!info":
                                    osubot.send(f"PRIVMSG {mp_id} :{config.help_msg}")
                                elif msg == "!queue":
                                    osubot.send(f"PRIVMSG {mp_id} :Host queue: {' => '.join(queue[num])}")
        lock.release()

except KeyboardInterrupt:
    with lock:
        for room in rooms:
            if room['id'] and room['close on exit']:
                osubot.send(f"PRIVMSG {room['id']} :!mp close")
                room['id'] = ''
                print(f"(#{room['num']}) Room closed")
    config_reader.process()
    config_reader.stop()
    osubot.close()
