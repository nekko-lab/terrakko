import { VM } from './VM';

/**
 * VMリポジトリインターフェース（将来用）
 * v1ではProxmoxから直接取得するため、実装は将来追加
 */
export interface VMRepository {
  save(vm: VM): Promise<void>;
  findById(vmId: number): Promise<VM | null>;
  findByOwner(discordId: string): Promise<VM[]>;
  delete(vmId: number): Promise<void>;
}
