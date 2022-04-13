####
#
# Author: Ryan Gillespie
# Description: Digicert -> Neustar Domain Validator
# Date: 4/2022
# 
#
####
import sys
import httpx
from rich.pretty import pprint
from datetime import datetime, timedelta

class DomainGetter():
    def __init__(self,KEY):
        self.key = KEY
        self.headers = {"X-DC-DEVKEY": KEY}
        self.session = {}


    def getExpiryDomainCount(self) -> int:
        url = "https://www.digicert.com/services/v2/domain/expiration-count"
        sess = httpx.Client()
        response = sess.get(url=url,headers=self.headers)

        check_response(response)
        self.session[self.key] = sess
        edc = response.json()["number_of_expiry_soon_domains"]
        return int(edc)
        
    def getExpiryDomains(self):
        url = "https://www.digicert.com/services/v2/domain?limit=1000"
        sess = httpx.Client()
        response = sess.get(url=url,headers=self.headers)

        check_response(response)
        self.session[self.key] = sess
        domains = response.json()["domains"]

        exp_date = datetime.now() + timedelta(180) #expires 180 days from now
        
        for domain in domains:            
            dcv_expiration = domain.get("dcv_expiration") # Some domains don't have this

            if dcv_expiration:
                ev_exp_str = domain["dcv_expiration"]["ev"]
                ov_exp_str = domain["dcv_expiration"]["ov"]
            else:
                print(f"Domain {domain['name']} id: {domain['id']} \t\t{'has no dcv_expiration field...':<50}")
                continue
        
            ev_exp = datetime.strptime(ev_exp_str,"%Y-%m-%d")
            ov_exp = datetime.strptime(ov_exp_str,"%Y-%m-%d")
            min_exp = ev_exp if ev_exp < ov_exp else ov_exp # Get lowest date
            if min_exp < exp_date:
                num_days = (min_exp - datetime.now()).days
                print(f"{domain['name']} id: {domain['id']} expires in {num_days} days")
                print(f"exp_date = {dcv_expiration}")

        return domains


def check_response(response):
    if response.status_code != 200:
        print(f"Error: {response}")
        if DEBUG:
            print(response)
            print(url)
            print(self.headers)
        sys.exit(0)


def main():
    KEY = input("Please enter the DigiCert API Key: ")
    dg = DomainGetter(KEY)
    pprint(dg.getExpiryDomainCount())

    domains = dg.getExpiryDomains()
    # for domain in domains:
    #     print(f"id: {domain['id']}\tname: {domain['name']}\tdcv_method: {domain['dcv_method']}")


if __name__ == "__main__":
    main()