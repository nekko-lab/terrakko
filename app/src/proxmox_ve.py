##########################################################################
#                                                                        #
#       Proxmox VE API                                                   #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# PVE API
from proxmoxer import ProxmoxAPI

# Tasks
from proxmoxer.tools import Tasks

# Asyncio
import asyncio

# urllib
import urllib.parse

# sys
import sys

# random
import random

# re
import re

#------ Import files ----------------------------------------------------#

# config.py
import config

# db.py
import db

# proxmox_ve.py
import proxmox_ve



#------ Init variable ---------------------------------------------------#

# Arguments
ARGS = sys.argv

# Proxmox VE
pve     = ""

# Region
region  = ""

# VM template ID
temp_id = 0

# Node
node    = ""

#------ Initialize Proxmox VE info --------------------------------------#
# Set up the Proxmox VE API and get the region, template ID, and node    #
#------------------------------------------------------------------------#

async def InitializePVEInfo():
    global pve, region, temp_id, node # Declare global variables
    
    print('Initializing Proxmox VE info...')
    
    # Set up the Proxmox VE API
    pve = ProxmoxAPI(config.PVE_HOST, user=config.PVE_USER, token_name=config.PVE_TOKEN, token_value=config.PVE_SECRET, verify_ssl=False)
    
    # Region
    index  = random.randint(0, len(config.PVE_REGION) - 1)
    region = config.PVE_REGION[index]
    
    # Node
    node = pve.nodes(region)
    
    # VM template ID
    temp_id = int(config.PVE_TEMP_ID[index])
    
    print('Proxmox VE info initialized')

#------ Start instance --------------------------------------------------#
# Start a VM instance with the given VM ID                               #
#------------------------------------------------------------------------#

def StartInstance(r, vmid):
    
    if int(vmid) > 90000 or int(vmid) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
        
    else: # Start the VM instance
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "stopped": # Check if the VM is not running
            
            print(f"Starting VM ID: {vmid}")
            
            # Set the VM status to running
            start_task = pve.nodes(r).qemu(vmid).status.start.post()
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, start_task)
            
            print(f"Started VM ID: {vmid}")
            
        else: # The VM is already running
            
            print(f"VM ID {vmid} is already running")

#------ Stop instance ----------------------------------------------------#
# Stop a VM instance with the given VM ID                                 #
#-------------------------------------------------------------------------#

def StopInstance(r, vmid):
    
    if int(vmid) > 90000 or int(vmid) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
        
    else: # Stop the VM instance
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] != "stopped": # Check if the VM is not stopped
            
            print(f"Stopping VM ID: {vmid}")
            
            # Set the VM status to stopped
            stop_task = pve.nodes(r).qemu(vmid).status.stop.post()
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, stop_task)
            
            print(f"Stopped VM ID: {vmid}")
            
        else: # The VM is already stopped
            
            print(f"VM ID {vmid} is already stopped")

#------ Shutdown instance ------------------------------------------------#
# Shutdown a VM instance with the given VM ID                             #
#-------------------------------------------------------------------------#

def ShutdownInstance(r, vmid):
    
    if int(vmid) > 90000 or int(vmid) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
        
    else: # Shutdown the VM instance
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "running": # Check if the VM is running
            
            print(f"Shutting down VM ID: {vmid}")
            
            # Set the VM status to shutdown
            shutdown_task = pve.nodes(r).qemu(vmid).status.shutdown.post()
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, shutdown_task)
            
            print(f"Shutdown VM ID: {vmid}")
            
        else: # The VM is not running
            
            print(f"VM ID {vmid} is not running")

#------ Reboot instance --------------------------------------------------#
# Reboot a VM instance with the given VM ID                               #
#-------------------------------------------------------------------------#

def RebootInstance(r, vmid):
    
    if int(vmid) > 90000 or int(vmid) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
        
    else: # Reboot the VM instance
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "running": # Check if the VM is running
            
            print(f"Rebooting VM ID: {vmid}")
            
            # Set the VM status to reboot
            reboot_task = pve.nodes(r).qemu(vmid).status.reboot.post()
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, reboot_task)
            
            print(f"Rebooted VM ID: {vmid}")
            
        else: # The VM is not running
            
            print(f"VM ID {vmid} is not running")

#------ Create instance --------------------------------------------------#
# Create a VM instance                                                    #
#-------------------------------------------------------------------------#

async def CreateInstance(clone_vm_id, vm_name, ciuser, passwd, sshkey):
    
    if int(clone_vm_id) > 90000 or int(clone_vm_id) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
    
    else: # Create the VM instance
        try: # Try to create the VM instance
            
            print(f"Creating VM...")
            print(f"VM ID: {clone_vm_id}\tVM Name: {vm_name}")
            print(f"Cloning VM...")
            
            # Set the VM status to clone
            clone_task = node.qemu(temp_id).clone.create(newid=clone_vm_id, name=vm_name, pool='dev')
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, clone_task)
        
            print(f"Cloned VM ID: {clone_vm_id}")
            
            # Initialize the VM instance
            await InitializeInstance(clone_vm_id, ciuser, passwd, sshkey)
            
        except Exception as e: # Catch any exceptions
            
            print(f"Creation failed: {e}")

#------ Initialize instance ----------------------------------------------#
# Initialize a VM instance with the given VM ID, CI user, password, and   #
# SSH key                                                                 #
#-------------------------------------------------------------------------#

