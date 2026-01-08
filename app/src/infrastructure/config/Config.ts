import * as dotenv from 'dotenv';

dotenv.config();

export const LOGO = `
                                              _ 
  _____  _____ ____  ____  ____  _  __ _  __ |_\\_ 
 /__ __\\/  __//  __\\/  __\\/  _ \\/ |/ // |/ //\\_  \\_ 
   / \\  |  \\  |  \\/||  \\/|| /_\\||   / |   /|_  \\_  \\ 
   | |  |  /_ |    /|    /| | |||   \\ |   \\| \\_  \\__| 
   \\_/  \\____\\\\_/\\_\\\\_/\\_\\\\_/ \\/\\_|\\_\\\\_|\\_\\\\__\\___/
`;

export class Config {
  public static readonly VERSION = '0.4.0';
  public static readonly DOMAIN = process.env.DOMAIN || '';
  public static readonly TIME = 180; // Timeout in seconds

  // Database
  public static readonly DB_PATH = './db/';
  public static readonly DB_NAME = 'userdata';
  public static readonly DB_FILE = `${Config.DB_PATH}${Config.DB_NAME}.db`;

  // Proxmox VE
  public static readonly PVE_HOST = process.env.PVE_HOST || '';
  public static readonly PVE_USER = process.env.PVE_USER || '';
  public static readonly PVE_PASS = process.env.PVE_PASS || '';
  public static readonly PVE_TOKEN = process.env.PVE_TOKEN || '';
  public static readonly PVE_SECRET = process.env.PVE_SECRET || '';
  public static readonly PVE_REGION: string[] = Config.parseJsonEnv('PVE_REGION', []);
  public static readonly PVE_TEMP_ID: number[] = Config.parseJsonEnv('PVE_TEMP_ID', []);

  // Discord Bot
  public static readonly DIS_TOKEN = process.env.DIS_TOKEN || '';
  public static readonly DIS_CHANNEL_ID = parseInt(process.env.DIS_CHANNEL_ID || '0', 10);

  private static parseJsonEnv(key: string, defaultValue: any): any {
    const value = process.env[key];
    if (!value) {
      return defaultValue;
    }
    try {
      return JSON.parse(value);
    } catch (error) {
      console.error(`Failed to parse ${key} as JSON:`, error);
      return defaultValue;
    }
  }

  public static validate(): void {
    const required = [
      'DOMAIN',
      'PVE_HOST',
      'PVE_USER',
      'PVE_TOKEN',
      'PVE_SECRET',
      'PVE_REGION',
      'PVE_TEMP_ID',
      'DIS_TOKEN',
      'DIS_CHANNEL_ID'
    ];

    const missing: string[] = [];
    for (const key of required) {
      if (key === 'PVE_REGION' || key === 'PVE_TEMP_ID') {
        const value = Config.parseJsonEnv(key, null);
        if (!value || (Array.isArray(value) && value.length === 0)) {
          missing.push(key);
        }
      } else if (!process.env[key]) {
        missing.push(key);
      }
    }

    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }
}
