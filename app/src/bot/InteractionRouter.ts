import {
  Interaction,
  ButtonInteraction,
  ModalSubmitInteraction,
  StringSelectMenuInteraction
} from 'discord.js';
import { VMService } from '../domain/vm/VMService';
import { UserService } from '../domain/user/UserService';
import { MenuBuilder } from '../ui/MenuBuilder';
import { ComponentFactory } from '../ui/ComponentFactory';
import { EmbedBuilder as CustomEmbedBuilder } from '../ui/EmbedBuilder';
import { Logger } from '../utils/Logger';
import { Validator } from '../utils/Validator';
import { SessionManager } from '../domain/session/SessionManager';
import { Session } from '../domain/session/Session';

export class InteractionRouter {
  private vmService: VMService;
  private userService: UserService;
  private sessionManager: SessionManager;

  constructor(vmService: VMService, userService: UserService) {
    this.vmService = vmService;
    this.userService = userService;
    this.sessionManager = new SessionManager();
  }

  /**
   * Interactionを処理
   */
  public async handle(interaction: Interaction): Promise<void> {
    try {
      if (interaction.isButton()) {
        await this.handleButton(interaction);
      } else if (interaction.isModalSubmit()) {
        await this.handleModal(interaction);
      } else if (interaction.isStringSelectMenu()) {
        await this.handleSelectMenu(interaction);
      }
    } catch (error) {
      Logger.error('Error handling interaction', error as Error);
      if (interaction.isRepliable() && !interaction.replied && !interaction.deferred) {
        await interaction.reply({
          embeds: [CustomEmbedBuilder.createErrorEmbed('An error occurred.')],
          ephemeral: true
        }).catch(() => {});
      }
    }
  }

  /**
   * ボタンインタラクションを処理
   */
  private async handleButton(interaction: ButtonInteraction): Promise<void> {
    const customId = interaction.customId;
    const userId = interaction.user.id;

    // メインメニュー関連
    if (customId === 'goto_mainmenu') {
      await this.showMainMenu(interaction);
      return;
    }

    if (customId === 'create') {
      await interaction.reply({
        content: `User: ${userId}\nCreate VM.`,
        ephemeral: true
      });
      await interaction.editReply({
        content: 'How many VMs do you want to create?',
        components: [ComponentFactory.createVMCountSelect()]
      });
      return;
    }

    if (customId === 'info') {
      await this.showVMInfoSelect(interaction, 'info');
      return;
    }

    if (customId === 'delete') {
      await this.showVMInfoSelect(interaction, 'delete');
      return;
    }

    if (customId === 'userdata') {
      await this.showUserConfigModal(interaction);
      return;
    }

    // 電源操作ボタン
    if (customId.startsWith('power_')) {
      await this.handlePowerControl(interaction, customId);
      return;
    }

    // 削除ボタン
    if (customId.startsWith('delete_vm_')) {
      const vmid = parseInt(customId.replace('delete_vm_', ''), 10);
      await this.showDeleteConfirm(interaction, vmid);
      return;
    }

    // 確認ボタン
    if (customId === 'yes' || customId === 'no') {
      await this.handleConfirmButton(interaction, customId);
      return;
    }
  }

  /**
   * モーダルインタラクションを処理
   */
  private async handleModal(interaction: ModalSubmitInteraction): Promise<void> {
    const customId = interaction.customId;

    if (customId === 'user_config_modal') {
      await this.handleUserConfigSubmit(interaction);
      return;
    }

    if (customId === 'vm_name_modal') {
      await this.handleVMNameSubmit(interaction);
      return;
    }
  }

  /**
   * セレクトメニューインタラクションを処理
   */
  private async handleSelectMenu(interaction: StringSelectMenuInteraction): Promise<void> {
    const customId = interaction.customId;

    if (customId === 'select_vm_count') {
      const count = parseInt(interaction.values[0], 10);
      if (Validator.isValidVMCount(count)) {
        const modal = ComponentFactory.createVMNameModal(count);
        await interaction.showModal(modal);
      }
      return;
    }

    if (customId === 'select_vm') {
      const value = interaction.values[0];
      const [, vmidStr] = value.split(' ');
      const vmid = parseInt(vmidStr, 10);

      // モーダルデータからモードを取得（簡略化のため、メッセージから判断）
      // 実際の実装ではセッション管理が必要
      await interaction.reply({
        content: 'VM selected. Processing...',
        ephemeral: true
      });

      // ここでVM情報を表示または削除確認を表示
      // 簡略化のため、VM情報を表示
      try {
        const vms = await this.vmService.listUserVMs(interaction.user.id);
        const vm = vms.find(v => v.vmId === vmid);
        if (vm) {
          const menu = MenuBuilder.buildVMInfoMenu(vm);
          await interaction.editReply({
            ...menu,
            content: 'What do you want to do with this VM?'
          });
        }
      } catch (error) {
        Logger.error('Error handling VM select', error as Error);
        await interaction.editReply({
          content: 'Failed to get VM information.',
          embeds: []
        });
      }
      return;
    }
  }

