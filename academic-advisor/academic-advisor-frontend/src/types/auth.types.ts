// academic-advisor/academic-advisor-frontend/src/types/auth.types.ts
export interface User {
  uid: string;
  email: string;
  displayName: string | null;
  role: 'student' | 'faculty' | 'admin';
  department?: string;
  registrationNumber?: string;
  rollNumber?: string; // ✅ ADD this
  facultyId?: string;
  photoURL?: string;
  emailVerified: boolean;
  metadata: {
    createdAt: string;
    lastLoginAt: string;
    lastActiveAt: string;
    loginCount?: number;
  };
  preferences?: {
    notifications: {
      email: boolean;
      push: boolean;
      sms: boolean;
    };
    theme: 'system' | 'light' | 'dark';
    language: string;
  };
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

// ✅ UPDATE: Support both email and roll_number login
export interface LoginCredentials {
  email?: string;           // Optional for students
  roll_number?: string;     // ✅ ADD: For student login
  password: string;
  rememberMe: boolean;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  refreshToken: () => Promise<void>;
}