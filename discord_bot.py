'''
20200425수정 
0425 검색추가,  message.author.id로 변경
0504 과거전적 이번달 0 수정
0508 명령어 축약형 추가 
0704 !추가 추가
0714 등록시 스코어세이버 풀 주소 사용가능
0715 함수 분할, 셀레늄 제거(requeㅋst대체)
0806 비교, 그래프, 내정보, 타정보 다듬기/ 답변 메세지 변경/ 축약형 추가
0810 @bot.command 사용, asyncio 추가
2021 YEAR
0814 font error -> ignore
'''
from bot_command_set import *
from discord.ext import commands
import discord, asyncio, re, os, shlex, subprocess, time
#from selenium import webdriver

SCORESABER_USER_ID_MIN = 10 ##스코어세이버 주소 10자리는 넘겠지?
game = discord.Game("오전 5시30~40분을 제외하고 작동")
intents = discord.Intents.default()
intents.message_content = True #discord.py 2.x: prefix 명령에 필요 (개발자 포털에서도 활성화)
bot = commands.Bot(command_prefix = '!', status=discord.Status.online, activity=game, help_command = None, intents=intents)
number = 0
ENCODING = 'utf-8'

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    with open(os.path.join(DIR_PATH,'token.txt'),'r', encoding=ENCODING) as text:
        TOKEN = text.readlines()[0].split("#")[0] #첫번째 줄 #빼고 token으로 사용

import slash_commands
slash_commands.setup(bot) # /info, /recommend (버튼 UI는 slash_commands.py)

#------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
    try:
    	synced = await bot.tree.sync()
    	print(f"slash commands synced: {len(synced)}")
    except Exception as ex:
    	print("slash sync failed:", ex)
    print("ready")

#------------------------------------------------------------------------------------------------
@bot.command(aliases=['Help','HELP'])
async def help(ctx):
	await ctx.send("it will be updated soon... maybe")
 
@bot.command(aliases=['S','검색']) # 검색
async def s(ctx):
	await 검색하기(ctx)

@bot.command(aliases=['R','등록']) # 등록
async def r(ctx):
	await 정보등록(ctx)

@bot.command(aliases=['or','OR','타등록']) # 타등록
async def Or(ctx):
	await 타_등록(ctx)

@bot.command(aliases=['A','추가']) # 추가 
async def a(ctx, link = None):
	await 추가하기(ctx, link)

@bot.command(aliases=['H','내전적']) # 내전적
async def h(ctx, *args):
    historyNum=None
    fileOption=None
    if len(args)>=1:
    	historyNum = args[0]
    	if(not historyNum.isdecimal()): 
    		await ctx.send("숫자를 입력해주세요")
    		return
    
    if len(args)==2:
    	fileOption = args[1].lower()
    	if fileOption != "csv" and fileOption != "txt":
    		await ctx.send("입력을 확인해주세요 csv, txt로만 저장할 수 있습니다.")
    		return

    if len(args)>=3:
    	await ctx.send("입력을 확인해주세요")
    	return

    await 내_전적(ctx, historyNum, fileOption)

@bot.command(aliases=['G','그래프']) # 그래프
async def g(ctx, graph_number = None):
	await 그래프그리기(ctx, graph_number)

@bot.command(aliases=['C','비교']) # 비교
async def c(ctx):
	await 비교하기(ctx)	

@bot.command(aliases=['I','내정보']) # 내정보
async def i(ctx):
	await 내_정보(ctx)

@bot.command() # 랭킹
async def 랭킹(ctx, country = None):
	await 랭킹보기(ctx, country)

@bot.command(aliases=['Oi','OI','타정보']) # 타정보
async def oi(ctx, player=""):
	await 타_정보(ctx, player)

@bot.command(aliases=['REC','곡추천']) # 곡추천 (ScoreSaber)
async def rec(ctx, link = None, num = '8'):
	await 곡_추천(ctx, link, num)

