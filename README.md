# osu_autohost
Osu! chat bot which creates in-game lobby with auto host rotation

# How to use
1. Download this repository
2. Fill in config.py (see below)
3. Run main.py with python
- If you want to stop the bot, just press ctrl+c in console window, bot will automatically close the lobby and stop running

# How to correctly fill config.py
Open it with any text editor and fill with your data. Variable notation:
| Variable | Description | Where you can get it |
| :--- | :--- | :--- |
| lobby_name | Lobby name. Players see it in lobby list | |
| lobby_password | Password to join the lobby. Leave it blank for no password | |
| osuirc_name | Your osu! account username | https://osu.ppy.sh/p/irc |
| osuirc_password | Osu IRC password. It's different from your account password | https://osu.ppy.sh/p/irc |
| help_msg | Message which bot will send on `!info` command | |
| commands_timeout | Timeout in seconds for !info and !queue commands | |