async def InitializeInstance(vmid, ciuser, passwd, sshkey):
    
    try: # Try to initialize the VM instance
        
        print(f"Initializing VM...")
        
        # Set the VM status to initialize
        node.qemu(vmid).config.set(
            
            ciuser=ciuser,                                              # Cloud-init user
            
            cipassword=passwd,                                          # Cloud-init password
            
            sshkeys=urllib.parse.quote(sshkey.encode('utf-8'), safe='') # Cloud-init SSH key
            
        )
        
        # Start the VM instance
        init_task = node.qemu(vmid).status.start.post()
        
        # Wait for the task to complete
        Tasks.blocking_status(pve, init_task)
        
        print(f"Initialized VM ID: {vmid}")
        
    except Exception as e: # Catch any exceptions
        
        print(f"Initalization failed: {e}")

#------ Delete instance --------------------------------------------------#
# Delete a VM instance with the given VM ID                               #
#-------------------------------------------------------------------------#

async def DeleteInstance(r, vmid):
    
    if int(vmid) > 90000 or int(vmid) < 100: # Check if the VM ID is valid
        
        print("Invalid VM ID")
    
    else: # Delete the VM instance
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "stopped": # Check if the VM is stopped
            
            print(f"Deleting VM ID: {vmid}")
            
            # Set the VM status to delete
            delete_task = pve.nodes(r).qemu(vmid).delete()
            
            # Wait for the task to complete
            Tasks.blocking_status(pve, delete_task)
            
            print(f"Deleted VM ID: {vmid}")
            
        else: # The VM is not stopped
            
            print(f"VM ID {vmid} is running, please stop it first!")

#------ Get VMID ---------------------------------------------------------#
# Get the next available VM ID                                            #
#-------------------------------------------------------------------------#

def GetVMID():
    
    try: # Try to get the next available VM ID
        
        return pve.cluster.nextid.get()
    
    except Exception as e: # Catch any exceptions
        
        print(f"Getting VM ID failed: {e}")
        
        return None

#------ Get VM status ----------------------------------------------------#
# Get the status of a VM instance with the given VM ID                    #
#-------------------------------------------------------------------------#

async def GetVMStatus(r, vmid):
    
    try: # Try to get the status of the VM instance
        
        return pve.nodes(r).qemu(vmid).status.current.get()
    
    except Exception as e: # Catch any exceptions
        
        print(f"Getting VM status failed: {e}")
        
        return None

#------ Get all VM Status ------------------------------------------------#
# Get the status of all VM instances                                      #
#-------------------------------------------------------------------------#

def GetNodeVM(author_id):
    
    try: # Try to get the status of all VM instances
        
        print("Getting VM status")
        
        # Get the status of all VM instances
        pve.nodes.get() # Catch exception if not logged in
        
        # Return the status of all VM instances sorted by VM ID
        return sorted(
            [
            
                [pve_node['node'], int(vm['vmid']), vm['name'], vm['status']]  # Node, VM ID, VM name, VM status
                
                for pve_node in pve.nodes.get()                                # Get the status of all nodes
                
                for vm in pve("nodes/{0}/qemu".format(pve_node['node'])).get() # Get the status of all VM instances
                
                if 100 <= int(vm['vmid']) < 90000                              # Check if the VM ID is valid
                
                if re.match(f"{author_id}", vm['name'])                        # Check if the VM name matches the author ID
                
            ], 
            
            key=lambda x: x[1]                                                 # Sort by VM ID
        
        )
        
    except Exception as e: # Catch any exceptions
        
        print(f"Getting VM status failed: {e}")
        
        return None

#------ Get VM IP addresses ----------------------------------------------#
# Get the IP addresses of a VM instance with the given VM ID              #
#-------------------------------------------------------------------------#

def GetVMIPAddresses(r, vmid):
    
    try: # Try to get the IP addresses of the VM instance
        
        print(f"Getting IP addresses for VM ID: {vmid}")
        
        # Get the IP addresses of the VM instance
        interfaces = pve.nodes(r).qemu(vmid).agent.get('network-get-interfaces')['result']
        
        # Return the IPv4 and IPv6 addresses
        ipv4_addresses = []
        
        ipv6_addresses = []

        # Get the IP addresses
        for interface in interfaces:
            
            for ip_info in interface.get('ip-addresses', []):
                
                if ip_info['ip-address-type'] == 'ipv4': # IPv4 address
                    
                    ipv4_addresses.append(ip_info['ip-address'])
                    
                elif ip_info['ip-address-type'] == 'ipv6': # IPv6 address
                    
                    ipv6_addresses.append(ip_info['ip-address'])

        # Return the IP addresses
        return ipv4_addresses, ipv6_addresses
    
    except Exception as e: # Catch any exceptions
        
        print(f"Getting IP addresses failed: {e}")
        
        return None, None

#------ Initialize Proxmox VE info ----------------------------------------#
# Initialize the Proxmox VE info                                           #
#--------------------------------------------------------------------------#

try: # Try to initialize the Proxmox VE info
    
    asyncio.run(InitializePVEInfo())
    
except Exception as e: # Catch any exceptions
    
    print(f"Proxmox VE info initialization failed: {e}")
    
    exit(1)

#--------------------------------------------------------------------------#