  /**
   * メインメニューを表示
   */
  private async showMainMenu(interaction: ButtonInteraction): Promise<void> {
    const userName = interaction.user.username;
    const menu = MenuBuilder.buildMainMenu(userName);
    await interaction.reply({
      ...menu,
      ephemeral: true
    });
  }

  /**
   * VM情報選択を表示
   */
  private async showVMInfoSelect(interaction: ButtonInteraction, mode: 'info' | 'delete'): Promise<void> {
    const userId = interaction.user.id;

    try {
      const vms = await this.vmService.listUserVMs(userId);

      if (vms.length === 0) {
        await interaction.reply({
          content: `User: ${userId}\nNo VMs found.`,
          ephemeral: true
        });
        return;
      }

      const selectMenu = ComponentFactory.createVMSelectMenu(
        vms,
        mode === 'info' ? 'Which VM do you want to show information?' : 'Which VM do you want to delete?'
      );

      if (!selectMenu) {
        await interaction.reply({
          content: 'Failed to create VM select menu.',
          ephemeral: true
        });
        return;
      }

      const message = mode === 'info'
        ? `User: ${userId}\nShow VM info and operate VM startup.\n\nWhich VM do you want to show information?`
        : `User: ${userId}\nDelete VM.\n\nWhich VM do you want to delete?`;

      await interaction.reply({
        content: message,
        components: [selectMenu],
        ephemeral: true
      });
    } catch (error) {
      Logger.error('Error showing VM select', error as Error);
      await interaction.reply({
        content: 'Failed to get VM list.',
        ephemeral: true
      });
    }
  }

  /**
   * ユーザー設定モーダルを表示
   */
  private async showUserConfigModal(interaction: ButtonInteraction): Promise<void> {
    try {
      const user = await this.userService.getUser(interaction.user.id);
      const modal = ComponentFactory.createUserConfigModal(
        user?.username || '',
        user?.password || '',
        user?.sshPublicKey || ''
      );
      await interaction.showModal(modal);
    } catch (error) {
      Logger.error('Error showing user config modal', error as Error);
      await interaction.reply({
        content: 'Failed to load user configuration.',
        ephemeral: true
      });
    }
  }

  /**
   * ユーザー設定モーダル送信を処理
   */
  private async handleUserConfigSubmit(interaction: ModalSubmitInteraction): Promise<void> {
    const userId = interaction.user.id;
    const username = interaction.fields.getTextInputValue('username_input');
    const password = interaction.fields.getTextInputValue('password_input');
    const sshKey = interaction.fields.getTextInputValue('sshkey_input');

    if (!Validator.isNotEmpty(username) || !Validator.isNotEmpty(password) || !Validator.isNotEmpty(sshKey)) {
      await interaction.reply({
        content: 'Invalid input. All fields are required.',
        ephemeral: true
      });
      return;
    }

    try {
      const user = await this.userService.getUser(userId);
      if (!user) {
        await interaction.reply({
          content: 'User not found.',
          ephemeral: true
        });
        return;
      }

      // セッションに保存
      const session = this.sessionManager.create(userId);
      session.set('action', 'userdata');
      session.set('username', username);
      session.set('password', password);
      session.set('sshKey', sshKey);

      await interaction.reply({
        content: `User Name:\t${username}\nPassword:\t||${password}||\nSSH Key:\t||${sshKey}||\n\nDo you want to save this?`,
        components: [ComponentFactory.createConfirmButtons()],
        ephemeral: true
      });
    } catch (error) {
      Logger.error('Error handling user config submit', error as Error);
      await interaction.reply({
        content: 'Failed to save user configuration.',
        ephemeral: true
      });
    }
  }

