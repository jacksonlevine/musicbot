import discord
import asyncio
import subprocess
import uuid
import os

song_queue = []
current_ffmpeg_process = None
paused = False

class Context:
    def __init__(self, message, client, args):
        self.message = message
        self.client = client
        self.args = args
        self.volume = 1
        self.filename = None
        self.url = None

async def join(ctx):
    channel = ctx.message.author.voice.channel

    if not channel:
        return await send_message(ctx, "You're not connected to any vc!")

    voice = get_voice(ctx)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        await channel.connect()
    await send_message(ctx, "Joined channel!")


async def leave(ctx):
    voice = get_voice(ctx)

    if not voice:
        return await send_message(ctx, "I'm not in a voice channel.")

    if voice.is_playing():
        voice.stop()  # Stop the audio playback first
    await voice.disconnect()
    await send_message(ctx, "Disconnected from the voice channel.")


async def play(ctx):
    global current_ffmpeg_process
    global paused
    global song_queue
    if paused:
        paused = False
        song_queue = []

    await join(ctx)

    parse_args(ctx)

    if not ctx.url:
        return await send_message(ctx, "Please provide a valid YouTube URL.")

    # filename to be downloaded
    filename = f'downloads/{uuid.uuid4()}.mp3'
    ctx.filename(filename)

    await send_message(ctx, f"Downloading to {filename}...")

    # command to download MP3 using yt-dlp
    # todo we should be able to have yt-dlp save the file as the video title, so we can leave identify the songs being
    # played, instead of uuids. We would have to parse the output from subprocess below.
    command = ['yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '0', '-o', filename, ctx.url]

    try:
        # run the command
        subprocess.run(command, check=True)
        # have to do this before i actually append otherwise the other thread is ON IT!
        await send_message(ctx, f"Added {filename} to queue.")
        # append the filename to the queued files to play
        song_queue.append(ctx)

    except subprocess.CalledProcessError as e:
        await send_message(ctx, f"An error occurred while downloading: {str(e)}")
    except Exception as e:
        await send_message(ctx, f"An unexpected error occurred: {str(e)}")


async def pause(ctx):
    global paused
    global current_ffmpeg_process

    voice = get_voice(ctx)
    if not voice or not voice.is_playing():
        return await send_message(ctx, "Nothing is currently playing.")

    voice.stop()
    ffmpeg_clean()
    paused = True
    await send_message(ctx,
        "Playback stopped. Type !resume to resume the queue, or !play a link to start a fresh one. If you !resume, then further calls to !play will keep adding to the existing queue.")

async def resume(ctx):
    global paused
    paused = False


async def skip(ctx):
    global current_ffmpeg_process

    voice = get_voice(ctx)
    if not voice or not voice.is_playing():
        return await send_message(ctx, "Nothing is currently playing.")

    voice.stop()
    ffmpeg_clean()
    await send_message(ctx, "Song skipped.")


async def clear(ctx):
    global paused
    global song_queue
    song_queue = []
    paused = False
    await send_message(ctx, "Cleared song queue.")

command_map = {
    "join": join,
    "leave": leave,
    "play": play,
    "queue": play,
    "pause": pause,
    "stop": pause,
    "resume": resume,
    "skip": skip,
    "clear": clear,
}

def parse_volume(ctx, volume):
    volume = volume[2:] # remove v:
    try:
        ctx.volume =  max(0.0, min(float(volume), 4.0))
    except ValueError:
        return None

def parse_url(ctx, url):
    ctx.url = url

def parse_args(ctx):
    for arg in ctx.args.split(" "):
        arg_cmd = arg_map.get(arg)
        if arg_cmd:
            arg_cmd(ctx, arg)

arg_map = {
    "v": parse_volume,
    "": parse_url,
}

async def attend_to_song_queue():
    global song_queue
    global current_ffmpeg_process
    global paused
    while True:
        if len(song_queue) == 0 or paused:
            await asyncio.sleep(1)  # Sleep for a short time when the queue is empty
            continue

        ctx = song_queue.pop(0)
        voice = get_voice(ctx)

        if not voice or not voice.is_connected():
            await join(ctx)

        filename = ctx.filename
        volume = ctx.volume
        try:
            current_ffmpeg_process = discord.FFmpegPCMAudio(executable="ffmpeg", source=filename,
                                                            options=f"-filter:a \"volume={volume}\"")
            voice.play(current_ffmpeg_process)
            await send_message(ctx,f"Now playing: {filename}")
            while voice.is_playing():
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            ffmpeg_clean()
        # Cleanup after playing
        os.remove(filename)

async def send_message(ctx, msg):
    await ctx.message.channel.send(msg)

def ffmpeg_clean():
    global current_ffmpeg_process
    if current_ffmpeg_process:
        current_ffmpeg_process.cleanup()
        current_ffmpeg_process = None

def get_voice(ctx):
    return discord.utils.get(ctx.client.voice_clients, guild=ctx.message.guild)
