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
    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
    else:
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] != "running":
            print(f"Starting VM ID: {vmid}")
            
            start_task = pve.nodes(r).qemu(vmid).status.start.post()
            Tasks.blocking_status(pve, start_task)
            
            print(f"Started VM ID: {vmid}")
        else:
            print(f"VM ID {vmid} not found")

#------ Stop instance ----------------------------------------------------#

def StopInstance(r, vmid):
    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
    else:
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] != "stopped":
            print(f"Stopping VM ID: {vmid}")
            
            stop_task = pve.nodes(r).qemu(vmid).status.stop.post()
            Tasks.blocking_status(pve, stop_task)
            
            print(f"Stopped VM ID: {vmid}")
        else:
            print(f"VM ID {vmid} not found")

#------ Shutdown instance ------------------------------------------------#

def ShutdownInstance(r, vmid):
    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
    else:
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "running":
            print(f"Shutting down VM ID: {vmid}")
            
            shutdown_task = pve.nodes(r).qemu(vmid).status.shutdown.post()
            Tasks.blocking_status(pve, shutdown_task)
            
            print(f"Shutdown VM ID: {vmid}")
        else:
            print(f"VM ID {vmid} not found")

#------ Reboot instance --------------------------------------------------#

def RebootInstance(r, vmid):
    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
    else:
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "running":
            print(f"Rebooting VM ID: {vmid}")
            
            reboot_task = pve.nodes(r).qemu(vmid).status.reboot.post()
            Tasks.blocking_status(pve, reboot_task)
            
            print(f"Rebooted VM ID: {vmid}")
        else:
            print(f"VM ID {vmid} not found")

#------ Create instance --------------------------------------------------#

async def CreateInstance(clone_vm_id, vm_name, ciuser, passwd, sshkey):
    if int(clone_vm_id) > 90000 or int(clone_vm_id) < 100:
        print("Invalid VM ID")
    
    else:
        try:
            print(f"Creating VM...")
            print(f"VM ID: {clone_vm_id}\tVM Name: {vm_name}")
            print(f"Cloning VM...")
            
            clone_task = node.qemu(temp_id).clone.create(newid=clone_vm_id, name=vm_name, pool='dev')
            Tasks.blocking_status(pve, clone_task)
        
            print(f"Cloned VM ID: {clone_vm_id}")
            
            await InitializeInstance(clone_vm_id, ciuser, passwd, sshkey)
        except Exception as e:
            print(f"Creation failed: {e}")

#------ Initialize instance ----------------------------------------------#

async def InitializeInstance(vmid, ciuser, passwd, sshkey):
    try:
        print(f"Initializing VM...")
        
        node.qemu(vmid).config.set(
            ciuser=ciuser,
            cipassword=passwd,
            sshkeys=urllib.parse.quote(sshkey.encode('utf-8'), safe='')
        )
        
        init_task = node.qemu(vmid).status.start.post()
        Tasks.blocking_status(pve, init_task)
        
        print(f"Initialized VM ID: {vmid}")
    except Exception as e:
        print(f"Initalization failed: {e}")

#------ Delete instance --------------------------------------------------#

async def DeleteInstance(r, vmid):
    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
    
    else:
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] != "stopped":
            StopInstance(r, vmid)
            asyncio.sleep(1)
        
        if pve.nodes(r).qemu(vmid).status.current.get()['status'] == "stopped":
            print(f"Deleting VM ID: {vmid}")
            
            delete_task = pve.nodes(r).qemu(vmid).delete()
            Tasks.blocking_status(pve, delete_task)
            
            print(f"Deleted VM ID: {vmid}")
        else:
            print(f"VM ID {vmid} is running, please stop it first!")

#------ Get VMID ---------------------------------------------------------#

def GetVMID():
    try:
        return pve.cluster.nextid.get()
    except Exception as e:
        print(f"Getting VM ID failed: {e}")
        
        return None

#------ Get VM status ----------------------------------------------------#

async def GetVMStatus(r, vmid):
    try:
        return pve.nodes(r).qemu(vmid).status.current.get()
    except Exception as e:
        print(f"Getting VM status failed: {e}")
        
        return None

#------ Get all VM Status ------------------------------------------------#

def GetNodeVM(author_id):
    try:
        print("Getting VM status")
        
        pve.nodes.get() # Catch exception if not logged in
        return sorted([
            [pve_node['node'], int(vm['vmid']), vm['name'], vm['status']]
            for pve_node in pve.nodes.get()
            for vm in pve("nodes/{0}/qemu".format(pve_node['node'])).get()
            if 100 <= int(vm['vmid']) < 90000
            if re.match(f"{author_id}", vm['name'])
        ], key=lambda x: x[1])
    except Exception as e:
        print(f"Getting VM status failed: {e}")
        
        return None

#------ Get VM IP addresses ----------------------------------------------#

def GetVMIPAddresses(r, vmid):
    try:
        print(f"Getting IP addresses for VM ID: {vmid}")
        
        interfaces = pve.nodes(r).qemu(vmid).agent.get('network-get-interfaces')['result']
        ipv4_addresses = []
        ipv6_addresses = []

        for interface in interfaces:
            for ip_info in interface.get('ip-addresses', []):
                if ip_info['ip-address-type'] == 'ipv4':
                    ipv4_addresses.append(ip_info['ip-address'])
                elif ip_info['ip-address-type'] == 'ipv6':
                    ipv6_addresses.append(ip_info['ip-address'])

        return ipv4_addresses, ipv6_addresses
    except Exception as e:
        print(f"Getting IP addresses failed: {e}")
        
        return None, None

#------ Initialize Proxmox VE info ----------------------------------------#

try:
    asyncio.run(InitializePVEInfo())
except Exception as e:
    print(f"Proxmox VE info initialization failed: {e}")
    
    exit(1)

#--------------------------------------------------------------------------#