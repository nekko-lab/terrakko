import { VMStatus } from '../../types/VMStatus';
import { Region } from '../../types/Region';

export class VM {
  public readonly vmId: number;
  public name: string;
  public readonly ownerDiscordId: string;
  public region: Region;
  public status: VMStatus;
  public hostname: string;
  public ipv4?: string[];
  public ipv6?: string[];

  constructor(
    vmId: number,
    name: string,
    ownerDiscordId: string,
    region: Region,
    status: VMStatus,
    hostname: string,
    ipv4?: string[],
    ipv6?: string[]
  ) {
    this.vmId = vmId;
    this.name = name;
    this.ownerDiscordId = ownerDiscordId;
    this.region = region;
    this.status = status;
    this.hostname = hostname;
    this.ipv4 = ipv4;
    this.ipv6 = ipv6;
  }

  /**
   * VMが実行中かチェック
   */
  public isRunning(): boolean {
    return this.status === VMStatus.RUNNING;
  }

  /**
   * VMが停止中かチェック
   */
  public isStopped(): boolean {
    return this.status === VMStatus.STOPPED;
  }

  /**
   * 所有者かチェック
   */
  public isOwner(discordId: string): boolean {
    return this.ownerDiscordId === discordId;
  }
}
