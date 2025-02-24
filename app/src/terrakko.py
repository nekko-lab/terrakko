#!/usr/local/bin/python3.11
# -*- coding: utf-8 -*-

##########################################################################
#                                                       _                #
#           _____  _____ ____  ____  ____  _  __ _  __ |_\_              #
#          /__ __\/  __//  __\/  __\/  _ \/ |/ // |/ //\_  \_            #
#            / \  |  \  |  \/||  \/|| /_\||   / |   /|_  \_  \           #
#            | |  |  /_ |    /|    /| | |||   \ |   \| \_  \__|          #
#            \_/  \____\\_/\_\\_/\_\\_/ \/\_|\_\\_|\_\\__\___/           #
#                                                                        #
##########################################################################

#------ Library ---------------------------------------------------------#

# discord
import discord

# discord commands
from discord.ext import commands

# discord Interaction, TextStyle
from discord import Interaction, TextStyle, app_commands

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

#------ User session ----------------------------------------------------#
# Keep the user session                                                  #
#------------------------------------------------------------------------#

class UserSession():
    
    # Initialize the class
    def __init__(self, ctx):
        
        # Context
        self.ctx = ctx
    

    # Set the current user
    def set_current_user(self):
        
        # Set the current user
        return self.ctx.author.id

#------ Task Status -----------------------------------------------------#
# Wait for task completion                                               #
#------------------------------------------------------------------------#

async def WaitForTaskCompletion(interaction, vmid, task):
    
    # Task status
    data = {"status": ""}
    
    # Wait for task completion
    await asyncio.sleep(10)
    
    # VM status
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

#------ Bot Ready -------------------------------------------------------#
# Bot is ready                                                           #
#------------------------------------------------------------------------#

# Bot event: on_ready
@bot.event

async def on_ready(): # Bot is ready
    
    await asyncio.sleep(1)
    
    # Print the logo and version
    print(config.LOGO)
    
    print(f"Nekko Cloud: {config.version}")
    
    print('Nekko Cloud\'s VM is available!')

#------ Bot Interaction -------------------------------------------------#
# Bot interaction                                                        #
#------------------------------------------------------------------------#

# Bot event: on interaction
@bot.event

async def on_interaction(interaction: discord.Interaction): # Bot interaction
    
    # Print the user id 
    print(f"{interaction.user.id} is now operating {interaction.data}")

#------ Confirm and execute ---------------------------------------------#
# Confirm and Execute the task (Create, Delete, UserData)                #
#------------------------------------------------------------------------#

