// core/integrations/firebase/storage.ts
import { firebaseApp } from './config';
import {
  ref,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject,
  UploadTaskSnapshot
} from 'firebase/storage';

class FirebaseStorageService {
  async uploadFile(
    path: string,
    file: File,
    onProgress?: (progress: number, snapshot?: UploadTaskSnapshot) => void
  ): Promise<{ downloadUrl: string; metadata: any }> {
    const storage = firebaseApp.getStorage();
    const storageRef = ref(storage, path);
    const uploadTask = uploadBytesResumable(storageRef, file);

    return new Promise((resolve, reject) => {
      uploadTask.on(
        'state_changed',
        (snapshot) => {
          if (onProgress && snapshot.totalBytes > 0) {
            const progress = Math.round((snapshot.bytesTransferred * 100) / snapshot.totalBytes);
            onProgress(progress, snapshot);
          }
        },
        (error) => {
          console.error('File upload failed:', error);
          reject(error);
        },
        async () => {
          const url = await getDownloadURL(uploadTask.snapshot.ref);
          resolve({
            downloadUrl: url,
            metadata: uploadTask.snapshot.metadata
          });
        }
      );
    });
  }

  async getDownloadURL(path: string): Promise<string> {
    const storage = firebaseApp.getStorage();
    const storageRef = ref(storage, path);
    return await getDownloadURL(storageRef);
  }

  async deleteFile(path: string): Promise<void> {
    const storage = firebaseApp.getStorage();
    const storageRef = ref(storage, path);
    await deleteObject(storageRef);
  }
}

export const firebaseStorage = new FirebaseStorageService();