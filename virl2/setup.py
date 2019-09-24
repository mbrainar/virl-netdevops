import os
from jinja2 import Environment, FileSystemLoader
from simple_client import ClientLibrary
import logging
from datetime import datetime
import json

# Variables
controller = "https://192.168.34.11"
controller_user = "admin"
controller_password = "Cisco123"
lab_name = "routed-access"
lab_definition_path = "{}.yaml".format(lab_name)
path = os.path.dirname(os.path.abspath(__file__))


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
        if lab.name == lab_name or lab.id == "ca2afb":
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
def create_nso_inventory(addresses):
    output_filename = "virl2-nso-inventory.xml"
    context = {'context': addresses}
    with open(output_filename, 'w') as f:
        xml = render_template('virl2-nso-template.xml', context)
        f.write(xml)

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
    print("Writing NSO inventory file")
    create_nso_inventory(addresses)



if __name__ == "__main__":
    main()
