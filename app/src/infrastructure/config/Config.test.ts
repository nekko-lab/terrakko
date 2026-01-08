import { Config } from './Config';

describe('Config', () => {
  // Save original environment variables
  const originalEnv = process.env;

  beforeEach(() => {
    // Reset environment for each test
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    // Restore original environment
    process.env = originalEnv;
  });

  describe('Environment Variables from .env.test', () => {
    test('should load DOMAIN from environment', () => {
      expect(Config.DOMAIN).toBe('.proxmoxve.internal.nekko-lab.dev');
    });

    test('should load PVE_HOST from environment', () => {
      expect(Config.PVE_HOST).toBe('10.0.128.103');
    });

    test('should load PVE_USER from environment', () => {
      expect(Config.PVE_USER).toBe('tfuser@pve');
    });

    test('should load PVE_TOKEN from environment', () => {
      expect(Config.PVE_TOKEN).toBe('cloudinit');
    });

    test('should load PVE_SECRET from environment', () => {
      expect(Config.PVE_SECRET).toBe('d3cc2db0-4332-4e75-987a-78dbd1b9b7fc');
    });

    test('should load and parse PVE_REGION as JSON array', () => {
      expect(Config.PVE_REGION).toEqual(['dev-proxmox-mk', 'dev-proxmox-ur']);
      expect(Array.isArray(Config.PVE_REGION)).toBe(true);
      expect(Config.PVE_REGION.length).toBe(2);
    });

    test('should load and parse PVE_TEMP_ID as JSON array', () => {
      expect(Config.PVE_TEMP_ID).toEqual(['90100', '90101']);
      expect(Array.isArray(Config.PVE_TEMP_ID)).toBe(true);
      expect(Config.PVE_TEMP_ID.length).toBe(2);
    });

    test('should load DIS_TOKEN from environment', () => {
      expect(Config.DIS_TOKEN).toBe('MTI5NDYzNTA3ODQ3MDg2NDkxNg.GzP-EJ.-jmmjr-XjtrXfRvueSAyp9w5TGCmUxxzFj4ZF4');
    });

    test('should load and parse DIS_CHANNEL_ID as number', () => {
      expect(Config.DIS_CHANNEL_ID).toBe(1297112224665698336);
      expect(typeof Config.DIS_CHANNEL_ID).toBe('number');
    });
  });

  describe('Static Configuration', () => {
    test('should have VERSION defined', () => {
      expect(Config.VERSION).toBe('0.4.0');
    });

    test('should have TIME timeout defined', () => {
      expect(Config.TIME).toBe(180);
    });

    test('should have database configuration', () => {
      expect(Config.DB_PATH).toBe('./db/');
      expect(Config.DB_NAME).toBe('userdata');
      expect(Config.DB_FILE).toBe('./db/userdata.db');
    });
  });

  describe('validate', () => {
    test('should not throw error when all required env vars are present', () => {
      // Environment variables are already loaded from .env.test
      expect(() => Config.validate()).not.toThrow();
    });

    test('should throw error when required env var is missing', () => {
      // Remove a required variable
      delete process.env.DOMAIN;

      // Need to reload the module to pick up the change
      jest.resetModules();
      const { Config: TestConfig } = require('./Config');

      expect(() => TestConfig.validate()).toThrow('Missing required environment variables: DOMAIN');
    });
  });
});
