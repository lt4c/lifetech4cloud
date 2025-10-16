import React from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';

const navigationItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: '📊',
    href: '/dashboard',
  },
  {
    id: 'users',
    label: 'User Management',
    icon: '👥',
    href: '/admin/users',
    permission: 'user:read',
  },
  {
    id: 'roles',
    label: 'Role Management',
    icon: '🔒',
    href: '/admin/roles',
    permission: 'role:read',
  },
  {
    id: 'vps',
    label: 'VPS Management',
    icon: '🖥️',
    href: '/admin/vps',
    permission: 'vps:read',
  },
  {
    id: 'support',
    label: 'Support',
    icon: '💬',
    href: '/admin/support',
    permission: 'support:read',
  },
  {
    id: 'monitoring',
    label: 'System Monitoring',
    icon: '📈',
    href: '/admin/monitoring',
    permission: 'system:monitoring',
    children: [
      {
        id: 'workers',
        label: 'Worker Status',
        icon: '⚙️',
        href: '/admin/monitoring/workers',
      },
      {
        id: 'metrics',
        label: 'System Metrics',
        icon: '📊',
        href: '/admin/monitoring/metrics',
      },
      {
        id: 'audit',
        label: 'Audit Logs',
        icon: '📋',
        href: '/admin/monitoring/audit',
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    href: '/admin/settings',
    permission: 'settings:read',
  },
];

export default function Home() {
  const user = {
    name: 'Admin User',
    email: 'admin@lifetech4code.com',
    avatar: '/api/placeholder/32/32',
  };

  return (
    <AdminLayout
      title="Admin Dashboard"
      navigationItems={navigationItems}
      currentPath="/dashboard"
      user={user}
    >
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="glass rounded-lg p-6">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Welcome to LifeTech4Code Admin
          </h1>
          <p className="text-text-secondary">
            Manage users, roles, VPS instances, and system settings from this centralized dashboard.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-surface-hover rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Total Users</p>
                <p className="text-2xl font-bold text-text-primary">1,234</p>
              </div>
              <div className="text-3xl">👥</div>
            </div>
          </div>
          <div className="bg-surface-hover rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Active VPS</p>
                <p className="text-2xl font-bold text-text-primary">89</p>
              </div>
              <div className="text-3xl">🖥️</div>
            </div>
          </div>
          <div className="bg-surface-hover rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Support Tickets</p>
                <p className="text-2xl font-bold text-text-primary">12</p>
              </div>
              <div className="text-3xl">💬</div>
            </div>
          </div>
          <div className="bg-surface-hover rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">Revenue</p>
                <p className="text-2xl font-bold text-text-primary">$15,420</p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-surface rounded-lg p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Recent Activity
          </h2>
          <div className="space-y-4">
            {[
              'User john_doe created a new VPS instance',
              'Role "Moderator" was updated by admin',
              'Support ticket #1234 was resolved',
              'System backup completed successfully',
            ].map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 py-2">
                <div className="w-2 h-2 bg-primary rounded-full"></div>
                <span className="text-text-secondary">{activity}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
