import { Client, GatewayIntentBits, Message, ActivityType } from 'discord.js';
import { Config, LOGO } from '../infrastructure/config/Config';
import { Logger } from '../utils/Logger';
import { InteractionRouter } from './InteractionRouter';
import { MenuCommand } from '../commands/MenuCommand';
import { VMService } from '../domain/vm/VMService';
import { UserService } from '../domain/user/UserService';
import { ProxmoxClient } from '../infrastructure/proxmox/ProxmoxClient';
import { ProxmoxVMAdapter } from '../infrastructure/proxmox/ProxmoxVMAdapter';

export class TerrakkoBot {
  private client: Client;
  private interactionRouter: InteractionRouter;
  private menuCommand: MenuCommand;
  private vmService: VMService;
  private userService: UserService;
  private proxmoxClient: ProxmoxClient;

  constructor() {
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
      ]
    });

    // サービス初期化
    this.proxmoxClient = new ProxmoxClient();
    const vmAdapter = new ProxmoxVMAdapter(this.proxmoxClient);
    this.userService = new UserService();
    this.userService.setProxmoxClient(this.proxmoxClient); // ProxmoxClientを設定（Tag作成に必要）
    this.vmService = new VMService(vmAdapter, this.userService);
    this.interactionRouter = new InteractionRouter(this.vmService, this.userService);
    this.menuCommand = new MenuCommand(this.userService);

    this.setupEventHandlers();
  }

  /**
   * イベントハンドラを設定
   */
  private setupEventHandlers(): void {
    this.client.once('ready', () => this.onReady());
    this.client.on('messageCreate', (message) => this.onMessage(message));
    this.client.on('interactionCreate', (interaction) => this.onInteraction(interaction));
    this.client.on('error', (error) => Logger.error('Discord client error', error));
  }

  /**
   * Bot準備完了時の処理
   */
  private async onReady(): Promise<void> {
    Logger.info(LOGO);
    Logger.info(`Nekko Cloud: ${Config.VERSION}`);
    Logger.info("Nekko Cloud's VM is available!");

    // Proxmox APIを初期化
    try {
      await this.proxmoxClient.initialize();
      Logger.info('Proxmox VE initialized');
    } catch (error) {
      Logger.error('Failed to initialize Proxmox VE', error as Error);
    }

    // アクティビティを設定
    this.client.user?.setActivity('Nekko Cloud', { type: ActivityType.Playing });
  }

  /**
   * メッセージ受信時の処理
   */
  private async onMessage(message: Message): Promise<void> {
    // Bot自身のメッセージは無視
    if (message.author.bot) {
      return;
    }

    // プレフィックスコマンドをチェック（"trk!" またはメンション）
    const prefix = 'trk!';
    const isMentioned = message.mentions.has(this.client.user!);
    const hasPrefix = message.content.startsWith(prefix);

    if (isMentioned || hasPrefix) {
      const command = hasPrefix
        ? message.content.slice(prefix.length).trim()
        : message.content.replace(`<@!?${this.client.user?.id}>`, '').trim();

      if (command === '!' || command === '') {
        await this.menuCommand.execute(message);
      }
    }
  }

  /**
   * Interaction受信時の処理
   */
  private async onInteraction(interaction: any): Promise<void> {
    Logger.info(`${interaction.user.id} is now operating ${interaction.type}`);
    await this.interactionRouter.handle(interaction);
  }

  /**
   * Botをログイン
   */
  public async login(): Promise<void> {
    try {
      await this.client.login(Config.DIS_TOKEN);
    } catch (error) {
      Logger.error('Failed to login', error as Error);
      throw error;
    }
  }

  /**
   * Botを終了
   */
  public async destroy(): Promise<void> {
    this.client.destroy();
  }
}
