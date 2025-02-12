#!/usr/local/bin/python3.11
# -*- coding: utf-8 -*-

##########################################################################
#                                                    _                   #
#        _____  _____ ____  ____  ____  _  __ _  __ |_\_                 #
#       /__ __\/  __//  __\/  __\/  _ \/ |/ // |/ //\_  \_               #
#         / \  |  \  |  \/||  \/|| /_\||   / |   /|_  \_  \              #
#         | |  |  /_ |    /|    /| | |||   \ |   \| \_  \__|             #
#         \_/  \____\\_/\_\\_/\_\\_/ \/\_|\_\\_|\_\\__\___/              #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# discord
import discord

# discord commands
from discord.ext import commands

# discord Interaction, TextStyle
from discord import Interaction, TextStyle

# discord UI
from discord.ui import TextInput, Modal, Select, Button, View

# asyncio
import asyncio

# re
import re

#------ Import files ----------------------------------------------------#

# config.py
import config

# db.py
import db

# proxmox_ve.py
import proxmox_ve



#------ Initialize Bot --------------------------------------------------#
# Intents for the bot                                                    #
#------------------------------------------------------------------------#

# Intents
intents = discord.Intents.default()

# Intents: Message Content
intents.message_content = True

# Intents: Messages
intents.messages = True

# Bot commands options
bot = commands.Bot(
    
    command_prefix=commands.when_mentioned_or("trk"), # Command prefix
    
    case_insensitive=True,                            # Case insensitive
    
    intents=intents,                                  # Intents
    
    activity=discord.Game("Nekko Cloud")              # Activity
    
)

#------ Task Status -----------------------------------------------------#
# Wait for task completion                                               #
#------------------------------------------------------------------------#

async def WaitForTaskCompletion(interaction, vmid, task):
    data = {"status": ""}
    await asyncio.sleep(10)
    vm_status = ""
    
    if task == "create": # task: create
        
        await asyncio.sleep(180) # cloud-initからリクエストがあるまで待機に変更したい
        
        vm_status = "stopped"
        
    elif task == "delete": # task: delete
        
        vm_status = "stopped"
        
    elif task == "info": # task: info
        
        vm_status = "running"
        
    elif task == "start": # task: start
        
        vm_status = "running"
        
    elif task == "shutdown": # task: shutdown
        
        vm_status = "stopped"
        
    elif task == "stop": # task: stop
        
        vm_status = "stopped"
        
    elif task == "pause": # task: pause
        
        vm_status = "running"
        
    elif task == "reboot": # task: reboot
        
        vm_status = "running"
        
    else: # task: unknown
        
        await interaction.followup.send("Error", ephemeral=True)
        
        return 1
    
    
    while data["status"] == vm_status:  # running, stopped
        
        try: # Get VM status
            
            # current status
            data = proxmox_ve.node.qemu(vmid).status.current.get()
            
            print({vmid} is data["status"])
            
            await asyncio.sleep(5)
            
        except ConnectionError as e: # Connection error
            
            print(f"Connection error: {e}")
            
            await asyncio.sleep(5)
            
            continue
    
    # Task completed
    await interaction.followup.send("Tasks completed", ephemeral=True)

#------ Confirm and execute ------------------------------------#
# Confirm and Execute the task (Create, Delete, UserData)       #
#---------------------------------------------------------------#

