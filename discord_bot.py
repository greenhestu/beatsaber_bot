'''
20200425수정  조명근 
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
import discord, asyncio
#from selenium import webdriver


game = discord.Game("오전 5시30~40분을 제외하고 작동")
bot = commands.Bot(command_prefix = '!', status=discord.Status.online, activity=game, help_command = None)
number = 0
ENCODING = 'utf-8'
with open('token.txt','r', encoding=ENCODING) as text:
    TOKEN = text.read()
print(TOKEN)

#------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
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

#------------------------------------------------------------------------------------------------
async def 정보등록(ctx): 
    try:
    	sc = ctx.message.content.split()[-1]
    	sc = sc.split('u/')[-1]
    	if diccheck(str(ctx.author.id)):
    		await ctx.send(f'`{ctx.author}님은 이미 등록되어있습니다. 이번에 입력하신 정보로 재등록합니다`')
    	if regist(str(ctx.author.id),sc):
    		await ctx.send('성공적으로 등록되었습니다')
    	else:
    		await ctx.send('등록에 실패했습니다 올바른 주소를 입력해주세요')
    except:
    	await message.channel.send('입력을 확인해주세요')

async def 타_등록(ctx):
    try:
    	did = ctx.message.content.split()[-2]
    	sc = ctx.message.content.split()[-1]
    	sc = sc.split('u/')[-1]
    	if diccheck(str(did)):
    		await ctx.send(f'`{did}님은 이미 등록되어있습니다. 이번에 입력하신 정보로 재등록합니다.`')    		
    	if regist(str(did),sc):
    		await ctx.channel.send("성공적으로 등록되었습니다")
    	else:
    		await ctx.channel.send("등록에 실패했습니다 올바른 주소를 입력해주세요")
    except:
    	await ctx.channel.send("입력을 확인해주세요")

async def 추가하기(ctx, link):
    if link != None:
    	link = link.split('u/')[-1]
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
    	else:
    		imageurl = "https://new.scoresaber.com"+listdata[1]

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
    	else:
   			imageurl = "https://new.scoresaber.com"+listdata[1]
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

''' 과거 코드 (현재 삭제, 과거전적 없음)
@bot.event
async def on_message(message):

# 20200425추가
    if (message.content.startswith("!검색") or message.content.startswith("!s") or message.content.startswith("!S")):
    	try:
    		await message.channel.send("검색 중입니다. 잠시만 기다려주세요")
    		name = message.content.split()
    		opt = ppsearch(name[1])
    		output="```\n"
    		for element in opt:
    			output = output+"닉네임: "+element[0]+"\n"
    			output = output+"PP: "+element[1]+"\n"
    			output = output+"주소: "+element[2]+"\n\n"
    		output = output+"```"
    		await message.channel.send(output)
    		await message.channel.send(str(name[1])+" 에 대한 검색결과입니다.")
    	except Exception as ex:
    		print('에러', ex) 
    		await message.channel.send("오류가 발생했습니다. 입력을 확인해주세요")
    	else:
    		global number
    		if (len(opt)>0):
    			await message.add_reaction('1️⃣')
    		if (len(opt)>1):
    			await message.add_reaction('2️⃣')
    		if (len(opt)>2):
    			await message.add_reaction('3️⃣')
    		if (len(opt)>3):
    			await message.add_reaction('4️⃣')
    		if (len(opt)>4):
    			await message.add_reaction('5️⃣')
    		await message.add_reaction('❎')
    		
    		await message.channel.send('몇번째 계정으로 등록할지 반응해주세요')

    		def check(reaction, user):
    			global number
    			returnvalue = False
    			if(user == message.author):
    				number = {'1️⃣':1,'2️⃣':2,'3️⃣':3,'4️⃣':4,'5️⃣':5,'❎':-1}.get(str(reaction.emoji), 0)
    				if number != 0:
    					returnvalue = True
    			return returnvalue

    		try:
    			reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
    		except :
    			await message.channel.send('오류가 발생했습니다. 계정이 등록되지 않았습니다.')
    		else:
    			if number == -1:
    				await message.channel.send("계정등록을 취소합니다")
    			else:
    				regist(str(message.author.id), str(opt[number-1][2]))
    				await message.channel.send(str(number)+"번째 계정이 등록되었습니다")
    			await message.clear_reactions()
