from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import json
import os
import requests
import sys

# download cookies.txt using the chrome browser plugin
CREDS='credentials.txt'
INDIA_URL = 'https://www.screener.in/screens/245964/All-Time-High/?page='
USA_URL = 'https://in.tradingview.com/markets/stocks-usa/highs-and-lows-ath/'
WATCHLIST_LOC = '/tmp/watchlist.txt'
USA_WATCHLIST_LOC = '/tmp/watchlist_usa.txt'
S3_BUCKET = 'umarye.com'
INDEX_PAGE_LOC = '/tmp/index.html'


creds = ''
with open(CREDS, 'r') as infile:
    creds = json.load(infile)


conn = boto.connect_s3(creds["access_key"], creds["secret_key"],
                       calling_format=boto.s3.connection.OrdinaryCallingFormat())

ENV = Environment(loader=FileSystemLoader('./templates'))
template = ENV.get_template('index.html')

stocks = []
temp = set()

cnt=0
for i in range(1,5):
    # download watchlist data from screener passing the cookie file
    BASH_CMD = 'curl -s --cookie ~/Downloads/cookies.txt ' + INDIA_URL + str(i) + '>' + WATCHLIST_LOC
    os.system(BASH_CMD)

    soup = BeautifulSoup(open(WATCHLIST_LOC), "lxml")
    items = soup.findAll('tr')
    if len(items) > 0:
	    items.pop(0)
    else:
	    print("Its time to download the cookies again.")
	    sys.exit(0)



    with open('ignore.txt', 'r') as f:
	    blacklist = f.read().splitlines() 

    for item in items:
	    elements = item.findAll('td')
	    if len(elements) > 0:
		    stock_name = elements[1].text.strip()
		    if stock_name.strip() not in  blacklist and stock_name not in temp:
			    cnt+=1
			    market_cap = elements[3].text.strip()
			    curr_price = elements[2].text.strip()
			    down_from_52w_high = elements[13].text.strip()
			    an_item = dict(serial_number=cnt,stock_name=stock_name,market_cap=market_cap,curr_price=curr_price,down_from_52w_high=down_from_52w_high)
			    stocks.append(an_item)
		    temp.add(stock_name)


stocks_usa = []
etfs = []

BASH_CMD = 'curl -s --cookie /Users/amit/Downloads/cookies.txt ' + USA_URL + '>' + USA_WATCHLIST_LOC
os.system(BASH_CMD)
soup = BeautifulSoup(open(USA_WATCHLIST_LOC), "lxml")
items = soup.findAll('tr')
if len(items) > 0:
    items.pop(0)
else:
    print("Its time to download the cookies again.\nAlready deleted old cookies.")
    os.remove('/Users/amit/Downloads/cookies.txt')
    sys.exit(0)


for item in items:
    elements = item.findAll('td')
    tickr = elements[0].find('a').contents[0].strip()
    #print tickr
    stock_name = elements[0]['title'].strip()
    stock_vol =  str(elements[5].contents[0].strip())
    stock_price = elements[1].contents[0].strip()
    market_cap =  elements[6].contents[0].strip()

    valid_market_cap = 0
    try:
        temp = str(market_cap)
    except:
        valid_market_cap = 1

    if tickr not in blacklist and\
    float(stock_price) > 10.0 and\
    valid_market_cap == 0 and 'B' in str(market_cap):
        if 'M' in stock_vol:
            pass
        elif 'K' in stock_vol:
            if int(float((stock_vol.replace('K', '')))) < 300:
                #print "ignored1", tickr, stock_vol
                continue
            else:
                pass
        else:
            #print "ignored1", tickr, stock_vol
            continue
        

        if stock_name not in  blacklist:
            an_item = dict(stock_name=stock_name,tickr=tickr,stock_price=stock_price)
            
            if 'ETF' in stock_name:
                etfs.append(an_item)
            else:
                stocks_usa.append(an_item)

    

#html = template.render(data1=stocks,data2=stocks_usa,data3=etfs)
html = template.render(data1=stocks,data2=stocks_usa)
with open(INDEX_PAGE_LOC, 'w') as fh:
    fh.write(html)

# upload index.html to s3 bucket=market-watchlist
bucket = conn.lookup(S3_BUCKET)
key = Key(bucket)
key.name = 'index.html'
key.set_contents_from_filename(INDEX_PAGE_LOC)
