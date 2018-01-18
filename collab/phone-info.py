#created by lfane
#1/17/18
#Loops through a list of Cisco IP phones; opens each phones webpage and dumps contents to a file
import requests
from bs4 import BeautifulSoup

#Open text file containing phone IPs
filePhoneReport = open("phonereport.csv","w")

#Open the text file containing the phoneIPs and put the IPs into a list
with open("phoneIPs.txt") as temp_file:
    mylist = temp_file.read().splitlines()

#Loop through the IPs in the list; attempt to get URL, if the URL throws an exception, move on
for phoneIP in mylist:
    phoneURL=("http://"+ phoneIP)
    try:
        r=requests.get(phoneURL)
        page = requests.get(phoneURL)
        soup = BeautifulSoup(page.text, 'html.parser')
        table_div = soup.find('div')
        table = table_div.find('table')
    
        #Print header row separated by commas
        title=""
        content=""
        for row in table.find_all('tr'):
            for td in row.find_all('td')[0]:
                title = title + "," + td.text
        filePhoneReport.write(title[1:])
        filePhoneReport.write("\n")
    
        #Print content row separated by commas
        for row2 in table.find_all('tr'):
            for td in row2.find_all('td')[2]:
                content = content+ "," + td.text
        filePhoneReport.write(content[1:])
        filePhoneReport.write("\n")
    except requests.exceptions.RequestException as err:
        pass
filePhoneReport.close()