@bot.command(aliases=['BLREC','블곡추천','bl곡추천']) # 곡추천 (BeatLeader)
async def blrec(ctx, link = None, num = '8'):
	await 블_곡_추천(ctx, link, num)

@bot.command(aliases=['UREC','유저추천']) # 유저추천 (ScoreSaber)
async def urec(ctx, link = None, num = '8'):
	await 유저_추천(ctx, link, num)

#------------------------------------------------------------------------------------------------
async def 정보등록(ctx): 
    try:
    	sc = ctx.message.content.split()[-1]
    	sc = re.findall(f'\d{{{SCORESABER_USER_ID_MIN},}}', sc)[0]
    	if diccheck(str(ctx.author.id)):
    		await ctx.send(f'`{ctx.author}님은 이미 등록되어있습니다. 이번에 입력하신 정보로 재등록합니다`')
    	if regist(str(ctx.author.id),sc):
    		await ctx.send('성공적으로 등록되었습니다')
    	else:
    		await ctx.send('등록에 실패했습니다 올바른 주소를 입력해주세요')
    except:
    	await ctx.send('입력을 확인해주세요')

async def 타_등록(ctx):
    try:
    	did = ctx.message.content.split()[-2]
    	sc = ctx.message.content.split()[-1]
    	sc = re.findall(f'\d{{{SCORESABER_USER_ID_MIN},}}', sc)[0]
    	if diccheck(str(did)):
    		await ctx.send(f'`{did}님은 이미 등록되어있습니다. 이번에 입력하신 정보로 재등록합니다.`')    		
    	if regist(str(did),sc):
    		await ctx.send("성공적으로 등록되었습니다")
    	else:
    		await ctx.send("등록에 실패했습니다 올바른 주소를 입력해주세요")
    except:
    	await ctx.send("입력을 확인해주세요")

async def 추가하기(ctx, link):
    if link != None:
    	link = re.findall(f'\d{{{SCORESABER_USER_ID_MIN},}}', link)[0]
    	username = validcheck(link)
    	if(username!= False):
    		dupcheck = open('Added_User_List.txt', 'r')
    		checker = dupcheck.readlines()
    		dupcheck.close()

    		if (link+'\n' in checker):
    			await ctx.send(f'{username}님의 전적은 이미 기록중입니다')
    		elif checker[len(checker)-1] == link:
    			await ctx.send(f'{username}님의 전적은 이미 기록중입니다')
    		else:
    			add_user = open('Added_User_List.txt', 'a')
    			add_user.write('\n'+link)
    			add_user.close()
    			await ctx.send(f'{username}님의 전적이 내일부터 기록됩니다')
    	else:
    		await ctx.send("존재하지 않는 유저입니다")
    else:
    	await ctx.send("입력을 확인해주세요")

async def 내_정보(ctx):
    discordid = str(ctx.author.id)
    listdata = embeddata(discordid)
    if listdata == "notregist":
    	await ctx.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    elif listdata == "scoresabererror":
    	await ctx.send("스코어세이버와의 연결이 불안정합니다")
    elif listdata == "fileerror":
    	await ctx.send("전적을 읽는동안 문제가 발생했습니다")
    else:
    	description = ""
    	for i in range(3,len(listdata)):
    		description+=listdata[i]
    	if listdata[1] == "/images/oculus.png":
    		imageurl= "https://scoresaber.com/imports/images/oculus.png"
    	elif listdata[1].startswith("http"):
    		imageurl = listdata[1]
    	else:
    		imageurl = "https://scoresaber.com"+listdata[1]

    	embed=discord.Embed(title=listdata[0]+"'s profile", url="https://scoresaber.com/u/"+listdata[2],description= description,color=0x00ff56)
    	embed.set_thumbnail(url=imageurl)
    	await ctx.send(embed= embed)