class ConfirmAndExecute(View):
    
    def __init__(self, mode, vmname, ciname, cipass, sshkey, r, vmid, timeout=config.TIME): # Initialize the class
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # mode: create, delete, userdata
        self.mode   = mode
        
        # vmname
        self.vmname = vmname
        
        # ciname
        self.ciname = ciname
        
        # cipass
        self.cipass = cipass
        
        # sshkey
        self.sshkey = sshkey
        
        # region
        self.region = r
        
        # vmid
        self.vmid   = vmid
    
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes") # UI: Yes button
    
    async def yes(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Yes
        
        if self.mode == "create": # mode: create
            
            # message: Creating VM
            await interaction.response.send_message("Inform you here when the VM is completed.\nCreating VM...", ephemeral=True)
            
            for i in range(len(self.vmname)): # Create VM
                
                # Create VM instance (VMID, VM Name, User Name, Password, SSH Key)
                await proxmox_ve.CreateInstance(proxmox_ve.GetVMID(), f"{interaction.user.id}-{self.vmname[i].value}", self.ciname, self.cipass, self.sshkey)
                
                await asyncio.sleep(1)
            
            
            # Wait for task completion: task == create
            await WaitForTaskCompletion(interaction, self.vmid, "create")
            
        elif self.mode == "delete": # mode: delete
            
            # message: Deleting VM
            await interaction.response.send_message("Inform you here when the VM is completed.\nDeleting VM...", ephemeral=True)
            
            # Delete VM instance
            await proxmox_ve.DeleteInstance(self.region, self.vmid)
            
            # Wait for task completion: task == delete
            await WaitForTaskCompletion(interaction, self.vmid, "delete")
            
        elif self.mode == "userdata": # mode: userdata
            
            # message: Saving user data
            await db.update_data(interaction.user.id, self.ciname, self.cipass, self.sshkey)
            
            # message: User data saved
            await interaction.response.send_message("Tasks completed", ephemeral=True)
            
        else: # mode: unknown
            
            # message: Error
            await interaction.response.send_message("Error", ephemeral=True)
    
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="no") # UI: No button
    
    async def no(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: No
        
        # message: Canceled
        await interaction.response.send_message("Canceled", ephemeral=True)

#------ Operate VM power ------------------------------------------------#
# Operate the VM instance's power: Start, Shutdown, Reboot, Stop         #
#------------------------------------------------------------------------#

class OperateVMPower(View):
    
    def __init__(self, r, vmid, ctx, timeout=config.TIME): # Initialize the class
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # vmid
        self.vmid = vmid
        
        # region
        self.region = r
        
        # status
        self.status = {}
    
    
    async def UpdateVMStatus(self): # Update the VM status
        
        # Get VM status
        self.status = await proxmox_ve.GetVMStatus(self.region, self.vmid)
    
    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start") # UI: Start button
    
    async def StartVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Start VM
        
        # Update the VM status
        await self.UpdateVMStatus()
        
        if self.status["status"] == "stopped": # status: stopped
            
            # message: Start VM
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nStart VM", ephemeral=True)
            
            # Start VM instance
            proxmox_ve.StartInstance(self.region, self.vmid)
            
            # Wait for task completion: task == start
            await WaitForTaskCompletion(interaction, self.vmid, "start")
            
        else: # status: running
            
            # message: VM is already running
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already running.", ephemeral=True)
    
    
    @discord.ui.button(label="Shutdown", style=discord.ButtonStyle.gray, custom_id="shutdown") # UI: Shutdown button
    
    async def ShutdownVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Shutdown VM
        
        # Update the VM status
        await self.UpdateVMStatus()
        
        if self.status["status"] == "running": # status: running
            
            # message: Shutdown VM
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nShutdown VM", ephemeral=True)
            
            # Shutdown VM instance
            proxmox_ve.ShutdownInstance(self.region, self.vmid)
            
            # Wait for task completion: task == shutdown
            await WaitForTaskCompletion(interaction, self.vmid, "shutdown")
            
        else: # status: stopped
            
            # message: VM is already stopped
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)
    
    
    @discord.ui.button(label="Reboot", style=discord.ButtonStyle.blurple, custom_id="reboot") # UI: Reboot button
    
    async def ReOperateVMPower(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Reboot VM
        
        # Update the VM status
        await self.UpdateVMStatus()
        
        if self.status["status"] == "running": # status: running
            
            # message: Reboot VM
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nReboot VM", ephemeral=True)
            
            # Reboot VM instance
            proxmox_ve.RebootInstance(self.region, self.vmid)
            
            # Wait for task completion: task == reboot
            await WaitForTaskCompletion(interaction, self.vmid, "reboot")
            
        else: # status: stopped
            
            # message: VM is already stopped
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)
    
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="stop") # UI: Stop button
    
    async def StopVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Stop VM
        
        # Update the VM status
        await self.UpdateVMStatus()
        
        if self.status["status"] == "running": # status: running
            
            # message: Stop VM
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nStop VM", ephemeral=True)
            
            # Stop VM instance
            proxmox_ve.StopInstance(self.region, self.vmid)
            
            # Wait for task completion: task == stop
            await WaitForTaskCompletion(interaction, self.vmid, "stop")
            
        else: # status: stopped
            
            # message: VM is already stopped
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)

