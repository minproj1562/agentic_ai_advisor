// services/auth.service.ts
import { 
  signInWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  User as FirebaseUser
} from 'firebase/auth';
import { 
  doc, 
  getDoc, 
  setDoc,
  serverTimestamp 
} from 'firebase/firestore';
import { auth, db } from './firebase.config';
import { User, LoginCredentials } from '../types/auth.types';

class AuthService {
  async login(credentials: LoginCredentials): Promise<User> {
    try {
      const userCredential = await signInWithEmailAndPassword(
        auth,
        credentials.email,
        credentials.password
      );

      const uid = userCredential.user.uid;
      
      // Try to get user document
      let userDoc = await getDoc(doc(db, 'users', uid));
      
      // If user document doesn't exist, create it
      if (!userDoc.exists()) {
        console.log('Creating user document for:', uid);
        
        const newUserData = {
          uid: uid,
          email: userCredential.user.email,
          displayName: userCredential.user.displayName || userCredential.user.email?.split('@')[0] || 'User',
          role: this.determineRole(userCredential.user.email || ''),
          emailVerified: userCredential.user.emailVerified,
          metadata: {
            createdAt: serverTimestamp(),
            lastLoginAt: serverTimestamp(),
            lastActiveAt: serverTimestamp(),
            loginCount: 1,
          },
          preferences: {
            notifications: {
              email: true,
              push: true,
              sms: false,
            },
            theme: 'system',
            language: 'en',
          },
        };

        await setDoc(doc(db, 'users', uid), newUserData);
        
        // Return the user data without the 'id' property
        return {
          uid: uid,
          email: newUserData.email || '',
          displayName: newUserData.displayName,
          role: newUserData.role,
          emailVerified: newUserData.emailVerified,
          metadata: {
            createdAt: new Date().toISOString(),
            lastLoginAt: new Date().toISOString(),
            lastActiveAt: new Date().toISOString(),
            loginCount: 1,
          },
          preferences: newUserData.preferences
        } as User;
      }

      // Update last login
      await setDoc(doc(db, 'users', uid), {
        'metadata.lastLoginAt': serverTimestamp(),
        'metadata.loginCount': (userDoc.data()?.metadata?.loginCount || 0) + 1,
      }, { merge: true });

      const userData = userDoc.data();
      
      // Return the user data without the 'id' property
      return {
        uid: uid,
        email: userData?.email || '',
        displayName: userData?.displayName || '',
        role: userData?.role || 'student',
        emailVerified: userData?.emailVerified || false,
        metadata: userData?.metadata || {
          createdAt: new Date().toISOString(),
          lastLoginAt: new Date().toISOString(),
          lastActiveAt: new Date().toISOString(),
          loginCount: 1,
        },
        preferences: userData?.preferences || {
          notifications: {
            email: true,
            push: true,
            sms: false,
          },
          theme: 'system',
          language: 'en',
        }
      } as User;
    } catch (error: any) {
      console.error('Login error:', error);
      throw error;
    }
  }

  private determineRole(email: string): 'student' | 'faculty' {
    // Logic to determine role based on email pattern
    if (email.includes('faculty') || email.includes('prof') || email.includes('dr')) {
      return 'faculty';
    }
    return 'student';
  }

  async logout(): Promise<void> {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  }

  async resetPassword(email: string): Promise<void> {
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (error) {
      console.error('Password reset error:', error);
      throw error;
    }
  }

  async getUserProfile(uid: string): Promise<User | null> {
    try {
      const userDoc = await getDoc(doc(db, 'users', uid));
      if (userDoc.exists()) {
        const userData = userDoc.data();
        return {
          uid: uid,
          email: userData.email || '',
          displayName: userData.displayName || '',
          role: userData.role || 'student',
          emailVerified: userData.emailVerified || false,
          metadata: userData.metadata || {
            createdAt: new Date().toISOString(),
            lastLoginAt: new Date().toISOString(),
            lastActiveAt: new Date().toISOString(),
            loginCount: 1,
          },
          preferences: userData.preferences || {
            notifications: {
              email: true,
              push: true,
              sms: false,
            },
            theme: 'system',
            language: 'en',
          }
        } as User;
      }
      return null;
    } catch (error) {
      console.error('Get user profile error:', error);
      return null;
    }
  }
}

export const authService = new AuthService();