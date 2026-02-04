// src/contexts/AuthContext.tsx (Fixed faculty login detection)
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
  sendPasswordResetEmail
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
  email: string;
  password: string;
  rememberMe?: boolean;
  userType?: 'student' | 'faculty'; // ADD THIS
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
      const { email, password, rememberMe, userType } = credentials;
      
      console.log('Login attempt:', { email, userType });
      
      // First, try to sign in
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const userDoc = await getDoc(doc(db, 'users', userCredential.user.uid));
      
      if (!userDoc.exists()) {
        await signOut(auth);
        toast.error('Account not properly registered. Please complete registration.');
        navigate('/register');
        throw new Error('Account not properly registered');
      }
      
      const userData = userDoc.data() as User;
      console.log('User data from DB:', userData);
      
      // FIXED: Check user type from credentials instead of path
      if (userType && userData.role !== userType) {
        await signOut(auth);
        
        if (userData.role === 'faculty' && userType === 'student') {
          toast.error('You are a faculty member. Please use the faculty login.');
        } else if (userData.role === 'student' && userType === 'faculty') {
          toast.error('You are a student. Please use the student login.');
        } else {
          toast.error(`Account type mismatch. Your account is ${userData.role}.`);
        }
        
        throw new Error('Wrong login portal');
      }
      
      setUser(userData);
      
      // Navigate based on role
          if (userData.role === 'faculty') {
      // Check if profile setup is complete
      try {
        const setupStatus = await apiClient.get('/faculty-profile/check-setup-status');
        
        if (setupStatus.data.needs_setup) {
          navigate('/faculty/profile-setup', { replace: true });
          toast.success('Please complete your profile setup.');
          return;
        }
      } catch (error) {
        // If check fails, redirect to setup anyway for safety
        console.log('Setup status check failed, redirecting to setup');
      }
      
      navigate('/faculty/dashboard', { replace: true });
      toast.success(`Welcome back, Professor ${userData.name}!`);
    } else if (userData.role === 'student') {
      navigate('/student/dashboard', { replace: true });
      toast.success(`Welcome back, ${userData.name}!`);
    }
    
  } catch (error: any) {
      console.error('Login error:', error);
      
      // Handle specific auth errors
      if (error.code === 'auth/user-not-found') {
        toast.error('No account found with this email. Please register first.');
        setTimeout(() => navigate('/register'), 2000);
      } else if (error.code === 'auth/wrong-password') {
        toast.error('Incorrect password. Please try again.');
      } else if (error.code === 'auth/invalid-email') {
        toast.error('Invalid email format.');
      } else if (error.message === 'Wrong login portal') {
        // Already handled above
      } else if (error.message === 'Account not properly registered') {
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
      
      // Ensure role is set
      const completeUserData = {
        ...userData,
        uid: userCredential.user.uid,
        email: userCredential.user.email,
        createdAt: new Date(),
        profileComplete: false
      };

      await setDoc(doc(db, 'users', userCredential.user.uid), completeUserData);

      // Sign out after registration
      await signOut(auth);
      
      const roleMessage = userData.role === 'faculty' ? 'Faculty registration successful!' : 'Student registration successful!';
      toast.success(`${roleMessage} Please login to continue.`);
      
      // Redirect to login page
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
        // New Google user - need to complete registration
        const userData: Partial<User> = {
          uid: userCredential.user.uid,
          email: userCredential.user.email || '',
          name: userCredential.user.displayName || '',
          role: 'student', // Default for Google sign-in
        };
        
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          ...userData,
          createdAt: new Date(),
          profileComplete: false
        });
        
        toast('Please complete your profile to continue.', {
          icon: 'ℹ️',
        });
        navigate('/complete-profile');
      } else {
        const userData = userDoc.data() as User;
        setUser(userData);
        
        if (userData.role === 'faculty') {
          navigate('/faculty/dashboard');
        } else if (userData.role === 'student') {
          navigate('/student/dashboard');
        }
        
        toast.success('Google sign-in successful!');
      }
    } catch (error: any) {
      toast.error(error.message || 'Google sign-in failed');
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
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      isAuthenticated: !!user, 
      login, 
      register, 
      logout, 
      googleSignIn,
      resetPassword 
    }}>
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
        if (user.role === 'faculty') {
          navigate('/faculty/dashboard', { replace: true });
        } else if (user.role === 'student') {
          navigate('/student/dashboard', { replace: true });
        }
      }
    }
  }, [user, loading, navigate, location]);

  return null;
};