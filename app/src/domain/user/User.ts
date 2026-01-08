import { Region } from '../../types/Region';

export class User {
  public readonly discordId: string;
  public username: string;
  public sshPublicKey: string;
  public password: string;
  public discordUsername?: string;
  public proxmoxTagId?: string;
  public region?: Region;

  constructor(
    discordId: string,
    username: string,
    password: string,
    sshPublicKey: string,
    discordUsername?: string,
    proxmoxTagId?: string,
    region?: Region
  ) {
    this.discordId = discordId;
    this.username = username;
    this.password = password;
    this.sshPublicKey = sshPublicKey;
    this.discordUsername = discordUsername;
    this.proxmoxTagId = proxmoxTagId;
    this.region = region;
  }

  /**
   * ユーザーが有効かチェック（必須フィールドが設定されているか）
   */
  public isValid(): boolean {
    return (
      this.discordId.length > 0 &&
      this.username.length > 0 &&
      this.password.length > 0 &&
      this.sshPublicKey.length > 0
    );
  }
}
