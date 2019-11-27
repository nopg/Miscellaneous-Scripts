def login(self):
        
        base_url = 'https://%s:%s/'%(self.vmanage_host,self.vmanage_port)
        login_action = '/j_security_check'

        #Format data for loginForm

        login_data = {'j_username' : username, 'j_password' : password}

        #URL for posting login data

        login_url = base_url + login_action

        #URL for retrieving client token
        token_url = base_url + 'dataservice/client/token'

        sess = requests.session()
        
        #If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False)
        if b'<html>' in login_response.content:
            print ("Login Failed")
            exit(0)
            
        #update token to session headers
        
        login_token = sess.get(url=token_url, verify=False)

        if login_token.status_code == 200:
            if b'<html>' in login_token.content:
                print ("Login Token Failed")
                exit(0)
            
            sess.headers['X-XSRF-TOKEN'] = login_token.content
            self.session[vmanage_host] = sess