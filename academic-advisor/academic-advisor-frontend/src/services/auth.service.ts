// src/services/auth.service.ts
/**
 * AuthService
 *
 * Handles Firebase Auth sign-in and Firestore user document management.
 *
 * Key change from original
 * ------------------------
 * REMOVED hardcoded APPROVED_FACULTY_EMAILS set.
 * Now fetches from MongoDB via API with a simple in-memory cache
 * (5-minute TTL) so we don't hit the API on every keystroke.
 *
 * Faculty email validation still uses the regex:
 *   firstname.lastname@fcrit.ac.in  (letters only, no digits)
 * That validation is format-only and doesn't need the DB.
 *
 * The DB lookup is only for showing the green "approved" hint on Login.
 * It is NON-BLOCKING — if the API fails, login still works normally.
 */

import {
  signInWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  User as FirebaseUser,
} from 'firebase/auth';
import {
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
} from 'firebase/firestore';
import axios from 'axios';
import { auth, db } from './firebase.config';
import { User, LoginCredentials } from '../types/auth.types';

// ─── Constants ────────────────────────────────────────────────────────────────

const FACULTY_EMAIL_DOMAIN = '@fcrit.ac.in';

const BASE_URL =
  (import.meta as any).env?.VITE_API_URL
    ? `${(import.meta as any).env.VITE_API_URL}/api/v1`
    : 'http://localhost:8000/api/v1';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Returns true if email matches firstname.lastname@fcrit.ac.in
 * Pure regex — no network call needed.
 */
const isFacultyEmailFormat = (email: string): boolean => {
  const lower = email.toLowerCase().trim();
  if (!lower.endsWith(FACULTY_EMAIL_DOMAIN)) return false;
  const local = lower.split('@')[0];
  // Only letters, at least one char each side of the dot
  return /^[a-z]+\.[a-z]+$/.test(local);
};

/**
 * Derives display name from faculty email.
 * "poonam.bari@fcrit.ac.in" → "Poonam Bari"
 */
