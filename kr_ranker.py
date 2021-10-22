import os 
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class kr_ranker:
	def __init__(self):
		self.url = ''
		self.name = ''
		self.pp = ''
		#self.diff = ''
		self.txt = ''
		self.bool = 1

hestu = 'hestu`s pp'
dir_path = os.path.dirname(os.path.abspath(__file__))
path =os.path.join(dir_path, "data/") #"C:/Users/cmk/Desktop/python_bs/" # 

date = datetime.now()
ENCODING = 'utf-8'
ERRORS = 'ignore'
#--------------------------------------------------------
'''
selenium_exist = True
try:
	options = webdriver.ChromeOptions()

	options.add_argument('headless')
	options.add_argument("no-sandbox")

	options.add_argument('window-size=1920x1080')

	options.add_argument("disable-gpu")   # 가속 사용 x
	options.add_argument("lang=ko_KR")
	options.add_argument("user-agent=bokurin")

	driver = webdriver.Chrome('./chromedriver.exe', chrome_options=options)
except:
	selenium_exist = False
	print("selenium error")
'''
selenium_exist = False
#-------------------------------------------------------

link = 'https://scoresaber.com/global?country=kr'
link2 = 'https://scoresaber.com/global/2&country=kr'
rank = [[],[]]
tail = 0

def make():
	global tail
	for i in range(51):
		a = kr_ranker()
		rank[tail].append(a)
	tail +=1


def page_declare(address, index):

	def request_retry(address, maxRetryNum):
		try: 
			responce = requests.get(address, timeout=10)
			soup = BeautifulSoup(responce.text.encode('utf-8', 'replace'), 'html.parser')
			if(len(soup.findAll('td', attrs={'class': 'player'}))<50):
				raise(Exception('# of player is less than 50'))
			return soup
		except Exception as e:
			print(e)
			if(maxRetryNum > 0):
				return request_retry(address, maxRetryNum-1)

	global hestu, selenium_exist
	if(selenium_exist):
		driver.get(address)
		responce = driver.page_source
		soup = BeautifulSoup(responce, 'html.parser')
	else:
		soup = request_retry(address, 5)
	trs = soup.find_all('tr')[1:]

	for i, tr in enumerate(trs):
		rank[index][i+1].txt = tr
		rank[index][i+1].url = rank[index][i+1].txt.find('a')['href'].split('/')[-1]
		rank[index][i+1].name = rank[index][i+1].txt.find('span', attrs={'class':'pp'}).text
		rank[index][i+1].pp = rank[index][i+1].txt.find('span',attrs={'class':'ppValue'}).text.replace(',','')
		print(rank[index][i+1].name)
	'''
	tags = soup.findAll('td', attrs={'class': 'player'})
	pp_list = soup.findAll('td', attrs={'class': 'pp'})
	tags_file = str(tags).split('/u/')
	pp_file = str(pp_list).split('ppValue">')

	for i in range(1, 51):
		rank[index][i].txt = tags_file[i]
		rank[index][i].url = rank[index][i].txt.split('"')[0]
	
		rank[index][i].name = rank[index][i].txt.split('</')[0].split('700;">')[1]
		forcsv = pp_file[i].split('</span')[0]
		forcsv = str(forcsv).replace(',', '')
		rank[index][i].pp = forcsv
		if rank[index][i].name == "Hestu":
			hestu = rank[index][i].pp
		print(rank[index][i].name)
	'''
def writing(index, value):
	for i in range(1,51):
		playerfile = open(path+"PP_text/"+rank[index][i].url+".txt", 'a', encoding=ENCODING, errors=ERRORS)
		#playerfile = open(path+"PP_text_test/"+rank[index][i].url+".txt", 'a', encoding=ENCODING, errors=ERRORS)
		strDate = '{}-{}-{}'.format(date.year, date.month, date.day)
		if int(date.day ==1):
			playerfile.write("nextmonth\n")
		try:
			writeContent = strDate + f', {str(rank[index][i].pp)}, Rank: {i+(value-1)*50}, Name: {str(rank[index][i].name)}\n'
			playerfile.write(writeContent)
		except Exception as e:
			writeContent = strDate + f', {str(rank[index][i].pp)}, Rank: {i+(value-1)*50}, Name: <error>\n'
			playerfile.write(writeContent)
			log = open("log.txt",'a')
			log.write(f'{strDate}, {str(e)}\n')
			log.close()
		playerfile.close()

#한국 1,2페이지 pp변동
make()
page_declare(link,0)
writing(0, 1)
make()
page_declare(link2,1)
writing(1, 2)

#-------------------------------------------------------------------------------------------------
# 내 pp 변동

hestu_writing = open(path+"Hestu_PP.txt", 'a', encoding=ENCODING, errors=ERRORS)
hestu_writing.write('{}-{}-{}'.format(date.year, date.month, date.day)+", "+hestu+"pp\n")
hestu_writing.close()

#-------------------------------------------------------------------------------------------------


'''
for i in range(1,51):
	playerfile = open(path+"PP_text/"+rank[i].url+".txt", 'r')
	lines = playerfile.readlines()
	for line in lines:
		if line == "#"+rank[i].name:
			rank[i].bool = 0
	playerfile.close()
'''
#driver.get_screenshot_as_file('capture_kr_rank.png')
# 스크린샷 
if(selenium_exist):
	driver.quit()
