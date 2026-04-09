// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom'; // ✅ Added useLocation
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User as FirebaseUser,
  GoogleAuthProvider,
  signInWithPopup,
  sendPasswordResetEmail,
  signInWithCustomToken,
} from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { auth, db } from '../services/firebase.config';
import toast from 'react-hot-toast';
import apiClient from '../services/api.service';

interface User {
  uid: string;
  email: string;
  name: string;
  role: 'student' | 'faculty' | 'admin';
  profileComplete?: boolean;
  department?: string;
  rollNumber?: string;
}

// ✅ Separate interfaces for each login type
interface StudentLoginCredentials {
  roll_number: string;
  password: string;
  rememberMe?: boolean;
  userType: 'student';
}

interface EmailLoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
  userType: 'faculty' | 'admin';
}

type LoginCredentials = StudentLoginCredentials | EmailLoginCredentials;

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (email: string, password: string, userData: Partial<User>) => Promise<void>;
  logout: () => Promise<void>;
  googleSignIn: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Helper functions
const getDashboardPath = (role: string): string => {
  switch (role) {
    case 'faculty':
      return '/faculty/dashboard';
    case 'admin':
      return '/admin/dashboard';
    default:
      return '/student/dashboard';
  }
};

const getRoleLabel = (role: string): string => {
  switch (role) {
    case 'faculty':
      return 'Faculty';
    case 'admin':
      return 'Admin';
    default:
      return 'Student';
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          if (userDoc.exists()) {
            const userData = userDoc.data() as Omit<User, 'uid' | 'email'>;
            setUser({
              ...userData,
              uid: firebaseUser.uid,
              email: firebaseUser.email || '',
            });
          } else {
            console.warn('User document not found in Firestore for:', firebaseUser.uid);
            setUser(null);
          }
        } catch (error) {
          console.error('Error fetching user data:', error);
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // ==================== STUDENT LOGIN ====================
  const loginStudent = async (credentials: StudentLoginCredentials) => {
    try {
      console.log('🎓 Student login attempt:', credentials.roll_number);

      // Call backend API
      const response = await apiClient.post('/auth/student/login', {
        roll_number: credentials.roll_number,
        password: credentials.password,
      });

      const { token, user: userData, requires_password_change } = response.data;

      console.log('✅ Backend response:', { userData, requires_password_change });

      // Sign in to Firebase with custom token
      await signInWithCustomToken(auth, token);

      console.log('✅ Firebase authentication successful');

      // Set user state
      setUser({
        uid: userData.uid,
        email: userData.email || `${credentials.roll_number}@student.college.edu`,
        name: userData.name,
        role: 'student',
        department: userData.branch,
        rollNumber: userData.roll_number,
      });

      // Show password change warning if needed
      if (requires_password_change) {
        toast.success('Login successful! Please change your default password.', {
          duration: 5000,
          icon: '🔐',
        });
      } else {
        toast.success(`Welcome back, ${userData.name}!`);
      }

      // Navigate to student dashboard
      navigate('/student/dashboard', { replace: true });
    } catch (error: any) {
      console.error('❌ Student login error:', error);

      if (error.response?.status === 401) {
        throw new Error('Invalid roll number or password');
      } else if (error.response?.status === 404) {
        throw new Error('Student not found with this roll number');
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else {
        throw new Error('Login failed. Please try again.');
      }
    }
  };

  // ==================== FACULTY/ADMIN LOGIN ====================
  const loginEmailUser = async (credentials: EmailLoginCredentials) => {
    try {
      console.log('👤 Email login attempt:', credentials.email);

      // Sign in with Firebase Auth
      const userCredential = await signInWithEmailAndPassword(
        auth,
        credentials.email,
        credentials.password
      );

      // Get user data from Firestore
      const userDoc = await getDoc(doc(db, 'users', userCredential.user.uid));

      if (!userDoc.exists()) {
        await signOut(auth);
        toast.error('Account not properly registered. Please complete registration.');
        navigate('/register');
        throw new Error('Account not properly registered');
      }

      const userData = userDoc.data() as User;
      console.log('✅ User data from Firestore:', { role: userData.role, name: userData.name });

      // ===== ROLE MISMATCH CHECK =====
      if (userData.role !== credentials.userType) {
        await signOut(auth);

        const actualRole = getRoleLabel(userData.role);
        const attemptedRole = getRoleLabel(credentials.userType);

        toast.error(
          `You are registered as ${actualRole}. Please switch to the ${actualRole} login tab.`,
          { duration: 5000 }
        );

        throw new Error('Wrong login portal');
      }

      // Set user state
      setUser(userData);

      // Navigate based on role
      if (userData.role === 'faculty') {
        // Check faculty profile setup
        try {
          const setupStatus = await apiClient.get('/faculty-profile/check-setup-status');
          if (setupStatus.data.needs_setup) {
            navigate('/faculty/profile-setup', { replace: true });
            toast.success('Please complete your profile setup.');
            return;
          }
        } catch (error) {
          console.log('Setup status check failed, continuing to dashboard');
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
    } catch (error: any) {
      console.error('❌ Email login error:', error);

      if (error.code === 'auth/user-not-found') {
        toast.error('No account found with this email. Please register first.');
        setTimeout(() => navigate('/register'), 2000);
      } else if (error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
        throw new Error('Incorrect password. Please try again.');
      } else if (error.code === 'auth/invalid-email') {
        throw new Error('Invalid email format.');
      } else if (error.message === 'Wrong login portal') {
        // Already handled with toast
        throw error;
      } else if (error.message === 'Account not properly registered') {
        // Already handled
        throw error;
      } else {
        throw new Error(error.message || 'Login failed');
      }
    }
  };

  // ==================== MAIN LOGIN DISPATCHER ====================
  const login = async (credentials: LoginCredentials) => {
    if (credentials.userType === 'student') {
      await loginStudent(credentials as StudentLoginCredentials);
    } else {
      await loginEmailUser(credentials as EmailLoginCredentials);
    }
  };

  // ==================== REGISTER ====================
  const register = async (email: string, password: string, userData: Partial<User>) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);

      const completeUserData = {
        ...userData,
        uid: userCredential.user.uid,
        email: userCredential.user.email,
        createdAt: new Date(),
        profileComplete: false,
      };

      await setDoc(doc(db, 'users', userCredential.user.uid), completeUserData);

      await signOut(auth);

      const roleMessage =
        userData.role === 'faculty' ? 'Faculty registration successful!' : 'Registration successful!';
      toast.success(`${roleMessage} Please login to continue.`);

      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error: any) {
      if (error.code === 'auth/email-already-in-use') {
        toast.error('This email is already registered. Please login.');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        toast.error(error.message || 'Registration failed');
      }
      throw error;
    }
  };

  // ==================== GOOGLE SIGN IN ====================
  const googleSignIn = async () => {
    try {
      const provider = new GoogleAuthProvider();
      const userCredential = await signInWithPopup(auth, provider);

      const userDoc = await getDoc(doc(db, 'users', userCredential.user.uid));

      if (!userDoc.exists()) {
        const userData: Partial<User> = {
          uid: userCredential.user.uid,
          email: userCredential.user.email || '',
          name: userCredential.user.displayName || '',
          role: 'student',
        };

        await setDoc(doc(db, 'users', userCredential.user.uid), {
          ...userData,
          createdAt: new Date(),
          profileComplete: false,
        });

        toast('Please complete your profile to continue.', { icon: 'ℹ️' });
        navigate('/complete-profile');
      } else {
        const userData = userDoc.data() as User;
        setUser(userData);

        navigate(getDashboardPath(userData.role));
        toast.success('Google sign-in successful!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Google sign-in failed');
      throw error;
    }
  };

  // ==================== RESET PASSWORD ====================
  const resetPassword = async (email: string) => {
    try {
      await sendPasswordResetEmail(auth, email);
      toast.success('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        toast.error('No account found with this email.');
      } else {
        toast.error(error.message || 'Failed to send reset email');
      }
      throw error;
    }
  };

  // ==================== LOGOUT ====================
  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      navigate('/');
      toast.success('Logged out successfully');
    } catch (error: any) {
      toast.error('Logout failed');
      throw error;
    }
  };

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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const AuthRedirect: React.FC = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && user) {
      if (location.pathname === '/login' || location.pathname === '/register') {
        navigate(getDashboardPath(user.role), { replace: true });
      }
    }
  }, [user, loading, navigate, location]);

  return null;
};