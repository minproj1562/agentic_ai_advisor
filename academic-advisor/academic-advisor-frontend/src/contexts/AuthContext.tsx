// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Helper: get dashboard path for each role
const getDashboardPath = (role: string): string => {
  switch (role) {
    case 'faculty': return '/faculty/dashboard';
    case 'admin': return '/admin/dashboard';
    default: return '/student/dashboard';
  }
};

// Helper: get role label
const getRoleLabel = (role: string): string => {
  switch (role) {
    case 'faculty': return 'Faculty';
    case 'admin': return 'Admin';
    default: return 'Student';
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

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

  const login = async (credentials: LoginCredentials) => {
    try {
      const { email, roll_number, password, rememberMe, userType } = credentials;
      
      console.log('Login attempt:', { email, roll_number, userType });
      
      let firebaseUser: FirebaseUser;

      // ===== STUDENT LOGIN (roll_number) =====
      if (userType === 'student' && roll_number) {
        try {
          // Call backend to authenticate student with roll_number
          const response = await apiClient.post('/auth/login-student', {
            roll_number,
            password,
          });

          // Sign in with Firebase custom token
          await signInWithCustomToken(auth, response.data.token);
          firebaseUser = auth.currentUser!;

          if (!firebaseUser) {
            throw new Error('Failed to authenticate with Firebase');
          }
        } catch (error: any) {
          console.error('Student login error:', error);
          if (error.response?.status === 401) {
            toast.error('Invalid roll number or password');
            throw new Error('Invalid roll number or password');
          } else if (error.response?.data?.message) {
            toast.error(error.response.data.message);
            throw new Error(error.response.data.message);
          } else {
            toast.error('Student authentication failed');
            throw new Error('Student authentication failed');
          }
        }
      }
      // ===== EMAIL/PASSWORD LOGIN (faculty/admin) =====
      else if (email && (userType === 'faculty' || userType === 'admin')) {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        firebaseUser = userCredential.user;
      } else {
        throw new Error('Invalid credentials provided');
      }

      // Get user data from Firestore
      const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));

      if (!userDoc.exists()) {
        await signOut(auth);
        toast.error('Account not properly registered. Please complete registration.');
        navigate('/register');
        throw new Error('Account not properly registered');
      }

      const userData = userDoc.data() as User;
      console.log('User data from Firestore:', { role: userData.role, name: userData.name });

      // ===== ROLE MISMATCH CHECK =====
      if (userType && userData.role !== userType) {
        await signOut(auth);

        const actualRole = getRoleLabel(userData.role);
        const attemptedRole = getRoleLabel(userType);

        toast.error(
          `You are registered as ${actualRole}. Please switch to the ${actualRole} login tab.`
        );

        throw new Error('Wrong login portal');
      }

      // ===== SET USER STATE =====
      setUser(userData);

      // ===== NAVIGATE BASED ON ROLE =====
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

      } else if (userData.role === 'student') {
        navigate('/student/dashboard', { replace: true });
        toast.success(`Welcome back, ${userData.name}!`);

      } else {
        // Unknown role fallback
        navigate('/student/dashboard', { replace: true });
        toast.success(`Welcome, ${userData.name}!`);
      }

    } catch (error: any) {
      console.error('Login error:', error);

      if (error.code === 'auth/user-not-found') {
        toast.error('No account found with this email. Please register first.');
        setTimeout(() => navigate('/register'), 2000);
      } else if (error.code === 'auth/wrong-password') {
        toast.error('Incorrect password. Please try again.');
      } else if (error.code === 'auth/invalid-credential') {
        toast.error('Invalid credentials. Please check your email and password.');
      } else if (error.code === 'auth/invalid-email') {
        toast.error('Invalid email format.');
      } else if (error.message === 'Wrong login portal') {
        // Already handled above with toast
      } else if (error.message === 'Account not properly registered') {
        // Already handled above
      } else if (error.message === 'Invalid roll number or password') {
        // Already handled above
      } else if (error.message === 'Student authentication failed') {
        // Already handled above
      } else {
        toast.error(error.message || 'Login failed');
      }
      throw error;
    }
  };

  const register = async (email: string, password: string, userData: Partial<User>) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);

      const completeUserData = {
        ...userData,
        uid: userCredential.user.uid,
        email: userCredential.user.email,
        createdAt: new Date(),
        profileComplete: false
      };

      await setDoc(doc(db, 'users', userCredential.user.uid), completeUserData);

      await signOut(auth);

      const roleMessage = userData.role === 'faculty'
        ? 'Faculty registration successful!'
        : 'Registration successful!';
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
          profileComplete: false
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
      if (error.code === 'auth/popup-closed-by-user') {
        toast.error('Sign-in cancelled');
      } else if (error.code === 'auth/popup-blocked') {
        toast.error('Popup blocked. Please allow popups for this site.');
      } else {
        toast.error(error.message || 'Google sign-in failed');
      }
      throw error;
    }
  };

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
        resetPassword
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
      // If user is on login/register page but already authenticated, redirect to dashboard
      if (location.pathname === '/login' || location.pathname === '/register') {
        navigate(getDashboardPath(user.role), { replace: true });
      }
    }
  }, [user, loading, navigate, location]);

  return null;
};