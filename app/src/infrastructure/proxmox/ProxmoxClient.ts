import axios, { AxiosInstance, AxiosResponse } from 'axios';
import https from 'https';
import { Config } from '../config/Config';
import { Logger } from '../../utils/Logger';

export class ProxmoxClient {
  private axiosInstance: AxiosInstance;
  private region: string = '';
  private tempId: number = 0;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: `https://${Config.PVE_HOST}/api2/json`,
      timeout: 30000,
      httpsAgent: new https.Agent({
        rejectUnauthorized: false
      })
    });
  }

  /**
   * Proxmox APIを初期化（認証とリージョン/テンプレートIDの設定）
   */
  public async initialize(): Promise<void> {
    try {
      // Token認証の場合
      if (Config.PVE_TOKEN && Config.PVE_SECRET) {
        this.axiosInstance.defaults.headers.common['Authorization'] = 
          `PVEAPIToken=${Config.PVE_USER}!${Config.PVE_TOKEN}=${Config.PVE_SECRET}`;
      } else {
        // Password認証の場合（将来用）
        throw new Error('Password authentication not implemented. Please use token authentication.');
      }

      // リージョンとテンプレートIDをランダムに選択
      const index = Math.floor(Math.random() * Config.PVE_REGION.length);
      this.region = Config.PVE_REGION[index];
      this.tempId = Config.PVE_TEMP_ID[index];

      Logger.info(`Proxmox VE info initialized - Region: ${this.region}, Template ID: ${this.tempId}`);
    } catch (error) {
      Logger.error('Failed to initialize Proxmox VE', error as Error);
      throw error;
    }
  }

  /**
   * GETリクエスト
   */
  public async get<T = any>(path: string): Promise<T> {
    try {
      const response: AxiosResponse<any> = await this.axiosInstance.get(path);
      return (response.data as any)['data'] || response.data;
    } catch (error: any) {
      Logger.error(`GET request failed: ${path}`, error);
      throw error;
    }
  }

  /**
   * POSTリクエスト
   */
  public async post<T = any>(path: string, data?: any): Promise<T> {
    try {
      const response: AxiosResponse<any> = await this.axiosInstance.post(path, data);
      return (response.data as any)['data'] || response.data;
    } catch (error: any) {
      Logger.error(`POST request failed: ${path}`, error);
      throw error;
    }
  }

  /**
   * PUTリクエスト
   */
  public async put<T = any>(path: string, data?: any): Promise<T> {
    try {
      const response: AxiosResponse<any> = await this.axiosInstance.put(path, data);
      return (response.data as any)['data'] || response.data;
    } catch (error: any) {
      Logger.error(`PUT request failed: ${path}`, error);
      throw error;
    }
  }

  /**
   * DELETEリクエスト
   */
  public async delete<T = any>(path: string): Promise<T> {
    try {
      const response: AxiosResponse<any> = await this.axiosInstance.delete(path);
      return (response.data as any)['data'] || response.data;
    } catch (error: any) {
      Logger.error(`DELETE request failed: ${path}`, error);
      throw error;
    }
  }

  public getRegion(): string {
    return this.region;
  }

  public getTemplateId(): number {
    return this.tempId;
  }

  /**
   * Tagを作成
   * POST /api2/json/cluster/tags
   * Reference: https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/tags
   */
  public async createTag(tagId: string, comment?: string): Promise<void> {
    try {
      await this.post('/cluster/tags', {
        tagid: tagId,
        comment: comment || ''
      });
      Logger.info(`Tag created: ${tagId}`);
    } catch (error: any) {
      // Tagが既に存在する場合は無視（409 Conflict）
      if (error.response?.status === 400 && error.response?.data?.data?.includes('already exists')) {
        Logger.info(`Tag already exists: ${tagId}`);
        return;
      }
      Logger.error(`Failed to create tag: ${tagId}`, error);
      throw error;
    }
  }

  /**
   * Tagを削除
   * DELETE /api2/json/cluster/tags/{tagid}
   */
  public async deleteTag(tagId: string): Promise<void> {
    try {
      await this.delete(`/cluster/tags/${encodeURIComponent(tagId)}`);
      Logger.info(`Tag deleted: ${tagId}`);
    } catch (error) {
      Logger.error(`Failed to delete tag: ${tagId}`, error as Error);
      throw error;
    }
  }

  /**
   * Tag一覧を取得
   * GET /api2/json/cluster/tags
   */
  public async listTags(): Promise<any[]> {
    try {
      return await this.get<any[]>('/cluster/tags') || [];
    } catch (error) {
      Logger.error('Failed to list tags', error as Error);
      return [];
    }
  }
}
