export class Time {
  /**
   * 秒をミリ秒に変換
   */
  public static secondsToMs(seconds: number): number {
    return seconds * 1000;
  }

  /**
   * ミリ秒を秒に変換
   */
  public static msToSeconds(ms: number): number {
    return Math.floor(ms / 1000);
  }

  /**
   * 指定された秒数だけ待機
   */
  public static async sleep(seconds: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, this.secondsToMs(seconds)));
  }

  /**
   * 現在時刻から指定秒数後のDateを取得
   */
  public static addSeconds(date: Date, seconds: number): Date {
    return new Date(date.getTime() + this.secondsToMs(seconds));
  }

  /**
   * 日時が期限切れかどうかをチェック
   */
  public static isExpired(expiresAt: Date): boolean {
    return new Date() > expiresAt;
  }
}
