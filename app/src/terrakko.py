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

#---------------------------------------------------------------#
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
    
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="yes")
    async def yes(self, interaction: discord.Interaction, button: discord.Button) -> None:
        if self.mode == "create":
            await interaction.response.send_message("Inform you here when the VM is completed.\nCreating VM...", ephemeral=True)
            for i in range(len(self.vmname)):
                await proxmox_ve.CreateInstance(proxmox_ve.GetVMID(), f"{interaction.user.id}-{self.vmname[i].value}", self.ciname, self.cipass, self.sshkey)
                await asyncio.sleep(1)
            
            await WaitForTaskCompletion(interaction, self.vmid, "create")
        elif self.mode == "delete":
            await interaction.response.send_message("Inform you here when the VM is completed.\nDeleting VM...", ephemeral=True)
            await proxmox_ve.DeleteInstance(self.region, self.vmid)
            await WaitForTaskCompletion(interaction, self.vmid, "delete")
        elif self.mode == "userdata":
            await db.update_data(interaction.user.id, self.ciname, self.cipass, self.sshkey)
            await interaction.response.send_message("Tasks completed", ephemeral=True)
        else:
            await interaction.response.send_message("Error", ephemeral=True)
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="no")
    async def no(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.response.send_message("Canceled", ephemeral=True)

#---------------------------------------------------------------#
# Operate VM: Start, Shutdown, Reboot, Stop
class BootVM(View):
    def __init__(self, r, vmid, ctx, timeout=config.TIME):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.vmid = vmid
        self.region = r
        self.status = {}
    
    async def UpdateStatus(self):
        self.status = await proxmox_ve.GetVMStatus(self.region, self.vmid)
    
    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start")
    async def StartVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await self.UpdateStatus()
        if self.status["status"] == "stopped":
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nStart VM", ephemeral=True)
            proxmox_ve.StartInstance(self.region, self.vmid)
            
            await WaitForTaskCompletion(interaction, self.vmid, "start")
        else:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already running.", ephemeral=True)
    
    @discord.ui.button(label="Shutdown", style=discord.ButtonStyle.gray, custom_id="shutdown")
    async def ShutdownVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await self.UpdateStatus()
        if self.status["status"] == "running":
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nShutdown VM", ephemeral=True)
            proxmox_ve.ShutdownInstance(self.region, self.vmid)
            
            await WaitForTaskCompletion(interaction, self.vmid, "shutdown")
        else:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)
    
    @discord.ui.button(label="Reboot", style=discord.ButtonStyle.blurple, custom_id="reboot")
    async def RebootVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await self.UpdateStatus()
        if self.status["status"] == "running":
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nReboot VM", ephemeral=True)
            proxmox_ve.RebootInstance(self.region, self.vmid)
            
            await WaitForTaskCompletion(interaction, self.vmid, "reboot")
        else:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="stop")
    async def StopVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await self.UpdateStatus()
        if self.status["status"] == "running":
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nStop VM", ephemeral=True)
            proxmox_ve.StopInstance(self.region, self.vmid)
            
            await WaitForTaskCompletion(interaction, self.vmid, "stop")
        else:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nVM is already stopped.", ephemeral=True)

#---------------------------------------------------------------#
# Selected VM Name
class VMNameSelectMenu(View):
    def __init__(self, mode, ctx, timeout=config.TIME):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.mode = mode
    
    @discord.ui.select(
        custom_id="SelectVM",
        placeholder="Select your VM"
    )
    async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0].split(" ") # region, vmid, vmname, status
        status = await proxmox_ve.GetVMStatus(val[0], val[1])
        
        if re.match(f"{self.ctx.author.id}", val[2]) and status != None:
            ipv4, ipv6 = proxmox_ve.GetVMIPAddresses(val[0], val[1])
            msg = f"VM Name: {status['name']}\nVMID: {status['vmid']}\nRegion: {val[0]}\nStatus: {status['status']}\nHost name: vm{status['vmid']}{config.DOMEIN}\nIPv4: {ipv4}\nIPv6: {ipv6}"
            
            if self.mode == "delete":
                try:
                    await interaction.response.send_message(msg, ephemeral=True)
                    await interaction.followup.send("Do you want to delete this VM?\n(You must stop the VM before deleting it.)", ephemeral=True)
                    await interaction.followup.send(view=ConfirmAndExecute("delete", "", "", "", "", val[0], val[1], config.TIME), ephemeral=True)
                except Exception as e:
                    print(f"Delete Error: {e}")
            elif self.mode == "info":
                try:
                    await interaction.response.send_message("What do you want to do with this VM?", ephemeral=True)
                    await interaction.edit_original_response(content=msg, view=BootVM(val[0], val[1], self.ctx, timeout=config.TIME))
                except Exception as e:
                    print(f"Info Error: {e}")
            else:
                await interaction.response.send_message(f"{val[1]}\nError", ephemeral=True)
        else:
            await interaction.response.send_message("You cannot operate this VM.", ephemeral=True)

#---------------------------------------------------------------#
# Set Cloud-init
class SetCloudinit(Modal):
    def __init__(self, vmnum, title: str) -> None:
        super().__init__(title=title)
        self.vmname = []
        for i in range(int(vmnum)):
            self.vmname.append(TextInput(label=f"VM Name {i+1}", style=TextStyle.short, required=True))   # VM Name
            self.add_item(self.vmname[i])
        self.clone_vm_id = proxmox_ve.GetVMID()     # Clone VM ID
    
    async def on_submit(self, interaction: Interaction) -> None:    # on_submit: Modalの送信ボタンが押されたときに呼び出される関数（on_submit以外の名前はエラー）
        if self.clone_vm_id == None:
            await interaction.response.send_message("Getting VM ID failed.", ephemeral=True)
            
            return 0
        
        userlist = await db.get_userdata(interaction.user.id)
        
        if len(userlist) != 5:
            await interaction.response.send_message("User data not found.", ephemeral=True)
            
            return 0
        
        msg = ""
        for vmname in self.vmname:
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
class MenuView(View):
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
        view = VMNameSelectMenu("info", self.ctx, timeout=config.TIME)
        if len(self.VMList) == 0:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nNo VMs found.", ephemeral=True)
        else:
            for vm in self.VMList[:24]:
                view.on_select.add_option(
                    label=f"{vm[1]:05}: {vm[2]} | {vm[0]}",
                    value=f"{vm[0]} {vm[1]} {vm[2]} {vm[3]}"
                )
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nShow VM info.\n\nWhich VM do you want to show information?", view=view, ephemeral=True)
    
    @discord.ui.button(label="Delete VM", style=discord.ButtonStyle.red, custom_id="delete")
    async def DeleteVM(self, interaction: discord.Interaction, button: discord.Button) -> None:
        view = VMNameSelectMenu("delete", self.ctx, timeout=config.TIME)
        if len(self.VMList) == 0:
            await interaction.response.send_message(f"User: {self.ctx.author.name}\nNo VMs found.", ephemeral=True)
        else:
            for vm in self.VMList[:24]:
                view.on_select.add_option(
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
    await ctx.send(view=MenuView(ctx, timeout=config.TIME), ephemeral=True)

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