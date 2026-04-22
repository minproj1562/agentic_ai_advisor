// src/components/dashboard/sections/Settings.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  User, Bell, Shield, Palette, Save,
  Lock, Eye, EyeOff, CheckCircle,
  AlertCircle, Loader2, ShieldCheck,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  EmailAuthProvider,
  reauthenticateWithCredential,
  updatePassword,
} from 'firebase/auth';
import {
  doc, getDoc, updateDoc, serverTimestamp,
} from 'firebase/firestore';
import { auth, db } from '../../../services/firebase.config';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SettingsProps {
  facultyId: string;
}

// ─── Password strength helper ─────────────────────────────────────────────────

const getPasswordStrength = (password: string) => {
  let score = 0;
  if (password.length >= 8)           score++;
  if (/[A-Z]/.test(password))         score++;
  if (/[a-z]/.test(password))         score++;
  if (/\d/.test(password))            score++;
  if (/[^A-Za-z0-9]/.test(password))  score++;

  if (score <= 1) return { score, label: 'Weak',   color: 'bg-red-500',    text: 'text-red-500'    };
  if (score <= 3) return { score, label: 'Medium', color: 'bg-yellow-500', text: 'text-yellow-500' };
  return              { score, label: 'Strong', color: 'bg-green-500',  text: 'text-green-500'  };
};

// ─── Component ────────────────────────────────────────────────────────────────