async def 타_정보(ctx, player):
    discordid = str(player)
    listdata = embeddata(discordid)
    if listdata == "notregist":
    	await ctx.send("등록되어있지 않은 계정입니다")
    elif listdata == "scoresabererror":
    	await ctx.send("스코어세이버와의 연결이 불안정합니다")
    elif listdata == "fileerror":
    	await ctx.send("전적을 읽는동안 문제가 발생했습니다")
    else:
    	description = ""
    	for i in range(3,len(listdata)):
    		description+=listdata[i]
    	if listdata[1] == "/images/oculus.png":
    		imageurl= "https://scoresaber.com/imports/images/oculus.png"
    	elif listdata[1].startswith("http"):
    		imageurl = listdata[1]
    	else:
   			imageurl = "https://scoresaber.com"+listdata[1]
    	embed=discord.Embed(title=listdata[0]+"'s profile", url="https://scoresaber.com/u/"+listdata[2],description= description,color=0x00ff56)
    	embed.set_thumbnail(url=imageurl)
    	await ctx.send(embed= embed)

async def 랭킹보기(ctx, country):
    if country == None:
    	await ctx.send("https://scoresaber.com/global")
    else:
    	await ctx.send("https://scoresaber.com/global?country="+str(country))

async def 내_전적(ctx, history_number, fileOption):
    temp = history(str(ctx.author.id))
    if temp == False: await ctx.send("입력을 확인해주세요")
    elif temp == "regist": await ctx.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    elif temp == "notrecord": await ctx.send(f'{ctx.author}님의 전적이 기록되어 있지 않습니다.\n`!추가 [스코어세이버 주소]를 입력해 전적이 기록되도록 할 수 있습니다`')
    else:
    	opt = '```'
    	history_length = len(temp)
    	history_overflow = -1
    	if history_length >= 20: #기본 20개 기록된 게 20개보다 적으면 history_overflow에 기록
    		x = 20
    	else:
    		#history_overflow = history_length #기본 키워드에서는 메시지 출력 x
    		x = history_length

    	if history_number != None:
    		num = int(history_number)
    		if num > history_length:
    			history_overflow = history_length
    		if fileOption == None:
    			x = min(48, num, history_length) #디스코드 한번에 보낼 수 있는게 최대 50줄임 #50줄은 도배 같아서 20줄
    		else:
    			x = min(num, history_length)

    	for i in range(x):
    		try:
    			opt = opt + str(temp[history_length-x+i]) 
    		except:
    			await ctx.send("알 수 없는 오류가 발생했습니다")
    			break
    	opt += '```'
    	if history_overflow > 0:
    		await ctx.send(f'{ctx.author}님의 전적은 {history_overflow}개만 기록되어 있습니다')
    		history_overflow = -1
    	if x!=0:
    		if fileOption != None:
    			fileName = "history."+fileOption
    			f = open(fileName,'w')
    			f.write(opt.strip('```'))
    			f.close()
    			await ctx.send(file = discord.File(fileName))
    		else:	
    			await ctx.send(opt)
    			await ctx.send(f'{ctx.author}님의 전적을 출력했습니다')

async def 그래프그리기(ctx, graph_number):
    if graph_number == None:
    	answer = HistoryGraph(str(ctx.author.id))
    	if answer == True:
    		history_overflow = overflowcheck()
    		if history_overflow>0:
    			await ctx.channel.send(f'{ctx.author}님의 전적은 {history_overflow}개만 기록되어 있습니다')
    			freeoverflow()	
    		await ctx.channel.send(file = discord.File("graph.png"))
    	else:
    		await ctx.channel.send(str(answer))
    else:
    	answer = HistoryGraph(str(ctx.author.id), int(graph_number))
    	if answer == True:
    		history_overflow = overflowcheck()
    		if history_overflow>0:
    			await ctx.send(f'{ctx.author}님의 전적은 {history_overflow}개만 기록되어 있습니다')	
    			freeoverflow()
    		await ctx.send(file = discord.File("graph.png"))
    	else:
    		await ctx.send(str(answer))

