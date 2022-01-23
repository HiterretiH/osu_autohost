import threading
import time
import yaml


def find_dict_in_list(arr, key, value) -> dict:
    for d in arr:
        if d.get(key) == value:
            return d
    return {}


def get_number(used: list, st: str) -> str:
    while st in used:
        st += st
    return st


class ConfigReaderWriter(threading.Thread):
    def __init__(self, lock: threading.Lock, config: list, file_name: str, timeout: int = 180):
        super().__init__()
        self._lock = lock
        self._config = config
        self._file = open(file_name, "r+")
        self._timeout = timeout
        self._stopped = False

    def run(self):
        while not self._stopped:
            self.process()
            time.sleep(self._timeout)

    def stop(self):
        self._stopped = True

    def process(self):
        current_config, comments, commented_rooms = self.read()

        with self._lock:
            for room in self._config:
                if room.get("old_id"):
                    current_room = find_dict_in_list(current_config, "num", room.get("num"))
                    if room.get("id") or room.get("recreate when closed"):
                        current_room.update({"id": room.get("id")})
                    else:
                        commented_rooms.append(current_room)
                        current_config.remove(current_room)
                    room.pop("old_id")
            self._config.clear()
            self._config.extend(current_config)

        if commented_rooms:
            comments += "\n\n" + "\n".join(["#" + line for line in yaml.dump(commented_rooms).split("\n")])

        self.write(yaml.dump(current_config).replace("\n-", "\n\n-") + "\n" + comments)
        print("Config updated")

    def read(self):
        """
        :return: three objects:
            - current rooms: list;
            - commented lines: str;
            - rooms with parsing error: list
        """

        self._file.seek(0)
        text = self._file.read()
        comments = "\n".join(filter(lambda line: line.startswith("#"), text.split("\n")))
        current_config = yaml.safe_load(text)
        with_err = []
        if not current_config:
            return [], comments, with_err
        if type(current_config) != list:
            print(f"Error while reading rooms file! Looks like you forget '- ' somewhere")
            return [], comments, with_err
        used_numbers = []
        for [i, room] in enumerate(current_config):
            if type(room) != dict or (not room.get("name") and not room.get("id")) or \
                    (not room.get("name") and (room.get("recreate when closed") or room.get("discard when empty"))):
                print(f"Error while reading rooms file! Please check commented room")
                with_err.append(room)
                current_config.remove(room)
                continue

            room.update({
                "name": str(room.get("name")),
                "password": str(room.get("password")) if room.get("password") else "",
                "id": str(room.get("id")) if room.get("id") else "",
                "recreate when closed": bool(room.get("recreate when closed")),
                "discard when empty": bool(room.get("discard when empty")),
                "close on exit": bool(room.get("close on exit")),
                "old_id": "",
                "num": get_number(used_numbers, str(room.get("num")) if room.get("num") else str(i))
            })

            used_numbers.append(room.get("number"))

        return current_config, comments, with_err

    def write(self, data=""):
        self._file.seek(0)
        self._file.truncate()
        self._file.write(data)
        self._file.flush()
