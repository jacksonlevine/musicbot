import discord
import yt_dlp
import os
import asyncio
import subprocess
from pprint import pprint
import uuid


# Replace with your actual bot token
TOKEN = os.environ['DISCORD_911BOT_TOKEN']

# Set up the Discord client
intents = discord.Intents.all()
client = discord.Client(intents=intents)


def print_object_properties(obj):
    for attr in dir(obj):
        # Filter out special attributes and methods
        if not attr.startswith('__'):
            value = getattr(obj, attr)
            print(f"{attr}: {value}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(attend_to_song_queue())

song_queue = []
current_ffmpeg_process = None

async def attend_to_song_queue():
    global song_queue
    global current_ffmpeg_process
    while True:
        if len(song_queue) > 0:
            filename, voice_channel, guildname, txtchannel = song_queue.pop(0)
            voice = discord.utils.get(client.voice_clients, guild=guildname)

            if not voice or not voice.is_connected():
                try:
                    voice = await voice_channel.connect()
                except Exception as e:
                    print(f"Error connecting to voice channel: {e}")
                    continue

            try:
                current_ffmpeg_process = discord.FFmpegPCMAudio(executable="ffmpeg", source=filename)
                voice.play(current_ffmpeg_process)
                await txtchannel.send(f"Now playing: {filename}")
                while voice.is_playing():
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"Error playing audio: {e}")
            finally:
                if current_ffmpeg_process:
                    current_ffmpeg_process.cleanup()
                    current_ffmpeg_process = None
            # Cleanup after playing
            os.remove(filename)
        else:
            await asyncio.sleep(1)  # Sleep for a short time when the queue is empty


@client.event
async def on_message(message):
    global song_queue
    global current_ffmpeg_process

    if message.author == client.user:
        return

    # command to join the voice channel
    if message.content.startswith('!join'):
        channel = message.author.voice.channel


        if not channel:
            await message.channel.send("You're not connected to any vc!")
        else:
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                voice = await channel.connect()
                await message.channel.send("Joined channel!")

    if message.content.startswith('!stop'):
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice and voice.is_playing():
            voice.stop()
            if current_ffmpeg_process:
                    current_ffmpeg_process.cleanup()
                    current_ffmpeg_process = None
            await message.channel.send("Playback stopped.")
        else:
            await message.channel.send("Nothing is currently playing.")

    if message.content.startswith('!play'):

        channel = message.author.voice.channel

        if not channel:
            await message.channel.send("You're not connected to any vc!")
        else:
            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                voice = await channel.connect()
                await message.channel.send("Joined channel!")

        url = message.content[len('!play '):].strip()
        
        if not url:
            await message.channel.send("Please provide a valid YouTube URL.")
            return
        
        # filename to be downloaded
        filename = f'downloads/{uuid.uuid4()}.mp3'

        await message.channel.send(f"Downloading to {filename}...")

        # command to download MP3 using yt-dlp
        command = ['yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '0', '-o', filename, url]
        
        try:
            # run the command
            subprocess.run(command, check=True)
            # have to do this before i actually append otherwise the other thread is ON IT!
            await message.channel.send(f"Added {filename} to queue.") 
            # append the filename to the queued files to play
            song_queue.append((filename, message.author.voice.channel, message.guild, message.channel))
            
            
        except subprocess.CalledProcessError as e:
            await message.channel.send(f"An error occurred while downloading: {str(e)}")
        except Exception as e:
            await message.channel.send(f"An unexpected error occurred: {str(e)}")

    # command to leavae the voice channel
    if message.content.startswith('!leave'):
        channel = message.author.voice.channel
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice:
            if voice.is_playing():
                voice.stop()  # Stop the audio playback first
            await voice.disconnect()
            await message.channel.send("Disconnected from the voice channel.")
        else:
            await message.channel.send("I'm not in a voice channel.")

# Run the bot with your token
client.run(TOKEN)