async def 비교하기(ctx):
    mes = ctx.message.content.split('-')
    if len(mes) != 2:
    	await ctx.send("- 뒤에 비교할 유저의 스코어세이버 주소를 입력해주세요")
    else:
    	userlinks = mes[1].split(',')
    	command = mes[0].split()
    	if len(command) == 1:
    		answer = Comparegraph(userlinks)
    		if answer == True:
    			await ctx.send(file = discord.File("graph.png"))
    		else:
    			await ctx.send(str(answer))
    	elif len(command) == 2:
    		answer = Comparegraph(userlinks, int(command[1]))
    		if answer == True:
    			await ctx.send(file = discord.File("graph.png"))
    		else:
    			await ctx.send(str(answer))
    	else:
    		await ctx.send("입력을 확인해주세요")

#------------------------------------------------------------------------------------------------
# 곡/유저 추천 (recommend/ — 리더보드 topology 기반, 자세한 건 recommend/README.md)
RECOMMEND_DIR = os.path.join(DIR_PATH, 'recommend')
UPDATE_DIR = os.path.join(RECOMMEND_DIR, 'update_jobs')
UPDATE_LOG_DIR = os.path.join(UPDATE_DIR, 'logs')

UPDATE_JOB_STEPS = {
    'users': {
        'label': 'ScoreSaber 유저 PP 기록',
        'steps': [
            (DIR_PATH, ['python3', 'kr_ranker.py']),
            (DIR_PATH, ['python3', 'added_user.py']),
        ],
    },
    'user_recommend': {
        'label': 'ScoreSaber 유저 추천 데이터',
        'steps': [
            (os.path.join(RECOMMEND_DIR, 'ss_users'), ['python3', 'fetch.py']),
        ],
    },
    'users_all': {
        'label': 'ScoreSaber 유저 PP 기록+추천 데이터',
        'steps': [
            (DIR_PATH, ['python3', 'kr_ranker.py']),
            (DIR_PATH, ['python3', 'added_user.py']),
            (os.path.join(RECOMMEND_DIR, 'ss_users'), ['python3', 'fetch.py']),
        ],
    },
    'ss_maps': {
        'label': 'ScoreSaber 맵 추천 데이터',
        'steps': [
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'catalog']),
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'scores']),
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'scores-rest-page1']),
        ],
    },
    'bl_maps': {
        'label': 'BeatLeader 맵 추천 데이터',
        'steps': [
            (os.path.join(RECOMMEND_DIR, 'bl_maps'), ['python3', 'fetch.py']),
        ],
    },
    'maps_all': {
        'label': 'ScoreSaber+BeatLeader 맵 추천 데이터',
        'steps': [
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'catalog']),
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'scores']),
            (os.path.join(RECOMMEND_DIR, 'ss_maps'), ['python3', 'fetch.py', 'scores-rest-page1']),
            (os.path.join(RECOMMEND_DIR, 'bl_maps'), ['python3', 'fetch.py']),
        ],
    },
}

USER_UPDATE_ALIASES = {
    '': 'users',
    'pp': 'users',
    'record': 'users',
    'records': 'users',
    '전적': 'users',
    '기록': 'users',
    '추천': 'user_recommend',
    'recommend': 'user_recommend',
    'rec': 'user_recommend',
    '전체': 'users_all',
    '모두': 'users_all',
    'all': 'users_all',
}

MAP_UPDATE_ALIASES = {
    '': 'maps_all',
    'all': 'maps_all',
    'both': 'maps_all',
    '전체': 'maps_all',
    '모두': 'maps_all',
    'ss': 'ss_maps',
    'scoresaber': 'ss_maps',
    '스코어세이버': 'ss_maps',
    'bl': 'bl_maps',
    'beatleader': 'bl_maps',
    '비트리더': 'bl_maps',
}

