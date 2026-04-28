// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence,
} from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { auth, db } from '../services/firebase.config';
import toast from 'react-hot-toast';
import apiClient from '../services/api.service';

// ─── Types ────────────────────────────────────────────────────────────────────

interface User {
  uid: string;
  email: string;
  name: string;
  role: 'student' | 'faculty' | 'admin';
  profileComplete?: boolean;
  department?: string;
  rollNumber?: string;
  branch?: string;
  semester?: number;
}

interface LoginCredentials {
  email?: string;
  roll_number?: string;
  password: string;
  rememberMe?: boolean;
  userType?: 'student' | 'faculty' | 'admin';
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (email: string, password: string, userData: Partial<User>) => Promise<void>;
  logout: () => Promise<void>;
  googleSignIn: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

// ─── Storage helpers ──────────────────────────────────────────────────────────

const STORAGE_KEYS = {
  TOKEN:    'auth_token',
  ROLE:     'user_role',
  USER:     'auth_user',
} as const;

function saveSession(token: string, role: string, user: User, _remember: boolean = true) {
  // Always use localStorage so sessions persist across page refreshes
  const s = localStorage;
  s.setItem(STORAGE_KEYS.TOKEN, token);
  s.setItem(STORAGE_KEYS.ROLE,  role);
  s.setItem(STORAGE_KEYS.USER,  JSON.stringify(user));
}

function clearSession() {
  [localStorage, sessionStorage].forEach(s => {
    s.removeItem(STORAGE_KEYS.TOKEN);
    s.removeItem(STORAGE_KEYS.ROLE);
    s.removeItem(STORAGE_KEYS.USER);
  });
}

function getStoredToken(): string | null {
  return (
    localStorage.getItem(STORAGE_KEYS.TOKEN) ||
    sessionStorage.getItem(STORAGE_KEYS.TOKEN) ||
    null
  );
}

function getStoredUser(): User | null {
  const raw =
    localStorage.getItem(STORAGE_KEYS.USER) ||
    sessionStorage.getItem(STORAGE_KEYS.USER);
  if (!raw) return null;
  try { return JSON.parse(raw) as User; }
  catch { return null; }
}

function getStoredRole(): string | null {
  return (
    localStorage.getItem(STORAGE_KEYS.ROLE) ||
    sessionStorage.getItem(STORAGE_KEYS.ROLE) ||
    null
  );
}

// ─── Route helpers ────────────────────────────────────────────────────────────

const getDashboardPath = (role: string): string => {
  switch (role) {
    case 'faculty': return '/faculty/dashboard';
    case 'admin':   return '/admin/dashboard';
    default:        return '/student/dashboard';
  }
};

const getRoleLabel = (role: string): string => {
  switch (role) {
    case 'faculty': return 'Faculty';
    case 'admin':   return 'Admin';
    default:        return 'Student';
  }
};

const FACULTY_EMAIL_DOMAIN = '@fcrit.ac.in';

// ─── Provider ─────────────────────────────────────────────────────────────────

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser]       = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate              = useNavigate();

  // Track Firebase unsubscribe so we can clean it up
  const firebaseUnsubRef = useRef<(() => void) | null>(null);

  // ── getToken — for use anywhere in the app ──────────────────────────────

  const getToken = async (): Promise<string | null> => {
    // Faculty/admin: get a fresh Firebase ID token
    if (auth.currentUser) {
      try {
        const fresh = await auth.currentUser.getIdToken(false);
        // Keep storage in sync
        const s = localStorage.getItem(STORAGE_KEYS.TOKEN)
          ? localStorage
          : sessionStorage;
        s.setItem(STORAGE_KEYS.TOKEN, fresh);
        return fresh;
      } catch (e) {
        console.warn('Firebase getIdToken failed:', e);
      }
    }

    // Students: return stored JWT
    return getStoredToken();
  };

  // ── Session restoration on mount ────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;

    const restoreSession = async () => {
      // Ensure Firebase uses local persistence so sessions survive refresh
      try {
        await setPersistence(auth, browserLocalPersistence);
      } catch (e) {
        console.warn('Could not set Firebase persistence:', e);
      }

      try {
        const role  = getStoredRole();
        const token = getStoredToken();
        const saved = getStoredUser();

        // ── Student: pure JWT, no Firebase ──────────────────────────────
        if (role === 'student' && token && saved) {
          // Immediately restore from cache — user sees dashboard instantly
          if (!cancelled) {
            setUser(saved);
            setLoading(false);
          }

          // Background verify — only clear on definitive 401 (expired token)
          try {
            const { data } = await apiClient.get('/auth/verify-token');
            if (data.success && !cancelled) {
              // Merge fresh data from backend
              setUser({ ...saved, ...data.user });
            }
          } catch (err: any) {
            // Only clear session on 401 (token actually expired/invalid)
            // Don't clear on network errors, 500s, etc.
            if (err?.response?.status === 401) {
              console.warn('Student token expired, clearing session');
              clearSession();
              if (!cancelled) {
                setUser(null);
              }
            } else {
              console.warn('Token verify failed (network/server), keeping cached session:', err?.message);
            }
          }
          return; // Don't fall through to Firebase path
        }

        // ── Faculty / Admin: Firebase auth state ─────────────────────────
        firebaseUnsubRef.current = onAuthStateChanged(auth, async (fbUser) => {
          if (cancelled) return;

          if (fbUser) {
            try {
              // Get a fresh ID token and always store in localStorage
              const freshToken = await fbUser.getIdToken(false);
              localStorage.setItem(STORAGE_KEYS.TOKEN, freshToken);

              // Load user data from Firestore
              const snap = await getDoc(doc(db, 'users', fbUser.uid));
              if (snap.exists()) {
                const userData = snap.data() as Omit<User, 'uid' | 'email'>;
                const fullUser = {
                  ...userData,
                  uid:   fbUser.uid,
                  email: fbUser.email || '',
                };
                setUser(fullUser);
                // Keep localStorage in sync
                localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(fullUser));
                localStorage.setItem(STORAGE_KEYS.ROLE, userData.role || 'faculty');
              } else {
                setUser(null);
              }
            } catch (err) {
              console.error('Error restoring Firebase session:', err);
              // Try to use cached user data as fallback
              if (saved) {
                setUser(saved);
              } else {
                setUser(null);
              }
            }
          } else {
            // No Firebase session — if not a student, clear everything
            if (role !== 'student') {
              clearSession();
              setUser(null);
            }
          }

          setLoading(false);
        });

      } catch (err) {
        console.error('Session restore error:', err);
        if (!cancelled) setLoading(false);
      }
    };

    restoreSession();

    return () => {
      cancelled = true;
      firebaseUnsubRef.current?.();
    };
  }, []);

  // ── Auto-refresh Firebase token for faculty/admin ────────────────────────

  useEffect(() => {
    // Only run for faculty/admin (Firebase users)
    const unsub = onAuthStateChanged(auth, async (fbUser) => {
      if (!fbUser) return;
      try {
        const fresh = await fbUser.getIdToken(false);
        const s = localStorage.getItem(STORAGE_KEYS.TOKEN)
          ? localStorage
          : sessionStorage;
        s.setItem(STORAGE_KEYS.TOKEN, fresh);
      } catch (e) {
        console.warn('Token auto-refresh failed:', e);
      }
    });
    return () => unsub();
  }, []);

  // ── Login ────────────────────────────────────────────────────────────────

  const login = async (credentials: LoginCredentials) => {
    const { email, roll_number, password, userType, rememberMe = false } = credentials;

    // ════════════════════════════════════════════════════════
    //  STUDENT LOGIN — Pure JWT, zero Firebase involvement
    // ════════════════════════════════════════════════════════
    if (userType === 'student') {
      if (!roll_number) throw new Error('Roll number is required');

      const { data } = await apiClient.post('/auth/student/login', {
        roll_number,
        password,
      });

      if (!data.success) throw new Error(data.message || 'Login failed');

      const { token, user: userData, requires_password_change } = data;

      // Store JWT (plain HS256) — NO Firebase
      saveSession(token, 'student', { ...userData, role: 'student' }, rememberMe);
      setUser({ ...userData, role: 'student' });

      if (requires_password_change) {
        toast('Please change your default password', { icon: 'ℹ️' });
        navigate('/student/change-password', { replace: true });
      } else {
        navigate('/student/dashboard', { replace: true });
        toast.success(`Welcome back, ${userData.name}!`);
      }

      return;
    }

    // ════════════════════════════════════════════════════════
    //  FACULTY / ADMIN LOGIN — Firebase only
    // ════════════════════════════════════════════════════════
    if (!email) throw new Error('Email is required');

    // Always use local persistence so sessions persist across refresh
    await setPersistence(auth, browserLocalPersistence);

    const cred       = await signInWithEmailAndPassword(auth, email, password);
    const firebaseToken = await cred.user.getIdToken();

    // Fetch user doc from Firestore
    const snap = await getDoc(doc(db, 'users', cred.user.uid));
    if (!snap.exists()) {
      await signOut(auth);
      toast.error('Account not properly registered.');
      navigate('/register');
      throw new Error('Account not properly registered');
    }

    const userData = snap.data() as User;

    // Role mismatch check
    if (userType && userData.role !== userType) {
      await signOut(auth);
      toast.error(
        `You are registered as ${getRoleLabel(userData.role)}. ` +
        `Please switch to the ${getRoleLabel(userData.role)} login tab.`,
      );
      throw new Error('Wrong login portal');
    }

    // Store Firebase token
    saveSession(firebaseToken, userData.role, userData, rememberMe);
    setUser(userData);

    // Navigate
    if (userData.role === 'faculty') {
      try {
        const setup = await apiClient.get('/faculty-profile/check-setup-status');
        if (setup.data.needs_setup) {
          navigate('/faculty/profile-setup', { replace: true });
          toast.success('Please complete your profile setup.');
          return;
        }
      } catch {
        // Ignore — go to dashboard
      }
      navigate('/faculty/dashboard', { replace: true });
      toast.success(`Welcome back, Professor ${userData.name}!`);

    } else if (userData.role === 'admin') {
      navigate('/admin/dashboard', { replace: true });
      toast.success(`Welcome, Admin ${userData.name}!`);

    } else {
      navigate('/student/dashboard', { replace: true });
      toast.success(`Welcome, ${userData.name}!`);
    }
  };

  // ── Register ─────────────────────────────────────────────────────────────

  const register = async (
    email: string,
    password: string,
    userData: Partial<User>,
  ) => {
    const cred = await createUserWithEmailAndPassword(auth, email, password);

    await setDoc(doc(db, 'users', cred.user.uid), {
      ...userData,
      uid:            cred.user.uid,
      email:          cred.user.email,
      createdAt:      new Date(),
      profileComplete: false,
    });

    await signOut(auth);

    const msg = userData.role === 'faculty'
      ? 'Faculty registration successful!'
      : 'Registration successful!';
    toast.success(`${msg} Please login to continue.`);
    setTimeout(() => navigate('/login'), 2000);
  };

  // ── Google Sign-In ───────────────────────────────────────────────────────

  const googleSignIn = async () => {
    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });

    const result = await signInWithPopup(auth, provider);
    const fbUser = result.user;

    if (fbUser.email?.endsWith(FACULTY_EMAIL_DOMAIN)) {
      toast.error('Faculty must use the Faculty tab with email & password.');
      await auth.signOut();
      return;
    }

    const snap = await getDoc(doc(db, 'users', fbUser.uid));
    if (snap.exists()) {
      const userData = snap.data() as User;
      setUser(userData);
      navigate(getDashboardPath(userData.role));
      toast.success('Login successful!');
    } else {
      toast.error('No account found. Please register first.');
      await auth.signOut();
      navigate('/register', {
        state: {
          googleData: {
            email:       fbUser.email,
            displayName: fbUser.displayName,
            photoURL:    fbUser.photoURL,
          },
        },
      });
    }
  };

  // ── Reset Password ───────────────────────────────────────────────────────

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email);
    toast.success('Password reset email sent! Check your inbox.');
  };

  // ── Logout ───────────────────────────────────────────────────────────────

  const logout = async () => {
    clearSession();

    if (auth.currentUser) {
      await signOut(auth);
    }

    setUser(null);
    navigate('/');
    toast.success('Logged out successfully');
  };

  // ── Context value ────────────────────────────────────────────────────────

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        googleSignIn,
        resetPassword,
        getToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ─── Auth redirect helper ─────────────────────────────────────────────────────

export const AuthRedirect: React.FC = () => {
  const { user, loading } = useAuth();
  const navigate          = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      const current = window.location.pathname;
      if (current === '/login' || current === '/register') {
        navigate(getDashboardPath(user.role), { replace: true });
      }
    }
  }, [user, loading, navigate]);

  return null;
};