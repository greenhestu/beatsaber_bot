'''
7/17 등록 유효성 검사
7/18 embed 내정보 함수 추가
7/19 graph 함수 추가, embed 수정
여러 언어, 국가에 대응하는 건 어렵다...
유저는 정말 생각지도 못한 입력을 하기도 한다.
7/31 비교 추가, pchip이용한 보간, 한글 추가
8/6 그래프 디자인 변경
9/21 그래프 값 입력 안하면 부족메세지 출력x, 그래프와 비교에서 데이터 이상하면 넘기기
2021 YEAR
0814 font error -> ignore
0825 change encoding to cp949
'''
# ref https://en.wikipedia.org/wiki/Unicode_font
#	  http://www.fontsaddict.com/
import requests, pickle, time, datetime
from matplotlib import pyplot as plt
from matplotlib import font_manager as fm
from scipy.interpolate import interp1d, pchip_interpolate
import numpy as np
from bs4 import BeautifulSoup
Url="https://scoresaber.com/global"
scurl = "https://scoresaber.com/u/"
newsclink = 'https://new.scoresaber.com/api/player/'
path ="D:/beatsaber/PP_text/" 
font_loc = "C:/Windows/Fonts/gulim.ttc"
font_prop = fm.FontProperties(fname = font_loc, size = 12).get_name()
#font_prop = fm.FontProperties(family='Arial Unicode MS', size=12).get_name()
history_overflow = -1
ENCODING = 'utf-8'
ERRORS = 'ignore'


kordataformet = ["이름","지금 안씀","url"," 세계랭킹: "," PP: "," 랭크곡 평균 정확도: "," 플레이한 곡의 개수: "]
engdataformet = ["이름","지금 안씀","url"," GlobalRank: "," PP: "," AvgRanksongAcc: "," TotalPlayCount: "]

did_sc = {}				# 딕셔너리 선언  디스코드 아이디 : 슼세 
#피클 이용해 우저데이터 가져오기
f = open("userdata.bin",'rb')
did_sc = pickle.load(f)
f.close()



#------------------------------------------------------------------------------------------------
'''
유저 이름 입력을 받아 그 유저가 딕셔너리에 저장되어있으면
전적을 리스트로 내보내고 
아니면 notrecord반환
'''
def regist(did, address):
	if validcheck(address) :
		did_sc[did] = address
		f = open("userdata.bin",'wb')
		pickle.dump(did_sc,f)
		f.close()
		return True
	return False
#------------------------------------------------------------------------------------------------
'''
유효성검사
'''
#슼세가 유효한가
def validcheck(userlink):
	link = newsclink+str(userlink)+'/basic'
	source = requests.get(link)
	element_list = str(source.text).split(':')
	if(len(element_list) < 4):
		return False	
	name = element_list[3].split(',')[0].strip().strip('"')
	return name
#등록된 유저인가
def diccheck(discordid):
	if discordid in did_sc:
		return True
	else:
		return False
#전적이 기록되고 있는가
def recordcheck(userlink):
	try:
		f = open(path+userlink+'.txt','r', encoding=ENCODING, errors=ERRORS)
	except Exception as ex:
		print(ex)
		return False
	f.close()
	return True

def overflowcheck():   # from import 는 공유가 아니라 덮어 씌우기로 변수 공유 후 변경에도 공유가 안됨 
	return history_overflow
def freeoverflow():
	print("free")
	global history_overflow
	history_overflow = -1


#------------------------------------------------------------------------------------------------
'''
내전적
과거전적 관련함수
'''
def history(did):
	past = 0
	new = 0
	if did in did_sc:
		optlist = []
		print(str(did_sc[did])+'.txt')
		try:
			f = open(path+str(did_sc[did])+'.txt','r', encoding=ENCODING, errors=ERRORS)
		except Exception as ex:
			print(ex)
			return "notrecord"
		while True:
			line = f.readline()
			if not line:break
			if line =="nextmonth\n":
				continue
			try:
				new = float(str(line).replace('\n','').split(",")[1])
				outpt = str(line).split("Name")[0]+"증가량: "+str(round((new - past),2))+"\n"
				past = new
			except:
				outpt = line
			optlist.append(outpt)
		f.close()
		return optlist
		
	else:
		return "regist"