def update_pid_path(job_key):
    return os.path.join(UPDATE_DIR, f'{job_key}.pid')

def pid_is_running(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (ValueError, ProcessLookupError):
        return False
    except PermissionError:
        return True

def running_update_job(job_key):
    try:
        with open(update_pid_path(job_key), 'r', encoding=ENCODING) as f:
            pid = f.read().strip()
    except FileNotFoundError:
        return None
    return pid if pid_is_running(pid) else None

def map_job_conflicts(job_key):
    user_jobs = ['users', 'user_recommend', 'users_all']
    if job_key in user_jobs:
        return user_jobs
    if job_key == 'maps_all':
        return ['maps_all', 'ss_maps', 'bl_maps']
    if job_key in ('ss_maps', 'bl_maps'):
        return ['maps_all', job_key]
    return [job_key]

def latest_update_log(job_key):
    try:
        names = [
            name for name in os.listdir(UPDATE_LOG_DIR)
            if name.startswith(job_key + '-') and name.endswith('.log')
        ]
    except FileNotFoundError:
        return None
    if not names:
        return None
    return max(
        (os.path.join(UPDATE_LOG_DIR, name) for name in names),
        key=lambda path: os.path.getmtime(path),
    )

def make_update_script(job_key):
    job = UPDATE_JOB_STEPS[job_key]
    lines = [
        'set -euo pipefail',
        f'echo "== {job["label"]} update started: $(date -Is) =="',
    ]
    for cwd, cmd in job['steps']:
        lines.append(f'echo "== {cwd}: {" ".join(cmd)} =="')
        lines.append(f'cd {shlex.quote(cwd)}')
        lines.append(' '.join(shlex.quote(part) for part in cmd))
    lines.append('echo "== update complete: $(date -Is) =="')
    return '\n'.join(lines) + '\n'

def start_update_job(job_key):
    os.makedirs(UPDATE_LOG_DIR, exist_ok=True)
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    log_path = os.path.join(UPDATE_LOG_DIR, f'{job_key}-{timestamp}.log')
    open(log_path, 'a', encoding=ENCODING).close()
    launcher = (
        f'setsid bash -lc {shlex.quote(make_update_script(job_key))} '
        f'>> {shlex.quote(log_path)} 2>&1 < /dev/null & echo $!'
    )
    proc = subprocess.run(
        ['bash', '-lc', launcher],
        cwd=RECOMMEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    pid = proc.stdout.strip().splitlines()[-1]
    with open(update_pid_path(job_key), 'w', encoding=ENCODING) as f:
        f.write(pid)
    return pid, log_path

async def 갱신권한확인(ctx):
    perms = getattr(ctx.author, 'guild_permissions', None)
    if perms and (perms.manage_guild or perms.administrator):
        return True
    try:
        if await bot.is_owner(ctx.author):
            return True
    except Exception:
        pass
    await ctx.send('이 명령어는 서버 관리 권한이 있는 유저만 실행할 수 있습니다.')
    return False

async def 추천데이터_갱신(ctx, job_key):
    for key in map_job_conflicts(job_key):
        pid = running_update_job(key)
        if pid:
            await ctx.send(
                f'이미 `{UPDATE_JOB_STEPS[key]["label"]}` 갱신이 실행 중입니다. '
                f'pid={pid}'
            )
            return
    pid, log_path = start_update_job(job_key)
    await ctx.send(
        f'`{UPDATE_JOB_STEPS[job_key]["label"]}` 갱신을 백그라운드에서 시작했습니다.\n'
        f'pid={pid}\n'
        f'로그: `{log_path}`'
    )

def 갱신상태문구():
    lines = []
    for key, job in UPDATE_JOB_STEPS.items():
        pid = running_update_job(key)
        log_path = latest_update_log(key)
        status = f'실행 중 pid={pid}' if pid else '실행 중 아님'
        if log_path:
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(log_path)))
            status += f', 최근 로그={os.path.basename(log_path)} ({mtime})'
        lines.append(f'- {job["label"]}: {status}')
    return '\n'.join(lines)

