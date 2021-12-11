import os 
import time
import requests
#from bs4 import BeautifulSoup
from datetime import datetime

class kr_ranker:
	def __init__(self):
		self.id = ''
		self.name = ''
		self.pp = ''
		#self.diff = ''
		self.bool = 1

dir_path = os.path.dirname(os.path.abspath(__file__))
path =os.path.join(dir_path, "data/") 

date = datetime.now()
ENCODING = 'utf-8'
ERRORS = 'ignore'

link = 'https://scoresaber.com/api/players?countries=KR&page=' 
rank = []

def make():
	page = []
	for i in range(51):
		a = kr_ranker()
		page.append(a)
	rank.append(page)


def page_declare(address, index):

	def request_retry(address, maxRetryNum):
		try: 
			response = requests.get(address, timeout=10)
			if(response.status_code != 200):
				Exception("HTTP status is not 200")
			json = response.json()
			return json
		except Exception as e:
			print(e)
			if(maxRetryNum > 0):
				return request_retry(address, maxRetryNum-1)
	
	json = request_retry(address, 3)
	print(json)

	for i, data in enumerate(json["players"]):
		rank[index][i+1].id = data['id']
		rank[index][i+1].name = data['name']
		rank[index][i+1].pp = data['pp']
		print(rank[index][i+1].name)

def writing(index):
	for i in range(1,51):
		#오늘 랭킹이 기록되어있으면 패스
		with open(path+"PP_text/"+rank[index][i].id+".txt", 'r') as DupChecker:
			textline = DupChecker.readlines()
			if(textline[-1].startswith('{}-{}-{}'.format(date.year, date.month, date.day))):
				print(f'{rank[index][i].name} already wrote')
				continue
		#기록용
		playerfile = open(path+"PP_text/"+rank[index][i].id+".txt", 'a', encoding=ENCODING, errors=ERRORS)
		#테스트용
		#playerfile = open(path+"PP_text_test/"+rank[index][i].id+".txt", 'a', encoding=ENCODING, errors=ERRORS)
		strDate = '{}-{}-{}'.format(date.year, date.month, date.day)
		if int(date.day ==1):
			playerfile.write("nextmonth\n")
		try:
			writeContent = strDate + f', {str(rank[index][i].pp)}, Rank: {i+index*50}, Name: {str(rank[index][i].name)}\n'
			playerfile.write(writeContent)
		except Exception as e:
			writeContent = strDate + f', {str(rank[index][i].pp)}, Rank: {i+index*50}, Name: <error>\n'
			playerfile.write(writeContent)
			log = open("log.txt",'a')
			log.write(f'{strDate}, {str(e)}\n')
			log.close()
		playerfile.close()

#한국 1,2페이지 pp변동
for i in range(2):
	address = link+str(i+1)
	make()
	page_declare(address,i)
	writing(i)

'''
for i in range(1,51):
	playerfile = open(path+"PP_text/"+rank[i].id+".txt", 'r')
	lines = playerfile.readlines()
	for line in lines:
		if line == "#"+rank[i].name:
			rank[i].bool = 0
	playerfile.close()
'''