#-------------------------------------------------------------------------------------- 
    if (message.content.startswith("!등록") or message.content.startswith("!r") or message.content.startswith("!R")) :
    	try:
    		sc = message.content.split()[-1]
    		sc = sc.split('u/')[-1]
    		if diccheck(str(message.author.id)):
    			await message.channel.send("`"+str(message.author)+"님은 이미 등록되어있습니다 이번에 입력하신 정보로 재등록합니다`")
    		if regist(str(message.author.id),sc):
    			await message.channel.send("성공적으로 등록되었습니다")
    		else:
    			await message.channel.send("등록에 실패했습니다 올바른 주소를 입력해주세요")
    	except:
    		await message.channel.send("입력을 확인해주세요")

    if (message.content.startswith("!타등록") or message.content.startswith("!or") or message.content.startswith("!OR")):
    	try:
    		did = message.content.split()[-2]
    		sc = message.content.split()[-1]
    		if diccheck(str(did)):
    			await message.channel.send("`"+str(message.author)+"님은 이미 등록되어있습니다 이번에 입력하신 정보로 재등록합니다`")    		
    		if regist(str(did),sc):
    			await message.channel.send("성공적으로 등록되었습니다")
    		else:
    			await message.channel.send("등록에 실패했습니다 올바른 주소를 입력해주세요")
    	except:
    		await message.channel.send("입력을 확인해주세요")
#-------------------------------------------------------------------------------------- 
    if (message.content.startswith("!추가") or message.content.startswith("!a") or message.content.startswith("!A")):
    	splitaddinput = message.content.split()
    	#splitaddinput[1] = link
    	if (len(splitaddinput) == 2):
    		splitaddinput[1] = splitaddinput[1].split('u/')[-1]
    		username = validcheck(splitaddinput[1])
    		if(username!= False):
    			dupcheck = open('Added_User_List.txt', 'r')
    			checker = dupcheck.readlines()
    			dupcheck.close()

    			if (splitaddinput[1]+'\n' in checker):
    				await message.channel.send(str(username)+"님의 전적은 이미 기록중입니다")
    			elif checker[len(checker)-1] == splitaddinput[1]:
    				await message.channel.send(str(username)+"님의 전적은 이미 기록중입니다")
    			else:
    				add_user = open('Added_User_List.txt', 'a')
    				add_user.write('\n'+splitaddinput[1])
    				add_user.close()
    				await message.channel.send(str(username)+"님의 전적이 내일부터 기록됩니다")
    		else:
    			await message.channel.send("존재하지 않는 유저입니다")
    	else:
    		await message.channel.send("입력을 확인해주세요")

#-------------------------------------------------------------------------------------- 
    if (message.content=="!내정보" or message.content=="!내능지" or message.content=="!i" or message.content=="!I"):
    	discordid = str(message.author.id)
    	listdata = embeddata(discordid)
    	if listdata == "notregist":
    		await message.channel.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    	elif listdata == "scoresabererror":
    		await message.channel.send("스코어세이버와의 연결이 불안정합니다")
    	elif listdata == "fileerror":
    		await message.channel.send("전적을 읽는동안 문제가 발생했습니다")
    	else:
    		description = ""
    		for i in range(3,len(listdata)):
    			description+=listdata[i]

    		if listdata[1] == "/images/oculus.png":
    			imageurl= "https://scoresaber.com/imports/images/oculus.png"
    		else:
    			imageurl = "https://new.scoresaber.com"+listdata[1]

    		embed=discord.Embed(title=listdata[0]+"'s profile", url="https://scoresaber.com/u/"+listdata[2],description= description,color=0x00ff56)
    		embed.set_thumbnail(url=imageurl)
    		await message.channel.send(embed= embed)

    if (message.content.startswith("!타정보") or message.content.startswith("!oi") or message.content.startswith("!OI")):
    	discordid = str(message.content.split()[-1])
    	listdata = embeddata(discordid)
    	if listdata == "notregist":
    		await message.channel.send("등록되어있지 않은 계정입니다")
    	elif listdata == "scoresabererror":
    		await message.channel.send("스코어세이버와의 연결이 불안정합니다")
    	elif listdata == "fileerror":
    		await message.channel.send("전적을 읽는동안 문제가 발생했습니다")
    	else:
    		description = ""
    		for i in range(3,len(listdata)):
    			description+=listdata[i]

    		if listdata[1] == "/images/oculus.png":
    			imageurl= "https://scoresaber.com/imports/images/oculus.png"
    		else:
    			imageurl = "https://new.scoresaber.com"+listdata[1]

    		embed=discord.Embed(title=listdata[0]+"'s profile", url="https://scoresaber.com/u/"+listdata[2],description= description,color=0x00ff56)
    		embed.set_thumbnail(url=imageurl)
    		await message.channel.send(embed= embed)


