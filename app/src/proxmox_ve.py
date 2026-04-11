##########################################################################
#                                                                        #
#       Proxmox VE API                                                   #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# PVE API
from proxmoxer import ProxmoxAPI

# Asyncio
import asyncio

# urllib
import urllib.parse

# datetime
import datetime

#------ Import files ----------------------------------------------------#

# config.py
import config

#------ Init variable ---------------------------------------------------#
# Proxmox VE                                                             #
#------------------------------------------------------------------------#

# Proxmox VE
pve = ""

#------ Initialize Proxmox VE info --------------------------------------#
# Set up the Proxmox VE API                                              #
#------------------------------------------------------------------------#

async def InitializePVEInfo():
    global pve

    print('Initializing Proxmox VE info...')

    # verify_ssl: True (system CA), path string (custom CA cert), or False (disabled - not recommended)
    verify_ssl = config.PVE_CA_CERT if config.PVE_CA_CERT else True
    pve = ProxmoxAPI(
        config.PVE_HOST,
        user=config.PVE_USER,
        token_name=config.PVE_TOKEN,
        token_value=config.PVE_SECRET,
        verify_ssl=verify_ssl
    )

    print('Proxmox VE info initialized')

#------ Get Region ------------------------------------------------------#
# Select the region with the fewest running VMs                          #
#------------------------------------------------------------------------#

async def GetRegion():
    min_count     = float('inf')
    selected_node = None
    selected_temp = None

    all_nodes = await asyncio.to_thread(pve.nodes.get)

    for node_info in all_nodes:
        if node_info.get('status') != 'online':
            continue
        r = node_info['node']
        try:
            vms = await asyncio.to_thread(pve.nodes(r).qemu.get)

            # Find template by name (VMID >= 90000)
            template_vm = next(
                (vm for vm in vms
                 if vm.get('name') == config.PVE_TEMP_NAME
                 and int(vm['vmid']) >= 90000),
                None
            )
            if template_vm is None:
                print(f"GetRegion: template '{config.PVE_TEMP_NAME}' not found on {r}, skipping")
                continue

            running = sum(
                1 for vm in vms
                if vm.get('status') == 'running'
                and 100 <= int(vm['vmid']) < 90000
            )
            if running < min_count:
                min_count     = running
                selected_node = r
                selected_temp = int(template_vm['vmid'])

        except Exception as e:
            print(f"GetRegion: skipping {r} due to error: {e}")
            continue

    if selected_node is None:
        raise RuntimeError(f"No node found with template '{config.PVE_TEMP_NAME}'")

    node = pve.nodes(selected_node)
    print(f"GetRegion: selected {selected_node} (template VMID: {selected_temp}, running VMs: {min_count})")
    return selected_node, node, selected_temp

#------ Watch task ------------------------------------------------------#
# Poll task status until completion or timeout                           #
#------------------------------------------------------------------------#

async def WatchTask(upid):
    node_id  = upid.split(':')[1]
    deadline = asyncio.get_event_loop().time() + config.TIME

    while asyncio.get_event_loop().time() < deadline:
        status = await asyncio.to_thread(
            pve.nodes(node_id).tasks(upid).status.get
        )
        if status['status'] == 'stopped':
            return status.get('exitstatus') == 'OK', status
        await asyncio.sleep(5)

    return False, {'exitstatus': 'TIMEOUT'}

#------ Audit log -------------------------------------------------------#
# Record privileged operations to stdout                                 #
#------------------------------------------------------------------------#

def AuditLog(user_id, command, vm_id, result):
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"[AUDIT] [{timestamp}] [{user_id}] [{command}] [VM:{vm_id}] [{result}]")

#------ Start instance --------------------------------------------------#
# Start a VM instance with the given VM ID                               #
#------------------------------------------------------------------------#

async def StartInstance(r, vmid):

    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
        return None

    current = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)

    if current['status'] != 'stopped':
        print(f"VM ID {vmid} is already running")
        return None

    print(f"Starting VM ID: {vmid}")
    upid = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.start.post)
    return upid

#------ Stop instance ---------------------------------------------------#
# Force-stop a VM instance with the given VM ID                         #
#------------------------------------------------------------------------#

async def StopInstance(r, vmid):

    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
        return None

    current = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)

    if current['status'] == 'stopped':
        print(f"VM ID {vmid} is already stopped")
        return None

    print(f"Stopping VM ID: {vmid}")
    upid = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.stop.post)
    return upid

#------ Shutdown instance -----------------------------------------------#
# Gracefully shut down a VM instance with the given VM ID               #
#------------------------------------------------------------------------#

async def ShutdownInstance(r, vmid):

    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
        return None

    current = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)

    if current['status'] != 'running':
        print(f"VM ID {vmid} is not running")
        return None

    print(f"Shutting down VM ID: {vmid}")
    upid = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.shutdown.post)
    return upid

#------ Reboot instance -------------------------------------------------#
# Reboot a VM instance with the given VM ID                             #
#------------------------------------------------------------------------#

async def RebootInstance(r, vmid):

    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
        return None

    current = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)

    if current['status'] != 'running':
        print(f"VM ID {vmid} is not running")
        return None

    print(f"Rebooting VM ID: {vmid}")
    upid = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.reboot.post)
    return upid

