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
INDIA_URL = 'https://www.screener.in/screens/157004/52-Week-Highs/'
WATCHLIST_LOC = '/tmp/watchlist.txt'
S3_BUCKET = 'umarye.com'
INDEX_PAGE_LOC = '/tmp/index.html'

# download watchlist data from screener passing the cookie file
BASH_CMD = 'curl -s --cookie /Users/amit/Downloads/cookies.txt ' + INDIA_URL + '>' + WATCHLIST_LOC
os.system(BASH_CMD)

creds = ''
with open(CREDS, 'r') as infile:
    creds = json.load(infile)


conn = boto.connect_s3(creds["access_key"], creds["secret_key"],
                       calling_format=boto.s3.connection.OrdinaryCallingFormat())


ENV = Environment(loader=FileSystemLoader('./templates'))
template = ENV.get_template('index.html')

soup = BeautifulSoup(open(WATCHLIST_LOC), "lxml")
items = soup.findAll('tr')
if len(items) > 0:
    items.pop(0)
else:
    print("Its time to download the cookies again.")
    sys.exit(0)


stocks = []

for item in items:
    elements = item.findAll('td')
    if len(elements) > 0:
        stock_name = elements[1].text.strip()
        down_from_52w_high = elements[13].text.strip()
        an_item = dict(stock_name=stock_name,down_from_52w_high=down_from_52w_high)
        stocks.append(an_item)

print stocks
html = template.render(data=stocks)
with open(INDEX_PAGE_LOC, 'w') as fh:
    fh.write(html)

# upload index.html to s3 bucket=market-watchlist
bucket = conn.lookup(S3_BUCKET)
key = Key(bucket)
key.name = 'index.html'
key.set_contents_from_filename(INDEX_PAGE_LOC)