#-------------------------------------------------------------------------------------- 
    if (message.content.startswith("!내전적") or message.content.startswith("!h") or message.content.startswith("!H")):
    	mes = message.content.split()
    	temp = history(str(message.author.id))
    	if temp == False: await message.channel.send("입력을 확인해주세요")
    	elif temp == "regist": await message.channel.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    	elif temp == "notrecord": await message.channel.send("기록되지않는 계정입니다\n`기록을 원하시면 !추가 [스코어세이버 주소]를 입력하여 전적이 기록되도록 할 수 있습니다`")
    	else:
    		opt = '```'
    		history_length = len(temp)
    		if history_length >= 20: #기본 20개 기록된 게 20개보다 적으면 history_overflow에 기록
    			x = 20
    			history_overflow = -1
    		else:
    			history_overflow = history_length
    			x = history_length

    		if len(mes)>1:
    			try:
    				num = int(mes[1])
    				if num > history_length:
    					history_overflow = history_length
    				x = min(48, num, history_length) #디스코드 한번에 보낼 수 있는게 최대 50줄임 #50줄은 도배 같아서 20줄
    			except:
    				await message.channel.send("숫자를 입력해주세요")
    				x=0
    		for i in range(x):
    			try:
    				opt = opt + str(temp[history_length-x+i]) 
    			except:
    				await message.channel.send("알 수 없는 오류가 발생했습니다")
    				break
    		opt += '```'
    		if history_overflow > 0:
    			await message.channel.send(str(message.author)+"님의 전적은 "+str(history_overflow)+"개만 기록되어 있습니다")
    			history_overflow = -1
    		if x!=0:
    			await message.channel.send(opt)
    			await message.channel.send(str(message.author)+" 님의 전적을 출력했습니다")

    if (message.content.startswith("!타전적") or message.content.startswith("!oh") or message.content.startswith("!OH")):
    	mes = message.content.split()
    	if len(mes)<=1:
    		await message.channel.send("찾고싶은 계정정보를 입력해주세요")
    	else:
    		tmp = mes[1]
    		if str(tmp) in did_sc:
    			temp = history(str(tmp))
    			if temp == False: await message.channel.send("입력을 확인해주세요")
    			elif temp == "regist": await message.channel.send("등록되어있지 않은 계정입니다")
    			elif temp == "notrecord": await message.channel.send("기록되지않는 계정입니다")
    			else:
    				opt = '```'
    				history_length = len(temp)
    				if history_length >= 20: #기본 20개 기록된 게 20개보다 적으면 history_overflow에 기록
    					x = 20
    					history_overflow = -1
    				else:
    					history_overflow = history_length
    					x = history_length

    				if len(mes)>2:
    					try:
    						num = int(mes[2])
    						if num > history_length:
    							history_overflow = history_length
    						x = min(48, num, history_length) #디스코드 한번에 보낼 수 있는게 최대 50줄임 
    					except:
    						await message.channel.send("숫자를 입력해주세요")
    						x=0
    				for i in range(x):
    					try:
    						opt = opt + str(temp[history_length-x+i])
    					except:
    						await message.channel.send("알 수 없는 오류가 발생했습니다")
    						break
    				opt += '```'

    				if history_overflow > 0:
    					await message.channel.send(str(tmp)+"님의 전적은 "+str(history_overflow)+"개만 기록되어 있습니다")
    					history_overflow = -1
    				if x!=0:
    					await message.channel.send(opt)
    					await message.channel.send(str(tmp)+" 님의 전적을 출력했습니다")
    		else: await message.channel.send("등록되지않은 계정입니다. 등록을 먼저해주세요")

