export class Validator {
  /**
   * VMIDが有効かどうかをチェック（100-89999の範囲）
   */
  public static isValidVMID(vmid: number): boolean {
    return vmid >= 100 && vmid < 90000;
  }

  /**
   * 文字列が空でないかチェック
   */
  public static isNotEmpty(value: string | null | undefined): boolean {
    return value !== null && value !== undefined && value.trim().length > 0;
  }

  /**
   * SSH公開鍵の基本的な形式チェック
   */
  public static isValidSSHKey(key: string): boolean {
    if (!this.isNotEmpty(key)) {
      return false;
    }
    // 基本的なSSH公開鍵フォーマット（ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp256等）
    const sshKeyPattern = /^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521|ssh-dss)\s+[A-Za-z0-9+/=]+(\s+.+)?$/;
    return sshKeyPattern.test(key.trim());
  }

  /**
   * CPUコア数が有効かチェック（1以上の整数）
   */
  public static isValidCPU(cpu: number): boolean {
    return Number.isInteger(cpu) && cpu >= 1;
  }

  /**
   * メモリサイズが有効かチェック（1以上の整数、MB単位）
   */
  public static isValidMemory(memory: number): boolean {
    return Number.isInteger(memory) && memory >= 1;
  }

  /**
   * VM数が有効かチェック（1-5の範囲）
   */
  public static isValidVMCount(count: number): boolean {
    return Number.isInteger(count) && count >= 1 && count <= 5;
  }
}
