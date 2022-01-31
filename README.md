# osu_autohost
Osu! chatbot, which creates and maintains an in-game lobbies with auto host rotation

# Table of Contents
- [Features](#features)
- [Usage](#usage)
- [Bot configuration](#bot-configuration)
- [Rooms configuration](#rooms-configuration)

# Features
- Generate players queue based on joining time
- Give host to the first player in the queue after every game
- Maintain several rooms at the same time
- Create a room with a given name and settings
- Connect to an existing room (but it must be a referee in this room)

# Usage
1. Download this repository:
    - Click on the green button "Clone" in the top right
    - Click "Download ZIP"
    - Extract the archive where you want
2. Download and install [python](https://www.python.org/downloads/) (don't forget to include it in the PATH via special checkbox in installation manager)
3. Install requirements:
   - Open console in the directory with the script
   - Run command `pip install -r requirements.txt`
4. Configure bot and rooms (see below)
5. Bot is ready to run! You can start it with the command `python main.py` or with a double-click on the `main.py` file

# Bot configuration
All configurations stored in `config.py`

So to start, just open it with your favorite text editor. And then fill in all variables as shown below

| Variable         | Description                                                 | Where you can get it     |
| :--------------- | :---------------------------------------------------------- | :----------------------- |
| osuirc_name      | Your osu! account username                                  | https://osu.ppy.sh/p/irc |
| osuirc_password  | Osu IRC password. It's different from your account password | https://osu.ppy.sh/p/irc |
| help_msg         | Message which bot will send on`!info` command               |                          |
| commands_timeout | Timeout in seconds for !info and !queue commands            |                          |

Sample file:
```python
osuirc_name = "User_name"
osuirc_password = "aaaa1111"

help_msg = "This is an auto host rotate lobby. This means that host status automatically changes between players, so everyone can set the map which want to play on. (source)[https://github.com/HiterretiH/osu_autohost]"
commands_timeout = 5
```

# Rooms configuration
All configuration related to rooms stored in `rooms.yaml`.
This file automatically updates when the program is running, so you can adjust room settings even if the bot is working.

Also, please note that every user can create only 4 existing in the same time tournament rooms.

Sample configuration:

```yaml
- name: 5*-6* auto host rotate | !info !queue  # create new room with given name

- id: '#mp_00000000'  # connect to existing room

- name: host rotate | !info !queue  # create new room with given options
  discard when empty: true
  recreate when closed: true
  password: qwerty
```

Every room description starts with a hyphen and space. Then on each new line, there is one new option. 
For more info about YAML, you can check [article on Wikipedia](https://en.wikipedia.org/wiki/YAML) or [YAML official website](https://yaml.org/)

Every room has the following options:

| Option | Description |
| :------------ | :----------- |
| name | Lobby name. Players can see it in the lobby list |
| password | Password to join the lobby. Leave it empty for no password |
| id | #mp_id. Uses only with existing rooms |
| close on exit | Can be true or false. If true, the lobby will be closed when the bot has terminated |
| recreate when closed | Can be true or false. If true, the lobby will be recreated if it's closed |
| discard when empty | Also can be true or false. If true, lobby settings will be discarded if the room is empty |
| num | Auto-generated unique identifier for every lobby. You can specify it, but it's better if the program generates it automatically |
| old_id | This value is used in the program. You don't need it, so you can skip it |

You can specify only those options that you need. e.g. you can set only `name` or only `id`.
If the option is not specified, it will be false/empty by default.

Settings such as `name` and `password` won't be applied to the existing room (only if `discard when empty` is true and the room becomes empty)
