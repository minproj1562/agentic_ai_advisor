// src/pages/Dashboard/StudentSettings.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, Bell, Shield, Eye } from 'lucide-react';
import { ChangePassword } from '../../components/dashboard/ChangePassword';

export const StudentSettings: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'profile' | 'password' | 'notifications' | 'privacy'>('password');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your account preferences</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Settings Menu */}
        <div className="bg-white rounded-xl shadow-sm border p-4 space-y-2">
          {[
            { id: 'profile', label: 'Profile', icon: User },
            { id: 'password', label: 'Password', icon: Lock },
            { id: 'notifications', label: 'Notifications', icon: Bell },
            { id: 'privacy', label: 'Privacy', icon: Shield },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id as any)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                activeSection === item.id
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'hover:bg-gray-50 text-gray-700'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </button>
          ))}
        </div>

        {/* Settings Content */}
        <div className="md:col-span-3 bg-white rounded-xl shadow-sm border p-6">
          {activeSection === 'password' && <ChangePassword />}
          {activeSection === 'profile' && (
            <div>
              <h2 className="text-lg font-bold mb-4">Profile Settings</h2>
              <p className="text-sm text-gray-500">Manage your profile information</p>
            </div>
          )}
          {activeSection === 'notifications' && (
            <div>
              <h2 className="text-lg font-bold mb-4">Notification Preferences</h2>
              <p className="text-sm text-gray-500">Control how you receive notifications</p>
            </div>
          )}
          {activeSection === 'privacy' && (
            <div>
              <h2 className="text-lg font-bold mb-4">Privacy Settings</h2>
              <p className="text-sm text-gray-500">Manage your data and privacy</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};