#------ Select VM Name --------------------------------------------------#
# Selected your VM Name                                                  #
#------------------------------------------------------------------------#

class SelectVMNameMenu(View):
    
    def __init__(self, mode, ctx, timeout=config.TIME): # Initialize the class
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # mode: delete, info
        self.mode = mode
    
    
    # UI: Select VM
    @discord.ui.select(
        
        custom_id="SelectVM",        # UI: Select VM
        
        placeholder="Select your VM" # UI: Placeholder
        
    )
    
    async def SelectedVM(self, interaction: discord.Interaction, select: discord.ui.Select): # Function: Select VM
        
        # Select VM values: region, vmid, vmname, status
        val = select.values[0].split(" ")
        
        # Get VM status
        status = await proxmox_ve.GetVMStatus(val[0], val[1])
        
        if re.match(f"{self.ctx.author.id}", val[2]) and status != None: # Check the VM owner
            
            # Get VM IP addresses
            ipv4, ipv6 = proxmox_ve.GetVMIPAddresses(val[0], val[1])
            
            # message: VM info
            msg = f"VM Name: {status['name']}\nVMID: {status['vmid']}\nRegion: {val[0]}\nStatus: {status['status']}\nHost name: vm{status['vmid']}{config.DOMEIN}\nIPv4: {ipv4}\nIPv6: {ipv6}"
            
            if self.mode == "delete": # mode: delete
                
                try: # Delete VM
                    
                    # message: Delete VM
                    await interaction.response.send_message(msg, ephemeral=True)
                    
                    # message: Do you want to delete this VM?
                    await interaction.followup.send("Do you want to delete this VM?\n(You must stop the VM before deleting it.)", ephemeral=True)
                    
                    # view: Confirm and Execute
                    await interaction.followup.send(view=ConfirmAndExecute("delete", "", "", "", "", val[0], val[1], config.TIME), ephemeral=True)
                    
                except Exception as e: # Delete Error
                    
                    print(f"Delete Error: {e}")
                
            elif self.mode == "info": # mode: info
                
                try: # Show VM info
                    
                    # message: Show VM info
                    await interaction.response.send_message("What do you want to do with this VM?", ephemeral=True)
                    
                    # view: Operate VM power
                    await interaction.edit_original_response(content=msg, view=OperateVMPower(val[0], val[1], self.ctx, timeout=config.TIME))
                
                except Exception as e: # Show Info Error
                    
                    print(f"Info Error: {e}")
                
            else: # mode: unknown
                
                # message: Error
                await interaction.response.send_message(f"{val[1]}\nError", ephemeral=True)
                
        else: # Not the VM owner
            
            # message: You cannot operate this VM
            await interaction.response.send_message("You cannot operate this VM.", ephemeral=True)

#------ Set Cloud-init --------------------------------------------------#
# Set up the VM's cloud-init settings                                    #
#------------------------------------------------------------------------#