class ConfirmAndExecute(View):
    
    # Initialize the class
    def __init__(self, mode, vmname, ciname, cipass, sshkey, r, vmid, timeout=config.TIME):
        
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
    
    
    # UI: Yes button
    @discord.ui.button(
        
        label="Yes",                     # UI: Yes
        
        style=discord.ButtonStyle.green, # UI: Green
        
        custom_id="yes"                  # UI: Yes
        
    )
    
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
    
    
    # UI: No button
    @discord.ui.button(
        
        label="No",                    # UI: No
        
        style=discord.ButtonStyle.red, # UI: Red
        
        custom_id="no"                 # UI: No
        
    )
    
    async def no(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: No
        
        # message: Canceled
        await interaction.response.send_message("Canceled", ephemeral=True)

#------ Operate VM power ------------------------------------------------#
# Operate the VM instance's power: Start, Shutdown, Reboot, Stop         #
#------------------------------------------------------------------------#

class OperateVMPower(View):
    
    # Initialize the class
    def __init__(self, r, vmid, ctx, timeout=config.TIME):
        
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
        
        # Update the VM status
        self.userses = UserSession(ctx)
    
    
    # Update the VM status
    async def UpdateVMStatus(self):
        
        # Get VM status
        self.status = await proxmox_ve.GetVMStatus(self.region, self.vmid)
    
    
    # UI: Start button
    @discord.ui.button(
        
        label="Start",                   # UI: Start
        
        style=discord.ButtonStyle.green, # UI: Green
        
        custom_id="start"                # UI: Start
        
    )
    
    async def StartVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Start VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # Update the VM status
            await self.UpdateVMStatus()
            
            if self.status["status"] == "stopped": # status: stopped
                
                # message: Start VM
                await interaction.response.send_message(f"User: {interaction.user.name}\nStart VM", ephemeral=True)
                
                # Start VM instance
                proxmox_ve.StartInstance(self.region, self.vmid)
                
                # Wait for task completion: task == start
                await WaitForTaskCompletion(interaction, self.vmid, "start")
                
            else: # status: running
                
                # message: VM is already running
                await interaction.response.send_message(f"User: {interaction.user.name}\nVM is already running.", ephemeral=True)

        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: Shutdown button
    @discord.ui.button(
        
        label="Shutdown",               # UI: Shutdown
        
        style=discord.ButtonStyle.gray, # UI: Gray
        
        custom_id="shutdown"            # UI: Shutdown
        
    )
    
    async def ShutdownVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Shutdown VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # Update the VM status
            await self.UpdateVMStatus()
            
            if self.status["status"] == "running": # status: running
                
                # message: Shutdown VM
                await interaction.response.send_message(f"User: {interaction.user.name}\nShutdown VM", ephemeral=True)
                
                # Shutdown VM instance
                proxmox_ve.ShutdownInstance(self.region, self.vmid)
                
                # Wait for task completion: task == shutdown
                await WaitForTaskCompletion(interaction, self.vmid, "shutdown")
                
            else: # status: stopped
                
                # message: VM is already stopped
                await interaction.response.send_message(f"User: {interaction.user.name}\nVM is already stopped.", ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: Reboot button
    @discord.ui.button(
        
        label="Reboot",                    # UI: Reboot
        
        style=discord.ButtonStyle.blurple, # UI: Blurple
        
        custom_id="reboot"                 # UI: Reboot
        
    )
    
    async def RebootVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Reboot VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # Update the VM status
            await self.UpdateVMStatus()
            
            if self.status["status"] == "running": # status: running
                
                # message: Reboot VM
                await interaction.response.send_message(f"User: {interaction.user.name}\nReboot VM", ephemeral=True)
                
                # Reboot VM instance
                proxmox_ve.RebootInstance(self.region, self.vmid)
                
                # Wait for task completion: task == reboot
                await WaitForTaskCompletion(interaction, self.vmid, "reboot")
                
            else: # status: stopped
                
                # message: VM is already stopped
                await interaction.response.send_message(f"User: {interaction.user.name}\nVM is already stopped.", ephemeral=True)

        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: Stop button
    @discord.ui.button(
        
        label="Stop",                  # UI: Stop
        
        style=discord.ButtonStyle.red, # UI: Red
        
        custom_id="stop"               # UI: Stop
        
    )
    
    async def StopVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Stop VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # Update the VM status
            await self.UpdateVMStatus()
            
            if self.status["status"] == "running": # status: running
                
                # message: Stop VM
                await interaction.response.send_message(f"User: {interaction.user.name}\nStop VM", ephemeral=True)
                
                # Stop VM instance
                proxmox_ve.StopInstance(self.region, self.vmid)
                
                # Wait for task completion: task == stop
                await WaitForTaskCompletion(interaction, self.vmid, "stop")
                
            else: # status: stopped
                
                # message: VM is already stopped
                await interaction.response.send_message(f"User: {interaction.user.name}\nVM is already stopped.", ephemeral=True)
        
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
                        
#------ Select VM Name --------------------------------------------------#
# Selected your VM Name                                                  #
#------------------------------------------------------------------------#

class SelectVMNameTab(View):
    
    # Initialize the class
    def __init__(self, ctx, mode, timeout=config.TIME):
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # mode: delete, info
        self.mode = mode
        
        # Update the user id
        self.userses = UserSession(ctx)
    
    
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
        
        if re.match(f"{interaction.user.id}", val[2]) and status != None: # Check the VM owner
            
            # Get VM IP addresses
            ipv4, ipv6 = proxmox_ve.GetVMIPAddresses(val[0], val[1])
            
            # message: Show VM info
            msg = f"VM Name: `{status['name']}`\nVMID: {status['vmid']}\nRegion: {val[0]}\nStatus: {status['status']}\nHost name: \n```bash\nvm{status['vmid']}{config.DOMAIN}\n```\nIPv4: {ipv4}\nIPv6: {ipv6}"
            
            if self.mode == "delete": # mode: delete
                
                try: # Delete VM
                    
                    if self.userses.set_current_user() == interaction.user.id: # Check the user id
                    
                        # message: Delete VM
                        await interaction.response.send_message(msg, ephemeral=True)
                        
                        # message: Do you want to delete this VM?
                        await interaction.followup.send("Do you want to delete this VM?\n(You must stop the VM before deleting it.)", ephemeral=True)
                        
                        # view: Confirm and Execute
                        await interaction.followup.send(view=ConfirmAndExecute("delete", "", "", "", "", val[0], val[1], config.TIME), ephemeral=True)
                    
                    else: # Illegal operation
                        
                        # message: Illegal operation
                        await interaction.response.send_message("Illegal operation!", ephemeral=True)
                        
                except Exception as e: # Delete Error
                    
                    print(f"Delete Error: {e}")
                
            elif self.mode == "info": # mode: info
                
                try: # Show VM info
                    
                    if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
                        # message: Show VM info
                        await interaction.response.send_message("What do you want to do with this VM?", ephemeral=True)
                        
                        # view: Operate VM power
                        await interaction.edit_original_response(content=msg, view=OperateVMPower(val[0], val[1], self.ctx, timeout=config.TIME))
                        
                    else: # Illegal operation
                        
                        # message: Illegal operation
                        await interaction.response.send_message("Illegal operation!", ephemeral=True)
                
                except Exception as e: # Show Info Error
                    
                    print(f"Info Error: {e}")
                
            else: # mode: unknown
                
                # message: Error
                await interaction.response.send_message(f"{val[1]}\nError", ephemeral=True)
                
        else: # Not the VM owner
            
            # message: You cannot operate this VM
            await interaction.response.send_message("You cannot operate this VM.", ephemeral=True)

#------ Profile configuration -------------------------------------------#
# Set up the VM's profile configuration                                  #
#------------------------------------------------------------------------#

class ProfileConfigurationForm(Modal):
    
    # Initialize the class
    def __init__(self, vmnum, title: str) -> None:
        
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
    
    
    async def on_submit(self, interaction: Interaction) -> None: # Modal: Submit button
        
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
            
        # message: Creating VM instance information (VM Name, User Name, Password, SSH Key)
        await interaction.response.send_message(msg, ephemeral=True)
        
        
        # view: Confirm and Execute
        confirm_view = ConfirmAndExecute(
                                         
            "create",        # mode: create
            
            self.vmname,     # vmname: VM Name
            
            userlist[2],     # ciname: User Name
            
            userlist[3],     # cipass: Password
            
            userlist[4],     # sshkey: SSH Key
            
            "",              # region
            
            self.clone_vm_id # vmid: VM Template ID
            
        )
        
        # message: Confirm and Execute
        await interaction.followup.send(view=confirm_view, ephemeral=True)
    
    
    async def on_error(self, interaction: Interaction, error: Exception) -> None: # Modal: Error
        
        # message: Error
        print("error: ProfileConfigurationForm")
        
        await interaction.response.send_message("Error: ProfileConfigurationForm", ephemeral=True)

    
    async def on_timeout(self) -> None: # Modal: Timeout
        
        # message: Timeout
        print("on timeout: ProfileConfigurationForm")

#------ Set User info ---------------------------------------------------#
# Set User info                                                          #
#------------------------------------------------------------------------#

class SetUserInfoForm(Modal):
    
    # Initialize the class
    def __init__(self, ctx, userdata, title: str) -> None:
        
        # title: Configure your info
        super().__init__(title=title)
        
        # ctx: context
        self.ctx = ctx
        
        # ciname: User Name
        self.ciname = TextInput(label="User Name", style=TextStyle.short, default=userdata[2], required=False)
        
        self.add_item(self.ciname) # Add item
        
        # cipass: Password
        self.cipass = TextInput(label="Password", style=TextStyle.short, default=userdata[3], required=False)
        
        self.add_item(self.cipass) # Add item
        
        # sshkey: SSH Key
        self.sshkey = TextInput(label="SSH Key", style=TextStyle.short, default=userdata[4], required=False)
        
        self.add_item(self.sshkey) # Add item
        
        # Update the user id
        self.userses = UserSession(ctx)
    
    
    async def on_submit(self, interaction: Interaction) -> None: # Modal: Submit button
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            if len(self.ciname.value) == 0 or len(self.cipass.value) == 0 or len(self.sshkey.value) == 0: # Invalid input.
                
                # message: Invalid input
                await interaction.response.send_message("Invalid input.", ephemeral=True)
                
            else: # Valid input.
                
                if self.userses.set_current_user() == interaction.user.id: # Check the user id
                
                    # message: User Name, Password, SSH Key
                    await interaction.response.send_message(f"User Name:\t{self.ciname}\nPassword:\t||{self.cipass}||\nSSH Key:\t||{self.sshkey}||\n\nDo you want to save this?", ephemeral=True)
                
                else: # Illegal operation
                    
                    # message: Illegal operation
                    await interaction.response.send_message("Illegal operation!", ephemeral=True)
                
                
                # view: Confirm and Execute
                confirm_view = ConfirmAndExecute(
                    
                    "userdata",        # mode: userdata
                    
                    "",                # vmname
                    
                    self.ciname.value, # ciname: User Name
                    
                    self.cipass.value, # cipass: Password
                    
                    self.sshkey.value, # sshkey: SSH Key
                    
                    "",                # region
                    
                    ""                 # vmid
                    
                )
                
                # message: Confirm and Execute
                await interaction.followup.send(view=confirm_view, ephemeral=True)
        
        else:
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    async def on_error(self, interaction: Interaction, error: Exception) -> None: # Modal: Error
        
        # message: Error
        print("error: SetUserInfoForm")
        
        await interaction.response.send_message("Error: SetUserInfoForm", ephemeral=True)
    
    
    async def on_timeout(self) -> None: # Modal: Timeout
        
        # message: Timeout
        print("on timeout: SetUserInfoForm")

#------ Select VM number ------------------------------------------------#
# Select VM Number                                                       #
#------------------------------------------------------------------------#

class SelectVMNumberTab(View):
    
    # Initialize the class
    def __init__(self, ctx, timeout=config.TIME):
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # Update the user id
        self.userses = UserSession(ctx)
    
    
    # UI: Select VM
    @discord.ui.select(
        
        cls=discord.ui.Select,                                                              # UI: Select VM
        
        placeholder="How many VMs do you want to create?",                                  # UI: Placeholder
        
        options=[discord.SelectOption(label=f"{i+1}", value=f"{i+1}") for i in range(0, 5)] # UI: Options

    )
    
    async def CallModal(self, interaction: discord.Interaction, select: discord.ui.Select): # Function: Call Modal
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # message: Configure your profile
            await interaction.response.send_modal(ProfileConfigurationForm(select.values[0], "Configure your profile."))

        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)

#------ Main menu -------------------------------------------------------#
# Main menu                                                              #
#------------------------------------------------------------------------#

class StartButton(View):
    
    # Initialize the class
    def __init__(self, ctx, timeout=config.TIME):
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # Update the user id
        self.userses = UserSession(ctx)
    
    
    # UI: Start button
    @discord.ui.button(
        
        label="Start",                   # UI: Start
        
        style=discord.ButtonStyle.green, # UI: Green
        
        custom_id="goto_mainmenu"        # UI: Goto Main Menu
    
    )
    
    async def StartTerrakko(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Start Terrakko
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # message: Start
            await interaction.response.send_message(view=MainMenu(self.ctx, timeout=config.TIME), ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)

#------------------------------------------------------------------------#

class MainMenu(View):
    
    # Initialize the class
    def __init__(self, ctx, timeout=config.TIME):
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx
        
        # VM List
        self.VMList = proxmox_ve.GetNodeVM(self.ctx.author.id)
        
        # Update the user id
        self.userses = UserSession(ctx)
    
    
    # UI: Create VM
    @discord.ui.button(
        
        label="Create VM",               # UI: Create VM
        
        style=discord.ButtonStyle.green, # UI: Green
        
        custom_id="create"               # UI: Create
        
    )
    
    async def CreateVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Create VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # message: Create VM
            await interaction.response.send_message(f"User: {interaction.user.id}\nCreate VM.", ephemeral=True)
            
            # View: Select VM Number
            await interaction.edit_original_response(content="How many VMs do you want to create?", view=SelectVMNumberTab(self.ctx, timeout=config.TIME))
            
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: Show VM info
    @discord.ui.button(
        
        label="Show VM info",              # UI: Show VM info
        
        style=discord.ButtonStyle.blurple, # UI: Blurple
        
        custom_id="info"                   # UI: Info
        
    )
    
    async def ShowInfo(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Show VM info
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # View: Select VM Name
            view = SelectVMNameTab("info", self.ctx, timeout=config.TIME)
            
            if len(self.VMList) == 0: # No VMs found.
                
                # message: No VMs found
                await interaction.response.send_message(f"User: {interaction.user.id}\nNo VMs found.", ephemeral=True)
                
            else: # VMs found.
                
                for vm in self.VMList[:24]: # Show VM info
                    
                    # VM Name, VM ID, Status, Region
                    view.SelectedVM.add_option(
                        
                        label=f"{vm[1]:05}: {vm[2]} | {vm[0]}",  # VM Name, User Name, Region
                        
                        value=f"{vm[0]} {vm[1]} {vm[2]} {vm[3]}" # Region, VM ID, VM Name, Status
                        
                    )
                
                # message: Show VM information
                await interaction.response.send_message(f"User: {interaction.user.id}\nShow VM info and operate VM startup.\n\nWhich VM do you want to show information?", view=view, ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: Delete VM
    @discord.ui.button(
        
        label="Delete VM",             # UI: Delete VM
        
        style=discord.ButtonStyle.red, # UI: Red
        
        custom_id="delete"             # UI: Delete
        
    )
    
    async def DeleteVM(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Delete VM
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # View: Select VM Name
            view = SelectVMNameTab("delete", self.ctx, timeout=config.TIME)
            
            if len(self.VMList) == 0: # No VMs found.
                
                # message: No VMs found
                await interaction.response.send_message(f"User: {interaction.user.id}\nNo VMs found.", ephemeral=True)
                
            else: # VMs found.
                
                for vm in self.VMList[:24]: # Delete VM
                    
                    # VM Name, VM ID, Status, Region
                    view.SelectedVM.add_option(
                        
                        label=f"{vm[1]:05}: {vm[2]} | {vm[0]}",  # VM Name, User Name, Region
                        
                        value=f"{vm[0]} {vm[1]} {vm[2]} {vm[3]}" # Region, VM ID, VM Name, Status
                        
                    )
                
                # message: Delete VM
                await interaction.response.send_message(f"User: {interaction.user.id}\nDelete VM.\n\nWhich VM do you want to delete?", view=view, ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)
    

    # UI: Configure your info
    @discord.ui.button(
        
        label="Configure your info",    # UI: Configure your info
        
        style=discord.ButtonStyle.gray, # UI: Gray
        
        custom_id="userdata"            # UI: Userdata
        
    )
    
    async def EditConf(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Configure your info
        
        if self.userses.set_current_user() == interaction.user.id:
            
            # message: Configure your info
            await interaction.response.send_modal(SetUserInfoForm(self.ctx, await db.get_userdata(interaction.user.id), "Configure your info."))
        
        else:
            
            # message: Illegal operation
            await interaction.response.send_message("Illegal operation!", ephemeral=True)

#------ Call Menu -------------------------------------------------------#
# Show menu command                                                      #
#------------------------------------------------------------------------#

# Show Menu command on Discord
@bot.command(
    
    name="!",                       # command: !
    
    description="Terrakko is here!" # Terrakko is here!
    
)

async def ShowMenu(ctx): # Show Menu command
    # Initialize PVE Info
    await proxmox_ve.InitializePVEInfo()
    
    if ctx.author.id in [row[0] for row in await db.get_column("uuid")]: # User data found
        
        # message: Hi $USER
        await ctx.send(f"Hi {ctx.author.name}!")
        
    else: # User data not found
        
        # message: Create user data
        await db.insert_data(ctx.author.id, "ncadmin", config.PVE_PASS, "")
        
        # message: Nice to meet you!
        await ctx.send(f"{ctx.author.name}, Nice to meet you!")
    
    
    print(f"now user is: {ctx.author.id}")
    
    # message: Create VM, Delete VM, Show info
    await ctx.send(f"Create VM:\tCreate a new VM\nDelete VM:\tDelete the VM\nShow VM Info:\tShow the VM information and operate VM startup\nConfigure your info: \tSet up your profile\n\nTerrakko v{config.version}\nPowered by Nekko Cloud")
    
    # View: Main Menu
    await ctx.send(view=StartButton(ctx, timeout=config.TIME))

#------ Delete Database -------------------------------------------------#
# Delete Database                                                        #
#------------------------------------------------------------------------#

class DeleteDB(View):
    
    # Initialize the class
    def __init__(self, ctx, timeout=config.TIME):
        
        # timeout = 180 sec
        super().__init__(timeout=timeout)
        
        # ctx: context
        self.ctx = ctx

        # Update the user id
        self.userses = UserSession(ctx)
    
    
    # UI: Yes button
    @discord.ui.button(
        
        label="Yes",                     # UI: Yes
        
        style=discord.ButtonStyle.green, # UI: Green
        
        custom_id="yes"                  # UI: Yes
    
    )
    
    async def yes(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: Yes
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # Delete user data
            db.delete_database()
            
            # message: User data deleted
            interaction.response.send_message("User data deleted", ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            interaction.response.send_message("Illegal operation!", ephemeral=True)
    
    
    # UI: No button
    @discord.ui.button(
        
        label="No",                    # UI: No
        
        style=discord.ButtonStyle.red, # UI: Red
        
        custom_id="no"                 # UI: No
        
    )
    
    async def no(self, interaction: discord.Interaction, button: discord.Button) -> None: # Function: No
        
        if self.userses.set_current_user() == interaction.user.id: # Check the user id
            
            # message: Canceled
            interaction.response.send_message("Canceled", ephemeral=True)
            
        else: # Illegal operation
            
            # message: Illegal operation
            interaction.response.send_message("Illegal operation!", ephemeral=True)

#------ Call database menu ----------------------------------------------#
# Delete Database command                                                #
#------------------------------------------------------------------------#

# Delete Database command on Discord
@bot.command(
    
    name="delete_db", # Command name        # command: delete_db
    
    description="Delete the all users data" # Delete the all users data
    
)

# Delete Database command
async def delete_db(ctx):
    
        # message: Delete user data
        # ctx.send("Delete user data", ephemeral=True)
        ctx.send("Not available", ephemeral=True)
        
        # View: Delete Database
        # ctx.send(view=DeleteDB(ctx, timeout=config.TIME), ephemeral=True)

#------ Start Bot -------------------------------------------------------#

# Run the bot
bot.run(config.DIS_TOKEN)

#------------------------------------------------------------------------#