const Settings: React.FC<SettingsProps> = ({ facultyId }) => {
  const [activeTab, setActiveTab] = useState('profile');

  // ── Profile state ──────────────────────────────────────────────────────────
  const [profileData, setProfileData] = useState({
    name:       '',
    email:      '',
    phone:      '',
    department: '',
    bio:        '',
  });

  // ── Notification state ─────────────────────────────────────────────────────
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications:   true,
    pushNotifications:    true,
    smsNotifications:     false,
    menteeUpdates:        true,
    appointmentReminders: true,
    systemUpdates:        false,
  });

  // ── Password state ─────────────────────────────────────────────────────────
  const [mustChangePassword, setMustChangePassword]   = useState(false);
  const [defaultPasswordHint, setDefaultPasswordHint] = useState('Fcrit@123');
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword:     '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new:     false,
    confirm: false,
  });
  const [passwordErrors, setPasswordErrors]     = useState<Record<string, string>>({});
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordChanged, setPasswordChanged]       = useState(false);

  // ── Privacy state ──────────────────────────────────────────────────────────
  const [privacySettings, setPrivacySettings] = useState({
    profileVisible: true,
    showEmail:      false,
    showPhone:      false,
    allowMessages:  true,
  });

  // ── Preferences state ──────────────────────────────────────────────────────
  const [preferences, setPreferences] = useState({
    theme:    'system',
    language: 'en',
    timezone: 'Asia/Kolkata',
  });

  // ── Load Firestore settings on mount ──────────────────────────────────────

  useEffect(() => {
    const loadSettings = async () => {
      if (!facultyId) return;
      try {
        const userDoc = await getDoc(doc(db, 'users', facultyId));
        if (userDoc.exists()) {
          const data = userDoc.data();

          // ✅ Read must_change_password flag set by admin_service.py
          setMustChangePassword(data?.must_change_password === true);

          // ✅ Read the default password hint stored by admin_service.py
          // Falls back to 'Fcrit@123' if not stored
          setDefaultPasswordHint(
            data?.default_password_hint || 'Fcrit@123'
          );

          // Pre-fill profile fields
          setProfileData({
            name:       data?.name       || data?.displayName || '',
            email:      data?.email      || '',
            phone:      data?.phone      || '',
            department: data?.department || '',
            bio:        data?.bio        || '',
          });

          // Pre-fill notifications
          setNotificationSettings((prev) => ({
            ...prev,
            ...(data?.preferences?.notifications || {}),
          }));
        }
      } catch (err) {
        console.error('Error loading settings:', err);
      }
    };
    loadSettings();
  }, [facultyId]);

  // ── Save settings mutation ─────────────────────────────────────────────────

  const saveSettings = useMutation({
    mutationFn: async (data: any) => {
      const token    = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/settings`,
        {
          method:  'PUT',
          headers: {
            'Content-Type':  'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        }
      );
      return response.json();
    },
    onSuccess: () => toast.success('Settings saved successfully'),
    onError:   () => toast.error('Failed to save settings'),
  });

  // ── Password validation ───────────────────────────────────────────────────

  const validatePassword = (): boolean => {
    const errs: Record<string, string> = {};

    if (!passwordForm.currentPassword) {
      errs.currentPassword = 'Current password is required';
    }
    if (!passwordForm.newPassword) {
      errs.newPassword = 'New password is required';
    } else if (passwordForm.newPassword.length < 8) {
      errs.newPassword = 'Must be at least 8 characters';
    } else if (!/[A-Z]/.test(passwordForm.newPassword)) {
      errs.newPassword = 'Must include at least one uppercase letter';
    } else if (!/[a-z]/.test(passwordForm.newPassword)) {
      errs.newPassword = 'Must include at least one lowercase letter';
    } else if (!/\d/.test(passwordForm.newPassword)) {
      errs.newPassword = 'Must include at least one number';
    } else if (passwordForm.newPassword === passwordForm.currentPassword) {
      errs.newPassword = 'New password must differ from current password';
    }
    if (!passwordForm.confirmPassword) {
      errs.confirmPassword = 'Please confirm your new password';
    } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }

    setPasswordErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // ── Handle password change ────────────────────────────────────────────────

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePassword()) return;

    setIsChangingPassword(true);
    try {
      const user = auth.currentUser;
      if (!user || !user.email) throw new Error('Not authenticated');

      // Step 1: Re-authenticate with current password
      const credential = EmailAuthProvider.credential(
        user.email,
        passwordForm.currentPassword
      );
      await reauthenticateWithCredential(user, credential);

      // Step 2: Update Firebase Auth password
      await updatePassword(user, passwordForm.newPassword);

      // Step 3: ✅ Clear must_change_password flag in Firestore
      // We update both 'users' and 'faculty' collections for consistency
      const updateData = {
        must_change_password: false,       // ← flag cleared
        password_changed_at: serverTimestamp(),
        default_password_hint: null,       // ← remove the hint
      };
      await updateDoc(doc(db, 'users',   facultyId), updateData);
      // 'faculty' collection may not have this field — use try/catch
      try {
        await updateDoc(doc(db, 'faculty', facultyId), {
          must_change_password:  false,
          password_changed_at:  serverTimestamp(),
        });
      } catch {
        // Non-fatal: faculty collection update is best-effort
      }

      // Step 4: Update local state
      setMustChangePassword(false);
      setPasswordChanged(true);
      setPasswordForm({
        currentPassword: '',
        newPassword:     '',
        confirmPassword: '',
      });
      setPasswordErrors({});

      toast.success('✅ Password changed successfully!');
      setTimeout(() => setPasswordChanged(false), 3000);

    } catch (error: any) {
      console.error('Change password error:', error);

      if (
        error.code === 'auth/wrong-password' ||
        error.code === 'auth/invalid-credential'
      ) {
        setPasswordErrors({
          currentPassword: 'Current password is incorrect',
        });
      } else if (error.code === 'auth/weak-password') {
        setPasswordErrors({ newPassword: 'Password is too weak' });
      } else if (error.code === 'auth/requires-recent-login') {
        toast.error(
          'Please log out and log in again before changing your password'
        );
      } else {
        toast.error(error.message || 'Failed to change password');
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  // ── Tabs config ───────────────────────────────────────────────────────────

  const tabs = [
    { id: 'profile',       label: 'Profile',      icon: User    },
    { id: 'password',      label: 'Password',      icon: Lock    },
    { id: 'notifications', label: 'Notifications', icon: Bell    },
    { id: 'privacy',       label: 'Privacy',       icon: Shield  },
    { id: 'preferences',   label: 'Preferences',   icon: Palette },
  ];

  const strength = getPasswordStrength(passwordForm.newPassword);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">

      {/* Page title */}
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Settings
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Manage your account and preferences
        </p>
      </div>

      {/* ✅ Must-change-password banner — shown everywhere except Password tab */}
      {mustChangePassword && activeTab !== 'password' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-xl p-4 flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                Please change your default password
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                Your account uses the default password{' '}
                {/* ✅ Dynamic — read from Firestore, not hardcoded */}
                <code className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">
                  {defaultPasswordHint}
                </code>
                . Update it now to secure your account.
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('password')}
            className="flex-shrink-0 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition-colors whitespace-nowrap"
          >
            Change Now →
          </button>
        </motion.div>
      )}

      {/* Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">

        {/* Tab bar */}
        <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <nav className="flex min-w-max">
            {tabs.map((tab) => {
              const Icon     = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative flex items-center gap-2 px-6 py-4 border-b-2 transition-colors whitespace-nowrap ${
                    isActive
                      ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{tab.label}</span>
                  {/* ✅ Red dot on Password tab when must_change_password is True */}
                  {tab.id === 'password' && mustChangePassword && (
                    <span className="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">

          {/* ── Profile Tab ── */}
          {activeTab === 'profile' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) =>
                      setProfileData({ ...profileData, name: e.target.value })
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={profileData.email}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-gray-400">
                    Email cannot be changed
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) =>
                      setProfileData({ ...profileData, phone: e.target.value })
                    }
                    placeholder="+91 XXXXX XXXXX"
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Department
                  </label>
                  <input
                    type="text"
                    value={profileData.department}
                    disabled
                    className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Bio
                  </label>
                  <textarea
                    value={profileData.bio}
                    onChange={(e) =>
                      setProfileData({ ...profileData, bio: e.target.value })
                    }
                    rows={3}
                    placeholder="Brief description about yourself..."
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => saveSettings.mutate(profileData)}
                  disabled={saveSettings.isPending}
                  className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white rounded-lg transition-all"
                >
                  {saveSettings.isPending
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Save    className="w-4 h-4" />
                  }
                  Save Changes
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Password Tab ── */}
          {activeTab === 'password' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-lg space-y-6"
            >
              {/* Header */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                  <Lock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Change Password
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Update your account password
                  </p>
                </div>
              </div>

              {/* ✅ First-login warning — shows dynamic password hint from Firestore */}
              {mustChangePassword && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4 flex items-start gap-3"
                >
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                      Action required: Change your default password
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                      Enter{' '}
                      {/* ✅ Read from Firestore — not hardcoded */}
                      <code className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">
                        {defaultPasswordHint}
                      </code>{' '}
                      as your current password, then set a new one.
                    </p>
                  </div>
                </motion.div>
              )}

              {/* ✅ Success state */}
              {passwordChanged && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-4 flex items-center gap-3"
                >
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">
                    Password changed successfully!
                  </p>
                </motion.div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-5">

                {/* Current Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Current Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type={showPasswords.current ? 'text' : 'password'}
                      value={passwordForm.currentPassword}
                      onChange={(e) => {
                        setPasswordForm((p) => ({
                          ...p, currentPassword: e.target.value,
                        }));
                        if (passwordErrors.currentPassword) {
                          setPasswordErrors((p) => ({
                            ...p, currentPassword: '',
                          }));
                        }
                      }}
                      // ✅ Placeholder shows the actual default password from Firestore
                      placeholder={
                        mustChangePassword
                          ? `${defaultPasswordHint} (default)`
                          : 'Enter current password'
                      }
                      className={`w-full pl-10 pr-10 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                        passwordErrors.currentPassword
                          ? 'border-red-300 focus:ring-red-500'
                          : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowPasswords((p) => ({
                          ...p, current: !p.current,
                        }))
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPasswords.current
                        ? <EyeOff className="w-4 h-4" />
                        : <Eye    className="w-4 h-4" />
                      }
                    </button>
                  </div>
                  {passwordErrors.currentPassword && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {passwordErrors.currentPassword}
                    </p>
                  )}
                </div>

                {/* New Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type={showPasswords.new ? 'text' : 'password'}
                      value={passwordForm.newPassword}
                      onChange={(e) => {
                        setPasswordForm((p) => ({
                          ...p, newPassword: e.target.value,
                        }));
                        if (passwordErrors.newPassword) {
                          setPasswordErrors((p) => ({
                            ...p, newPassword: '',
                          }));
                        }
                      }}
                      placeholder="Enter new password"
                      className={`w-full pl-10 pr-10 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                        passwordErrors.newPassword
                          ? 'border-red-300 focus:ring-red-500'
                          : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowPasswords((p) => ({ ...p, new: !p.new }))
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPasswords.new
                        ? <EyeOff className="w-4 h-4" />
                        : <Eye    className="w-4 h-4" />
                      }
                    </button>
                  </div>

                  {/* Strength bar */}
                  {passwordForm.newPassword && (
                    <div className="mt-2">
                      <div className="flex gap-1 mb-1">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <div
                            key={i}
                            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                              i <= strength.score
                                ? strength.color
                                : 'bg-gray-200 dark:bg-gray-600'
                            }`}
                          />
                        ))}
                      </div>
                      <p className={`text-xs ${strength.text}`}>
                        Strength: <strong>{strength.label}</strong>
                      </p>
                    </div>
                  )}

                  {passwordErrors.newPassword && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {passwordErrors.newPassword}
                    </p>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type={showPasswords.confirm ? 'text' : 'password'}
                      value={passwordForm.confirmPassword}
                      onChange={(e) => {
                        setPasswordForm((p) => ({
                          ...p, confirmPassword: e.target.value,
                        }));
                        if (passwordErrors.confirmPassword) {
                          setPasswordErrors((p) => ({
                            ...p, confirmPassword: '',
                          }));
                        }
                      }}
                      placeholder="Confirm new password"
                      className={`w-full pl-10 pr-10 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
                        passwordErrors.confirmPassword
                          ? 'border-red-300 focus:ring-red-500'
                          : passwordForm.confirmPassword &&
                            passwordForm.newPassword ===
                              passwordForm.confirmPassword
                          ? 'border-green-400 focus:ring-green-500'
                          : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowPasswords((p) => ({
                          ...p, confirm: !p.confirm,
                        }))
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPasswords.confirm
                        ? <EyeOff className="w-4 h-4" />
                        : <Eye    className="w-4 h-4" />
                      }
                    </button>
                  </div>
                  {passwordForm.confirmPassword &&
                    passwordForm.newPassword === passwordForm.confirmPassword && (
                    <p className="mt-1 text-xs text-green-500 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Passwords match
                    </p>
                  )}
                  {passwordErrors.confirmPassword && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {passwordErrors.confirmPassword}
                    </p>
                  )}
                </div>

                {/* Requirements checklist */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-3">
                    Password requirements:
                  </p>
                  <ul className="space-y-1.5">
                    {[
                      { label: 'At least 8 characters',     met: passwordForm.newPassword.length >= 8 },
                      { label: 'One uppercase letter (A–Z)', met: /[A-Z]/.test(passwordForm.newPassword) },
                      { label: 'One lowercase letter (a–z)', met: /[a-z]/.test(passwordForm.newPassword) },
                      { label: 'One number (0–9)',           met: /\d/.test(passwordForm.newPassword) },
                    ].map(({ label, met }) => (
                      <li
                        key={label}
                        className={`text-xs flex items-center gap-2 transition-colors ${
                          met
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-gray-500 dark:text-gray-400'
                        }`}
                      >
                        <CheckCircle
                          className={`w-3.5 h-3.5 flex-shrink-0 ${
                            met
                              ? 'text-green-500'
                              : 'text-gray-300 dark:text-gray-600'
                          }`}
                        />
                        {label}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={isChangingPassword}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                >
                  {isChangingPassword ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Changing Password...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      Change Password
                    </>
                  )}
                </button>
              </form>
            </motion.div>
          )}

          {/* ── Notifications Tab ── */}
          {activeTab === 'notifications' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {[
                { key: 'emailNotifications',   label: 'Email Notifications',   desc: 'Receive updates via email'           },
                { key: 'pushNotifications',    label: 'Push Notifications',    desc: 'Browser push notifications'          },
                { key: 'smsNotifications',     label: 'SMS Notifications',     desc: 'Receive SMS alerts'                  },
                { key: 'menteeUpdates',        label: 'Mentee Updates',        desc: 'Updates about your mentees'          },
                { key: 'appointmentReminders', label: 'Appointment Reminders', desc: 'Reminders for upcoming appointments' },
                { key: 'systemUpdates',        label: 'System Updates',        desc: 'Platform updates and announcements'  },
              ].map(({ key, label, desc }) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {desc}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setNotificationSettings((prev) => ({
                        ...prev,
                        [key]: !prev[key as keyof typeof prev],
                      }))
                    }
                    className={`relative w-11 h-6 rounded-full transition-colors focus:outline-none ${
                      notificationSettings[key as keyof typeof notificationSettings]
                        ? 'bg-indigo-600'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                        notificationSettings[key as keyof typeof notificationSettings]
                          ? 'translate-x-5'
                          : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              ))}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() =>
                    saveSettings.mutate({ notifications: notificationSettings })
                  }
                  disabled={saveSettings.isPending}
                  className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white rounded-lg transition-all"
                >
                  {saveSettings.isPending
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Save    className="w-4 h-4" />
                  }
                  Save Preferences
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Privacy Tab ── */}
          {activeTab === 'privacy' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {[
                { key: 'profileVisible', label: 'Public Profile',  desc: 'Make your profile visible to students' },
                { key: 'showEmail',      label: 'Show Email',      desc: 'Display your email on your profile'    },
                { key: 'showPhone',      label: 'Show Phone',      desc: 'Display your phone number on profile'  },
                { key: 'allowMessages',  label: 'Allow Messages',  desc: 'Let students send you messages'        },
              ].map(({ key, label, desc }) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {desc}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      setPrivacySettings((prev) => ({
                        ...prev,
                        [key]: !prev[key as keyof typeof prev],
                      }))
                    }
                    className={`relative w-11 h-6 rounded-full transition-colors focus:outline-none ${
                      privacySettings[key as keyof typeof privacySettings]
                        ? 'bg-indigo-600'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                        privacySettings[key as keyof typeof privacySettings]
                          ? 'translate-x-5'
                          : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              ))}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() =>
                    saveSettings.mutate({ privacy: privacySettings })
                  }
                  disabled={saveSettings.isPending}
                  className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white rounded-lg transition-all"
                >
                  {saveSettings.isPending
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Save    className="w-4 h-4" />
                  }
                  Save Privacy Settings
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Preferences Tab ── */}
          {activeTab === 'preferences' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Theme
                  </label>
                  <select
                    value={preferences.theme}
                    onChange={(e) =>
                      setPreferences((p) => ({ ...p, theme: e.target.value }))
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System Default</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Language
                  </label>
                  <select
                    value={preferences.language}
                    onChange={(e) =>
                      setPreferences((p) => ({
                        ...p, language: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="mr">Marathi</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Timezone
                  </label>
                  <select
                    value={preferences.timezone}
                    onChange={(e) =>
                      setPreferences((p) => ({
                        ...p, timezone: e.target.value,
                      }))
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="Asia/Kolkata">IST (Asia/Kolkata)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => saveSettings.mutate({ preferences })}
                  disabled={saveSettings.isPending}
                  className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 text-white rounded-lg transition-all"
                >
                  {saveSettings.isPending
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Save    className="w-4 h-4" />
                  }
                  Save Preferences
                </button>
              </div>
            </motion.div>
          )}

        </div>
      </div>
    </div>
  );
};

export default Settings;