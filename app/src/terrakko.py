#!/usr/bin/env python3
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
from discord.ui import View

# asyncio
import asyncio

# logging
import logging

# secrets
import secrets

# string
import string

# requests (bw-agent HTTP call)
import requests

#------ Logging setup ---------------------------------------------------#
# Must be configured before importing proxmox_ve, which runs PVE
# initialization at module load time and emits log messages.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

#------ Import files ----------------------------------------------------#

# config.py
import config

# proxmox_ve.py
import proxmox_ve

#------ Initialize Bot --------------------------------------------------#

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="trk", case_insensitive=True, intents=intents, activity=discord.Game("Nekko Cloud"))

# Active DM sessions: user IDs who have run /terrakko console
active_sessions: set[int] = set()

#------ Bot events ------------------------------------------------------#

@bot.event
async def on_ready():
    if config.DISCORD_GUILD_ID:
        guild = discord.Object(id=config.DISCORD_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        logger.info("Commands synced to guild %s (immediate)", config.DISCORD_GUILD_ID)
    await bot.tree.sync()
    logger.info("Global commands synced (DM available within 1 hour)")
    logger.info(config.LOGO)
    logger.info("Terrakko v%s ready — logged in as %s", config.version, bot.user)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    cmd = interaction.data.get("name", "unknown") if interaction.data else "unknown"
    logger.debug("user %s triggered /%s", interaction.user.id, cmd)

#------ Global app command error handler --------------------------------#

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"コマンドはクールダウン中です。**{error.retry_after:.0f} 秒**後に再試行してください。",
            ephemeral=True,
        )
    else:
        logger.error("Unhandled app command error: %s", error)
        if not interaction.response.is_done():
            await interaction.response.send_message("予期しないエラーが発生しました。", ephemeral=True)

#------ Helpers ---------------------------------------------------------#

async def send_dm_or_fallback(user, interaction, content):
    """Send DM to user. Falls back to ephemeral followup if DM is blocked."""
    try:
        await user.send(content)
    except discord.Forbidden:
        try:
            await interaction.followup.send(content, ephemeral=True)
        except Exception:
            logger.warning("Failed to notify user %s", user.id)


async def monitor_and_notify(upid, user, interaction, success_msg, fail_msg):
    """Watch a PVE task in the background and notify the user on completion."""
    try:
        ok, status = await proxmox_ve.WatchTask(upid)
        exitstatus = status.get('exitstatus', 'UNKNOWN')
        message = success_msg if ok else f"{fail_msg} (exitstatus: {exitstatus})"
    except Exception as e:
        logger.error("monitor_and_notify: unexpected error for task %s: %s", upid, e)
        message = f"{fail_msg} (予期しないエラー: {e})"
    await send_dm_or_fallback(user, interaction, message)


async def get_owned_vm(user_id, vmid):
    """Return vm tuple [node, vmid_int, name, status] if user owns it, else None."""
    vms = await proxmox_ve.GetNodeVM(user_id) or []

    return next((v for v in vms if str(v[1]) == str(vmid)), None)


