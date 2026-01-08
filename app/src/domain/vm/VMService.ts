import { VM } from './VM';
import { VMAdapter } from '../../infrastructure/proxmox/ProxmoxVMAdapter';
import { UserService } from '../user/UserService';
import { VMStatus } from '../../types/VMStatus';
import { Region } from '../../types/Region';
import { Config } from '../../infrastructure/config/Config';
import { Logger } from '../../utils/Logger';
import { Validator } from '../../utils/Validator';

export interface CreateVMParams {
  ownerId: string;
  vmName: string;
  count: number;
  cpu?: number;
  memory?: number;
}

export class VMService {
  private vmAdapter: VMAdapter;
  private userService: UserService;

  constructor(vmAdapter: VMAdapter, userService: UserService) {
    this.vmAdapter = vmAdapter;
    this.userService = userService;
  }

  /**
   * VMを作成
   */
  public async createVM(params: CreateVMParams): Promise<VM[]> {
    if (!Validator.isValidVMCount(params.count)) {
      throw new Error('Invalid VM count (must be 1-5)');
    }

    // ユーザー情報を取得
    const user = await this.userService.getUser(params.ownerId);
    if (!user || !user.sshPublicKey || user.sshPublicKey.length === 0) {
      throw new Error('User not found or SSH key not configured');
    }

    if (!user.proxmoxTagId) {
      throw new Error('User does not have a Proxmox tag. Please configure your Discord username first.');
    }

    const createdVMs: VM[] = [];

    try {
      // VM名の重複チェック（複数作成の場合もチェック）
      const vmNames: string[] = [];
      for (let i = 0; i < params.count; i++) {
        const vmName = params.count === 1 ? params.vmName : `${params.vmName}-${i + 1}`;
        vmNames.push(vmName);
        
        // VM名の重複をチェック
        const exists = await this.vmAdapter.checkVMNameExists(vmName);
        if (exists) {
          throw new Error(`VM name "${vmName}" already exists. Please choose a different name.`);
        }
      }

      for (let i = 0; i < params.count; i++) {
        // VMIDを取得
        const vmid = await this.vmAdapter.getNextVMID();
        if (!vmid) {
          throw new Error('Failed to get next VM ID');
        }

        // VM名（ユーザー入力のみ、重複チェック済み）
        const vmName = vmNames[i];
        
        // VMをクローンして作成（Tag付与）
        await this.vmAdapter.cloneTemplate(
          vmid,
          vmName,
          user.username,
          user.password,
          user.sshPublicKey,
          user.proxmoxTagId
        );

        // VM情報を取得
        const region = await this.getRegion();
        const status = await this.vmAdapter.getStatus(region, vmid);
        
        if (!status) {
          throw new Error('Failed to get VM status after creation');
        }

        const hostname = `vm${vmid}${Config.DOMAIN}`;
        const vm = new VM(
          vmid,
          vmName,
          params.ownerId,
          region,
          status.status === 'running' ? VMStatus.RUNNING : VMStatus.STOPPED,
          hostname
        );

        createdVMs.push(vm);
        
        // 複数作成時は少し待機
        if (i < params.count - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      Logger.info(`Created ${createdVMs.length} VMs for user ${params.ownerId}`);
      return createdVMs;
    } catch (error) {
      Logger.error('Failed to create VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを削除
   */
  public async deleteVM(vmId: number, requesterId: string): Promise<void> {
    // VM情報を取得して所有者チェック
    const vm = await this.getVM(vmId);
    if (!vm) {
      throw new Error('VM not found');
    }

    if (!vm.isOwner(requesterId)) {
      throw new Error('Permission denied: You can only delete your own VMs');
    }

    try {
      await this.vmAdapter.delete(vm.region, vmId);
      Logger.info(`VM deleted: ${vmId} by user ${requesterId}`);
    } catch (error) {
      Logger.error('Failed to delete VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを起動
   */
  public async powerOn(vmId: number): Promise<void> {
    const vm = await this.getVM(vmId);
    if (!vm) {
      throw new Error('VM not found');
    }

    try {
      await this.vmAdapter.start(vm.region, vmId);
      Logger.info(`VM started: ${vmId}`);
    } catch (error) {
      Logger.error('Failed to start VM', error as Error);
      throw error;
    }
  }

  /**
   * VMをシャットダウン
   */
  public async shutdown(vmId: number): Promise<void> {
    const vm = await this.getVM(vmId);
    if (!vm) {
      throw new Error('VM not found');
    }

    try {
      await this.vmAdapter.shutdown(vm.region, vmId);
      Logger.info(`VM shutdown: ${vmId}`);
    } catch (error) {
      Logger.error('Failed to shutdown VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを再起動
   */
  public async reboot(vmId: number): Promise<void> {
    const vm = await this.getVM(vmId);
    if (!vm) {
      throw new Error('VM not found');
    }

    try {
      await this.vmAdapter.reboot(vm.region, vmId);
      Logger.info(`VM rebooted: ${vmId}`);
    } catch (error) {
      Logger.error('Failed to reboot VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを停止（強制停止）
   */
  public async stop(vmId: number): Promise<void> {
    const vm = await this.getVM(vmId);
    if (!vm) {
      throw new Error('VM not found');
    }

    try {
      await this.vmAdapter.stop(vm.region, vmId);
      Logger.info(`VM stopped: ${vmId}`);
    } catch (error) {
      Logger.error('Failed to stop VM', error as Error);
      throw error;
    }
  }

  /**
   * ユーザーのVM一覧を取得（Tagベース）
   */
  public async listUserVMs(discordId: string): Promise<VM[]> {
    try {
      // ユーザー情報を取得してTag IDを取得
      const user = await this.userService.getUser(discordId);
      if (!user || !user.proxmoxTagId) {
        return [];
      }

      const vmInfos = await this.vmAdapter.listUserVMs(user.proxmoxTagId);
      const vms: VM[] = [];

      for (const info of vmInfos) {
        const status = await this.vmAdapter.getStatus(info.region, info.vmid);
        if (!status) {
          continue;
        }

        const hostname = `vm${info.vmid}${Config.DOMAIN}`;
        const ipAddresses = await this.vmAdapter.getIPAddresses(info.region, info.vmid);

        const vm = new VM(
          info.vmid,
          info.name,
          discordId,
          info.region,
          status.status === 'running' ? VMStatus.RUNNING : VMStatus.STOPPED,
          hostname,
          ipAddresses?.ipv4,
          ipAddresses?.ipv6
        );

        vms.push(vm);
      }

      return vms;
    } catch (error) {
      Logger.error('Failed to list user VMs', error as Error);
      return [];
    }
  }

  /**
   * VM情報を取得（Tagから所有者を判定）
   */
  private async getVM(vmId: number): Promise<VM | null> {
    try {
      // すべてのリージョンから検索
      const regions = Config.PVE_REGION;
      
      for (const region of regions) {
        const status = await this.vmAdapter.getStatus(region, vmId);
        if (status) {
          const hostname = `vm${vmId}${Config.DOMAIN}`;
          const ipAddresses = await this.vmAdapter.getIPAddresses(region, vmId);
          
          // VMの設定を取得してTagを確認
          // VM設定からTagを取得するために、VM一覧から検索する方法を使用
          // または、VM設定APIを呼び出す必要がある
          // 簡略化のため、全ユーザーから検索
          const ownerId = await this.findOwnerByVM(region, vmId);

          return new VM(
            vmId,
            status.name,
            ownerId || 'unknown',
            region,
            status.status === 'running' ? VMStatus.RUNNING : VMStatus.STOPPED,
            hostname,
            ipAddresses?.ipv4,
            ipAddresses?.ipv6
          );
        }
      }

      return null;
    } catch (error) {
      Logger.error('Failed to get VM', error as Error);
      return null;
    }
  }

  /**
   * VMのTagから所有者を検索
   */
  private async findOwnerByVM(region: Region, vmId: number): Promise<string | null> {
    try {
      // VM設定を取得してTagを確認
      const config = await this.vmAdapter.getVMConfig(region, vmId);
      if (!config || !config.tags) {
        return null;
      }

      const tags = config.tags.split(',');
      const { UserDAO } = await import('../../infrastructure/db/UserDAO');
      const userDAO = new UserDAO();

      // Tagから所有者を検索
      for (const tag of tags) {
        const userData = userDAO.getByTagId(tag.trim());
        if (userData) {
          return userData.uuid;
        }
      }

      return null;
    } catch (error) {
      Logger.error('Failed to find owner by VM', error as Error);
      return null;
    }
  }

  /**
   * VM名の重複チェック
   */
  public async checkVMNameExists(vmName: string): Promise<boolean> {
    return await this.vmAdapter.checkVMNameExists(vmName);
  }

  /**
   * リージョンを取得（ランダム選択、将来的にはユーザー設定から取得）
   */
  private async getRegion(): Promise<Region> {
    const regions = Config.PVE_REGION;
    const index = Math.floor(Math.random() * regions.length);
    return regions[index];
  }
}