@bot.command(aliases=['UPDATEUSERS','updateusers','유저갱신','유저정보업데이트','유저추천데이터갱신'])
async def 유저정보갱신(ctx, kind='전적'):
    if not await 갱신권한확인(ctx):
        return
    job_key = USER_UPDATE_ALIASES.get(str(kind).strip().lower())
    if job_key is None:
        await ctx.send('범위는 `전적`, `추천`, `전체` 중 하나로 입력해주세요. 예: `!유저정보갱신 전적`')
        return
    await 추천데이터_갱신(ctx, job_key)

@bot.command(aliases=['UPDATEMAPS','updatemaps','맵갱신','맵정보업데이트'])
async def 맵정보갱신(ctx, platform='all'):
    if not await 갱신권한확인(ctx):
        return
    job_key = MAP_UPDATE_ALIASES.get(str(platform).strip().lower())
    if job_key is None:
        await ctx.send('플랫폼은 `전체`, `ss`, `bl` 중 하나로 입력해주세요. 예: `!맵정보갱신 ss`')
        return
    await 추천데이터_갱신(ctx, job_key)

@bot.command(aliases=['UPDATESTATUS','updatestatus'])
async def 갱신상태(ctx):
    if not await 갱신권한확인(ctx):
        return
    await ctx.send('```\n' + 갱신상태문구() + '\n```')

async def 추천실행(tool, target, num, playlist_path=None):
    '''recommend/<tool>/similar.py를 실행해 출력을 받아온다 (로컬 DB만 읽음, API 호출 없음)'''
    script = os.path.join(RECOMMEND_DIR, tool, 'similar.py')
    cmd = ['python3', script, str(target), str(num)]
    if playlist_path != None:
    	cmd.append('--playlist='+playlist_path)
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return out.decode('utf-8', 'ignore').strip()

async def 추천응답(ctx, tool, target, num):
    if not str(num).isdecimal():
    	await ctx.send("개수는 숫자로 입력해주세요")
    	return
    num = min(int(num), 15) #discord 2000자 제한
    playlist_path = os.path.join(RECOMMEND_DIR, f'pl_{tool}_{target}.bplist')
    answer = await 추천실행(tool, target, num, playlist_path)
    if not answer:
    	await ctx.send("추천 데이터가 없습니다. 관리자에게 문의해주세요 (recommend/ 데이터 수집 필요)")
    	return
    if len(answer) > 1900:
    	answer = answer[:1900]+"\n...(생략)"
    await ctx.send("```\n"+answer+"\n```")
    if os.path.exists(playlist_path): #추천 결과를 게임에서 바로 쓸 수 있는 플레이리스트로 첨부
    	await ctx.send(file = discord.File(playlist_path, filename = f'similar_{target}.bplist'))
    	os.remove(playlist_path)

async def 곡_추천(ctx, link, num):
    if link == None:
    	await ctx.send("`!곡추천 [스코어세이버 리더보드 주소|id] [개수]` 형식으로 입력해주세요")
    	return
    found = re.findall(r'\d+', link)
    if not found:
    	await ctx.send("리더보드 id를 찾을 수 없습니다. 입력을 확인해주세요")
    	return
    await 추천응답(ctx, 'ss_maps', found[-1], num) #map/45827/difficulty/313895 처럼 마지막 숫자가 리더보드 id

async def 블_곡_추천(ctx, link, num):
    if link == None:
    	await ctx.send("`!블곡추천 [비트리더 리더보드 주소|id] [개수]` 형식으로 입력해주세요")
    	return
    m = re.search(r'global/([0-9a-fx]+)', link)
    target = m.group(1) if m else link.rstrip('/').split('/')[-1]
    await 추천응답(ctx, 'bl_maps', target, num)

