import { ProxmoxClient } from './ProxmoxClient';
import { VMStatus } from '../../types/VMStatus';
import { Region } from '../../types/Region';
import { Validator } from '../../utils/Validator';
import { Logger } from '../../utils/Logger';
import { Time } from '../../utils/Time';
import * as querystring from 'querystring';

export interface VMInfo {
  vmid: number;
  name: string;
  status: VMStatus;
  region: string;
}

export interface VMStatusResponse {
  status: VMStatus;
  vmid: number;
  name: string;
  [key: string]: any;
}

export interface VMIPAddress {
  ipv4: string[];
  ipv6: string[];
}

export interface VMAdapter {
  cloneTemplate(vmid: number, vmName: string, ciUser: string, ciPassword: string, sshKey: string, tagId?: string): Promise<void>;
  start(region: Region, vmid: number): Promise<void>;
  stop(region: Region, vmid: number): Promise<void>;
  shutdown(region: Region, vmid: number): Promise<void>;
  reboot(region: Region, vmid: number): Promise<void>;
  delete(region: Region, vmid: number): Promise<void>;
  getStatus(region: Region, vmid: number): Promise<VMStatusResponse | null>;
  getIPAddresses(region: Region, vmid: number): Promise<VMIPAddress | null>;
  getVMConfig(region: Region, vmid: number): Promise<any>;
  getNextVMID(): Promise<number | null>;
  listUserVMs(tagId: string): Promise<VMInfo[]>;
  checkVMNameExists(vmName: string): Promise<boolean>;
}

export class ProxmoxVMAdapter implements VMAdapter {
  private client: ProxmoxClient;

  constructor(client: ProxmoxClient) {
    this.client = client;
  }

  /**
   * タスクの完了を待機
   */
  private async waitForTask(taskUpid: string, maxWait: number = 300): Promise<void> {
    const startTime = Date.now();
    const maxWaitMs = maxWait * 1000;

    while (Date.now() - startTime < maxWaitMs) {
      try {
        const [node, taskId] = taskUpid.split(':');
        const taskStatus = await this.client.get<any>(`/nodes/${node}/tasks/${taskId}/status`);
        
        if (taskStatus.status === 'stopped') {
          if (taskStatus.exitstatus === 'OK') {
            return;
          } else {
            throw new Error(`Task failed: ${taskStatus.exitstatus}`);
          }
        }

        await Time.sleep(2);
      } catch (error) {
        Logger.error('Error waiting for task', error as Error);
        await Time.sleep(2);
      }
    }

    throw new Error('Task timeout');
  }

  /**
   * VM名の重複をチェック
   */
  public async checkVMNameExists(vmName: string): Promise<boolean> {
    try {
      const nodes = await this.client.get<any[]>('/nodes');
      
      for (const node of nodes) {
        const vms = await this.client.get<any[]>(`/nodes/${node.node}/qemu`).catch(() => []);
        
        for (const vm of vms) {
          if (vm.name === vmName) {
            return true;
          }
        }
      }
      
      return false;
    } catch (error) {
      Logger.error('Failed to check VM name existence', error as Error);
      throw error;
    }
  }

  /**
   * テンプレートからVMをクローンして作成
   */
  public async cloneTemplate(
    vmid: number,
    vmName: string,
    ciUser: string,
    ciPassword: string,
    sshKey: string,
    tagId?: string
  ): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const region = this.client.getRegion();
      const templateId = this.client.getTemplateId();

      Logger.info(`Cloning VM - Template ID: ${templateId}, New VMID: ${vmid}, Name: ${vmName}`);

      // クローン実行
      const cloneResult = await this.client.post<{ data: string }>(
        `/nodes/${region}/qemu/${templateId}/clone`,
        {
          newid: vmid,
          name: vmName,
          pool: 'dev'
        }
      );

      const taskUpid = cloneResult.data || cloneResult as any;
      await this.waitForTask(typeof taskUpid === 'string' ? taskUpid : taskUpid.upid);

      Logger.info(`VM cloned: ${vmid}`);

      // Tagを設定（指定されている場合）
      if (tagId) {
        await this.setVMTags(region, vmid, tagId);
      }

