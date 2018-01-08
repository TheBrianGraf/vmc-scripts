"""

Basic Tests against the Skyscraper API
VMC API documentation available at https://vmc.vmware.com/swagger/index.html#/
CSP API documentation is available at https://console.cloud.vmware.com/csp/gateway/api-docs
vCenter API documentation is available at https://code.vmware.com/apis/191/vsphere-automation

Matt Dreyer
August 11, 2017

You can install python 3.6 from https://www.python.org/downloads/windows/

You can install the dependent python packages locally (handy for Lambda) with:
pip install requests -t . --upgrade
pip install simplejson -t . --upgrade
pip install certifi -t . --upgrade
pip install prettytable -t . --upgrade
pip install colorama -t . --upgrade


"""
import os  # need this for file path to read access tokens
import requests  # need this for Get/Post/Delete
import certifi  # need this for HTTPS
import simplejson as json  # need this for JSON
import prettytable  # need this for pretty output
import sys  # need this for command line arguments
import uuid  # need this to automatically name newly created VMs
from colorama import init  # need this for stupid color tricks
init()  # turn on stupid color tricks


# To use this script you need to create an OAuth Refresh token for your Org
# You can generate an OAuth Refresh Token using the tool at vmc.vmware.com
# https://console.cloud.vmware.com/csp/gateway/portal/#/user/tokens
#
# !!!IMPORTANT!!! The Oauth Refresh Token is unique to each Org, please be sure
#                 these are aligned or you will get authentication errors
#
strAccessKey = open(os.path.expanduser("~\.vmc\\access-token.txt")).read().strip()

# If you are in more than one org, then you should configure that here
tenantid = open(os.path.expanduser("~\.vmc\\default-org.txt")).read().strip()


#------------------------------------------------
#----- Shouldn't need to touch anything below here
#------------------------------------------------

# where are our service end points
strProdURL = "https://vmc.vmware.com"
strCSPProdURL = "https://console.cloud.vmware.com"


# Stupid color tricks
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def disable(self):
    self.HEADER = ''
    self.OKBLUE = ''
    self.OKGREEN = ''
    self.WARNING = ''
    self.FAIL = ''
    self.ENDC = ''


#-------------------- Login to the service
def getAccessToken(myKey):
    params = {'refresh_token': myKey}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(
        strCSPProdURL +
        '/csp/gateway/am/api/auth/api-tokens/authorize',
        params=params,
        headers=headers)
    json_response = response.json()
    access_token = json_response['access_token']

    # debug only
#    print(response.status_code)
#    print(response.json())

    return access_token


#-------------------- Figure out which Org we are in
def getTenantID(sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}

    response = requests.get(strProdURL + '/vmc/api/orgs', headers=myHeader)

# debug only
#    print(response.status_code)
#    print(response.json())

# parse the response to grab our tenant id
    jsonResponse = response.json()
    strTenant = str(jsonResponse[0]['id'])

    return(strTenant)

#-------------------- List our SDDCs


