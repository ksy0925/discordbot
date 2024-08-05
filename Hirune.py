import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import os
import asyncio
from PIL import ImageGrab
import shutil
import random

# 봇의 접두사(prefix) 설정
prefix = "/"

# Intents 설정
intents = discord.Intents.all()

# 봇 객체 생성
bot = commands.Bot(command_prefix=prefix, intents=intents)

# YouTube DL 설정
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        ffmpeg_path = r"C:\Users\ksy09\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"  # FFmpeg 실행 파일의 전체 경로로 변경하세요
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, **ffmpeg_options), data=data)

# '/유튜브' 명령어 처리
@bot.command(name='유튜브')
async def play_youtube(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("음성 채널에 먼저 입장해주세요.")
        return

    channel = ctx.message.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send(f'현재 재생 중: {player.title}')

# '/캡쳐' 명령어 처리
@bot.command(name='캡쳐')
async def capture_screen(ctx):
    try:
        # 사용자의 바탕화면 경로 가져오기
        user_desktop_path = get_user_desktop_path(ctx.author)
        
        # 캡쳐 이미지를 임시 디렉토리에 저장
        temp_capture_path = 'temp_capture.png'
        ImageGrab.grab().save(temp_capture_path)
        
        # 바탕화면으로 캡쳐 이미지 이동
        destination_path = os.path.join(user_desktop_path, 'discord_capture.png')
        shutil.move(temp_capture_path, destination_path)
        
        await ctx.send("디스코드 창이 캡쳐되어 사용자의 바탕화면에 저장되었습니다.")
    except Exception as e:
        await ctx.send(f"오류 발생: {e}")

# 사용자의 바탕화면 경로를 가져오는 함수
def get_user_desktop_path(author):
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    user_desktop_path = os.path.join(desktop_path, str(author))
    if not os.path.exists(user_desktop_path):
        os.makedirs(user_desktop_path)
    return user_desktop_path

# '/플래피버드' 명령어 처리
@bot.command(name='플래피버드')
async def flappy_bird(ctx):
    await ctx.send("플래피 버드 게임을 시작합니다! 게임 중에는 '위' 또는 '아래'를 입력하여 조작하세요.")
    await ctx.send("준비... 시작!")

    game_over = False
    bird_position = 5  # 새의 초기 높이
    pipe_gap = random.randint(2, 6)  # 파이프 사이 간격
    score = 0

    while not game_over:
        # 게임 보드 그리기
        board = ""
        for height in range(10):
            if height == bird_position:
                board += "B"  # 새의 위치
            elif height == pipe_gap or height == pipe_gap + 1:
                board += "PP"  # 파이프
            else:
                board += "_"
            board += "\n"
        
        await ctx.send(f"점수: {score}\n```\n{board}```")

        # 사용자 입력 받기
        def check(m):
            return m.author == ctx.author and m.content.lower() in ['위', '아래']
        
        try:
            message = await bot.wait_for('message', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("시간 초과! 게임 오버!")
            game_over = True
            continue

        direction = message.content.lower()

        # 새의 이동 처리
        if direction == "위":
            bird_position -= 1
        elif direction == "아래":
            bird_position += 1
        
        # 게임 종료 조건 확인
        if bird_position < 0 or bird_position > 9:
            await ctx.send("게임 오버!")
            game_over = True
        elif bird_position == pipe_gap or bird_position == pipe_gap + 1:
            await ctx.send("게임 오버!")
            game_over = True
        else:
            score += 1  # 파이프를 통과하면 점수 상승
            pipe_gap = random.randint(2, 7)  # 새로운 파이프 위치

    await ctx.send(f"최종 점수: {score}")

# 가위바위보 게임 변수
user_choice = {}
bot_choice = {}

@bot.command(name='가위바위보')
async def rock_paper_scissors(ctx):
    user_id = ctx.author.id
    bot_choice[user_id] = random.choice(['가위', '바위', '보'])
    
    rules = "게임 규칙:\n1. '/가위바위보'를 입력하여 게임을 시작합니다.\n2. 봇이 자동으로 선택을 합니다.\n3. 당신의 선택을 '가위', '바위', '보' 중 하나로 입력하세요.\n4. '/결과'를 입력하여 게임 결과를 확인합니다."
    
    await ctx.send(f"{ctx.author.mention}님, 가위바위보 게임을 시작합니다!\n{rules}\n당신의 선택을 입력해주세요 (가위/바위/보):")

@bot.command(name='결과')
async def result(ctx):
    user_id = ctx.author.id
    if user_id not in bot_choice:
        await ctx.send("먼저 '/가위바위보' 명령어로 게임을 시작해주세요.")
        return

    if user_id not in user_choice:
        await ctx.send("선택을 입력해주세요 (가위/바위/보).")
        return

    user = user_choice[user_id]
    bot = bot_choice[user_id]

    await ctx.send(f"당신의 선택: {user}")
    await ctx.send(f"봇의 선택: {bot}")

    if user == bot:
        result = "비겼습니다!"
    elif (user == '가위' and bot == '보') or (user == '바위' and bot == '가위') or (user == '보' and bot == '바위'):
        result = "이겼습니다!"
    else:
        result = "졌습니다!"

    await ctx.send(result)

    # 게임 초기화
    del user_choice[user_id]
    del bot_choice[user_id]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() in ['가위', '바위', '보']:
        user_id = message.author.id
        if user_id in bot_choice:
            user_choice[user_id] = message.content.lower()
            await message.channel.send(f"{message.author.mention}님의 선택이 저장되었습니다. '/결과' 명령어로 결과를 확인하세요.")
        else:
            await message.channel.send("먼저 '/가위바위보' 명령어로 게임을 시작해주세요.")

    await bot.process_commands(message)





# '/안녕' 명령어 처리
@bot.command(name='안녕')
async def say_hello(ctx):
    await ctx.send('안녕하세요!')

# '/히루네참가' 명령어 처리
@bot.command(name='히루네참가')
async def join_voice_channel(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("음성 채널에 참가하였습니다.")
    else:
        await ctx.send("음성 채널에 먼저 입장해주세요.")

# '/명령어' 명령어 처리
@bot.command(name='명령어')
async def show_commands(ctx):
    command_list = """
/안녕 -> 인사합니다.
/유튜브 [URL] -> 유튜브 오디오를 재생합니다.
/멈춰 -> 오디오 재생을 멈춥니다.
/캡쳐 -> 디스코드 창을 캡쳐하여 바탕화면에 저장합니다.
/플래피버드 -> 플래피 버드 게임을 시작합니다.
"""
    await ctx.send(f"다음은 사용 가능한 명령어입니다:\n{command_list}")

# '/멈춰' 명령어 처리
@bot.command(name='멈춰')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("재생을 멈추고 음성 채널에서 나갔습니다.")
    else:
        await ctx.send("봇이 음성 채널에 없습니다.")

@bot.event
async def on_ready():
    print(f'봇이 로그인했습니다: {bot.user.name}')

# 봇 토큰으로 실행
bot.run('')  # 실제 봇 토큰으로 교체하세요.
