
    # def get_request_pa_cli(self, mount_point, commands):
    #     """GET request"""

    #     command_list = commands.split()
        
    #     params = []
    #     for command in command_list:
    #         params.append("<" + command + ">")
    #     for command in command_list[::-1]:
    #         params.append("</" + command + ">")
        
    #     command = ''.join(params)

    #     url = "https://{}:443/api{}{}&key={}".format(self.pa_ip, mount_point, command, self.key)
    #     print(url)
    #     response = self.session[self.pa_ip].get(url, verify=False)
    #     data = response.text
    #     return data

    # def get_request_pa_cli_and_param(self, mount_point, commands):
    #     """GET request"""

    #     command_list = commands.split()
    #     value = command_list.pop()
    #     params = []

    #     for command in command_list:
    #         params.append("<" + command + ">")
    #     params.append(value)

    #     for command in command_list[::-1]:
    #         params.append("</" + command + ">")
        
    #     command = ''.join(params)

    #     url = "https://{}:443/api{}{}&key={}".format(self.pa_ip, mount_point, command, self.key)
    #     print(url)
    #     response = self.session[self.pa_ip].get(url, verify=False)
    #     data = response.text
    #     return data

    # def post_request(
    #     self, mount_point, payload, headers={"Content-Type": "application/json"}
    # ):
    #     """POST request"""
    #     url = "https://{}:443/dataservice/{}".format(self.vmanage_ip, mount_point)
    #     payload = json.dumps(payload)
    #     response = self.session[self.vmanage_ip].post(
    #         url=url, data=payload, headers=headers, verify=False
    #     )
    #     print(response)
    #     data = response.text
    #     return data

# def write_etree_output(profile, type):

#     #GRAB FILENAME
#     if type == 'virus':
#         data = etree.tostring(profile[0][0]).decode()
#         with open ("Antivirus-profiles.xml", "w") as fout:
#             fout.write(data)




    # tree = etree.parse(io.StringIO(av))
    # root = tree.getroot()
    #print(tree.getroot().text)
    #print(tree[0])
    #print(root.tag)

    #d = xmltodict.parse(av)
    #print(d)


    # def pp_xml(text):
    #     b = xmltodict.parse(test)
    #     pp_json(b)

    #for elem in av_objects.iter():
    #    print(elem)
    # tree = etree.ElementTree(av_objects)
    # e = av_objects.findall(".//result/virus/entry")
    # for i in e:
    #     print(i)
    #     print(i.text)
    #     print(i.attrib)

