#created by lfane

import requests
from bs4 import BeautifulSoup

page = requests.get('http://10.2.1.164/')
soup = BeautifulSoup(page.text, 'html.parser')
table_div = soup.find('div')
table = table_div.find('table')
table_rows = table.find_all('tr')
for tr in table_rows:
 td = tr.find_all('td')
 row = [i.text for i in td]
 print(row)