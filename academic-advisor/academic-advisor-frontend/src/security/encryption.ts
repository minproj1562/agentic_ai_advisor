// src/security/encryption.ts
import CryptoJS from 'crypto-js';

export class EncryptionService {
  private static instance: EncryptionService;
  private key: string;

  private constructor() {
    // Use Vite environment variables
    this.key = import.meta.env.VITE_ENCRYPTION_KEY || 'default-secure-key-2024';
  }

  static getInstance(): EncryptionService {
    if (!EncryptionService.instance) {
      EncryptionService.instance = new EncryptionService();
    }
    return EncryptionService.instance;
  }

  encrypt(data: any): string {
    try {
      const jsonString = JSON.stringify(data);
      return CryptoJS.AES.encrypt(jsonString, this.key).toString();
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  decrypt(encryptedData: string): any {
    try {
      const bytes = CryptoJS.AES.decrypt(encryptedData, this.key);
      const decryptedString = bytes.toString(CryptoJS.enc.Utf8);
      
      if (!decryptedString) {
        throw new Error('Failed to decrypt data - invalid key or data');
      }
      
      return JSON.parse(decryptedString);
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  hashPassword(password: string): string {
    return CryptoJS.SHA256(password + this.key).toString();
  }

  generateSecureToken(): string {
    return CryptoJS.lib.WordArray.random(32).toString();
  }

  generateIV(): string {
    return CryptoJS.lib.WordArray.random(16).toString();
  }

  // For more secure encryption with IV
  encryptWithIV(data: any, iv: string): string {
    const jsonString = JSON.stringify(data);
    const encrypted = CryptoJS.AES.encrypt(jsonString, this.key, {
      iv: CryptoJS.enc.Hex.parse(iv)
    });
    return encrypted.toString();
  }

  decryptWithIV(encryptedData: string, iv: string): any {
    const bytes = CryptoJS.AES.decrypt(encryptedData, this.key, {
      iv: CryptoJS.enc.Hex.parse(iv)
    });
    const decryptedString = bytes.toString(CryptoJS.enc.Utf8);
    return JSON.parse(decryptedString);
  }

  // Simple string encryption (for non-JSON data)
  encryptString(text: string): string {
    return CryptoJS.AES.encrypt(text, this.key).toString();
  }

  decryptString(encryptedText: string): string {
    const bytes = CryptoJS.AES.decrypt(encryptedText, this.key);
    return bytes.toString(CryptoJS.enc.Utf8);
  }

  // Generate a random key (for one-time use)
  generateRandomKey(length: number = 32): string {
    return CryptoJS.lib.WordArray.random(length).toString();
  }

  // Verify hash matches
  verifyHash(data: string, hash: string): boolean {
    return this.hashPassword(data) === hash;
  }
}

// Export singleton instance
export const encryptionService = EncryptionService.getInstance();