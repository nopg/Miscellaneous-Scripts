#created by lfane

import requests
from bs4 import BeautifulSoup

page = requests.get('http://10.2.1.164/')
soup = BeautifulSoup(page.text, 'html.parser')
table_div = soup.find('div')
table = table_div.find('table')

#Print header row separated by commas
title=""
content=""
for row in table.find_all('tr'):
    for td in row.find_all('td')[0]:
        title = title + "," + td.text
print(title[1:])

#Print content row separated by commas
for row2 in table.find_all('tr'):
    for td in row2.find_all('td')[2]:
        content = content + "," + td.text
print(content[1:])

#table_rows = table.find_all('tr')
#for tr in table_rows:
# td = tr.find_all('td')
# row = [i.text for i in td]
# print(row)