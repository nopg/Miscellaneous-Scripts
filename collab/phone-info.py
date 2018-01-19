#created by lfane
#1/17/18; looks for arguments
import sys
import requests
from bs4 import BeautifulSoup

#Check that arguments where passed
if len(sys.argv) ==3:
    #Open text file containing phone IPs
    filePhoneReport = open(sys.argv[2],"w")

    #Open the text file containing the phoneIPs and put the IPs into a list
    with open(sys.argv[1]) as temp_file:
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
else:
    print("ERROR: Not enough arguments.  Please pass an input and output file")
    print("Example: python phone-info.py phoneinfo.txt myreport.csv")
    print("If the text file containing the list of IPs is not in this same directory, include the path")
    print("Exiting Now.")