'''
num달 전의 did 라는 사람의 전적을 리스트로 반환
없으면 notrecord반환 
'''
def month_history(did, num):
	if did in did_sc:
		nowcond = 0
		optlist = [[]]
		print(str(did_sc[did])+'.txt')
		try:
			f = open(path+str(did_sc[did])+'.txt','r', encoding=ENCODING, errors=ERRORS)
		except Exception as ex:
			print(ex)
			return "notrecord"
		while True:
			line = f.readline()
			if not line:break
			if line=="nextmonth\n":
				nowcond+=1
				optlist.append([])
				continue
			try:
				new = float(str(line).replace('\n','').split(",")[1])
				outpt = str(line).split("Name")[0]+"증가량: "+str(round((new - past),2))+"\n"
				past = new
			except:
				outpt = line
			optlist[nowcond].append(outpt)
		f.close()
		return optlist[num]
		
	else:
		return "regist"

def DrawingGraph(name, historylist):
    start = time.time()
    nowdate = datetime.datetime.now()
    xarray = []
    real_list=[]
    for i in range(len(historylist)):
    	date = historylist[i][0].split('-')
    	try: 
    	    real_list.append(float(historylist[i][1]))
    	    historydate = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
    	    diff = nowdate - historydate
    	    xarray.append(int(diff.days))
    	except:
    	    continue
    	
    # x축 (날짜) 계산
    x = np.array(xarray)
    y = np.array(real_list)
    #p = np.poly1d(np.polyfit(x,y,4)) 추세선
    #f = interp1d(x,y,kind = 'cubic')
    listlen = len(historylist)
    t = np.linspace(min(x),max(x),5*listlen)
    pchip = pchip_interpolate(x,y,t)
    if(listlen > 40):
    	plt.plot(x,y, linestyle = 'None', marker = '.', markerfacecolor = 'blue')
    else:
    	plt.plot(x,y, linestyle = 'None', marker = 'o', markerfacecolor = 'blue')
    #plt.plot(t,f(t),'r-')
    plt.plot(t,pchip,'r-')
    #plt.plot(t,p(t),'g-') 추세선
    
    plt.title(name+"'s history "+str(time.strftime('%Y-%m-%d', time.localtime(time.time()))), fontproperties = font_prop, fontsize = 13)
    plt.xlabel("days ago")
    plt.ylabel("Performance Point")
    plt.xticks()
    if max(x) < 5000:
    	plt.axis([max(x),min(x),min(y)*0.99,max(y)*1.01])
    else:
    	plt.axis([max(x),min(x),min(y)*0.995,max(y)*1.005])

    plt.savefig('graph.png')
    plt.clf()
    print(time.time()-start)

def HistoryGraph(discordid, num=None):
	global history_overflow
	if not diccheck(discordid):
		return "등록을 먼저 해주세요\n`!등록 [스코어세이버 주소]를 이용해 등록할 수 있습니다`"
	userlink = did_sc[discordid]
	if not recordcheck(userlink):
		return "전적이 기록되어 있지 않아 그래프를 그릴 수 없습니다.\n`기록을 원하시면 !추가 [스코어세이버 주소]를 입력하여 전적이 기록되도록 할 수 있습니다`"
	f = open(path+str(did_sc[discordid])+'.txt','r', encoding=ENCODING, errors=ERRORS)
	historylist = f.readlines()
	f.close()
	while "nextmonth\n" in historylist:
		historylist.remove("nextmonth\n")

	length = len(historylist)
	if(length == 1):
		return "전적이 1개만 기록되어있어 그래프를 그릴 수 없습니다."
	if num!=None: #num입력이 있었는지 확인
	    if length < num:
	        history_overflow = length
	else:
	    num = 20

	if length >= num:
	    actualloc = -1*num
	else:
	    actualloc = -1*length
	historylist = historylist[actualloc:]
	name = historylist[-1].split(':')[-1].strip()
	for i in range(0,-1*actualloc):
		historylist[i]=historylist[i].split(',')[0:2]
	historylist.reverse()
	DrawingGraph(name, historylist)
	return True