const nameFromFacultyEmail = (email: string): string => {
  const local = email.split('@')[0];
  return local
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

/**
 * Determine role from email pattern.
 * Faculty: firstname.lastname@fcrit.ac.in
 * Admin:   anything with "admin"
 * Default: student
 */
const determineRoleFromEmail = (
  email: string
): 'student' | 'faculty' | 'admin' => {
  const lower = email.toLowerCase().trim();
  if (isFacultyEmailFormat(lower)) return 'faculty';
  if (lower.includes('admin'))      return 'admin';
  return 'student';
};

// ─── In-memory cache for faculty emails from MongoDB ─────────────────────────
// This avoids hitting the API on every login attempt.
// TTL: 5 minutes.

let _emailCache:    Set<string> | null = null;
let _cacheExpiry:   number             = 0;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Fetch approved faculty emails from MongoDB via the backend API.
 * Returns cached result if still fresh.
 * Never throws — returns empty Set on any error.
 */
async function fetchFacultyEmailsFromDB(): Promise<Set<string>> {
  const now = Date.now();

  // Return cached value if still valid
  if (_emailCache !== null && now < _cacheExpiry) {
    return _emailCache;
  }

  try {
    const res = await axios.get<{
      emails: Array<{ email: string }>;
    }>(`${BASE_URL}/faculty/approved-emails`, {
      timeout: 5000, // 5-second timeout — don't block login
    });

    const emails = (res.data.emails ?? []).map(
      (e) => e.email.toLowerCase().trim()
    );

    _emailCache  = new Set(emails);
    _cacheExpiry = now + CACHE_TTL_MS;

    return _emailCache;
  } catch (err) {
    // Non-fatal — login still works without the approval check
    console.warn('[AuthService] Could not fetch faculty emails from DB:', err);
    // Return existing cache even if expired, or empty set
    return _emailCache ?? new Set<string>();
  }
}

// ─── AuthService class ────────────────────────────────────────────────────────

class AuthService {
  /**
   * Sign in with email + password.
   *
   * Flow:
   * 1. Firebase Auth signInWithEmailAndPassword
   * 2. If faculty tab: validate email format
   * 3. Fetch/update Firestore user document
   * 4. Role-mismatch guard
   * 5. Return User object
   */
  async login(credentials: LoginCredentials): Promise<User> {
    try {
      const userCredential = await signInWithEmailAndPassword(
        auth,
        credentials.email,
        credentials.password
      );

      const { uid }    = userCredential.user;
      const emailLower = (userCredential.user.email ?? '').toLowerCase().trim();

      // ── Faculty email validation ─────────────────────────────────────────
      if (credentials.userType === 'faculty') {
        // Hard block: email must match firstname.lastname@fcrit.ac.in
        if (!isFacultyEmailFormat(emailLower)) {
          await signOut(auth);
          throw Object.assign(
            new Error(
              `Faculty email must be in the format ` +
              `firstname.lastname${FACULTY_EMAIL_DOMAIN}`
            ),
            { code: 'auth/invalid-faculty-email' }
          );
        }

        // Non-blocking: check if email is registered in MongoDB
        // This is just for logging — it does NOT block login
        const registeredEmails = await fetchFacultyEmailsFromDB();
        if (!registeredEmails.has(emailLower)) {
          console.warn(
            '[AuthService] Faculty email not found in MongoDB:',
            emailLower
          );
        }
      }

      // ── Firestore user document ───────────────────────────────────────────
      const userDocRef  = doc(db, 'users', uid);
      const userDocSnap = await getDoc(userDocRef);

      if (!userDocSnap.exists()) {
        // First login — create Firestore document
        // (normally created by admin_service, but fallback just in case)
        const isFaculty    = isFacultyEmailFormat(emailLower);
        const newUserData  = {
          uid,
          email:         userCredential.user.email,
          displayName:   isFaculty
            ? nameFromFacultyEmail(emailLower)
            : (userCredential.user.displayName ||
               emailLower.split('@')[0] ||
               'User'),
          role:          determineRoleFromEmail(emailLower),
          emailVerified: userCredential.user.emailVerified,
          // Faculty created by admin already has this set to True.
          // This path is a fallback — set to False since they set their own pw.
          must_change_password: false,
          metadata: {
            createdAt:    serverTimestamp(),
            lastLoginAt:  serverTimestamp(),
            lastActiveAt: serverTimestamp(),
            loginCount:   1,
          },
          preferences: {
            notifications: { email: true, push: true, sms: false },
            theme:    'system',
            language: 'en',
          },
        };

        await setDoc(userDocRef, newUserData);

        return {
          uid,
          email:         newUserData.email ?? '',
          displayName:   newUserData.displayName,
          role:          newUserData.role,
          emailVerified: newUserData.emailVerified,
          metadata: {
            createdAt:    new Date().toISOString(),
            lastLoginAt:  new Date().toISOString(),
            lastActiveAt: new Date().toISOString(),
            loginCount:   1,
          },
          preferences: newUserData.preferences,
        } as User;
      }

      // ── Existing user — update last-login timestamp ──────────────────────
      await setDoc(
        userDocRef,
        {
          'metadata.lastLoginAt': serverTimestamp(),
          'metadata.loginCount':
            (userDocSnap.data()?.metadata?.loginCount ?? 0) + 1,
        },
        { merge: true }
      );

      const userData = userDocSnap.data()!;

      // ── Role-mismatch guard ───────────────────────────────────────────────
      // Prevents a student from logging in via the Faculty tab
      if (credentials.userType && userData.role !== credentials.userType) {
        await signOut(auth);
        throw Object.assign(
          new Error(
            `You are registered as ${userData.role}. ` +
            `Please use the ${userData.role} login tab.`
          ),
          { code: 'auth/wrong-portal' }
        );
      }

      // ── Return typed User object ─────────────────────────────────────────
      return {
        uid,
        email:         userData.email         ?? '',
        displayName:   userData.displayName   ?? '',
        role:          userData.role          ?? 'student',
        emailVerified: userData.emailVerified ?? false,
        metadata:      userData.metadata      ?? {
          createdAt:    new Date().toISOString(),
          lastLoginAt:  new Date().toISOString(),
          lastActiveAt: new Date().toISOString(),
          loginCount:   1,
        },
        preferences: userData.preferences ?? {
          notifications: { email: true, push: true, sms: false },
          theme:    'system',
          language: 'en',
        },
      } as User;

    } catch (error: any) {
      console.error('[AuthService] Login error:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('[AuthService] Logout error:', error);
      throw error;
    }
  }

  async resetPassword(email: string): Promise<void> {
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (error) {
      console.error('[AuthService] Password reset error:', error);
      throw error;
    }
  }

  async getUserProfile(uid: string): Promise<User | null> {
    try {
      const userDoc = await getDoc(doc(db, 'users', uid));
      if (!userDoc.exists()) return null;

      const userData = userDoc.data();
      return {
        uid,
        email:         userData.email         ?? '',
        displayName:   userData.displayName   ?? '',
        role:          userData.role          ?? 'student',
        emailVerified: userData.emailVerified ?? false,
        metadata:      userData.metadata      ?? {
          createdAt:    new Date().toISOString(),
          lastLoginAt:  new Date().toISOString(),
          lastActiveAt: new Date().toISOString(),
          loginCount:   1,
        },
        preferences: userData.preferences ?? {
          notifications: { email: true, push: true, sms: false },
          theme:    'system',
          language: 'en',
        },
      } as User;
    } catch (error) {
      console.error('[AuthService] Get user profile error:', error);
      return null;
    }
  }

  // ─── Exposed utilities ───────────────────────────────────────────────────

  /** Format check only — no network call */
  isFacultyEmail(email: string): boolean {
    return isFacultyEmailFormat(email);
  }

  /** Checks MongoDB via API (async, cached) */
  async isRegisteredFacultyEmail(email: string): Promise<boolean> {
    const emails = await fetchFacultyEmailsFromDB();
    return emails.has(email.toLowerCase().trim());
  }

  /** Derive display name from faculty email */
  getFacultyDisplayName(email: string): string {
    return nameFromFacultyEmail(email);
  }
}

export const authService = new AuthService();