class SetCloudinit(Modal):
    
    def __init__(self, vmnum, title: str) -> None: # Initialize the class
        
        # title: Configure Cloud-init settings
        super().__init__(title=title)
        
        # vmname
        self.vmname = []
        
        # clone_vm_id
        for i in range(int(vmnum)): # VM Number
            
            # VM Name: TextInput
            self.vmname.append(TextInput(label=f"VM Name {i+1}", style=TextStyle.short, required=True))
            
            # Add item
            self.add_item(self.vmname[i])
        
        # clone_vm_id: VM Template ID
        self.clone_vm_id = proxmox_ve.GetVMID()
    
    
    async def on_submit(self, interaction: Interaction) -> None:    # on_submit: Modalの送信ボタンが押されたときに呼び出される関数（on_submit以外の名前はエラー）
        
        if self.clone_vm_id == None: # Get VM ID failed.
            
            # message: Getting VM ID failed
            await interaction.response.send_message("Getting VM ID failed.", ephemeral=True)
            
            return 0
        
        # Get user data
        userlist = await db.get_userdata(interaction.user.id)
        
        if len(userlist) != 5: # User data not found.
            
            # message: User data not found
            await interaction.response.send_message("User data not found.", ephemeral=True)
            
            return 0
        
        # init msg val
        msg = ""
        
        for vmname in self.vmname: # send message 
            
            # message: VM Name, User Name, Password, SSH Key
            msg += f"VM Name:\t{interaction.user.id}-{vmname}\nUser Name:\t{userlist[2]}\nPassword:\t||{userlist[3]}||\nSSH Key:\t||{userlist[4]}||\n"
        
        msg += "\nDo you want to create this?"
        
        await interaction.response.send_message(msg, ephemeral=True)
        confirm_view = ConfirmAndExecute(
            "create",
            self.vmname,
            userlist[2],
            userlist[3],
            userlist[4],
            "",
            self.clone_vm_id
        )
        await interaction.followup.send(view=confirm_view, ephemeral=True)
    
    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        print("error: SetCloudinit")
        await interaction.response.send_message("Error: SetCloudinit", ephemeral=True)

    async def on_timeout(self) -> None:
        print("on timeout: SetCloudinit")

#---------------------------------------------------------------#
# Set User Data
class SetUserData(Modal):
    def __init__(self, ctx, userdata, title: str) -> None:
        super().__init__(title=title)
        self.ctx = ctx
        self.ciname = TextInput(label="User Name", style=TextStyle.short, default=userdata[2], required=False)   # User Name
        self.add_item(self.ciname)
        self.cipass = TextInput(label="Password", style=TextStyle.short, default=userdata[3], required=False)    # Password
        self.add_item(self.cipass)
        self.sshkey = TextInput(label="SSH Key", style=TextStyle.short, default=userdata[4], required=False)     # SSH Key
        self.add_item(self.sshkey)
    
    async def on_submit(self, interaction: Interaction) -> None:    # on_submit: Modalの送信ボタンが押されたときに呼び出される関数（on_submit以外の名前はエラー）
        if len(self.ciname.value) == 0 or len(self.cipass.value) == 0 or len(self.sshkey.value) == 0:
            await interaction.response.send_message("Invalid input.", ephemeral=True)
        else:
            await interaction.response.send_message(f"User Name:\t{self.ciname}\nPassword:\t||{self.cipass}||\nSSH Key:\t||{self.sshkey}||\n\nDo you want to save this?", ephemeral=True)
            confirm_view = ConfirmAndExecute(
                "userdata",
                "",
                self.ciname.value,
                self.cipass.value,
                self.sshkey.value,
                "",
                ""
            )
            await interaction.followup.send(view=confirm_view, ephemeral=True)
    
    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        print("error: SetUserData")
        await interaction.response.send_message("Error: SetUserData", ephemeral=True)
    
    async def on_timeout(self) -> None:
        print("on timeout: SetUserData")

