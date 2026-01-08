import { Session } from './Session';
import { Config } from '../../infrastructure/config/Config';
import { Time } from '../../utils/Time';
import { Logger } from '../../utils/Logger';
import * as crypto from 'crypto';

export class SessionManager {
  private sessions: Map<string, Session> = new Map();
  private cleanupInterval: NodeJS.Timeout | null = null;
  private readonly TTL_SECONDS = Config.TIME; // 180秒

  constructor() {
    // 定期的に期限切れセッションをクリーンアップ（60秒ごと）
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60000);
  }

  /**
   * 新しいセッションを作成
   */
  public create(discordId: string): Session {
    const sessionId = this.generateSessionId();
    const expiresAt = Time.addSeconds(new Date(), this.TTL_SECONDS);

    const session = new Session(sessionId, discordId, expiresAt);
    this.sessions.set(sessionId, session);

    Logger.debug(`Session created: ${sessionId} for user ${discordId}`);
    return session;
  }

  /**
   * セッションIDからセッションを取得
   */
  public get(sessionId: string): Session | null {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      return null;
    }

    if (session.isExpired()) {
      this.sessions.delete(sessionId);
      return null;
    }

    return session;
  }

  /**
   * セッションIDとユーザーIDが一致するか検証
   */
  public validate(sessionId: string, discordId: string): boolean {
    const session = this.get(sessionId);
    
    if (!session) {
      return false;
    }

    return session.ownerDiscordId === discordId;
  }

  /**
   * セッションを削除
   */
  public delete(sessionId: string): boolean {
    return this.sessions.delete(sessionId);
  }

  /**
   * ユーザーのセッションをすべて削除
   */
  public deleteByUser(discordId: string): void {
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.ownerDiscordId === discordId) {
        this.sessions.delete(sessionId);
      }
    }
  }

  /**
   * 期限切れセッションをクリーンアップ
   */
  public cleanup(): void {
    let cleaned = 0;

    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.isExpired()) {
        this.sessions.delete(sessionId);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      Logger.debug(`Cleaned up ${cleaned} expired sessions`);
    }
  }

  /**
   * セッションIDを生成
   */
  private generateSessionId(): string {
    return crypto.randomBytes(16).toString('hex');
  }

  /**
   * ユーザーIDから最新のアクティブセッションを取得
   */
  public getLatestSessionByUser(discordId: string): Session | null {
    let latestSession: Session | null = null;
    let latestExpiresAt: Date = new Date(0);

    for (const [, session] of this.sessions.entries()) {
      if (session.ownerDiscordId === discordId && !session.isExpired()) {
        if (session.expiresAt > latestExpiresAt) {
          latestSession = session;
          latestExpiresAt = session.expiresAt;
        }
      }
    }

    return latestSession;
  }

  /**
   * リソースを解放
   */
  public destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.sessions.clear();
  }
}
