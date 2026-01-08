import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  StringSelectMenuBuilder,
  StringSelectMenuOptionBuilder,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle
} from 'discord.js';
import { VM } from '../domain/vm/VM';

export class ComponentFactory {
  /**
   * スタートボタン（メインメニューへ）を作成
   */
  public static createStartButton(): ActionRowBuilder<ButtonBuilder> {
    const button = new ButtonBuilder()
      .setCustomId('goto_mainmenu')
      .setLabel('Start')
      .setStyle(ButtonStyle.Success);

    return new ActionRowBuilder<ButtonBuilder>().addComponents(button);
  }

  /**
   * メインメニューのボタンを作成
   */
  public static createMainMenuButtons(): ActionRowBuilder<ButtonBuilder> {
    const createButton = new ButtonBuilder()
      .setCustomId('create')
      .setLabel('Create VM')
      .setStyle(ButtonStyle.Success);

    const infoButton = new ButtonBuilder()
      .setCustomId('info')
      .setLabel('Show VM info')
      .setStyle(ButtonStyle.Primary);

    const deleteButton = new ButtonBuilder()
      .setCustomId('delete')
      .setLabel('Delete VM')
      .setStyle(ButtonStyle.Danger);

    const configButton = new ButtonBuilder()
      .setCustomId('userdata')
      .setLabel('Configure your info')
      .setStyle(ButtonStyle.Secondary);

    return new ActionRowBuilder<ButtonBuilder>()
      .addComponents(createButton, infoButton, deleteButton, configButton);
  }

  /**
   * 確認ボタン（Yes/No）を作成
   */
  public static createConfirmButtons(): ActionRowBuilder<ButtonBuilder> {
    const yesButton = new ButtonBuilder()
      .setCustomId('yes')
      .setLabel('Yes')
      .setStyle(ButtonStyle.Success);

    const noButton = new ButtonBuilder()
      .setCustomId('no')
      .setLabel('No')
      .setStyle(ButtonStyle.Danger);

    return new ActionRowBuilder<ButtonBuilder>().addComponents(yesButton, noButton);
  }

  /**
   * VM電源操作ボタンを作成
   */
  public static createPowerControlButtons(vm: VM): ActionRowBuilder<ButtonBuilder>[] {
    const rows: ActionRowBuilder<ButtonBuilder>[] = [];

    const startButton = new ButtonBuilder()
      .setCustomId(`power_start_${vm.vmId}`)
      .setLabel('Start')
      .setStyle(ButtonStyle.Success)
      .setDisabled(vm.isRunning());

    const shutdownButton = new ButtonBuilder()
      .setCustomId(`power_shutdown_${vm.vmId}`)
      .setLabel('Shutdown')
      .setStyle(ButtonStyle.Secondary)
      .setDisabled(vm.isStopped());

    const rebootButton = new ButtonBuilder()
      .setCustomId(`power_reboot_${vm.vmId}`)
      .setLabel('Reboot')
      .setStyle(ButtonStyle.Primary)
      .setDisabled(vm.isStopped());

    const stopButton = new ButtonBuilder()
      .setCustomId(`power_stop_${vm.vmId}`)
      .setLabel('Stop')
      .setStyle(ButtonStyle.Danger)
      .setDisabled(vm.isStopped());

    rows.push(
      new ActionRowBuilder<ButtonBuilder>().addComponents(startButton, shutdownButton, rebootButton, stopButton)
    );

    const deleteButton = new ButtonBuilder()
      .setCustomId(`delete_vm_${vm.vmId}`)
      .setLabel('Delete VM')
      .setStyle(ButtonStyle.Danger);

    rows.push(new ActionRowBuilder<ButtonBuilder>().addComponents(deleteButton));

    return rows;
  }

  /**
   * VM数選択セレクトメニューを作成
   */
  public static createVMCountSelect(): ActionRowBuilder<StringSelectMenuBuilder> {
    const select = new StringSelectMenuBuilder()
      .setCustomId('select_vm_count')
      .setPlaceholder('How many VMs do you want to create?');

    for (let i = 1; i <= 5; i++) {
      select.addOptions(
        new StringSelectMenuOptionBuilder()
          .setLabel(`${i}`)
          .setValue(i.toString())
      );
    }

    return new ActionRowBuilder<StringSelectMenuBuilder>().addComponents(select);
  }

  /**
   * VM選択セレクトメニューを作成
   */
  public static createVMSelectMenu(vms: VM[], placeholder: string = 'Select your VM'): ActionRowBuilder<StringSelectMenuBuilder> | null {
    if (vms.length === 0) {
      return null;
    }

    const select = new StringSelectMenuBuilder()
      .setCustomId('select_vm')
      .setPlaceholder(placeholder);

    // Discordのセレクトメニューは最大25オプション
    const maxOptions = Math.min(vms.length, 25);
    for (let i = 0; i < maxOptions; i++) {
      const vm = vms[i];
      select.addOptions(
        new StringSelectMenuOptionBuilder()
          .setLabel(`${vm.vmId.toString().padStart(5, '0')}: ${vm.name} | ${vm.region}`)
          .setDescription(`Status: ${vm.status}`)
          .setValue(`${vm.region} ${vm.vmId} ${vm.name} ${vm.status}`)
      );
    }

    return new ActionRowBuilder<StringSelectMenuBuilder>().addComponents(select);
  }

  /**
   * ユーザー設定モーダルを作成
   */
  public static createUserConfigModal(defaultUsername: string = '', defaultPassword: string = '', defaultSSHKey: string = ''): ModalBuilder {
    const modal = new ModalBuilder()
      .setCustomId('user_config_modal')
      .setTitle('Configure your info');

    const usernameInput = new TextInputBuilder()
      .setCustomId('username_input')
      .setLabel('User Name')
      .setStyle(TextInputStyle.Short)
      .setValue(defaultUsername)
      .setRequired(true);

    const passwordInput = new TextInputBuilder()
      .setCustomId('password_input')
      .setLabel('Password')
      .setStyle(TextInputStyle.Short)
      .setValue(defaultPassword)
      .setRequired(true);

    const sshKeyInput = new TextInputBuilder()
      .setCustomId('sshkey_input')
      .setLabel('SSH Key')
      .setStyle(TextInputStyle.Paragraph)
      .setValue(defaultSSHKey)
      .setRequired(true);

    modal.addComponents(
      new ActionRowBuilder<TextInputBuilder>().addComponents(usernameInput),
      new ActionRowBuilder<TextInputBuilder>().addComponents(passwordInput),
      new ActionRowBuilder<TextInputBuilder>().addComponents(sshKeyInput)
    );

    return modal;
  }

  /**
   * VM名入力モーダルを作成（複数VM用）
   */
  public static createVMNameModal(vmCount: number): ModalBuilder {
    const modal = new ModalBuilder()
      .setCustomId('vm_name_modal')
      .setTitle('Configure VM names');

    // 最大5つのVM名入力フィールド
    const maxFields = Math.min(vmCount, 5);
    for (let i = 0; i < maxFields; i++) {
      const vmNameInput = new TextInputBuilder()
        .setCustomId(`vmname_input_${i}`)
        .setLabel(`VM Name ${i + 1}`)
        .setStyle(TextInputStyle.Short)
        .setRequired(true);

      modal.addComponents(
        new ActionRowBuilder<TextInputBuilder>().addComponents(vmNameInput)
      );
    }

    return modal;
  }
}
