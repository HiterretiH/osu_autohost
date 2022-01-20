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
        current_config = self.read()

        with self._lock:
            commented = []
            for room in self._config:
                if room.get("old_id"):
                    current_room = find_dict_in_list(current_config, "number", room.get("number"))
                    if room.get("recreate when closed"):
                        current_room.update({"id": room.get("id")})
                    else:
                        commented.append(current_room)
                        current_config.remove(current_room)
                    room.pop("old_id")
            self._config.clear()
            self._config.extend(current_config)

        self.write(yaml.dump(current_config).replace("-", "\n-"), yaml.dump(commented))
        print("Config updated")

    def read(self) -> list:
        self._file.seek(0)
        current_config = yaml.safe_load(self._file)
        if not current_config:
            return []
        used_numbers = []
        for [i, room] in enumerate(current_config):
            if type(room) != dict or not (room.get("name") or room.get("existing")):
                print(f"Error while reading rooms file! Please check room #{i}")
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
                "number": get_number(used_numbers, str(room.get("number")) if room.get("number") else str(i))
            })

            used_numbers.append(room.get("number"))

        return current_config

    def write(self, data="", commented=""):
        self._file.seek(0)
        self._file.truncate()
        if commented != "[]\n":
            commented = "\n".join(["#" + line for line in commented.split("\n")])
            self._file.write(data + "\n" + commented)
        else:
            self._file.write(data)
        self._file.flush()
