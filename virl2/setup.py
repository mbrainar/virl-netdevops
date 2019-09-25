import os
from jinja2 import Environment, FileSystemLoader
from simple_client import ClientLibrary
import logging
from datetime import datetime
import json
import requests

# Variables
path = os.path.dirname(os.path.abspath(__file__))

# VIRL Variables
controller = "https://192.168.34.11"
controller_user = "admin"
controller_password = "Cisco123"

lab_name = "routed-access"
lab_definition_path = "{}.yaml".format(lab_name)


# NSO variables
nso_host = "localhost"
nso_port = "8080"
nso_url = "http://{}:{}".format(nso_host, nso_port)
nso_user = "admin"
nso_pass = "admin"


# Connect to controller & create client session
# Returns: ClientLibrary object
def connect_controller(controller, controller_user, controller_password):
    return ClientLibrary(controller, controller_user, controller_password, ssl_verify=False)


# Clean up VIRL labs
def clean_up():
    pass


# Gets lab list and select our desired lab
# Returns: Lab object
def get_my_lab(client, lab_name):
    labs = client.all_labs()
    for lab in labs:
        if lab.name == lab_name or lab.id == "ae4a07":
        # if lab.name == lab_name:
            return client.join_existing_lab(lab.id, sync_lab=True)


# Import lab from lab definition YAML file
# Returns Lab object
def import_lab(client, path):
    return client.import_lab_from_path(path)


# Extract external connector addresses
# Returns: list of dictionaries containing node, interface & address
def extract_addresses(lab):
    addresses = []
    nodes = lab.nodes()
    for node in nodes:
        interfaces = node.physical_interfaces()
        for interface in interfaces:
            if interface.discovered_ipv4:
                print("  Found address {} on {} interface {}".format(interface.discovered_ipv4, node.label, interface.label))
                addresses.append({
                    "node_id": node.id,
                    "node_label": node.label,
                    "interface": interface.label,
                    "address": interface.discovered_ipv4,
                    "node_definition": node.node_definition,
                    "ned": ned_mapping(node.node_definition)})
    return addresses


# Create a mapping of VIRL2 node definitions to NSO NEDs
# Returns: dictionary of NED details
def ned_mapping(node_definition):
    if "nx" in node_definition:
        return {'prefix': "cisco-nx-id",
                'ned': "cisco-nx",
                'ns': "http://tail-f.com/ned/cisco-nx-id"}
    elif 'xr' in node_definition:
        return {'prefix': "cisco-ios-xr-id",
                'ned': "cisco-ios-xr",
                'ns': "http://tail-f.com/ned/cisco-ios-xr-id"}
    elif 'csr' in node_definition or 'ios' in node_definition:
        return {'prefix': "cisco-ios-cli-3.8",
                'ned': "cisco-ios-cli-3.8",
                'ns': "http://tail-f.com/ns/ned-id/cisco-ios-cli-3.8"}


# Render NSO inventory template
# Returns: rendered template object
def render_template(template_filename, context):
    environment = Environment(
        autoescape=False,
        loader=FileSystemLoader(os.path.join(path, 'templates')),
        trim_blocks=False)
    return environment.get_template(template_filename).render(context)


# Create NSO inventory file
def create_nso_inventory(lab_name, addresses, output_filename):
    context = {'lab_name': lab_name,
               'nodes': addresses}
    with open(output_filename, 'w') as f:
        xml = render_template('template-load.xml', context)
        f.write(xml)


# Create NSO authgroup
# def create_nso_authgroup(lab_name, output_filename):
#     context = {'lab_name': lab_name}
#     with open(output_filename, 'w') as f:
#         xml = render_template('template-authgroup.xml', context)
#         f.write(xml)


# Start NSO
def start_nso():
    print(os.system("./nso-setup.sh -n"))


# Load XML into NSO
def load_nso(xml_file):
    print(os.system("./nso-setup.sh -l {}".format(xml_file)))


# Add devices to NSO
def add_nso_authgroup(xml_file):
    url = "{}/restconf/data/tailf-ncs:devices/authgroups".format(nso_url)
    with open(xml_file, 'r') as f:
        payload = f.read()
    # print(payload)
    headers = {
        'Accept': "application/yang-data+json",
        'Content-Type': "application/yang-data+xml"
        }
    response = requests.request("POST", url, data=payload, headers=headers, auth=(nso_user, nso_pass))
    print(response.text)


# Add devices to NSO
def add_nso_devices(xml_file):
    url = "{}/restconf/data/tailf-ncs:devices".format(nso_url)
    with open(xml_file, 'r') as f:
        payload = f.read()
    # print(payload)
    headers = {
        'Accept': "application/yang-data+json",
        'Content-Type': "application/yang-data+xml"
        }
    response = requests.request("POST", url, data=payload, headers=headers, auth=(nso_user, nso_pass))
    print(response.text)


# Main function of setup app
def main():
    # Connect to controller & create client session
    try:
        client = connect_controller(controller, controller_user, controller_password)
        print("Connected to controller {}".format(controller))
    except:
        print("Unable to connect to controller {}".format(controller))
        quit()

    # Get and connect to my lab
    my_lab = get_my_lab(client, lab_name)

    # If my lab does not exist, import it
    if not my_lab:
        print("{} lab not found; importing it".format(lab_name))
        try:
            my_lab = import_lab(client, lab_definition_path)
            print("Importing lab definition {} as lab ID {}".format(lab_definition_path, my_lab.id))
        except:
            print("Unable to import lab")
    else:
        print("Found lab {} {}".format(my_lab.name, my_lab.id))

    # Start my lab
    print("Starting lab")
    try:
        my_lab.start()
        print("Lab started")
    except:
        print("Unable to start lab")

    # Sync DHCP addresses to lab object
    my_lab.sync_layer3_addresses()

    # Extract external connector addresses
    print("Extracting DHCP addresses from lab {}".format(my_lab.id))
    addresses = extract_addresses(my_lab)
    # print(json.dumps(addresses, indent=4))

    # Render NSO templates & write to files
    # authgroup
    # authgroup_filename = "{}-authgroup.xml".format(lab_name)
    # print("Writing NSO authgroup file to {}".format(authgroup_filename))
    # create_nso_authgroup(lab_name, authgroup_filename)
    # devices
    inventory_filename = "{}-load.xml".format(lab_name)
    print("Writing NSO inventory file to {}".format(inventory_filename))
    create_nso_inventory(lab_name, addresses, inventory_filename)

    # Check if NSO is running and if not, start it
    print("Starting NSO")
    start_nso()

    # Add authgroup to NSO
    # print("Adding authgroup to NSO")
    # add_nso_authgroup(authgroup_filename)

    # Add devices to NSO
    # print("Adding devices to NSO")
    # add_nso_devices(inventory_filename)

    # Load XML into NSO
    load_nso(inventory_filename)

if __name__ == "__main__":
    main()
