export class Session {
  public readonly id: string;
  public readonly ownerDiscordId: string;
  public readonly expiresAt: Date;
  public data: Map<string, unknown>;

  constructor(id: string, ownerDiscordId: string, expiresAt: Date, data?: Map<string, unknown>) {
    this.id = id;
    this.ownerDiscordId = ownerDiscordId;
    this.expiresAt = expiresAt;
    this.data = data || new Map<string, unknown>();
  }

  public isExpired(): boolean {
    return new Date() > this.expiresAt;
  }

  public get<T>(key: string): T | undefined {
    return this.data.get(key) as T | undefined;
  }

  public set(key: string, value: unknown): void {
    this.data.set(key, value);
  }

  public delete(key: string): boolean {
    return this.data.delete(key);
  }

  public clear(): void {
    this.data.clear();
  }
}