#---------------------------------------------------------------#
# Select VM Number
class SelectVMNumber(View):
    def __init__(self, ctx, timeout=config.TIME):
        super().__init__(timeout=timeout)
        self.ctx = ctx
    
    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="How many VMs do you want to create?",
        options=[discord.SelectOption(label=f"{i+1}", value=f"{i+1}") for i in range(0, 5)]
    )
    async def cisetting(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(SetCloudinit(select.values[0], "Configure Cloud-init settings."))

#---------------------------------------------------------------#
# Menu
class MainMenu(View):
    def __init__(self, ctx, timeout=config.TIME):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.VMList = proxmox_ve.GetNodeVM(self.ctx.author.id)
    
    @discord.ui.button(label="Create VM", style=discord.ButtonStyle.green, custom_id="create")
    async def CreateVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.response.send_message(f"User: {self.ctx.author.name}\nCreate VM.", ephemeral=True)
        await interaction.edit_original_response(content="How many VMs do you want to create?", view=SelectVMNumber(self.ctx, timeout=config.TIME))
    
    @discord.ui.button(label="Show VM info", style=discord.ButtonStyle.blurple, custom_id="info")
    async def ShowInfo(self, interaction: discord.Interaction, button: discord.Button) -> None:
        view = SelectVMNameMenu("info", self.ctx, timeout=config.TIME)
        if len(self.VMList) == 0:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nNo VMs found.", ephemeral=True)
        else:
            for vm in self.VMList[:24]:
                view.SelectedVM.add_option(
                    label=f"{vm[1]:05}: {vm[2]} | {vm[0]}",
                    value=f"{vm[0]} {vm[1]} {vm[2]} {vm[3]}"
                )
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nShow VM info.\n\nWhich VM do you want to show information?", view=view, ephemeral=True)
    
    @discord.ui.button(label="Delete VM", style=discord.ButtonStyle.red, custom_id="delete")
    async def DeleteVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        view = SelectVMNameMenu("delete", self.ctx, timeout=config.TIME)
        if len(self.VMList) == 0:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nNo VMs found.", ephemeral=True)
        else:
            for vm in self.VMList[:24]:
                view.SelectedVM.add_option(
                    label=f"{vm[1]:05}: {vm[2]} | {vm[0]}",
                    value=f"{vm[0]} {vm[1]} {vm[2]} {vm[3]}"
                )
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nDelete VM.\n\nWhich VM do you want to delete?", view=view, ephemeral=True)
    
    @discord.ui.button(label="Configure your info", style=discord.ButtonStyle.gray, custom_id="userdata")
    async def SetKey(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.response.send_modal(SetUserData(self.ctx, await db.get_userdata(self.ctx.author.id), "Configure your info."))

#---------------------------------------------------------------#
# Ready
@bot.event
async def on_ready():
    await asyncio.sleep(1)
    
    print(config.LOGO)
    print(f"Nekko Cloud: {config.version}")
    print('Nekko Cloud\'s VM is available!')

#---------------------------------------------------------------#
# Show menu command
@bot.command(name="!", description="Linuxコマンドを受け取り、チャンネルに表示します", ephemeral=True)
async def menu(ctx):
    await proxmox_ve.InitializePVEInfo()
    
    if ctx.author.id in [row[0] for row in await db.get_column("uuid")]:
        await ctx.send(f"Hi {ctx.author.name}!", ephemeral=True)
    else:
        await db.insert_data(ctx.author.id, "ncadmin", config.PVE_PASS, "")
        await ctx.send(f"{ctx.author.name}, Nice to meet you!", ephemeral=True)
    
    await ctx.send(f"Create VM:\tCreate a new VM\nDelete VM:\tDelete a VM\nShow info:\tShow VM information\n\nPowered by Nekko Cloud {config.version}", ephemeral=True)
    await ctx.send(view=MainMenu(ctx, timeout=config.TIME), ephemeral=True)

#---------------------------------------------------------------#
# Delete Database
class DeleteDB(View):
    def __init__(self, ctx, timeout=config.TIME):
        super().__init__(timeout=timeout)
        self.ctx = ctx
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes")
    async def yes(self, interaction: discord.Interaction, button: discord.Button) -> None:
        db.delete_database()
        interaction.response.send_message("User data deleted", ephemeral=True)
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="no")
    async def no(self, interaction: discord.Interaction, button: discord.Button) -> None:
        interaction.response.send_message("Canceled", ephemeral=True)

#---------------------------------------------------------------#
# Delete Database command
@bot.command(name="delete.db", description="Delete user data", ephemeral=True)
async def delete_db(ctx):
    ctx.send("Delete user data", ephemeral=True)
    ctx.send(view=DeleteDB(ctx, timeout=config.TIME), ephemeral=True)

#---------------------------------------------------------------#
# Start Bot
bot.run(config.DIS_TOKEN)

#---------------------------------------------------------------#