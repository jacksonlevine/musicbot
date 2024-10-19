To use:

Windows-specific commands, use from Windows Terminal:

Prerequisites:
- Install ffmpeg (have the folder w/ the .exe on your PATH)
- Install yt-dlp (have the folder w/ the .exe on your PATH)

Install requirements:
```
python -m pip install -r requirements.txt
```

Create virtual environment for discord bot token:
```
python -m venv venv
```
```
venv\Scripts\activate.bat
```
```
set DISCORD_911BOT_TOKEN=yourDiscordBotToken(replace this with yours)
```

Run the bot:
```
python bot.py
```

Enjoy!

!play <youtube link>

!stop

!join

!leave