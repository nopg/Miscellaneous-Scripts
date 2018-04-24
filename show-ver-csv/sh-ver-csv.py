import os
import sys
import re
import jtextfsm
import csv

DEBUG = False
DEBMAXLINES = 1

def format_fsm_cdp_output(re_table, fsm_results):
    #   FORMAT NEIGHBORS OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES (neighbor, port, ip address, etc) #
    cdpneighbors = []
    for neighbor in fsm_results:
        tempdevice = {}
        for position, header in enumerate(re_table.header):
            tempdevice[header] = neighbor[position]
        cdpneighbors.append(tempdevice)

    return cdpneighbors

def build_csv(output, filename):
    """
    BUILD CSV BASED ON AN EXISTING DICTIONARY

    :param output: existing dictionary to be written
    :param filename: filename to create csv
    :return:
    """
    print("Building CSV...")
    headers = list(output[0].keys())
    fout = open(filename, 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()

def version_csv(type, path):

    global DEBUG
    global DEBMAXLINES
    count = 1
    output = []

    if type == 'ios':
        re_table_template = "cisco_ios_show_version.textfsm"
    elif type == 'nx-os':
        re_table_template = "cisco_nxos_show_version.textfsm"

    for filename in os.listdir(path):
        if DEBUG:
            if count > DEBMAXLINES:
                break
            else:
                count += 1

        fin = open(path + '/' + filename, 'r')

        version_output = fin.read()

        ## parse the show version command using TextFSM
        re_table = jtextfsm.TextFSM(open(re_table_template))
        fsm_results = re_table.ParseText(version_output)

        fin.close()

        tempoutput = format_fsm_cdp_output(re_table, fsm_results)
        output.append(tempoutput[0])

    return output

def main():

    iosoutput = version_csv('ios', './version2/ios')

    nxosoutput = version_csv('nx-os', './version2/nxos')

    build_csv(iosoutput, 'ios-version-output.csv')
    build_csv(nxosoutput, 'nxos-version-output.csv')

    iosoutput.extend(nxosoutput)

    build_csv(iosoutput, 'combined-version-output.csv')

if __name__ == "__main__":
    main()
    print("Done.")