      // Cloud-init設定
      await this.initializeInstance(vmid, ciUser, ciPassword, sshKey);
    } catch (error) {
      Logger.error('Failed to clone template', error as Error);
      throw error;
    }
  }

  /**
   * VMにTagを設定
   * PUT /api2/json/nodes/{node}/qemu/{vmid}/config
   * Reference: https://pve.proxmox.com/pve-docs/api-viewer/#/nodes/{node}/qemu/{vmid}/config
   */
  private async setVMTags(region: Region, vmid: number, tagId: string): Promise<void> {
    try {
      // VMの現在の設定を取得
      const currentConfig = await this.client.get<any>(`/nodes/${region}/qemu/${vmid}/config`);
      const currentTags = currentConfig.tags ? currentConfig.tags.split(',') : [];
      
      // 既にタグが設定されている場合は追加、そうでなければ新規設定
      if (!currentTags.includes(tagId)) {
        currentTags.push(tagId);
        const tagsString = currentTags.join(',');
        
        await this.client.put(`/nodes/${region}/qemu/${vmid}/config`, {
          tags: tagsString
        });
        Logger.info(`Tag ${tagId} set for VM ${vmid}`);
      }
    } catch (error) {
      Logger.error(`Failed to set tag for VM ${vmid}`, error as Error);
      throw error;
    }
  }

  /**
   * VMを初期化（Cloud-init設定と起動）
   */
  private async initializeInstance(vmid: number, ciUser: string, ciPassword: string, sshKey: string): Promise<void> {
    try {
      const region = this.client.getRegion();

      Logger.info(`Initializing VM: ${vmid}`);

      // SSH鍵をURLエンコード
      const encodedSSHKey = querystring.escape(sshKey);

      // Cloud-init設定
      await this.client.put(
        `/nodes/${region}/qemu/${vmid}/config`,
        {
          ciuser: ciUser,
          cipassword: ciPassword,
          sshkeys: encodedSSHKey
        }
      );

      // VM起動
      const startResult = await this.client.post<{ data: string }>(
        `/nodes/${region}/qemu/${vmid}/status/start`
      );

      const taskUpid = startResult.data || startResult as any;
      await this.waitForTask(typeof taskUpid === 'string' ? taskUpid : taskUpid.upid);

      Logger.info(`VM initialized and started: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to initialize VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを起動
   */
  public async start(region: Region, vmid: number): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const status = await this.getStatus(region, vmid);
      if (!status) {
        throw new Error('VM not found');
      }

      if (status.status === VMStatus.RUNNING) {
        Logger.info(`VM ${vmid} is already running`);
        return;
      }

      Logger.info(`Starting VM: ${vmid}`);
      const result = await this.client.post<{ data: string }>(
        `/nodes/${region}/qemu/${vmid}/status/start`
      );

      const taskUpid = result.data || result as any;
      await this.waitForTask(typeof taskUpid === 'string' ? taskUpid : taskUpid.upid);

      Logger.info(`VM started: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to start VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを停止（強制停止）
   */
  public async stop(region: Region, vmid: number): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const status = await this.getStatus(region, vmid);
      if (!status) {
        throw new Error('VM not found');
      }

      if (status.status === VMStatus.STOPPED) {
        Logger.info(`VM ${vmid} is already stopped`);
        return;
      }

      Logger.info(`Stopping VM: ${vmid}`);
      const result = await this.client.post<{ data: string }>(
        `/nodes/${region}/qemu/${vmid}/status/stop`
      );

      const taskUpid = result.data || result as any;
      await this.waitForTask(typeof taskUpid === 'string' ? taskUpid : taskUpid.upid);

      Logger.info(`VM stopped: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to stop VM', error as Error);
      throw error;
    }
  }

  /**
   * VMをシャットダウン（正常停止）
   */
  public async shutdown(region: Region, vmid: number): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const status = await this.getStatus(region, vmid);
      if (!status) {
        throw new Error('VM not found');
      }

      if (status.status !== VMStatus.RUNNING) {
        Logger.info(`VM ${vmid} is not running`);
        return;
      }

      Logger.info(`Shutting down VM: ${vmid}`);
      await this.client.post(`/nodes/${region}/qemu/${vmid}/status/shutdown`);
      
      // シャットダウンは非同期なので少し待つ
      await Time.sleep(5);

      Logger.info(`VM shutdown initiated: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to shutdown VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを再起動
   */
  public async reboot(region: Region, vmid: number): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const status = await this.getStatus(region, vmid);
      if (!status) {
        throw new Error('VM not found');
      }

      if (status.status !== VMStatus.RUNNING) {
        Logger.info(`VM ${vmid} is not running`);
        return;
      }

      Logger.info(`Rebooting VM: ${vmid}`);
      await this.client.post(`/nodes/${region}/qemu/${vmid}/status/reboot`);

      Logger.info(`VM reboot initiated: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to reboot VM', error as Error);
      throw error;
    }
  }

  /**
   * VMを削除
   */
  public async delete(region: Region, vmid: number): Promise<void> {
    if (!Validator.isValidVMID(vmid)) {
      throw new Error('Invalid VM ID');
    }

    try {
      const status = await this.getStatus(region, vmid);
      if (!status) {
        throw new Error('VM not found');
      }

      if (status.status !== VMStatus.STOPPED) {
        throw new Error(`VM ${vmid} is running, please stop it first!`);
      }

      Logger.info(`Deleting VM: ${vmid}`);
      const result = await this.client.delete<{ data: string }>(
        `/nodes/${region}/qemu/${vmid}`
      );

      const taskUpid = result.data || result as any;
      await this.waitForTask(typeof taskUpid === 'string' ? taskUpid : taskUpid.upid);

      Logger.info(`VM deleted: ${vmid}`);
    } catch (error) {
      Logger.error('Failed to delete VM', error as Error);
      throw error;
    }
  }

  /**
   * VMのステータスを取得
   */
  public async getStatus(region: Region, vmid: number): Promise<VMStatusResponse | null> {
    try {
      const response = await this.client.get<VMStatusResponse>(
        `/nodes/${region}/qemu/${vmid}/status/current`
      );
      return response;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      Logger.error('Failed to get VM status', error);
      return null;
    }
  }

  /**
   * VMのIPアドレスを取得
   */
  public async getIPAddresses(region: Region, vmid: number): Promise<VMIPAddress | null> {
    try {
      const interfaces = await this.client.get<any>(
        `/nodes/${region}/qemu/${vmid}/agent/network-get-interfaces`
      );

      const ipv4Addresses: string[] = [];
      const ipv6Addresses: string[] = [];

      if (interfaces.result) {
        for (const iface of interfaces.result) {
          if (iface['ip-addresses']) {
            for (const ip of iface['ip-addresses']) {
              if (ip['ip-address-type'] === 'ipv4') {
                ipv4Addresses.push(ip['ip-address']);
              } else if (ip['ip-address-type'] === 'ipv6') {
                ipv6Addresses.push(ip['ip-address']);
              }
            }
          }
        }
      }

      return { ipv4: ipv4Addresses, ipv6: ipv6Addresses };
    } catch (error: any) {
      Logger.error('Failed to get VM IP addresses', error);
      return null;
    }
  }

  /**
   * VM設定を取得（Tag情報含む）
   * GET /api2/json/nodes/{node}/qemu/{vmid}/config
   */
  public async getVMConfig(region: Region, vmid: number): Promise<any> {
    try {
      return await this.client.get<any>(`/nodes/${region}/qemu/${vmid}/config`);
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      Logger.error('Failed to get VM config', error);
      return null;
    }
  }

  /**
   * 次の利用可能なVMIDを取得
   */
  public async getNextVMID(): Promise<number | null> {
    try {
      const response = await this.client.get<{ data: string }>('/cluster/nextid');
      const vmid = parseInt(response.data || response as any, 10);
      return isNaN(vmid) ? null : vmid;
    } catch (error) {
      Logger.error('Failed to get next VM ID', error as Error);
      return null;
    }
  }

  /**
   * ユーザーのVM一覧を取得（Tagでフィルタリング）
   */
  public async listUserVMs(tagId: string): Promise<VMInfo[]> {
    try {
      const nodes = await this.client.get<any[]>('/nodes');
      const vmList: VMInfo[] = [];

      for (const node of nodes) {
        // TagでフィルタリングしてVMを取得
        // GET /api2/json/nodes/{node}/qemu?tags={tagId}
        const vms = await this.client.get<any[]>(`/nodes/${node.node}/qemu?tags=${encodeURIComponent(tagId)}`).catch(() => []);

        for (const vm of vms) {
          const vmid = parseInt(vm.vmid, 10);
          if (Validator.isValidVMID(vmid)) {
            // Tagが含まれているか確認（APIのフィルタリングが完璧でない場合の保険）
            const vmTags = vm.tags ? vm.tags.split(',') : [];
            if (vmTags.includes(tagId)) {
              vmList.push({
                vmid: vmid,
                name: vm.name,
                status: vm.status === 'running' ? VMStatus.RUNNING : VMStatus.STOPPED,
                region: node.node
              });
            }
          }
        }
      }

      // VMIDでソート
      vmList.sort((a, b) => a.vmid - b.vmid);

      return vmList;
    } catch (error) {
      Logger.error('Failed to list user VMs', error as Error);
      return [];
    }
  }
}