#------ Create instance -------------------------------------------------#
# Clone a template and initialize with Cloud-init                       #
#------------------------------------------------------------------------#

async def CreateInstance(clone_vm_id, vm_name, ciuser, passwd, sshkey, discord_user_id):

    if int(clone_vm_id) > 90000 or int(clone_vm_id) < 100:
        print("Invalid VM ID")
        return None

    try:
        _, current_node, current_temp_id = await GetRegion()

        print(f"Creating VM... ID: {clone_vm_id}  Name: {vm_name}")
        print("Cloning VM...")

        clone_task = await asyncio.to_thread(
            current_node.qemu(current_temp_id).clone.create,
            newid=clone_vm_id, name=vm_name, pool='dev'
        )

        ok, _ = await WatchTask(clone_task)
        if not ok:
            raise RuntimeError(f"Clone failed for VM {clone_vm_id}")

        print(f"Cloned VM ID: {clone_vm_id}")

        # Assign ownership tag immediately after clone
        await asyncio.to_thread(
            current_node.qemu(clone_vm_id).config.set,
            tags=f"discord_{discord_user_id}"
        )

        upid = await InitializeInstance(clone_vm_id, ciuser, passwd, sshkey, current_node)
        AuditLog(discord_user_id, "build", clone_vm_id, "started")
        return upid

    except Exception as e:
        print(f"Creation failed: {e}")
        AuditLog(discord_user_id, "build", clone_vm_id, f"failed: {e}")
        return None

#------ Initialize instance ---------------------------------------------#
# Apply Cloud-init config and start the VM                              #
#------------------------------------------------------------------------#

async def InitializeInstance(vmid, ciuser, passwd, sshkey, current_node):

    try:
        print(f"Initializing VM ID: {vmid}...")

        await asyncio.to_thread(
            current_node.qemu(vmid).config.set,
            ciuser=ciuser,
            cipassword=passwd,
            sshkeys=urllib.parse.quote(sshkey.encode('utf-8'), safe='')
        )

        upid = await asyncio.to_thread(current_node.qemu(vmid).status.start.post)
        print(f"Initialized VM ID: {vmid}")
        return upid

    except Exception as e:
        print(f"Initialization failed: {e}")
        return None

#------ Delete instance -------------------------------------------------#
# Delete a stopped VM instance                                          #
#------------------------------------------------------------------------#

async def DeleteInstance(r, vmid, discord_user_id):

    if int(vmid) > 90000 or int(vmid) < 100:
        print("Invalid VM ID")
        return None

    current = await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)

    if current['status'] != 'stopped':
        print(f"VM ID {vmid} is running, please stop it first!")
        return None

    print(f"Deleting VM ID: {vmid}")
    upid = await asyncio.to_thread(pve.nodes(r).qemu(vmid).delete)
    AuditLog(discord_user_id, "delete", vmid, "started")
    return upid

#------ Get VMID --------------------------------------------------------#
# Get the next available VM ID from the cluster                         #
#------------------------------------------------------------------------#

async def GetVMID():

    try:
        return await asyncio.to_thread(pve.cluster.nextid.get)
    except Exception as e:
        print(f"Getting VM ID failed: {e}")
        return None

#------ Get VM status ---------------------------------------------------#
# Get the current status of a VM instance                               #
#------------------------------------------------------------------------#

async def GetVMStatus(r, vmid):

    try:
        return await asyncio.to_thread(pve.nodes(r).qemu(vmid).status.current.get)
    except Exception as e:
        print(f"Getting VM status failed: {e}")
        return None

#------ Get node VM list ------------------------------------------------#
# Get VMs owned by the given Discord user (tag-based)                   #
#------------------------------------------------------------------------#

async def GetNodeVM(author_id):

    try:
        tag   = f"discord_{author_id}"
        nodes = await asyncio.to_thread(pve.nodes.get)

        results = []
        for pve_node in nodes:
            vms = await asyncio.to_thread(
                pve(f"nodes/{pve_node['node']}/qemu").get
            )
            for vm in vms:
                if not (100 <= int(vm['vmid']) < 90000):
                    continue
                if tag in vm.get('tags', '').split(';'):
                    results.append([
                        pve_node['node'],
                        int(vm['vmid']),
                        vm['name'],
                        vm['status']
                    ])

        return sorted(results, key=lambda x: x[1])

    except Exception as e:
        print(f"Getting VM list failed: {e}")
        return None

#------ Get VM IP addresses ---------------------------------------------#
# Get IPv4 and IPv6 addresses via QEMU Guest Agent                      #
#------------------------------------------------------------------------#

async def GetVMIPAddresses(r, vmid):

    try:
        print(f"Getting IP addresses for VM ID: {vmid}")

        interfaces = await asyncio.to_thread(
            pve.nodes(r).qemu(vmid).agent.get, 'network-get-interfaces'
        )
        interfaces = interfaces['result']

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

#------ Initialize Proxmox VE info --------------------------------------#

try:
    asyncio.run(InitializePVEInfo())
except Exception as e:
    print(f"Proxmox VE info initialization failed: {e}")
    exit(1)

#------------------------------------------------------------------------#
