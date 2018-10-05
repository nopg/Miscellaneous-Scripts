import sys, os
import json
import getpass

import rest_api_lib_viptela as vip

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


def main_export_all_templates(obj, root_folder):

    os.makedirs(root_folder + "/device", exist_ok=True)
    os.makedirs(root_folder + "/feature", exist_ok=True)

    ## OUTPUT ALL FEATURE TEMPLATES
    response = obj.get_request("template/feature")
    json_response = json.loads(response)

    feature_data = json_response["data"]
    create_files(feature_data, "feature")

    ## GET ALL DEVICE TEMPLATES
    response = obj.get_request("template/device")
    json_response = json.loads(response)

    device_data = json_response["data"]
    create_files(device_data, "device")


def main_export_device_template(obj, root_folder, template_name):

    os.makedirs(root_folder + "/device", exist_ok=True)
    os.makedirs(root_folder + "/feature", exist_ok=True)

    ## GET ALL DEVICE TEMPLATES
    response = obj.get_request("template/device")
    json_response = json.loads(response)
    device_data = json_response["data"]

    found = False
    for each in device_data:
        if each["templateName"] == template_name:
            found = True
            grab_device_template(each["templateId"])

    if not found:
        print("\nDevice Template was not found!\n")
        sys.exit(0)


def main_import_all_templates(obj, root_folder):

    # GRAB DEVICE TEMPLATES, creates list containing output of each file #
    feature_templates = grab_files_read(root_folder + "/feature/")

    for template in feature_templates:
        data = json.loads(template)

        response = obj.post_request("template/feature", data)
        new_id = json.loads(response)["templateId"]
        print("Imported feature template: {}".format(data["templateName"]))

    device_templates = grab_files_read(root_folder + "/device/")
    for template in device_templates:
        data = json.loads(template)
        data["policyId"] = ""  #   ATTACHED TO ROUTING POLICY?
        data["factoryDefault"] = ""  #   NEVER A DEFAULT
        if data["configType"] == "template":  #   NOT A CLI BASED TEMPLATE
            # UPDATE OLD FEATURE TEMPLATE ID'S #
            for feature_template in data["generalTemplates"]:
                if "subTemplates" in feature_template:
                    for sub_template in feature_template["subTemplates"]:
                        old_feat_id = sub_template["templateId"]
                        # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                        new_id = find_feature_template(old_feat_id, feature_templates)
                        sub_template["templateId"] = new_id

                old_feat_id = feature_template["templateId"]
                # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                new_id = find_feature_template(old_feat_id, feature_templates)
                feature_template["templateId"] = new_id

        # CREATE DEVICE TEMPLATE
        response = obj.post_request("template/device/feature", data)
        print("Imported device template: {}\n".format(data["templateName"]))


def main_import_device_template(obj, root_folder,entry):

    # GRAB TEMPLATES, creates list containing output of each file #
    device_templates = grab_files_read(root_folder + "/device/")
    feature_templates = grab_files_read(root_folder + "/feature/")

    for template in device_templates:
        data = json.loads(template)
        if data["templateName"] == entry:
            blah = data["templateName"]
            print(f"data{blah}, entry={entry}")
            data["policyId"] = ""  #   ATTACHED TO ROUTING POLICY?
            data["factoryDefault"] = ""  #   NEVER A DEFAULT
            if data["configType"] == "template":  #   NOT A CLI BASED TEMPLATE
                # UPDATE OLD FEATURE TEMPLATE ID'S #
                for feature_template in data["generalTemplates"]:
                    if "subTemplates" in feature_template:
                        for sub_template in feature_template["subTemplates"]:
                            old_feat_id = sub_template["templateId"]
                            # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                            new_id = find_feature_template(old_feat_id, feature_templates)
                            sub_template["templateId"] = new_id

                    old_feat_id = feature_template["templateId"]
                    # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                    new_id = find_feature_template(old_feat_id, feature_templates)
                    feature_template["templateId"] = new_id

            # CREATE DEVICE TEMPLATE
            response = obj.post_request("template/device/feature", data)
            print("Imported device template: {}\n".format(data["templateName"]))

# Main Program
def main(selection, root_folder, entry, obj):
    if selection == "1":
        if entry:
            main_export_device_template(obj, root_folder, entry)
        else:
            main_export_all_templates(obj, root_folder)
    else:
        if entry:
            main_import_device_template(obj, root_folder, entry)
        else:
            main_import_all_templates(obj, root_folder)


# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 vip-templates.py <root template folder> <destination vmanage> <username>\n\n"
        )
        sys.exit(0)

    # Gather input
    root_folder = sys.argv[1]
    dest_vmanage_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    # Create connection with vManage as 'obj'
    obj = vip.rest_api_lib_viptela(dest_vmanage_ip, username, password)

    # MENU
    export_or_import = ""
    while(export_or_import != "1" and 
          export_or_import != "2"):

            export_or_import = input(
            """\n
            What would you like to do?

            1) EXPORT a device template (From vManage into json)
            2) IMPORT a device template (From json into vManage)

            Enter 1 or 2: """
            )
    
    entry = input(
        """\n
        (Enter Blank line for ALL device and feature templates)
        Enter a specific device template name: """
    )

    # Run program
    main(export_or_import, root_folder, entry, obj)

    # Done!
    print("\nComplete!\n")