#######################################################################dsfsldkfjsklfjsklfjds
#######################################################################dsfsldkfjsklfjsklfjds
#######################################################################dsfsldkfjsklfjsklfjds
def Drawingline(historylist,color):
    nowdate = datetime.datetime.now()
    xarray = []
    real_list = []
    for i in range(len(historylist)):
    	try:
    		date = historylist[i][0].split('-')
    		real_list.append(float(historylist[i][1]))
    		historydate = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
    		diff = nowdate - historydate
    		xarray.append(int(diff.days))
    	except:
    		continue
    # x축 (날짜) 계산
    x = np.array(xarray)
    y = np.array(real_list)
    #p = np.poly1d(np.polyfit(x,y,4)) 추세선
    f = interp1d(x,y,kind = 'linear')
    t = np.linspace(min(x),max(x),5*len(historylist))
    #plt.plot(x,y,'bo')
    plt.plot(t,f(t), color+'-')
    #plt.plot(t,p(t),'g-') 추세선

def Graphending():
    plt.xlabel("days ago")
    plt.ylabel("Performance Point")
    plt.xticks()
    plt.savefig("graph.png")
    plt.clf()

def Comparegraph(userlinks, num=20):
	nowdate = datetime.datetime.now()
	length = len(userlinks)
	namelist = []
	if(length>7):
		print("Too many component")
		return "8개 이상의 주소를 입력하셨습니다. 7개 이하로 입력해주세요" #요소가 너무 많음

	for i in range(length):
		userlinks[i] = userlinks[i].split('/u/')[-1].strip()
		#if not isdigit(dids[i]):
	minv = 99999
	maxv = 0
	colorcode = ['r', 'g', 'b', 'k', 'y', 'm', 'c']
	for j in range(length):
		if not recordcheck(userlinks[j]):
			return "기록되지 않는 유저가 포함되어있습니다"
		f = open(path+str(userlinks[j])+'.txt','r', encoding=ENCODING, errors=ERRORS)
		historylist = f.readlines()
		f.close()
		while "nextmonth\n" in historylist:
			historylist.remove("nextmonth\n")

		length = len(historylist)
		actualloc = max(-1*num,-1*length)
		historylist = historylist[actualloc:]
		name = historylist[-1].split(':')[-1].strip()
		namelist.append(name)
		for i in range(0,-1*actualloc):
			historylist[i]=historylist[i].split(',')[0:2]
			try:
				historylist[i][1]=float(historylist[i][1])
			except: 
				continue
			if (minv > historylist[i][1]):
				minv = historylist[i][1]
			if (maxv < historylist[i][1]):
				maxv = historylist[i][1]
		Drawingline(historylist, colorcode[j])
	if int(nowdate.hour) > 5:
		plt.axis([ num-1, 0 ,minv*0.995,maxv*1.005])
	else:
		plt.axis([num, 1 ,minv*0.995,maxv*1.005])		
	plt.legend(namelist, prop = {"family":font_prop})
	plt.title(str(namelist).replace("'","")+str(time.strftime('  %Y-%m-%d', time.localtime(time.time()))), fontproperties = font_prop, fontsize = 12)
	Graphending()
	return True
#######################################################################dsfsldkfjsklfjsklfjds
#######################################################################dsfsldkfjsklfjsklfjds
#######################################################################dsfsldkfjsklfjsklfjds


#------------------------------------------------------------------------------------------------
'''
내정보 
슼세 주소 반환용
'''
def mydata(discordid):
	if diccheck(discordid):
		return scurl+did_sc[discordid]
	else:
		return "등록된 계정이 없습니다. 등록을 먼저 해주세요"

