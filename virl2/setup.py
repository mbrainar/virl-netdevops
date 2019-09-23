# from Jinja2 import Template
from simple_client import ClientLibrary
import logging
from datetime import datetime
import json

# Variables
controller = "https://192.168.34.11"
controller_user = "admin"
controller_password = "Cisco123"
lab_definition_path = "test-network.yaml"
lab_name = "routed-access"

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
        if lab.name == lab_name or lab.id == "2741a7":
            print("Found {} as lab id {}".format(lab_name, lab.id))
            return client.join_existing_lab(lab.id, sync_lab=True)

# Import lab from lab definition YAML file
# Returns Lab object
def import_lab(client, path):
    return client.import_lab_from_path(path)


# Extract external connector addresses
# Returns: list containing dictionaries of node, interface & address
def extract_addresses(lab):
    addresses = []
    nodes = lab.nodes()
    for node in nodes:
        interfaces = node.physical_interfaces()
        for interface in interfaces:
            if interface.discovered_ipv4:
                addresses.append({
                    "node_id": node.id,
                    "node_label": node.label,
                    "interface": interface.label,
                    "address": interface.discovered_ipv4})
    return addresses


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
try:
    print(my_lab.start())
    print("Starting lab")
except:
    print("Unable to start lab")

# Extract external connector addresses
print(json.dumps(extract_addresses(my_lab), indent=4))