def getCDCs(tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs"

    response = requests.get(myURL, headers=myHeader)

# grab the names of the CDCs
    jsonResponse = response.json()

# debug only
#    print(response.status_code)
#    print(response.json())

    if response.status_code == 200:
        from prettytable import PrettyTable

        orgtable = PrettyTable(['OrgID'])
        orgtable.add_row([tenantid])

        print(bcolors.OKGREEN + str(orgtable) + bcolors.ENDC)

        table = PrettyTable(['Name', 'Cloud', 'Status', 'Hosts', 'ID'])

        for i in jsonResponse:
            hostcount = 0
            myURL = strProdURL + "/vmc/api/orgs/" + \
                tenantid + "/sddcs/" + i['id']
            response = requests.get(myURL, headers=myHeader)
            mySDDCs = response.json()
            if mySDDCs['resource_config']:
                hosts = mySDDCs['resource_config']['esx_hosts']
                if hosts:
                    for j in hosts:
                        hostcount = hostcount + 1
            table.add_row([i['name'], i['provider'],
                           i['sddc_state'], hostcount, i['id']])

        print(bcolors.OKGREEN + str(table) + bcolors.ENDC)
    else:
        print(response.status_code)
        print(response.json())

    return

#-------------------- List CGWs


def showVPN(gateway, vpnID, gatewayID, sddcId, tenantid, sessiontoken):
    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + \
        sddcId + "/" + gateway + "/" + gatewayID + "/vpns/" + vpnID
    response = requests.get(myURL, headers=myHeader)

    # grab the response
    jsonResponse = response.json()
# debug only
    print(response.status_code)
    print(response.json())

    return


#-------------------- List CGWs
def showCDCCGWs(sddcId, tenantid, sessiontoken):
    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddcId + "/cgws"
    response = requests.get(myURL, headers=myHeader)

    # grab the IDs of the CDCs
    jsonResponse = response.json()
# debug only
#    print(response.status_code)
#    print(response.json())

    from prettytable import PrettyTable
    table = PrettyTable(['CGW Property', 'ID'])

# Now spin through the CGW's and dump out  details
    for i in jsonResponse:

        # make the firewall rule table pretty
        firewalltable = PrettyTable(
            ['ID', 'Name', 'Source', 'Destination', 'Service', 'Action'])
        firewall = i['firewall_rules']
        for j in firewall:
            if str(j['services']) == "None":
                ports = "None"
            else:
                ports = "Some"
                ports = str(j['services'][0]['protocol']) + \
                    ":" + str(j['services'][0]['ports'][0])
            firewalltable.add_row(
                [j['id'], j['name'], j['source'], j['destination'], ports, j['action']])

        # make the NAT rule table pretty
        nattable = PrettyTable(
            ['ID', 'Name', 'Original', 'Translated', 'Action'])
        nat = i['nat_rules']
        for j in nat:
            nattable.add_row([j['id'],
                              j['name'],
                              j['public_ip'] + ":" + j['public_ports'],
                              j['internal_ip'] + ":" + j['internal_ports'],
                              j['action']])

        # make the Logical Networks table pretty
        networktable = PrettyTable(['ID', 'Name', 'Subnet', 'DHCP'])
        networks = i['logical_networks']
        for j in networks:
            networktable.add_row(
                [j['id'], j['name'], j['subnet_cidr'], j['dhcp_enabled']])

        # make the VPN table pretty
        vpntable = PrettyTable(
            ['ID', 'Name', 'Status', 'On-Prem Gateway', 'On-prem Network', 'CDC Network'])
        vpns = i['vpns']
        for j in vpns:
            vpntable.add_row([j['id'],
                              j['name'],
                              j['state'],
                              j['on_prem_gateway_ip'],
                              j['on_prem_network_cidr'],
                              j['internal_network_ids']])
            if j['state'] != "CONNECTED":
                vpnError = j['tunnel_statuses']
            else:
                vpnError = ""

        # print everything
        table.add_row(["ID", i['id']])
        table.add_row(["Public IP", i['eip']])
        table.add_row(["primary DNS", i['primary_dns']])
        table.add_row(["secondary DNS", i['secondary_dns']])

    # Print
    print(bcolors.WARNING + str(table) + bcolors.ENDC)
    print(bcolors.WARNING + "NAT Rules" + bcolors.ENDC)
    print(bcolors.WARNING + str(nattable) + bcolors.ENDC)
    print(bcolors.WARNING + "Firewall Rules" + bcolors.ENDC)
    print(bcolors.WARNING + str(firewalltable) + bcolors.ENDC)
    print(bcolors.WARNING + "Logical Networks" + bcolors.ENDC)
    print(bcolors.WARNING + str(networktable) + bcolors.ENDC)
    print(bcolors.WARNING + "VPNs" + bcolors.ENDC)
    print(bcolors.WARNING + str(vpntable) + bcolors.ENDC)
    print(
        bcolors.WARNING +
        "VPN Errors:" +
        str(vpnError) +
        bcolors.ENDC +
        "\n")
    # go get the public ip's too
    showPublicIPs(sddcId, tenantid, sessiontoken)
    return

#-------------------- List Public IPs


def showPublicIPs(sddcId, tenantid, sessiontoken):
    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + \
        tenantid + "/sddcs/" + sddcId + "/publicips"
    response = requests.get(myURL, headers=myHeader)

    # grab the response
    jsonResponse = response.json()
# debug only
#    print(response.status_code)
#    print(response.json())

    from prettytable import PrettyTable
    table = PrettyTable(['Public IP', 'Note'])

# Now spin through the CGW's and dump out  details
    for i in jsonResponse:
        table.add_row([i['public_ip'], i['name']])

    # Print
    print(bcolors.WARNING + "Public IPs" + bcolors.ENDC)
    print(bcolors.WARNING + str(table) + bcolors.ENDC)

    return


#-------------------- List MGWs
def showCDCMGWs(sddcId, tenantid, sessiontoken):
    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddcId + "/mgws"
    response = requests.get(myURL, headers=myHeader)

    # grab the IDs of the CDCs
    jsonResponse = response.json()
# debug only
#    print(response.status_code)
#    print(response.json())

    from prettytable import PrettyTable
    table = PrettyTable(['MGW Property', 'ID'])

# Now spin through the CGW's and dump out  details
    for i in jsonResponse:

        # make the firewall rule table pretty
        firewalltable = PrettyTable(
            ['ID', 'Name', 'Source', 'Destination', 'Service', 'Action'])
        firewall = i['firewall_rules']
        for j in firewall:
            if str(j['services']) == "None":
                ports = "None"
            else:
                ports = "Some"
                ports = str(j['services'][0]['protocol']) + \
                    ":" + str(j['services'][0]['ports'])
            firewalltable.add_row(
                [j['id'], j['name'], j['source'], j['destination'], ports, j['action']])

        # make the VPN table pretty
        vpntable = PrettyTable(
            ['ID', 'Name', 'Status', 'On-Prem Gateway', 'On-prem Network', 'CDC Network'])
        vpns = i['vpns']
        for j in vpns:
            vpntable.add_row([j['id'],
                              j['name'],
                              j['state'],
                              j['on_prem_gateway_ip'],
                              j['on_prem_network_cidr'],
                              j['internal_network_ids']])
            if j['state'] != "CONNECTED":
                vpnError = j['tunnel_statuses']
            else:
                vpnError = ""

        # print everything
        table.add_row(["ID", i['id']])
        table.add_row(["Public IP", i['eip']])
        table.add_row(["primary DNS", i['primary_dns']])
        table.add_row(["secondary DNS", i['secondary_dns']])
        #table.add_row(["Firewall Rules", firewalltable])
        #table.add_row(["NAT Rules", i['nat_rules']])
        #table.add_row(["VPNs", i['vpns']])

    # Print
    print(bcolors.WARNING + str(table) + bcolors.ENDC)
    print(bcolors.WARNING + "Firewall Rules" + bcolors.ENDC)
    print(bcolors.WARNING + str(firewalltable) + bcolors.ENDC)
    print(bcolors.WARNING + "VPNs" + bcolors.ENDC)
    print(bcolors.WARNING + str(vpntable) + bcolors.ENDC)
    print(
        bcolors.WARNING +
        "VPN Errors:" +
        str(vpnError) +
        bcolors.ENDC +
        "\n")

    return

#-------------------- Add hosts to an SDDC


def addCDChosts(sddc, hosts, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddc + "/esxs"
    strRequest = {"num_hosts": hosts}

    response = requests.post(myURL, json=strRequest, headers=myHeader)

# debug only
    print("result =" + str(response.status_code))
#    print(response.json())

# grab the ID of the new one we just created
    jsonResponse = response.json()
    strSDDC = jsonResponse['id']

    return(strSDDC)

#-------------------- Remove a host from an SDDC


def removeCDChost(sddcId, hostID, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + \
        "/sddcs/" + sddcId + "/esxs/" + hostID

    response = requests.delete(myURL, headers=myHeader)

# debug only
    print("result =" + str(response.status_code))

    return

#-------------------- Show hosts in an SDDC


def showCDChosts(sddcID, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddcID

    response = requests.get(myURL, headers=myHeader)

# grab the names of the CDCs
    jsonResponse = response.json()

# get the vC block (this is a bad hack to get the rest of the host name
# shown in vC inventory)
    cdcID = jsonResponse['resource_config']['vc_ip']
    cdcID = cdcID.split("vcenter")
    cdcID = cdcID[1]
    cdcID = cdcID.split("/")
    cdcID = cdcID[0]

# get the hosts block
    hosts = jsonResponse['resource_config']['esx_hosts']


# debug only
#    print(response.status_code)
#    print(response.json())

    from prettytable import PrettyTable
    table = PrettyTable(['Name', 'Status', 'ID'])

    for i in hosts:
        hostName = i['name'] + cdcID
        table.add_row([hostName, i['esx_state'], i['esx_id']])

    print(bcolors.OKGREEN + str(table) + bcolors.ENDC)

    return

#-------------------- Create a new SDDC


def makeCDC(name, provider, region, hosts, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs"
    strRequest = {
        "num_hosts": hosts,
        "name": name,
        "provider": provider,
        "region": region}

    response = requests.post(myURL, json=strRequest, headers=myHeader)

# debug only
    #print("result =" + str(response.status_code))

    jsonResponse = response.json()

    if str(response.status_code) != "202":
        print("\nERROR: " + str(jsonResponse['error_messages'][0]))

    return

#-------------------- Delete an SDDC


def deleteCDC(sddcId, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddcId

    response = requests.delete(myURL, headers=myHeader)
    jsonResponse = response.json()

# debug only
    print("result =" + str(response.status_code))

    if str(response.status_code) != "202":
        print("\nERROR: " + str(jsonResponse['error_messages'][0]))

    return

    #-------------------- Display the users in our org


def showORGusers(tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strCSPProdURL + "/csp/gateway/am/api/orgs/" + tenantid + "/users?expand=1"

    response = requests.get(myURL, headers=myHeader)
    jsonResponse = response.json()

# debug only
#    print("result =" + str(response.status_code))
#    print(jsonResponse)

    if str(response.status_code) != "200":
        print("\nERROR: " + str(jsonResponse))
    else:
        # get the users block
        users = jsonResponse['users']

        from prettytable import PrettyTable
        table = PrettyTable(['First Name', 'Last Name', 'User Name', 'Role'])

        for i in users:
            table.add_row([i['firstName'],
                           i['lastName'],
                           i['username'],
                           i['organizationRoles'][0]['displayName']])

        print(bcolors.OKGREEN + str(table) + bcolors.ENDC)

    return

#-------------------- Add a user to our Org


def addORGuser(userID, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strCSPProdURL + "/csp/gateway/am/api/orgs/" + tenantid + "/invitations"
    strRequest = {
        "usernames": [userID],
        "orgRole": "org_member",
        "invitationLink": "https://vmc.vmware.com/"}

    response = requests.post(myURL, json=strRequest, headers=myHeader)

# debug only
#    print("result =" + str(response.status_code))

    jsonResponse = response.json()

    if str(response.status_code) == "202":
        print("\nSuccess!  Have your user check their email (and their spam folder).")
    else:
        print("\nERROR: " + str(jsonResponse))

    return

#-------------------- Remove a user from our Org


def removeORGuser(userID, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strCSPProdURL + "/csp/gateway/am/api/users" + userID

    response = requests.delete(myURL, headers=myHeader)

# debug only
    print("result =" + str(response.status_code))

    if str(response.status_code) != "200":
        print("\nERROR: " + str(jsonResponse))

    return

#-------------------- Add a user to our Org


def getUserOrgs(sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs"

    response = requests.get(myURL, headers=myHeader)

# debug only
#    print("result =" + str(response.status_code))

    jsonResponse = response.json()

    if str(response.status_code) == "200":
        # get the users block
        myorgs = jsonResponse

        from prettytable import PrettyTable
        table = PrettyTable(['Name', 'Org ID', 'Short Org ID'])

        for i in myorgs:
            table.add_row([i['display_name'], i['id'], i['name']])

        print(bcolors.OKGREEN + str(table) + bcolors.ENDC)

    else:
        print("\nERROR: " + str(jsonResponse))

    return

    #-------------------- Display the tasks running in an Org (for an SDDC)


def showTasks(sddcID, tenantid, sessiontoken):

    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/tasks"

    response = requests.get(myURL, headers=myHeader)
    jsonResponse = response.json()

# debug only
#   print("result =" + str(response.status_code))
#    print(jsonResponse)

    if str(response.status_code) != "200":
        print("\nERROR: " + str(jsonResponse))
    else:
        # get the tasks back, they are returned as an array
        tasks = jsonResponse

        from prettytable import PrettyTable
        table = PrettyTable(['Task', 'Status', 'ID', 'Timestamp', 'User'])

        # dump the details for each task
        count = 0
        for i in tasks:
            for j in i['resource_id']:
                table.add_row([i['task_type'], i['sub_status'],
                               i['id'], i['start_time'], i['user_name']])
                count = count + 1
        print(bcolors.OKGREEN + str(table) + bcolors.ENDC)
        print("\n" + str(count) + " events displayed")
    return


#---------------Login to vCenter and get an API token
# this will only work if the MGW firewall rules are configured appropriately
def vCenterLogin(sddcID, sessiontoken):

    # Get the vCenter details from VMC
    myHeader = {'csp-auth-token': sessiontoken}
    myURL = strProdURL + "/vmc/api/orgs/" + tenantid + "/sddcs/" + sddcID
    response = requests.get(myURL, headers=myHeader)
    jsonResponse = response.json()

    vCenterURL = jsonResponse['resource_config']['vc_ip']
    vCenterUsername = jsonResponse['resource_config']['cloud_username']
    vCenterPassword = jsonResponse['resource_config']['cloud_password']

    # Now get an API token from vcenter
    myURL = vCenterURL + "rest/com/vmware/cis/session"
    response = requests.post(myURL, auth=(vCenterUsername, vCenterPassword))
    token = response.json()['value']
    vCenterAuthHeader = {'vmware-api-session-id': token}

    return(vCenterURL, vCenterAuthHeader)


def showVMs(sddcID, tenantid, sessiontoken):

    # first we need to get an authentaction token from vCenter
    vCenterURL, vCenterAuthHeader = vCenterLogin(sddcID, sessiontoken)

    # now get the VMs
    # for all vms use this : myURL = vCenterURL + "rest/vcenter/vm"
    # for management vms use this: myURL = vCenterURL + "rest/vcenter/vm?filter.resource_pools=resgroup-54"
    # for workload vms use this: myURL = vCenterURL +
    # "rest/vcenter/vm?filter.resource_pools=resgroup-55"
    myURL = vCenterURL + "rest/vcenter/vm"
    response = requests.get(myURL, headers=vCenterAuthHeader)

    # deal with silly vAPI wrapping
    vms = response.json()['value']

    from prettytable import PrettyTable
    table = PrettyTable(['Name', 'State', 'CPUs', 'Memory'])

    for i in vms:
        table.add_row([i['name'], i['power_state'],
                       i['cpu_count'], i['memory_size_MiB']])

    print(bcolors.OKGREEN + str(table) + bcolors.ENDC)

    return

 #------------ Create a VM from an OVF stored in Content Library


def createVM(sddcID, tenantid, sessiontoken, vmID):

    # first we need to get an authentaction token from vCenter
    vCenterURL, vCenterAuthHeader = vCenterLogin(sddcID, sessiontoken)

    # Lets give our cow a name
    vmname = "VM-" + str(uuid.uuid4())

    # now lets create a VM from an OVF template stored in the Content Library
    # first we need to create a deployment spec
    deploymentspec = {
        "target": {
            "resource_pool_id": "resgroup-55",
            "host_id": "host-31",
            "folder_id": "group-v52"
        },
        "deployment_spec": {
            "name": vmname,
            "accept_all_EULA": "true",
            "storage_mappings": [
                {
                    "key": "dont-delete-this-key",
                    "value": {
                        "type": "DATASTORE",
                        "datastore_id": "datastore-61",
                        "provisioning": "thin"
                    }
                }
            ],
            "storage_provisioning": "thin",
            "storage_profile_id": "aa6d5a82-1c88-45da-85d3-3d74b91a5bad",
        }
    }

    print("\nPlease wait, VM deployment is in process....")

    myURL = vCenterURL + "rest/com/vmware/vcenter/ovf/library-item/id:" + \
        vmID + "?~action=deploy"
    response = requests.post(
        myURL,
        headers=vCenterAuthHeader,
        json=deploymentspec)
    # print(response.status_code)
    # print(response.text)

    if response.status_code == 200:
        print("Succesfully created a VM named: " + vmname)
    else:
        print("Failed to create a VM \n" + response.text)
    return

    #------------ Create a VM from an OVF stored in Content Library


def showContentLibraries(sddcID, tenantid, sessiontoken):

    # first we need to get an authentaction token from vCenter
    vCenterURL, vCenterAuthHeader = vCenterLogin(sddcID, sessiontoken)

    # now find all of the content libraries
    myURL = vCenterURL + "rest/com/vmware/content/library"
    response = requests.get(myURL, headers=vCenterAuthHeader)
    libraries = response.json()['value']

    # now loop through the libraries and dump out the contents
    for i in libraries:
        myURL = vCenterURL + "rest/com/vmware/content/local-library/id:" + i
        response = requests.get(myURL, headers=vCenterAuthHeader)

        # subscribed libraries don't have names, bummer
        clDetails = response.json()['value']

        if 'name' in clDetails:
            clName = response.json()['value']['name']
            clID = i

            # First dump the name and ID of the Content Library
            from prettytable import PrettyTable
            bigtable = PrettyTable(['ID', 'Name'])
            bigtable.add_row([clName, clID])

            # now dump out the ids of the items in the library
            myURL = vCenterURL + "rest/com/vmware/content/library/item?library_id=" + clID
            response = requests.get(myURL, headers=vCenterAuthHeader)
            clItems = response.json()['value']

            # now dump out the names of the items in the content library
            from prettytable import PrettyTable
            table = PrettyTable(['ID', 'Name', 'Type', 'Size'])

            for j in clItems:
                myURL = vCenterURL + "rest/com/vmware/content/library/item/id:" + j
                response = requests.get(myURL, headers=vCenterAuthHeader)
                clItemName = response.json()['value']['name']
                clItemID = response.json()['value']['id']
                clItemSize = response.json()['value']['size']
                clItemType = response.json()['value']['type']

                table.add_row([clItemID, clItemName, clItemType, clItemSize])

            bigtable.add_row(["", table])
            print(bcolors.OKGREEN + str(bigtable) + bcolors.ENDC)

    return


#--------------------------------------------
#---------------- Main ----------------------
#--------------------------------------------


# Get our access token
sessiontoken = getAccessToken(strAccessKey)
#print("accesskey=  " + sessiontoken)


# get our tenant ID, only useful if you are a member of a single org
#tenantid = getTenantID(sessiontoken)
#print("tenant ID = " + tenantid)


# what does our user want us to do
if len(sys.argv) > 1:
    intent_name = sys.argv[1]
else:
    intent_name = ""

#------------------------
#--- execute the user's command
if intent_name == "show-sddcs":
    myCDCs = getCDCs(tenantid, sessiontoken)
elif intent_name == "create":
    sddcName = sys.argv[2]
    targetCloud = sys.argv[3]
    targetRegion = sys.argv[4]
    numHosts = sys.argv[5]
    makeCDC(
        sddcName,
        targetCloud,
        targetRegion,
        numHosts,
        tenantid,
        sessiontoken)
elif intent_name == "destroy":
    sddcId = sys.argv[2]
    deleteCDC(sddcId, tenantid, sessiontoken)
elif intent_name == "show-cgws":
    sddcId = sys.argv[2]
    showCDCCGWs(sddcId, tenantid, sessiontoken)
elif intent_name == "show-mgws":
    sddcId = sys.argv[2]
    showCDCMGWs(sddcId, tenantid, sessiontoken)
elif intent_name == "show-ips":
    sddcID = sys.argv[2]
    showPublicIPs(sddcID, tenantid, sessiontoken)
elif intent_name == "add-host":
    sddcID = sys.argv[2]
    numHosts = sys.argv[3]
    addCDChosts(sddcID, numHosts, tenantid, sessiontoken)
elif intent_name == "remove-host":
    sddcID = sys.argv[2]
    hostID = sys.argv[3]
    removeCDChost(sddcID, hostID, tenantid, sessiontoken)
elif intent_name == "show-hosts":
    sddcID = sys.argv[2]
    showCDChosts(sddcID, tenantid, sessiontoken)
elif intent_name == "show-users":
    showORGusers(tenantid, sessiontoken)
elif intent_name == "invite-user":
    userID = sys.argv[2]
    addORGuser(userID, tenantid, sessiontoken)
elif intent_name == "remove-user":
    userID = sys.argv[2]
    removeORGuser(userID, tenantid, sessiontoken)
elif intent_name == "show-orgs":
    getUserOrgs(sessiontoken)
elif intent_name == "show-tasks":
    sddcID = sys.argv[2]
    showTasks(sddcID, tenantid, sessiontoken)
elif intent_name == "show-vpn":
    gateway = sys.argv[2]
    sddcID = sys.argv[3]
    gatewayID = sys.argv[4]
    vpnID = sys.argv[5]
    showVPN(gateway, vpnID, gatewayID, sddcID, tenantid, sessiontoken)
elif intent_name == "show-vms":
    sddcID = sys.argv[2]
    showVMs(sddcID, tenantid, sessiontoken)
elif intent_name == "create-vm":
    sddcID = sys.argv[2]
    vmType = sys.argv[3]
    createVM(sddcID, tenantid, sessiontoken, vmType)
elif intent_name == "show-libraries":
    sddcID = sys.argv[2]
    showContentLibraries(sddcID, tenantid, sessiontoken)
else:
    print("\nPlease give me something to do like:")
    print("    show-sddcs")
    print("    create [name-of-SDDC] [ZEROCLOUD|AWS] [US_WEST_2] [Host Count]")
    print("    destroy [id-of-SDDC]")
    print("    show-vms [id-of-SDDC]")
    print("    show-libraries [id-of-SDDC]")
    print(
        "    create-vm [id-of-SDDC] [id-of-ovf-to-deploy (hint: show-libraries)]")
    print("    show-cgws [id-of-SDDC]")
    print("    show-mgws [id-of-SDDC]")
    print("    show-ips [id-of-SDDC]")
    print("    add-host [id-of-SDDC] [number of hosts to add]")
    print("    remove-host [id-of-SDDC] [ID of ESXi Host to remove]")
    print("    show-hosts [id-of-SDDC]")
    print("    show-users")
    print("    invite-user [user@company.com]")
    print("    remove-user [user@company.com]")
    print("    show-orgs")
    print("    show-tasks [id-of-SDDC]")
    print("    show-vpn [cgws|mgws] [id-of-SDDC] [id-of-gateway] [id-of-VPN]")