def embeddata(discordid):
	if not diccheck(discordid):
		return "notregist"
	date = datetime.datetime.now()
	userlink = did_sc[discordid]
	link = 'https://new.scoresaber.com/api/player/'+str(userlink)+'/full'
	try:
	    source = requests.get(link)
	    source = source.text
	except: 
		return "scoresabererror"
	country = str(source).split('"country": ')[1].split(",")[0].strip('"')
	dataformat = []
	if country == "KR":
		dataformat = kordataformet[:]
	elif (country == "JP") or (userlink == "76561198126686400"):
		dataformat = kordataformet[:]
	else:
		dataformat = engdataformet[:]

	Name = source.split('"playerName": ')[1].split(",")[0].strip('"')
	GlobalRank = source.split('"rank": ')[1].split(",")[0]
	CountryRank = source.split('"countryRank": ')[1].split(",")[0]
	PP = source.split('"pp": ')[1].split(",")[0]
	ImageLink = source.split('"avatar": ')[1].split(",")[0].strip('"')
	AvgRankAcc = source.split('"averageRankedAccuracy": ')[1].split(",")[0]
	TotalPlayCount = source.split('"totalPlayCount": ')[1].split(",")[0]

	dataformat[0] = Name
	dataformat[1] = ImageLink
	dataformat[2] = userlink
	dataformat[3] = dataformat[3]+"#"+GlobalRank+'\n'
	dataformat[4] = dataformat[4]+PP+'pp\n'
	dataformat[5] = dataformat[5]+str(round(float(AvgRankAcc),2))+'%\n'
	dataformat[6] = dataformat[6]+TotalPlayCount+'\n'
	if country == "KR":
		CountryRank = " 국내랭킹: "+"#"+CountryRank+'\n'	
	elif (country == "JP") or (userlink == "76561198126686400"):
		CountryRank = " "+country+" 랭킹: "+"#"+CountryRank+'\n'
	else:
		CountryRank = " "+country+" Rank: "+"#"+CountryRank+'\n'
	dataformat.insert(4,CountryRank)

	if recordcheck(userlink):
		try:
			f = open(path+userlink+'.txt','r', encoding=ENCODING, errors=ERRORS)
			lastline = f.readlines()
			lastline = lastline[-1].split(',')
			f.close()
		except:
			return "fileerror"
		ppchange = lastline[1]
		lastDate = lastline[0].split('-')
		lastDate = datetime.datetime(int(lastDate[0]),int(lastDate[1]),int(lastDate[2]))
		diff = date - lastDate
		if diff.days <= 1:
			if country == "KR":
				ppchange = " 오늘 얻은 PP: "+str(round(float(PP)-float(ppchange),2))+'pp\n'
			elif (country == "JP") or (userlink == "76561198126686400"):
				ppchange = " 오늘 얻은 PP: "+str(round(float(PP)-float(ppchange),2))+'pp\n'
			else:
				ppchange = " Today's PP change: "+str(round(float(PP)-float(ppchange),2))+'pp\n'
			dataformat.insert(6,ppchange)

	return dataformat





#------------------------------------------------------------------------------------------------
'''
검색용 name을 받아서 슼세에서 검색후 5번째까지 반환
'''
def ppsearch(name):
	opt =[]
	Url = 'https://scoresaber.com/global?search='+name
	response = requests.get(Url)
	soup = BeautifulSoup(response.content, "html.parser")
	body = soup.tbody
	modify = str(body).split('"rank"')[1:]
	i=1
	for element in modify:
		opt.append([])
		piece = element.split('">')
		opt[i-1].append(str(piece[3].split('</span')[0]))  # player name
		opt[i-1].append(str(piece[5].split('</span')[0]))# pp
		opt[i-1].append(str(piece[1].split('/u/')[1]))
		i+=1
		if(i>5): break
	
	return opt
#------------------------------------------------------------------------------------------------