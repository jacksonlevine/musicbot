import discord
import os
import commands

# Replace with your actual bot token
TOKEN = os.environ['DISCORD_911BOT_TOKEN']

# Set up the Discord client
intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(commands.attend_to_song_queue())

@client.event
async def on_message(message):

    if not message.content.startswith('!'):
        return

    if message.author == client.user:
        return

    print("Message content: \" " + message.content + " \" ")

    message_parts = message.content[1:].split(" ", 1)
    cmd, args = message_parts[0].lower(), None
    if len(message_parts) == 2:
        args = message_parts[1]

    cmd_func = commands.command_map.get(cmd)
    if cmd_func:
        ctx = commands.Context(message, client, args)
        return cmd_func(ctx)
    await commands.send_message(message, f"unknown command: '!{cmd}'")

# Run the bot with your token
client.run(TOKEN)