def generate_password(length: int = 10) -> str:
    """Generate a random alphanumeric password using secrets."""
    alphabet = string.ascii_letters + string.digits

    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def request_bw_send(password: str) -> str | None:
    """POST password to bw-agent and return the Send URL, or None on failure."""
    if not config.BW_AGENT_URL:
        return None
    try:
        resp = await asyncio.to_thread(
            requests.post,
            f"{config.BW_AGENT_URL}/send",
            json={"text": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("url")
    except Exception as e:
        logger.warning("bw-agent request failed: %s", e)

    return None


async def monitor_and_notify_build(upid, user, interaction, vm_name, vmid_int, password):
    """Watch a build task and deliver the generated password via bw-agent Send on success."""
    try:
        ok, status = await proxmox_ve.WatchTask(upid)
    except Exception as e:
        logger.error("monitor_and_notify_build: unexpected error for task %s: %s", upid, e)
        await send_dm_or_fallback(user, interaction,
            f"VM `{vm_name}` (VMID:{vmid_int}) のビルド監視中に予期しないエラーが発生しました。(error: {e})")
        return

    if not ok:
        exitstatus = status.get('exitstatus', 'UNKNOWN')
        await send_dm_or_fallback(user, interaction,
            f"VM `{vm_name}` (VMID:{vmid_int}) のビルドに失敗しました。(exitstatus: {exitstatus})")

        return

    send_url = await request_bw_send(password)
    if send_url:
        message = (f"VM `{vm_name}` (VMID:{vmid_int}) のビルドが完了しました。\n初期パスワード確認用ワンタイムリンク: {send_url}\n（このリンクは15分で失効します。リンク先でパスワードを確認してください）")
    else:
        message = (f"VM `{vm_name}` (VMID:{vmid_int}) のビルドが完了しました。\nパスワードの共有に失敗しました。PVE WebコンソールのCloud-initから変更してください。")

    await send_dm_or_fallback(user, interaction, message)


async def check_session(interaction: discord.Interaction) -> bool:
    """Return True if the user has an active DM session, otherwise reply and return False."""
    if interaction.user.id not in active_sessions:
        await interaction.response.send_message("先に `/terrakko console` を実行して DM セッションを開始してください。", ephemeral=True)

        return False

    return True

#------ Slash command groups: /terrakko ---------------------------------#

terrakko_group = app_commands.Group(name="terrakko", description="Terrakko operations")
vm_group       = app_commands.Group(name="vm",       description="VM operations")
lxc_group      = app_commands.Group(name="lxc",      description="LXC container operations (coming soon)")

#------ /terrakko help --------------------------------------------------#

def _build_help_embed() -> discord.Embed:
    embed = discord.Embed(title="Terrakko — コマンド一覧", description="まず `/terrakko console` を実行して DM セッションを開始してください。", color=discord.Color.blurple())
    embed.add_field(name="/terrakko console", value="DM セッションを開始する。VM 操作コマンドの使用前に必須。", inline=False)
    embed.add_field(name="/terrakko vm build", value=f"テンプレートから VM を作成する（CPU 最大 {config.VM_MAX_CPU} コア / メモリ最大 {config.VM_MAX_MEMORY} MB / ディスク最大 {config.VM_MAX_DISK} GB）。", inline=False)
    embed.add_field(name="/terrakko vm list", value="所有する VM の VMID・名前・ドメイン・ステータスの一覧を表示する。", inline=False)
    embed.add_field(name="/terrakko vm start", value="停止中の VM を起動する。", inline=False)
    embed.add_field(name="/terrakko vm shutdown", value="起動中の VM をグレースフルシャットダウンする（ACPI シグナル送信）。", inline=False)
    embed.add_field(name="/terrakko vm stop", value="起動中の VM を強制停止する（電源断）。", inline=False)
    embed.add_field(name="/terrakko vm status", value="VM のステータス・IP アドレスを確認する。", inline=False)
    embed.add_field(name="/terrakko vm delete", value="VM を削除する（二重確認あり）。起動中は削除不可。", inline=False)
    embed.set_footer(text="すべての操作完了通知は DM で届きます。")

    return embed


@terrakko_group.command(name="help", description="Show available commands")
async def terrakko_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=_build_help_embed(), ephemeral=True)

#------ /terrakko console -----------------------------------------------#

_CONSOLE_WELCOME = (
    "**Terrakko Console**\n"
    "DM セッションを開始しました。以降の操作はこの DM 上で行えます。\n\n"
    "**VM 操作コマンド**\n"
    "`/terrakko vm list`   — 所有する VM の一覧を表示\n"
    "`/terrakko vm build`  — テンプレートから VM を作成\n"
    "`/terrakko vm start`  — 停止中の VM を起動\n"
    "`/terrakko vm shutdown` — 起動中の VM をシャットダウン\n"
    "`/terrakko vm stop`    — 起動中の VM を強制停止\n"
    "`/terrakko vm status` — VM のステータス・IP を確認\n"
    "`/terrakko vm delete` — VM を削除\n\n"
    "コマンド一覧は `/terrakko help` で確認できます。"
)

@terrakko_group.command(name="console", description="Start a DM session with Terrakko")
async def terrakko_console(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await interaction.user.send(_CONSOLE_WELCOME)
        active_sessions.add(interaction.user.id)

        await interaction.followup.send("DM を開きました。", ephemeral=True)
        logger.info("Console session started: %s", interaction.user.id)
    except discord.Forbidden:
        await interaction.followup.send("DM を送信できませんでした。このサーバーのメンバーからの DM を許可してください。", ephemeral=True)

#------ Autocomplete ----------------------------------------------------#

async def autocomplete_stopped_vms(interaction: discord.Interaction, current: str):
    if interaction.user.id not in active_sessions:
        return []

    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []

    return [app_commands.Choice(name=f"{vm[2]} (VMID:{vm[1]})", value=str(vm[1])) for vm in vms if vm[3] == 'stopped' and current.lower() in vm[2].lower()][:25]


async def autocomplete_running_vms(interaction: discord.Interaction, current: str):
    if interaction.user.id not in active_sessions:
        return []

    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []

    return [app_commands.Choice(name=f"{vm[2]} (VMID:{vm[1]})", value=str(vm[1])) for vm in vms if vm[3] == 'running' and current.lower() in vm[2].lower()][:25]


async def autocomplete_all_vms(interaction: discord.Interaction, current: str):
    if interaction.user.id not in active_sessions:
        return []

    vms = await proxmox_ve.GetNodeVM(interaction.user.id) or []

    return [app_commands.Choice(name=f"{vm[2]} [{vm[3]}] (VMID:{vm[1]})", value=str(vm[1])) for vm in vms if current.lower() in vm[2].lower()][:25]

#------ /terrakko vm list -----------------------------------------------#

@vm_group.command(name="list", description="List all your VMs")
@app_commands.checks.cooldown(rate=5, per=30.0, key=lambda i: i.user.id)
async def vm_list(interaction: discord.Interaction):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    vms = await proxmox_ve.GetNodeVM(interaction.user.id)
    if not vms:
        await interaction.followup.send("所有している VM はありません。", ephemeral=True)
        
        return

    domain = config.DOMAIN or ""
    embed = discord.Embed(title="Your VMs", color=discord.Color.blurple())
    for node, vmid_int, name, status in vms:
        status_icon = "🟢" if status == "running" else "🔴"
        embed.add_field(name=f"{status_icon} {name}", value=f"VMID: `{vmid_int}` | Region: `{node}` | Domain: `vm{vmid_int}{domain}`", inline=False,)

    await interaction.followup.send(embed=embed, ephemeral=True)

#------ /terrakko vm status ---------------------------------------------#

@vm_group.command(name="status", description="Show VM status")
@app_commands.describe(vmid="Target VM")
@app_commands.autocomplete(vmid=autocomplete_all_vms)
@app_commands.checks.cooldown(rate=10, per=30.0, key=lambda i: i.user.id)
async def vm_status(interaction: discord.Interaction, vmid: str):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.followup.send("指定された VM は見つかりません（または操作権限がありません）。", ephemeral=True)
        return

    node, vmid_int, name, status = vm
    ipv4, ipv6 = await proxmox_ve.GetVMIPAddresses(node, vmid_int)

    color = discord.Color.green() if status == 'running' else discord.Color.red()
    embed = discord.Embed(title=f"VM Status: {name}", color=color)
    embed.add_field(name="VMID",      value=str(vmid_int),                      inline=True)
    embed.add_field(name="Region",    value=node,                               inline=True)
    embed.add_field(name="Status",    value=status,                             inline=True)
    domain = config.DOMAIN or ""
    embed.add_field(name="Host Name", value=f"vm{vmid_int}{domain}",            inline=False)
    embed.add_field(name="IPv4",      value="\n".join(ipv4) if ipv4 else "N/A", inline=True)
    embed.add_field(name="IPv6",      value="\n".join(ipv6) if ipv6 else "N/A", inline=True)

    await interaction.followup.send(embed=embed, ephemeral=True)

#------ /terrakko vm start ----------------------------------------------#

@vm_group.command(name="start", description="Start a stopped VM")
@app_commands.describe(vmid="Target VM (stopped only)")
@app_commands.autocomplete(vmid=autocomplete_stopped_vms)
@app_commands.checks.cooldown(rate=5, per=60.0, key=lambda i: i.user.id)
async def vm_start(interaction: discord.Interaction, vmid: str):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.followup.send("指定された VM は見つかりません（または操作権限がありません）。", ephemeral=True)
        return

    node, vmid_int, name, _ = vm
    upid = await proxmox_ve.StartInstance(node, vmid_int)
    if upid is None:
        await interaction.followup.send(f"VM {vmid_int} はすでに起動中です。", ephemeral=True)
        return

    await interaction.followup.send(f"VM `{name}` (VMID:{vmid_int}) の起動を開始しました。完了したら DM でお知らせします。", ephemeral=True)
    asyncio.create_task(monitor_and_notify(upid, interaction.user, interaction, f"VM `{name}` (VMID:{vmid_int}) が起動しました。", f"VM `{name}` (VMID:{vmid_int}) の起動に失敗しました。"))

#------ /terrakko vm shutdown -------------------------------------------#

@vm_group.command(name="shutdown", description="Gracefully shut down a running VM (ACPI signal)")
@app_commands.describe(vmid="Target VM (running only)")
@app_commands.autocomplete(vmid=autocomplete_running_vms)
@app_commands.checks.cooldown(rate=5, per=60.0, key=lambda i: i.user.id)
async def vm_shutdown(interaction: discord.Interaction, vmid: str):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.followup.send("指定された VM は見つかりません（または操作権限がありません）。", ephemeral=True)
        return

    node, vmid_int, name, _ = vm
    upid = await proxmox_ve.ShutdownInstance(node, vmid_int)
    if upid is None:
        await interaction.followup.send(f"VM {vmid_int} はすでに停止中です。", ephemeral=True)
        return

    await interaction.followup.send(f"VM `{name}` (VMID:{vmid_int}) のシャットダウンを開始しました。完了したら DM でお知らせします。", ephemeral=True)
    asyncio.create_task(monitor_and_notify(upid, interaction.user, interaction, f"VM `{name}` (VMID:{vmid_int}) がシャットダウンしました。", f"VM `{name}` (VMID:{vmid_int}) のシャットダウンに失敗しました。"))

#------ /terrakko vm stop -----------------------------------------------#

@vm_group.command(name="stop", description="Force stop a running VM (power off)")
@app_commands.describe(vmid="Target VM (running only)")
@app_commands.autocomplete(vmid=autocomplete_running_vms)
@app_commands.checks.cooldown(rate=5, per=60.0, key=lambda i: i.user.id)
async def vm_stop(interaction: discord.Interaction, vmid: str):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.followup.send("指定された VM は見つかりません（または操作権限がありません）。", ephemeral=True)
        return

    node, vmid_int, name, _ = vm
    upid = await proxmox_ve.StopInstance(node, vmid_int)
    if upid is None:
        await interaction.followup.send(f"VM {vmid_int} はすでに停止中です。", ephemeral=True)
        return

    await interaction.followup.send(f"VM `{name}` (VMID:{vmid_int}) の強制停止を開始しました。完了したら DM でお知らせします。", ephemeral=True)
    asyncio.create_task(monitor_and_notify(upid, interaction.user, interaction, f"VM `{name}` (VMID:{vmid_int}) が強制停止しました。", f"VM `{name}` (VMID:{vmid_int}) の強制停止に失敗しました。"))

#------ /terrakko vm build ----------------------------------------------#

@vm_group.command(name="build", description="Create a new VM from template")
@app_commands.describe(
    name="VM name",
    ciuser="Cloud-init username",
    cpu=f"CPU cores (default: 2, max: {config.VM_MAX_CPU})",
    memory=f"Memory in MB (default: 2048, max: {config.VM_MAX_MEMORY})",
    disk=f"Disk size in GB (default: 20, max: {config.VM_MAX_DISK})",
    replicas=f"Number of VMs to create (default: 1, max: {config.VM_MAX_REPLICAS})",
    sshkey="SSH public key (optional)",
)
@app_commands.checks.cooldown(rate=2, per=300.0, key=lambda i: i.user.id)
async def vm_build(
    interaction: discord.Interaction,
    name: str,
    ciuser: str,
    cpu: int = 2,
    memory: int = 2048,
    disk: int = 20,
    replicas: int = 1,
    sshkey: str = "",
):
    if not await check_session(interaction):
        return

    if not (1 <= replicas <= config.VM_MAX_REPLICAS):
        await interaction.response.send_message(f"レプリカ数は 1〜{config.VM_MAX_REPLICAS} の間で指定してください。", ephemeral=True)
        return

    if cpu < 1 or cpu > config.VM_MAX_CPU:
        await interaction.response.send_message(f"CPU は 1〜{config.VM_MAX_CPU} コアの範囲で指定してください。", ephemeral=True)
        return

    if memory < 512 or memory > config.VM_MAX_MEMORY:
        await interaction.response.send_message(f"メモリは 512〜{config.VM_MAX_MEMORY} MB の範囲で指定してください。", ephemeral=True)
        return

    if disk < 1 or disk > config.VM_MAX_DISK:
        await interaction.response.send_message(f"ディスクは 1〜{config.VM_MAX_DISK} GB の範囲で指定してください。", ephemeral=True)
        return

    await interaction.response.send_message(f"VM `{name}` のビルドを開始しました。完了したら DM でお知らせします。", ephemeral=True)

    for i in range(replicas):
        vm_name  = f"{name}-{i+1}" if replicas > 1 else name
        password = generate_password()
        vmid     = await proxmox_ve.GetVMID()
        if vmid is None:
            await send_dm_or_fallback(interaction.user, interaction, f"VM `{vm_name}` の VMID 取得に失敗しました。")
            continue

        upid = await proxmox_ve.CreateInstance(vmid, vm_name, ciuser, password, sshkey, interaction.user.id, cpu, memory, disk)
        if upid:
            asyncio.create_task(monitor_and_notify_build(upid, interaction.user, interaction, vm_name, int(vmid), password))
        else:
            await send_dm_or_fallback(interaction.user, interaction, f"VM `{vm_name}` のビルド開始に失敗しました。")

#------ /terrakko vm delete ---------------------------------------------#

class DeleteConfirmView(View):

    def __init__(self, node: str, vmid_int: int, vm_name: str, user_id: int, original_interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.node                 = node
        self.vmid_int             = vmid_int
        self.vm_name              = vm_name
        self.user_id              = user_id
        self.original_interaction = original_interaction

    @discord.ui.button(label="削除を確定する", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _button: discord.ui.Button):
        # Re-verify ownership before executing
        vm = await get_owned_vm(self.user_id, self.vmid_int)
        if vm is None:
            await interaction.response.send_message("所有権の確認に失敗しました。操作を中止します。", ephemeral=True)

            return

        node = vm[0]
        upid = await proxmox_ve.DeleteInstance(node, self.vmid_int, self.user_id)
        if upid is None:
            await interaction.response.send_message("削除に失敗しました。VM が起動中の場合は先に `/terrakko vm stop` で停止してください。", ephemeral=True)

            return

        await interaction.response.send_message(f"VM `{self.vm_name}` (VMID:{self.vmid_int}) の削除を開始しました。完了したら DM でお知らせします。", ephemeral=True)
        asyncio.create_task(monitor_and_notify(upid, interaction.user, self.original_interaction, f"VM `{self.vm_name}` (VMID:{self.vmid_int}) を削除しました。", f"VM `{self.vm_name}` (VMID:{self.vmid_int}) の削除に失敗しました。"))

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("削除をキャンセルしました。", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.original_interaction.edit_original_response(view=self)
        except Exception:
            pass
        logger.debug("DeleteConfirmView timed out for VM %s", self.vmid_int)


@vm_group.command(name="delete", description="Delete a VM (requires confirmation)")
@app_commands.describe(vmid="Target VM (stopped only)")
@app_commands.autocomplete(vmid=autocomplete_stopped_vms)
@app_commands.checks.cooldown(rate=3, per=60.0, key=lambda i: i.user.id)
async def vm_delete(interaction: discord.Interaction, vmid: str):
    if not await check_session(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    vm = await get_owned_vm(interaction.user.id, vmid)
    if vm is None:
        await interaction.followup.send("指定された VM は見つかりません（または操作権限がありません）。", ephemeral=True)
        return

    node, vmid_int, name, status = vm

    embed = discord.Embed(title="削除確認", description="**この操作は取り消せません。**", color=discord.Color.red())
    embed.add_field(name="VM Name", value=name,          inline=True)
    embed.add_field(name="VMID",    value=str(vmid_int), inline=True)
    embed.add_field(name="Status",  value=status,        inline=True)
    await interaction.followup.send(embed=embed, view=DeleteConfirmView(node, vmid_int, name, interaction.user.id, interaction), ephemeral=True)

#------ Register command groups -----------------------------------------#

terrakko_group.add_command(vm_group)
terrakko_group.add_command(lxc_group)
bot.tree.add_command(terrakko_group)

#------ Start Bot -------------------------------------------------------#

bot.run(config.DISCORD_TOKEN)

#------------------------------------------------------------------------#
