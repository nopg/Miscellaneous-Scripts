def grab_files_read(folder_name):
    """
    GRAB ALL FILES WITH ".vipt" EXTENSION WITHIN A FOLDER,
    RETURN LIST CONTAINING TEXT FOUND WITHIN FILES

    :param folder_name: base folder to recursively search
    :return: list containing the output of each folder
    """
    templates = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".vipt"):
                with open(root + file, "r") as fin:
                    data = fin.read()
                    templates.append(data)
    return templates

def create_files(data, template_type):
    """
    CREATE OUTPUT FILES BY FIRST RETRIEVING EACH OBJECT (FEATURE OR TEMPLATE)
    Based on 'template_type' will pull individal 'device' or 'feature' templates
    and output them to a file

    :param data: list of data to be written
    :param template_type: 'feature' or 'device'
    :return: None, print output
    """

    template_type = "/" + template_type + "/"
    if type(data) != list:
        data = [data]

    for each in data:
        response = obj.get_request(
            "template" + template_type + "object/" + each["templateId"]
        )
        template = json.loads(response)
        filename = template["templateName"].replace(os.path.sep, "_") + ".vipt"
        fout = open(root_folder + template_type + filename, "w")
        fout.write(json.dumps(template))
        fout.close()
        
        print("\tImported {} template: {}\n".format(template_type, template["templateName"]))

def find_feature_template(old_id, feature_templates):

    # SEARCH THROUGH TEMPLATES #
    for template in feature_templates:
        data = json.loads(template)
        if data["templateId"] == old_id:
            data["factoryDefault"] = False
            if "Factory_Default_" in data["templateName"]:
                data["templateName"] = "Imported_" + data["templateName"]
            # CREATE NEW TEMPLATE #
            response = obj.post_request("template/feature", data)
            print("\tImported feature template: {}".format(data["templateName"]))
            new_id = json.loads(response)["templateId"]
            return new_id

    # TEMPLATE NOT FOUND! #
    print("\nRequired feature template not found! ID: {}".format(old_id))
    print("Exiting...\n")
    sys.exit(0)

    
def grab_device_template(template_id):
    response = obj.get_request("template/device/object/" + template_id)
    device_template = json.loads(response)

    ## GET ALL FEATURE TEMPLATES
    response = obj.get_request("template/feature")
    json_response = json.loads(response)
    feature_data = json_response["data"]

    # GET FEATURE TEMPLATE ID'S #
    for feature_template in device_template["generalTemplates"]:
        if "subTemplates" in feature_template:
            for sub_template in feature_template["subTemplates"]:
                create_files(sub_template, "feature")

        create_files(feature_template, "feature")

    # CREATE DEVICE TEMPLATE
    create_files(device_template, "device")