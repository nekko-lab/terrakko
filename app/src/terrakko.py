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

# discord app_commands
from discord import app_commands

# discord UI
from discord.ui import TextInput, Modal, View

# discord TextStyle
from discord import TextStyle

# asyncio
import asyncio

#------ Import files ----------------------------------------------------#

# config.py
import config

# proxmox_ve.py
import proxmox_ve

#------ Initialize Bot --------------------------------------------------#

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(
    command_prefix="trk",
    case_insensitive=True,
    intents=intents,
    activity=discord.Game("Nekko Cloud")
)

#------ Bot events ------------------------------------------------------#

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(config.LOGO)
    print(f"Terrakko v{config.version} ready")
    print(f"Logged in as {bot.user}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    print(f"{interaction.user.id} triggered {interaction.data}")

#------ Helpers ---------------------------------------------------------#

async def send_dm_or_fallback(user, interaction, content):
    """Send DM to user. Falls back to ephemeral followup if DM is blocked."""
    try:
        await user.send(content)
    except discord.Forbidden:
        try:
            await interaction.followup.send(content, ephemeral=True)
        except Exception:
            print(f"Failed to notify user {user.id}: {content}")


async def monitor_and_notify(upid, user, interaction, success_msg, fail_msg):
    """Watch a PVE task in the background and notify the user on completion."""
    ok, status = await proxmox_ve.WatchTask(upid)
    exitstatus = status.get('exitstatus', 'UNKNOWN')
    message = success_msg if ok else f"{fail_msg} (exitstatus: {exitstatus})"
    await send_dm_or_fallback(user, interaction, message)


async def get_owned_vm(user_id, vmid):
    """Return vm tuple [node, vmid_int, name, status] if user owns it, else None."""
    vms = await proxmox_ve.GetNodeVM(user_id) or []
    return next((v for v in vms if str(v[1]) == str(vmid)), None)

#------ Slash command group: /vm ----------------------------------------#

vm_group = app_commands.Group(name="vm", description="VM operations")

#------ Autocomplete ----------------------------------------------------#

async def autocomplete_stopped_vms(
    interaction: discord.Interaction,
    current: str
):
    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []
    return [
        app_commands.Choice(name=f"{vm[2]} (VMID:{vm[1]})", value=str(vm[1]))
        for vm in vms
        if vm[3] == 'stopped' and current.lower() in vm[2].lower()
    ][:25]


async def autocomplete_running_vms(
    interaction: discord.Interaction,
    current: str
):
    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []
    return [
        app_commands.Choice(name=f"{vm[2]} (VMID:{vm[1]})", value=str(vm[1]))
        for vm in vms
        if vm[3] == 'running' and current.lower() in vm[2].lower()
    ][:25]


async def autocomplete_all_vms(
    interaction: discord.Interaction,
    current: str
):
    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []
    return [
        app_commands.Choice(
            name=f"{vm[2]} [{vm[3]}] (VMID:{vm[1]})",
            value=str(vm[1])
        )
        for vm in vms
        if current.lower() in vm[2].lower()
    ][:25]

#------ /vm status ------------------------------------------------------#

@vm_group.command(name="status", description="Show VM status")
@app_commands.describe(vmid="Target VM")
@app_commands.autocomplete(vmid=autocomplete_all_vms)
async def vm_status(interaction: discord.Interaction, vmid: str):
    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.response.send_message(
            "指定された VM は見つかりません（または操作権限がありません）。",
            ephemeral=True
        )
        return

    node, vmid_int, name, status = vm
    ipv4, ipv6 = await proxmox_ve.GetVMIPAddresses(node, vmid_int)

    color = discord.Color.green() if status == 'running' else discord.Color.red()
    embed = discord.Embed(title=f"VM Status: {name}", color=color)
    embed.add_field(name="VMID",      value=str(vmid_int),                    inline=True)
    embed.add_field(name="Region",    value=node,                              inline=True)
    embed.add_field(name="Status",    value=status,                            inline=True)
    embed.add_field(name="Host Name", value=f"vm{vmid_int}{config.DOMAIN}",   inline=False)
    embed.add_field(name="IPv4",      value="\n".join(ipv4) if ipv4 else "N/A", inline=True)
    embed.add_field(name="IPv6",      value="\n".join(ipv6) if ipv6 else "N/A", inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

#------ /vm start -------------------------------------------------------#

@vm_group.command(name="start", description="Start a stopped VM")
@app_commands.describe(vmid="Target VM (stopped only)")
@app_commands.autocomplete(vmid=autocomplete_stopped_vms)
async def vm_start(interaction: discord.Interaction, vmid: str):
    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.response.send_message(
            "指定された VM は見つかりません（または操作権限がありません）。",
            ephemeral=True
        )
        return

    node, vmid_int, name, _ = vm
    upid = await proxmox_ve.StartInstance(node, vmid_int)
    if upid is None:
        await interaction.response.send_message(
            f"VM {vmid_int} はすでに起動中です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"VM `{name}` (VMID:{vmid_int}) の起動を開始しました。完了したら DM でお知らせします。",
        ephemeral=True
    )
    asyncio.create_task(monitor_and_notify(
        upid, interaction.user, interaction,
        f"VM `{name}` (VMID:{vmid_int}) が起動しました。",
        f"VM `{name}` (VMID:{vmid_int}) の起動に失敗しました。"
    ))

#------ /vm stop --------------------------------------------------------#

@vm_group.command(name="stop", description="Shutdown a running VM")
@app_commands.describe(vmid="Target VM (running only)")
@app_commands.autocomplete(vmid=autocomplete_running_vms)
async def vm_stop(interaction: discord.Interaction, vmid: str):
    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.response.send_message(
            "指定された VM は見つかりません（または操作権限がありません）。",
            ephemeral=True
        )
        return

    node, vmid_int, name, _ = vm
    upid = await proxmox_ve.ShutdownInstance(node, vmid_int)
    if upid is None:
        await interaction.response.send_message(
            f"VM {vmid_int} はすでに停止中です。",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"VM `{name}` (VMID:{vmid_int}) の停止を開始しました。完了したら DM でお知らせします。",
        ephemeral=True
    )
    asyncio.create_task(monitor_and_notify(
        upid, interaction.user, interaction,
        f"VM `{name}` (VMID:{vmid_int}) が停止しました。",
        f"VM `{name}` (VMID:{vmid_int}) の停止に失敗しました。"
    ))

#------ /vm build -------------------------------------------------------#

class BuildModal(Modal, title="VM Build Configuration"):
    cpu    = TextInput(label="CPU Cores",   placeholder="2",     required=True)
    memory = TextInput(label="Memory (MB)", placeholder="2048",  required=True)
    disk   = TextInput(label="Disk (GB)",   placeholder="20",    required=True)
    ciuser = TextInput(label="Username",    placeholder="ubuntu", required=True)
    cipass = TextInput(label="Password",    style=TextStyle.short, required=True)

    def __init__(self, vm_name: str, replicas: int, sshkey: str):
        super().__init__()
        self.vm_name  = vm_name
        self.replicas = replicas
        self.sshkey   = sshkey

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"VM `{self.vm_name}` のビルドを開始しました。完了したら DM でお知らせします。",
            ephemeral=True
        )

        for i in range(self.replicas):
            name = f"{self.vm_name}-{i+1}" if self.replicas > 1 else self.vm_name
            vmid = await proxmox_ve.GetVMID()
            if vmid is None:
                await send_dm_or_fallback(
                    interaction.user, interaction,
                    f"VM `{name}` の VMID 取得に失敗しました。"
                )
                continue

            upid = await proxmox_ve.CreateInstance(
                vmid, name,
                str(self.ciuser), str(self.cipass), str(self.sshkey),
                interaction.user.id
            )
            if upid:
                asyncio.create_task(monitor_and_notify(
                    upid, interaction.user, interaction,
                    f"VM `{name}` のビルドが完了しました。",
                    f"VM `{name}` のビルドに失敗しました。"
                ))
            else:
                await send_dm_or_fallback(
                    interaction.user, interaction,
                    f"VM `{name}` のビルド開始に失敗しました。"
                )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        print(f"BuildModal error: {error}")
        await interaction.response.send_message(
            "ビルド処理中にエラーが発生しました。", ephemeral=True
        )


@vm_group.command(name="build", description="Create a new VM from template")
@app_commands.describe(name="VM name", replicas="Number of VMs to create (default: 1)", sshkey="SSH public key (optional)")
async def vm_build(interaction: discord.Interaction, name: str, replicas: int = 1, sshkey: str = ""):
    if replicas < 1 or replicas > 5:
        await interaction.response.send_message("レプリカ数は 1〜5 の間で指定してください。", ephemeral=True)
        
        return
    
    await interaction.response.send_modal(BuildModal(name, replicas, sshkey))

#------ /vm delete ------------------------------------------------------#

class DeleteConfirmView(View):

    def __init__(
        self,
        node: str,
        vmid_int: int,
        vm_name: str,
        user_id: int,
        original_interaction: discord.Interaction
    ):
        super().__init__(timeout=60)
        self.node                 = node
        self.vmid_int             = vmid_int
        self.vm_name              = vm_name
        self.user_id              = user_id
        self.original_interaction = original_interaction

    @discord.ui.button(label="削除を確定する", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Re-verify ownership before executing
        vm = await get_owned_vm(self.user_id, self.vmid_int)
        if vm is None:
            await interaction.response.send_message("所有権の確認に失敗しました。操作を中止します。", ephemeral=True)
            
            return

        upid = await proxmox_ve.DeleteInstance(self.node, self.vmid_int, self.user_id)
        if upid is None:
            await interaction.response.send_message("削除に失敗しました。VM が起動中の場合は先に `/vm stop` で停止してください。", ephemeral=True)
            
            return

        await interaction.response.send_message(
            f"VM `{self.vm_name}` (VMID:{self.vmid_int}) の削除を開始しました。完了したら DM でお知らせします。",
            ephemeral=True
        )
        asyncio.create_task(monitor_and_notify(
            upid, interaction.user, self.original_interaction,
            f"VM `{self.vm_name}` (VMID:{self.vmid_int}) を削除しました。",
            f"VM `{self.vm_name}` (VMID:{self.vmid_int}) の削除に失敗しました。"
        ))

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("削除をキャンセルしました。", ephemeral=True)

    async def on_timeout(self):
        print(f"DeleteConfirmView timed out for VM {self.vmid_int}")


@vm_group.command(name="delete", description="Delete a VM (requires confirmation)")
@app_commands.describe(vmid="Target VM")
@app_commands.autocomplete(vmid=autocomplete_all_vms)
async def vm_delete(interaction: discord.Interaction, vmid: str):
    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.response.send_message(
            "指定された VM は見つかりません（または操作権限がありません）。",
            ephemeral=True
        )
        return

    node, vmid_int, name, status = vm

    embed = discord.Embed(
        title="削除確認",
        description="**この操作は取り消せません。**",
        color=discord.Color.red()
    )
    embed.add_field(name="VM Name", value=name,          inline=True)
    embed.add_field(name="VMID",    value=str(vmid_int), inline=True)
    embed.add_field(name="Status",  value=status,        inline=True)

    await interaction.response.send_message(
        embed=embed,
        view=DeleteConfirmView(node, vmid_int, name, interaction.user.id, interaction),
        ephemeral=True
    )

#------ Register command group ------------------------------------------#

bot.tree.add_command(vm_group)

#------ Start Bot -------------------------------------------------------#

bot.run(config.DISCORD_TOKEN)

#------------------------------------------------------------------------#
