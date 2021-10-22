import os 
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

date = datetime.now() #날짜
dir_path = os.path.dirname(os.path.abspath(__file__))
path = dir_path#os.path.join(dir_path, "../")  #전적 텍스트 파일 경로
path_pp = os.path.join(dir_path, "data/")
link = 'https://new.scoresaber.com/api/player/'

added_user = open(os.path.join(dir_path, "Added_User_List.txt"), 'r')
Url = added_user.readlines()
added_user.close()
ENCODING='utf-8'
ERRORS = 'ignore'

#받아온 파일에서 \n지우기
for i in range(len(Url)):
	Url[i] = Url[i].strip()

playerinfo = ['name','grank','rank','pp','url']
#time.sleep(5)
# 스코어세이버 진입 상태 
def reading(url):
	global date
	global link
	global path

	try:
		DupChecker = open(path_pp+"PP_text/"+url+".txt", 'r')
		textline = DupChecker.readlines()
		if(textline[-1].startswith('{}-{}-{}'.format(date.year, date.month, date.day))):
			DupChecker.close()
			print('already wrote')
			return False
		DupChecker.close()
	except FileNotFoundError:
		print('1st writing')
	except UnicodeDecodeError:
		print("UnicodeDecodeError")

	playerinfo[4] = url

	source = requests.get(link+url+"/basic")
	soup = BeautifulSoup(source.text.encode('utf-8', 'replace'), 'html.parser')
	strsoup = str(soup)
	element_list = strsoup.split(':')
	if(len(element_list) < 4):
		print('wrong address')
		return False
	name = element_list[3].split(',')[0].strip().strip('"')
	playerinfo[0] = name
	rank = element_list[6].split(',')[0].strip()
	playerinfo[2] = rank
	pp = element_list[7].split(',')[0].strip()
	playerinfo[3] = pp
	print(playerinfo)

	return True
				
		#print(link)
		
for url in Url:

	#정보를 가져오는데 실패하면 작성 안함
	if(reading(url)):
	
		playerfile = open(path_pp+"PP_text/"+playerinfo[4]+".txt", 'a', encoding=ENCODING, errors=ERRORS)
		if int(date.day ==1):
			playerfile.write("nextmonth\n")
		#이름이 읽을 수 없는 문자인 경우
		try:
			playerfile.write('{}-{}-{}'.format(date.year, date.month, date.day)+", "+playerinfo[3]+", Rank: "+playerinfo[2].strip('#')+", Name: "+playerinfo[0]+"\n")
		except:
			playerfile.write('{}-{}-{}'.format(date.year, date.month, date.day)+", "+playerinfo[3]+", Global Rank: "+playerinfo[1]+", Rank: "+playerinfo[2]+", Name: "+" <error>"+"\n")
		playerfile.close()

		print('success')
	#writing()



'''
print('{}-{}-{}'.format(date.year, date.month, date.day)+"/ ", end='')
print (response[temp_pp_loc+20:temp_pp_loc+30])
# PP 추출 후 프린트  

temp_writing = open(path, 'a')
temp_writing.write("\n")
temp_writing.write('{}-{}-{}'.format(date.year, date.month, date.day)+" "+response[temp_pp_loc+20:temp_pp_loc+30])
temp_writing.close()
# PP 텍스트 작성
'''


'''
Url = ['76561198811476255']
resp = requests.get("https://scoresaber.com/u/"+Url[0])

print(requests.__cake__)
print('------------')

print('------------')
print(requests.__cake__)
time.sleep(100)
'''
