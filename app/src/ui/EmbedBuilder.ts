import { EmbedBuilder as DiscordEmbedBuilder, ColorResolvable } from 'discord.js';
import { Config } from '../infrastructure/config/Config';
import { VM } from '../domain/vm/VM';

export class EmbedBuilder {
  /**
   * メインメニューのEmbedを作成
   */
  public static createMainMenuEmbed(userName: string): DiscordEmbedBuilder {
    return new DiscordEmbedBuilder()
      .setTitle('Terrakko - VM Management')
      .setDescription(`Hi ${userName}!\n\nCreate VM:\tCreate a new VM\nDelete VM:\tDelete the VM\nShow VM Info:\tShow the VM information and operate VM startup\nConfigure your info:\tSet up your profile`)
      .setFooter({ text: `Terrakko v${Config.VERSION}\nPowered by Nekko Cloud` })
      .setColor(0x5865F2);
  }

  /**
   * VM情報のEmbedを作成
   */
  public static createVMInfoEmbed(vm: VM): DiscordEmbedBuilder {
    const embed = new DiscordEmbedBuilder()
      .setTitle(`VM Information: ${vm.name}`)
      .addFields(
        { name: 'VMID', value: vm.vmId.toString(), inline: true },
        { name: 'Region', value: vm.region, inline: true },
        { name: 'Status', value: vm.status, inline: true },
        { name: 'Hostname', value: `\`\`\`bash\n${vm.hostname}\n\`\`\``, inline: false }
      )
      .setColor(this.getStatusColor(vm.status));

    if (vm.ipv4 && vm.ipv4.length > 0) {
      embed.addFields({ name: 'IPv4', value: vm.ipv4.join(', '), inline: false });
    }

    if (vm.ipv6 && vm.ipv6.length > 0) {
      embed.addFields({ name: 'IPv6', value: vm.ipv6.join(', '), inline: false });
    }

    return embed;
  }

  /**
   * ステータスに応じた色を取得
   */
  private static getStatusColor(status: string): ColorResolvable {
    switch (status) {
      case 'running':
        return 0x57F287; // Green
      case 'stopped':
        return 0xED4245; // Red
      case 'paused':
        return 0xFEE75C; // Yellow
      default:
        return 0x5865F2; // Blurple
    }
  }

  /**
   * エラーメッセージのEmbedを作成
   */
  public static createErrorEmbed(message: string): DiscordEmbedBuilder {
    return new DiscordEmbedBuilder()
      .setTitle('Error')
      .setDescription(message)
      .setColor(0xED4245); // Red
  }

  /**
   * 成功メッセージのEmbedを作成
   */
  public static createSuccessEmbed(message: string): DiscordEmbedBuilder {
    return new DiscordEmbedBuilder()
      .setTitle('Success')
      .setDescription(message)
      .setColor(0x57F287); // Green
  }
}
