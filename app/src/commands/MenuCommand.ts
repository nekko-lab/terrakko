import { Message } from 'discord.js';
import { MenuBuilder } from '../ui/MenuBuilder';
import { ComponentFactory } from '../ui/ComponentFactory';
import { UserService } from '../domain/user/UserService';
import { Logger } from '../utils/Logger';

export class MenuCommand {
  private userService: UserService;

  constructor(userService: UserService) {
    this.userService = userService;
  }

  /**
   * メニューコマンドを実行
   */
  public async execute(message: Message): Promise<void> {
    try {
      const userId = message.author.id;
      const userName = message.author.username;
      const discordUsername = message.author.username; // Discordの固有ユーザー名

      // ユーザーが存在するか確認、存在しない場合は作成（Discordユーザー名も設定）
      const user = await this.userService.ensureUserExists(userId, 'ncadmin', discordUsername);

      // 挨拶メッセージ
      const greeting = user.sshPublicKey && user.sshPublicKey.length > 0
        ? `Hi ${userName}!`
        : `${userName}, Nice to meet you!`;

      await message.reply(greeting);

      // メインメニューを送信
      const menu = MenuBuilder.buildMainMenu(userName);
      await message.reply({
        ...menu,
        components: [...menu.components, ComponentFactory.createStartButton()]
      });

      Logger.info(`Menu displayed for user ${userId}`);
    } catch (error) {
      Logger.error('Failed to execute menu command', error as Error);
      await message.reply('An error occurred while displaying the menu.');
    }
  }
}
