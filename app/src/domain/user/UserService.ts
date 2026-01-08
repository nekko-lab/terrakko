import { User } from './User';
import { UserDAO } from '../../infrastructure/db/UserDAO';
import { ProxmoxClient } from '../../infrastructure/proxmox/ProxmoxClient';
import { Logger } from '../../utils/Logger';
import { Config } from '../../infrastructure/config/Config';

export class UserService {
  private userDAO: UserDAO;
  private proxmoxClient: ProxmoxClient | null = null;

  constructor() {
    this.userDAO = new UserDAO();
  }

  /**
   * ProxmoxClientを設定（Tag作成に必要）
   */
  public setProxmoxClient(client: ProxmoxClient): void {
    this.proxmoxClient = client;
  }

  /**
   * Proxmox Tag IDを生成（Discordユーザー名ベース）
   */
  private generateTagId(discordUsername: string): string {
    // Tag IDは英数字とハイフン、アンダースコアのみ使用可能
    // Discordユーザー名を正規化（小文字化、特殊文字をハイフンに変換）
    const normalized = discordUsername.toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    return `user-${normalized}`;
  }

  /**
   * ユーザーを登録または更新
   */
  public async registerUser(user: User): Promise<void> {
    if (!user.isValid()) {
      throw new Error('Invalid user data');
    }

    try {
      const existing = this.userDAO.get(user.discordId);
      let tagId = user.proxmoxTagId;
      
      // Discordユーザー名が指定されている場合、Tagを作成
      if (user.discordUsername && !tagId) {
        tagId = this.generateTagId(user.discordUsername);
        
        // ProxmoxにTagを作成
        if (this.proxmoxClient) {
          try {
            await this.proxmoxClient.createTag(tagId, `User tag for ${user.discordUsername}`);
            Logger.info(`Tag created for user ${user.discordId}: ${tagId}`);
          } catch (error) {
            Logger.error(`Failed to create tag for user ${user.discordId}`, error as Error);
            // Tag作成失敗でもユーザー登録は続行（既にTagが存在する場合など）
          }
        }
      }
      
      if (existing) {
        // 既存ユーザーを更新
        this.userDAO.update(
          user.discordId,
          user.username,
          user.password,
          user.sshPublicKey,
          user.discordUsername,
          tagId
        );
        Logger.info(`User updated: ${user.discordId}`);
      } else {
        // 新規ユーザーを登録
        this.userDAO.insert(
          user.discordId,
          user.username,
          user.password,
          user.sshPublicKey,
          user.discordUsername,
          tagId
        );
        Logger.info(`User registered: ${user.discordId}`);
      }
      
      // UserオブジェクトにTag IDを設定
      user.proxmoxTagId = tagId;
    } catch (error) {
      Logger.error('Failed to register user', error as Error);
      throw error;
    }
  }

  /**
   * ユーザーを取得
   */
  public async getUser(discordId: string): Promise<User | null> {
    try {
      const userData = this.userDAO.get(discordId);
      
      if (!userData) {
        return null;
      }

      return new User(
        userData.uuid,
        userData.username,
        userData.password,
        userData.sshkey,
        userData.discord_username,
        userData.proxmox_tag_id
      );
    } catch (error) {
      Logger.error('Failed to get user', error as Error);
      return null;
    }
  }

  /**
   * ユーザーを更新
   */
  public async updateUser(user: User): Promise<void> {
    await this.registerUser(user); // registerUserが更新も行う
  }

  /**
   * ユーザーが存在するかチェック
   */
  public async userExists(discordId: string): Promise<boolean> {
    return this.userDAO.exists(discordId);
  }

  /**
   * ユーザーが存在しない場合、デフォルトユーザーを作成
   */
  public async ensureUserExists(discordId: string, defaultUsername: string = 'ncadmin', discordUsername?: string): Promise<User> {
    let user = await this.getUser(discordId);
    
    if (!user) {
      // デフォルトユーザーを作成
      user = new User(discordId, defaultUsername, Config.PVE_PASS, '', discordUsername);
      await this.registerUser(user);
    } else if (discordUsername && !user.discordUsername) {
      // 既存ユーザーにDiscordユーザー名が設定されていない場合は更新
      user.discordUsername = discordUsername;
      await this.registerUser(user);
    }

    return user;
  }
}