  /**
   * VM名モーダル送信を処理
   */
  private async handleVMNameSubmit(interaction: ModalSubmitInteraction): Promise<void> {
    const userId = interaction.user.id;
    const vmNames: string[] = [];

    // モーダルからVM名を取得（最大5つ）
    for (let i = 0; i < 5; i++) {
      const field = interaction.fields.getTextInputValue(`vmname_input_${i}`);
      if (field && field.trim().length > 0) {
        vmNames.push(field.trim());
      }
    }

    if (vmNames.length === 0) {
      await interaction.reply({
        content: 'No VM names provided.',
        ephemeral: true
      });
      return;
    }

    try {
      const user = await this.userService.getUser(userId);
      if (!user || !user.sshPublicKey || user.sshPublicKey.length === 0) {
        await interaction.reply({
          content: 'User not found or SSH key not configured.',
          ephemeral: true
        });
        return;
      }

      // VM名の重複チェック
      const duplicateNames: string[] = [];
      for (const vmName of vmNames) {
        const exists = await this.vmService.checkVMNameExists(vmName);
        if (exists) {
          duplicateNames.push(vmName);
        }
      }

      if (duplicateNames.length > 0) {
        await interaction.reply({
          content: `VM name(s) already exist: ${duplicateNames.join(', ')}\nPlease choose different name(s).`,
          ephemeral: true
        });
        return;
      }

      // 確認メッセージを表示（VM名からユーザーIDを削除）
      let msg = '';
      for (const vmName of vmNames) {
        msg += `VM Name:\t${vmName}\nUser Name:\t${user.username}\nPassword:\t||${user.password}||\nSSH Key:\t||${user.sshPublicKey}||\n\n`;
      }
      msg += 'Do you want to create this?';

      await interaction.reply({
        content: msg,
        components: [ComponentFactory.createConfirmButtons()],
        ephemeral: true
      });

      // セッションにVM作成情報を保存
      const session = this.sessionManager.create(userId);
      session.set('vmNames', vmNames);
      session.set('action', 'createVM');
    } catch (error) {
      Logger.error('Error handling VM name submit', error as Error);
      await interaction.reply({
        content: 'Failed to process VM names.',
        ephemeral: true
      });
    }
  }

  /**
   * 確認ボタンを処理
   */
  private async handleConfirmButton(interaction: ButtonInteraction, customId: string): Promise<void> {
    const userId = interaction.user.id;
    
    // ユーザーの最新セッションを取得（簡略化のため、ユーザーIDベースで検索）
    // 実際の実装では、メッセージIDとセッションを紐付ける方が良い
    let session = this.findUserSession(userId);
    if (!session) {
      await interaction.reply({
        content: 'Session expired. Please try again.',
        ephemeral: true
      });
      return;
    }

    if (customId === 'no') {
      await interaction.reply({
        content: 'Canceled',
        ephemeral: true
      });
      return;
    }

    if (customId === 'yes') {
      const action = session.get<string>('action');
      const vmNames = session.get<string[]>('vmNames');

      if (action === 'createVM' && vmNames && vmNames.length > 0) {
        await interaction.deferReply({ ephemeral: true });
        await interaction.editReply({
          content: 'Inform you here when the VM is completed.\nCreating VM...'
        });

        try {
          // VMを作成（複数VMの場合も対応）
          for (let i = 0; i < vmNames.length; i++) {
            const vmName = vmNames[i];
            
            // VMService.createVM内でVM名の重複チェックが行われる
            const createdVMs = await this.vmService.createVM({
              ownerId: userId,
              vmName: vmName,
              count: 1
            });

            if (createdVMs.length > 0) {
              Logger.info(`VM created: ${createdVMs[0].vmId} - ${createdVMs[0].name}`);
            }
          }

          await interaction.editReply({
            content: 'Tasks completed',
            embeds: [CustomEmbedBuilder.createSuccessEmbed('VM(s) created successfully.')]
          });
        } catch (error) {
          Logger.error('Error creating VM', error as Error);
          await interaction.editReply({
            content: 'Failed to create VM(s).',
            embeds: [CustomEmbedBuilder.createErrorEmbed((error as Error).message)]
          });
        }
      } else if (action === 'deleteVM') {
        const vmid = session.get<number>('vmid');
        if (vmid) {
          await interaction.deferReply({ ephemeral: true });
          await interaction.editReply({
            content: 'Inform you here when the VM is completed.\nDeleting VM...'
          });

          try {
            await this.vmService.deleteVM(vmid, userId);
            await interaction.editReply({
              content: 'Tasks completed',
              embeds: [CustomEmbedBuilder.createSuccessEmbed('VM deleted successfully.')]
            });
          } catch (error) {
            Logger.error('Error deleting VM', error as Error);
            await interaction.editReply({
              content: 'Failed to delete VM.',
              embeds: [CustomEmbedBuilder.createErrorEmbed((error as Error).message)]
            });
          }
        }
      } else if (action === 'userdata') {
        const username = session.get<string>('username');
        const password = session.get<string>('password');
        const sshKey = session.get<string>('sshKey');

        if (username && password && sshKey) {
          try {
            const user = await this.userService.getUser(userId);
            if (user) {
              user.username = username;
              user.password = password;
              user.sshPublicKey = sshKey;
              await this.userService.updateUser(user);
            }
            await interaction.reply({
              content: 'Tasks completed',
              ephemeral: true
            });
          } catch (error) {
            Logger.error('Error updating user data', error as Error);
            await interaction.reply({
              content: 'Failed to update user data.',
              ephemeral: true
            });
          }
        }
      }
    }
  }