#--------------------------------------------------------------------------------------    		
    
    if message.content == ("딕셔너리"):
    	for key, value in did_sc:
    		await message.channel.send(str(key)+" : "+str(value))

    if message.content.startswith("삭제"):
    	user = message.content.split()[-1]
    	if str(user) in did_sc:
    		del did_sc[str(user)]
    		f = open("userdata.bin",'wb')
    		pickle.dump(did_sc,f)
    		f.close()
    		await message.channel.send(str(user)+" 님의 데이터를 제거했습니다")
    	else:
    		 await message.channel.send("존재하지 않는 유저입니다")
#--------------------------------------------------------------------------------------

    if message.content.startswith("!과거전적"):
    	mes = message.content.split()
    	if len(mes)==1:  
    		temp = False;
    	elif len(mes)==3 :
    		temp = month_history(str(mes[-2]),int(mes[-1])-1) 
    	elif len(mes)==2:	
    		temp = month_history(str(message.author.id),int(mes[-1])-1)
    	if temp == False: await message.channel.send("입력을 확인해주세요")
    	if temp == "regist": await message.channel.send("등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`")
    	if temp == "notrecord": await message.channel.send("기록되지않는 계정입니다\n`기록을 원하시면 !추가 [스코어세이버 주소]를 입력하여 전적이 기록되도록 핳 수 있습니다`")
    	else:
    		opt = '```\n'
    		x =  len(temp)
    		for i in range(x):
    			try:
    				opt = opt + str(temp[len(temp)-x+i]) 
    			except:
    				await message.channel.send("알 수 없는 오류가 발생했습니다")
    				break
    		opt += '```'
    		await message.channel.send(opt)
    		#await message.channel.send(opt)
    		await message.channel.send("과거전적을 출력했습니다")
#--------------------------------------------------------------------------------------
    if (message.content.startswith("!랭킹") or message.content.startswith("!rank") or message.content.startswith("!RANK")):
    	contury = message.content.split()
    	if len(contury) == 1:
    		await message.channel.send("https://scoresaber.com/global")
    	else:
    		await message.channel.send("https://scoresaber.com/global?country="+str(contury[-1]))
#testsection---------------------------------------------------------------------------

    if (message.content.startswith("!그래프") or message.content.startswith("!g") or message.content.startswith("!G")):
    	mes = message.content.split()
    	length = len(mes)
    	if length == 1:
    		answer = HistoryGraph(str(message.author.id))
    		if answer == True:
    			history_overflow = overflowcheck()
    			if history_overflow>0:
    				await message.channel.send(str(message.author)+"님의 전적은 "+str(history_overflow)+"개만 기록되어 있습니다")
    				freeoverflow()	
    			await message.channel.send(file = discord.File("graph.png"))
    		else:
    			await message.channel.send(str(answer))

    	elif length ==2:
    		answer = HistoryGraph(str(message.author.id), int(mes[1]))
    		if answer == True:

    			history_overflow = overflowcheck()
    			if history_overflow>0:
    				await message.channel.send(str(message.author)+"님의 전적은 "+str(history_overflow)+"개만 기록되어 있습니다")	
    				freeoverflow()
    			await message.channel.send(file = discord.File("graph.png"))
    		else:
    			await message.channel.send(str(answer))
    	else:
    		await message.channel.send("입력을 확인해주세요")

    if (message.content.startswith("!비교") or message.content.startswith("!c") or message.content.startswith("!C")):
    	mes = message.content.split('-')
    	if len(mes) != 2:
    		await message.channel.send("- 뒤에 비교할 유저의 스코어세이버 주소를 입력해주세요")
    	else:
    		userlinks = mes[1].split(',')
    		command = mes[0].split()
    		if len(command) == 1:
    			answer = Comparegraph(userlinks)
    			if answer == True:
    				await message.channel.send(file = discord.File("graph.png"))
    			else:
    				await message.channel.send(str(answer))
    		elif len(command) == 2:
    			answer = Comparegraph(userlinks, int(command[1]))
    			if answer == True:
    				await message.channel.send(file = discord.File("graph.png"))
    			else:
    				await message.channel.send(str(answer))
    		else:
    			await message.channel.send("입력을 확인해주세요")
'''