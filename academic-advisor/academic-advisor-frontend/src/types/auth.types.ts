export interface User {
  uid: string;
  email: string;
  displayName: string | null;
  role: 'student' | 'faculty' | 'admin';
  department?: string;
  registrationNumber?: string;
  facultyId?: string;
  photoURL?: string;
  emailVerified: boolean;
  metadata: {
    createdAt: string;
    lastLoginAt: string;
    lastActiveAt: string;
  };
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
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