  /**
   * 電源操作を処理
   */
  private async handlePowerControl(interaction: ButtonInteraction, customId: string): Promise<void> {
    const parts = customId.split('_');
    if (parts.length !== 3) {
      return;
    }

    const action = parts[1]; // start, stop, shutdown, reboot
    const vmid = parseInt(parts[2], 10);

    await interaction.deferReply({ ephemeral: true });

    try {
      switch (action) {
        case 'start':
          await this.vmService.powerOn(vmid);
          await interaction.editReply({
            content: `User: ${interaction.user.username}\nStart VM`,
            embeds: [CustomEmbedBuilder.createSuccessEmbed('VM started successfully.')]
          });
          break;
        case 'stop':
          await this.vmService.stop(vmid);
          await interaction.editReply({
            content: `User: ${interaction.user.username}\nStop VM`,
            embeds: [CustomEmbedBuilder.createSuccessEmbed('VM stopped successfully.')]
          });
          break;
        case 'shutdown':
          await this.vmService.shutdown(vmid);
          await interaction.editReply({
            content: `User: ${interaction.user.username}\nShutdown VM`,
            embeds: [CustomEmbedBuilder.createSuccessEmbed('VM shutdown initiated.')]
          });
          break;
        case 'reboot':
          await this.vmService.reboot(vmid);
          await interaction.editReply({
            content: `User: ${interaction.user.username}\nReboot VM`,
            embeds: [CustomEmbedBuilder.createSuccessEmbed('VM reboot initiated.')]
          });
          break;
      }
    } catch (error) {
      Logger.error('Error handling power control', error as Error);
      await interaction.editReply({
        content: 'Failed to execute power operation.',
        embeds: [CustomEmbedBuilder.createErrorEmbed((error as Error).message)]
      });
    }
  }

  /**
   * 削除確認を表示
   */
  private async showDeleteConfirm(interaction: ButtonInteraction, vmid: number): Promise<void> {
    try {
      const vms = await this.vmService.listUserVMs(interaction.user.id);
      const vm = vms.find(v => v.vmId === vmid);

      if (!vm) {
        await interaction.reply({
          content: 'VM not found.',
          ephemeral: true
        });
        return;
      }

      if (!vm.isOwner(interaction.user.id)) {
        await interaction.reply({
          content: 'You cannot operate this VM.',
          ephemeral: true
        });
        return;
      }

      // セッションに保存
      const session = this.sessionManager.create(interaction.user.id);
      session.set('action', 'deleteVM');
      session.set('vmid', vmid);

      const embed = CustomEmbedBuilder.createVMInfoEmbed(vm);
      await interaction.reply({
        embeds: [embed],
        content: 'Do you want to delete this VM?\n(You must stop the VM before deleting it.)',
        components: [ComponentFactory.createConfirmButtons()],
        ephemeral: true
      });
    } catch (error) {
      Logger.error('Error showing delete confirm', error as Error);
      await interaction.reply({
        content: 'Failed to get VM information.',
        ephemeral: true
      });
    }
  }

  /**
   * ユーザーの最新セッションを検索
   */
  private findUserSession(userId: string): Session | null {
    return this.sessionManager.getLatestSessionByUser(userId);
  }
}
