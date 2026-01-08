import { Validator } from './Validator';

describe('Validator', () => {
  describe('isValidVMID', () => {
    test('should return true for valid VMID in range 100-89999', () => {
      expect(Validator.isValidVMID(100)).toBe(true);
      expect(Validator.isValidVMID(1000)).toBe(true);
      expect(Validator.isValidVMID(89999)).toBe(true);
    });

    test('should return false for VMID less than 100', () => {
      expect(Validator.isValidVMID(99)).toBe(false);
      expect(Validator.isValidVMID(0)).toBe(false);
      expect(Validator.isValidVMID(-1)).toBe(false);
    });

    test('should return false for VMID greater than or equal to 90000', () => {
      expect(Validator.isValidVMID(90000)).toBe(false);
      expect(Validator.isValidVMID(100000)).toBe(false);
    });
  });

  describe('isNotEmpty', () => {
    test('should return true for non-empty strings', () => {
      expect(Validator.isNotEmpty('hello')).toBe(true);
      expect(Validator.isNotEmpty('  test  ')).toBe(true);
    });

    test('should return false for empty or whitespace strings', () => {
      expect(Validator.isNotEmpty('')).toBe(false);
      expect(Validator.isNotEmpty('   ')).toBe(false);
    });

    test('should return false for null or undefined', () => {
      expect(Validator.isNotEmpty(null)).toBe(false);
      expect(Validator.isNotEmpty(undefined)).toBe(false);
    });
  });

  describe('isValidSSHKey', () => {
    test('should return true for valid SSH RSA keys', () => {
      const validKey = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC test@example.com';
      expect(Validator.isValidSSHKey(validKey)).toBe(true);
    });

    test('should return true for valid SSH ED25519 keys', () => {
      const validKey = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFoo user@host';
      expect(Validator.isValidSSHKey(validKey)).toBe(true);
    });

    test('should return true for keys without comment', () => {
      const validKey = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC';
      expect(Validator.isValidSSHKey(validKey)).toBe(true);
    });

    test('should return false for invalid key format', () => {
      expect(Validator.isValidSSHKey('invalid-key')).toBe(false);
      expect(Validator.isValidSSHKey('ssh-rsa')).toBe(false);
      expect(Validator.isValidSSHKey('')).toBe(false);
    });
  });

  describe('isValidCPU', () => {
    test('should return true for positive integers', () => {
      expect(Validator.isValidCPU(1)).toBe(true);
      expect(Validator.isValidCPU(8)).toBe(true);
      expect(Validator.isValidCPU(64)).toBe(true);
    });

    test('should return false for zero or negative numbers', () => {
      expect(Validator.isValidCPU(0)).toBe(false);
      expect(Validator.isValidCPU(-1)).toBe(false);
    });

    test('should return false for non-integers', () => {
      expect(Validator.isValidCPU(1.5)).toBe(false);
      expect(Validator.isValidCPU(2.9)).toBe(false);
    });
  });

  describe('isValidMemory', () => {
    test('should return true for positive integers', () => {
      expect(Validator.isValidMemory(1)).toBe(true);
      expect(Validator.isValidMemory(1024)).toBe(true);
      expect(Validator.isValidMemory(16384)).toBe(true);
    });

    test('should return false for zero or negative numbers', () => {
      expect(Validator.isValidMemory(0)).toBe(false);
      expect(Validator.isValidMemory(-1024)).toBe(false);
    });

    test('should return false for non-integers', () => {
      expect(Validator.isValidMemory(1024.5)).toBe(false);
    });
  });

  describe('isValidVMCount', () => {
    test('should return true for valid VM count (1-5)', () => {
      expect(Validator.isValidVMCount(1)).toBe(true);
      expect(Validator.isValidVMCount(3)).toBe(true);
      expect(Validator.isValidVMCount(5)).toBe(true);
    });

    test('should return false for count less than 1', () => {
      expect(Validator.isValidVMCount(0)).toBe(false);
      expect(Validator.isValidVMCount(-1)).toBe(false);
    });

    test('should return false for count greater than 5', () => {
      expect(Validator.isValidVMCount(6)).toBe(false);
      expect(Validator.isValidVMCount(10)).toBe(false);
    });

    test('should return false for non-integers', () => {
      expect(Validator.isValidVMCount(2.5)).toBe(false);
    });
  });
});
