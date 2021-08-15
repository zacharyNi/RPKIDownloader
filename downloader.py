import requests
import os
import sys
import threading
import queue
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urlparse
import urllib.error
import re
import json
import datetime
import websocket
import configparser
import tarfile


cp = configparser.ConfigParser()
cp.read('config/collector_list.ini')

RIPE="https://ftp.ripe.net/rpki/"
RIPE_Collectors=cp.get('collector_list','ripe')
RIPE_collector_list=json.loads(RIPE_Collectors)

class DownloadThread(threading.Thread):
	def __init__(self, q, destfolder):
		super(DownloadThread, self).__init__()
		self.q = q
		self.destfolder = destfolder
		self.daemon = True
	def run(self):
		while True:
			url = self.q.get()
			try:
				self.download_url(url)
			except Exception as e:
				print("   Error: %s"%e)
			self.q.task_done()

	def download_url(self,url):
		vantage_folder=self.destfolder
		name=str(url.split('/')[4])+str("_")+str(url.split('/')[5])+str(url.split('/')[6])+str(url.split('/')[7])+str("_")+str(url.split('/')[-1])
		destination="./"+vantage_folder+"/"+name
		print(destination)
		r=requests.get(url, allow_redirects=True)
		open(destination, 'wb').write(r.content)
		print(name)

#	def download_url(self, url):
#		# change it to a different way if you require
#		name = url.split('/')[-1]
#		dest = os.path.join(self.destfolder, name)
#		print "[%s] Downloading %s -> %s"%(self.ident, url, dest)
#		urllib.urlretrieve(url, dest)

def download(urls, destfolder, numthreads=30):
	q = queue.Queue()
	for url in urls:
		q.put(url)
	for i in range(numthreads):
		t = DownloadThread(q, destfolder)
		t.start()
	q.join()

class timeHandler:
    def __init__(self, time):
        self.time=time
        st=time.split("-")
        self.start_year=st[0]
        self.start_month=st[1]
        if self.start_month[0]=='0':
            self.start_month=self.start_month[1:]
        self.start_day=st[2]
        if self.start_day[0]=='0':
            self.start_day=self.start_day[1:]

    def get(self):
        return datetime.datetime(int(self.start_year),int(self.start_month),int(self.start_day))
    
    def get_yr_month(self):
        return datetime.datetime(int(self.start_year),int(self.start_month),int(1))
    

def findElement(base_url, pattern_str):
    #use beautifulsoup to get element in html
    sources=[]
    bs4_parser = "html.parser"
    try:
        response = urllib.request.urlopen(base_url)
        html = BeautifulSoup(response.read(), bs4_parser)
        for link in html.findAll('a',text=re.compile(pattern_str)):
            sources.append(link['href'])
        response.close()
    except urllib.error.HTTPError:
        print(base_url + " dont have such data!") 
    return sources

class RPKIDownloader:
    def __init__(self):   
        self.chosen_collectors=[]
        self.start_time=""
        self.end_time=""
    
    def set_collector(self,collector):
        self.collector=collector
        chosen_collectors=[]
        if collector == "all":
            chosen_collectors=RIPE_collector_list
        else:
            collectors = collector.split(",")
            chosen_collectors=[]
            for c in collectors:
                if c.lower() in RIPE_collector_list:
                    chosen_collectors.append(c.lower())
        self.chosen_collectors=chosen_collectors

    def set_time(self,start_time,end_time):
        self.start_time=start_time
        self.end_time=end_time
    
    def run(self):
        if self.chosen_collectors==[]:
            print("no collectors chosen!")
            return
        elif self.start_time=="" or self.end_time=="":
            print("no start_time or end_time!")
            return
        else:
            self.geturl()
    
    def geturl(self):
        Urls=[]
        folder_name=str(self.start_time+"->"+self.end_time+"||"+self.collector)
        try:
            os.stat(folder_name)
        except:
            os.mkdir(folder_name)
            os.mkdir(folder_name+"/result")
        start_time_handler=timeHandler(self.start_time)
        end_time_handler=timeHandler(self.end_time)
        for cc in self.chosen_collectors:
            sources=[]
            base_url = RIPE + cc + "/"
            sources = findElement(base_url, '((19|20)\d\d)')
            years=[]
            for s in sources:
                years.append(s.split("/")[0])

            selected_years=[]
            start_year=start_time_handler.get().year
            end_year=end_time_handler.get().year
            for y in years:
                temp_year=int(y)
                if start_year<=temp_year and end_year>=temp_year:
                    selected_years.append(y)

            if len(selected_years)==0:
                print(cc+" dont have such data in your start_time and end_time--year")
                continue
            
            selected_packages=[]

            for sy in selected_years:
                sources=[]
                base_url = RIPE + cc + "/" + sy + "/"
                selected_months=[]
        
                sources = findElement(base_url, "(0?[1-9]|1[0-2])")
                for s in sources:
                    month=s.split("/")[0]
                    yr_month=datetime.datetime(int(sy),int(month),int(1))
                    start_yr_month= start_time_handler.get_yr_month()
                    end_yr_month= end_time_handler.get_yr_month()

                    if start_yr_month <= yr_month and end_yr_month >= yr_month:
                        selected_months.append(month)
                    
                if len(selected_months)==0:
                    print(cc+" dont have such data in your start_time and end_time--month")
                    continue
                
                for sm in selected_months:
                    selected_days=[]
                    base_url=RIPE + cc + "/" + sy + "/"+sm+"/"
                    sources = findElement(base_url, "((0|1|2|3)[0-9])") 
                    for s in sources:
                        day=s.split("/")[0]
                        accurate_time=datetime.datetime(int(sy),int(sm),int(day))
                        if start_time_handler.get() <=  accurate_time and end_time_handler.get() >=  accurate_time:
                            selected_days.append(day)
                    
                    if len(selected_days)==0:
                        print(cc+" dont have such data in your start_time and end_time--day")
                        continue
                    
                    for sd in selected_days:
                        final_url=RIPE + cc + "/" + sy + "/"+sm+"/"+sd+'/repo.tar.gz'
                        Urls.append(final_url)
        download(Urls, folder_name)

def untar(fname, dirs):
    """
    解压tar.gz文件
    :param fname: 压缩文件名
    :param dirs: 解压后的存放路径
    :return: bool
    """
    try:
        t = tarfile.open(fname)
        t.extractall(path = dirs)
        return True
    except Exception as e:
        print(e)
        return False

untar('aa.tar.gz','./')
            
    
if __name__=='__main__':
    rpki=RPKIDownloader()
    rpki.set_collector("afrinic.tal")
    rpki.set_time("2017-12-30","2018-01-05")
    rpki.run()