async def 유저_추천(ctx, link, num):
    if link == None: #입력 없으면 등록된 내 계정 사용
    	discordid = str(ctx.author.id)
    	if not diccheck(discordid):
    		await ctx.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    		return
    	target = did_sc[discordid]
    else:
    	found = re.findall(f'\d{{{SCORESABER_USER_ID_MIN},}}', link)
    	if not found:
    		await ctx.send("스코어세이버 id를 찾을 수 없습니다. 입력을 확인해주세요")
    		return
    	target = found[0]
    await 추천응답(ctx, 'ss_users', target, num)

#------------------------------------------------------------------------------------------------
async def 검색하기(ctx):
    try:
    	await ctx.send("검색 중입니다. 잠시만 기다려주세요")
    	name = ctx.message.content.split()
    	opt = ppsearch(name[1])
    	output="```\n"
    	for element in opt:
    		output = output+"닉네임: "+element[0]+"\n"
    		output = output+"PP: "+element[1]+"\n"
    		output = output+"주소: "+element[2]+"\n\n"
    	output = output+"```"
    	await ctx.send(output)
    	await ctx.send(str(name[1])+" 에 대한 검색결과입니다.")
    except Exception as ex:
    	print('에러', ex) 
    	await ctx.send("오류가 발생했습니다. 입력을 확인해주세요")
    else:
    	global number
    	if (len(opt)>0):
    		await ctx.message.add_reaction('1️⃣')
    	if (len(opt)>1):
    		await ctx.message.add_reaction('2️⃣')
    	if (len(opt)>2):
    		await ctx.message.add_reaction('3️⃣')
    	if (len(opt)>3):
    		await ctx.message.add_reaction('4️⃣')
    	if (len(opt)>4):
    		await ctx.message.add_reaction('5️⃣')
    	await ctx.message.add_reaction('❎')
    	
    	await ctx.send('몇번째 계정으로 등록할지 반응해주세요')

    	def check(reaction, user):
    		global number
    		returnvalue = False
    		if(user == ctx.author):
    			number = {'1️⃣':1,'2️⃣':2,'3️⃣':3,'4️⃣':4,'5️⃣':5,'❎':-1}.get(str(reaction.emoji), 0)
    			if number != 0:
    				returnvalue = True
    		return returnvalue
    	try:
    		reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    	except :
    		await ctx.send('오류가 발생했습니다. 계정이 등록되지 않았습니다.')
    	else:
    		if number == -1:
    			await ctx.send("계정등록을 취소합니다")
    		else:
    			regist(str(ctx.author.id), str(opt[number-1][2]))
    			await ctx.send(str(number)+"번째 계정이 등록되었습니다")
    		await ctx.message.clear_reactions()
#------------------------------------------------------------------------------------------------

bot.run(TOKEN)

#id = message.author.id #id라는 변수에는 메시지를 보낸사람의 ID를 담습니다.
#channel = message.channel #channel이라는 변수에는 메시지를 받은 채널의 ID를 담습니다.
'''
message.content ▶ 사용자가 보낸 내용을 표시합니다.

message.guild ▶ 보낸 서버 이름을 표시합니다.

message.author ▶ 보낸 유저의 태그까지 포함해서 표시합니다.

message.channel ▶ 보낸 유저의 채널을 표시합니다.

regist_info
'''

# 크롤링 세팅-----------------------------------------
'''
options = webdriver.ChromeOptions()

options.add_argument('headless')
options.add_argument("no-sandbox")

options.add_argument('window-size=1920x1080')

options.add_argument("disable-gpu")   # 가속 사용 x
options.add_argument("lang=ko_KR")
options.add_argument("user-agent=bokurin")

driver = webdriver.Chrome('./chromedriver.exe', chrome_options=options)
'''
