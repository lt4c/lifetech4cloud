'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface NavbarProps {
  title?: string;
  user?: {
    name: string;
    avatar?: string;
    email?: string;
  };
  onToggleSidebar?: () => void;
  sidebarCollapsed?: boolean;
  children?: React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({
  title,
  user,
  onToggleSidebar,
  sidebarCollapsed = false,
  children,
}) => {
  return (
    <nav className="bg-surface border-b border-gray-700 px-4 py-3 flex items-center justify-between shadow-sm">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-2 text-text-secondary hover:text-text-primary hover:bg-surface-hover rounded-md transition-colors focus-ring md:hidden"
          >
            {sidebarCollapsed ? '☰' : '✕'}
          </button>
        )}
        {title && (
          <h1 className="text-xl font-semibold text-text-primary truncate">
            {title}
          </h1>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {children}

        {/* User menu */}
        {user && (
          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-text-primary">
                {user.name}
              </div>
              {user.email && (
                <div className="text-xs text-text-secondary">
                  {user.email}
                </div>
              )}
            </div>
            {user.avatar ? (
              <img
                src={user.avatar}
                alt={user.name}
                className="w-8 h-8 rounded-full border-2 border-primary"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium border-2 border-primary">
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            <button className="p-1 text-text-secondary hover:text-text-primary">
              ▼
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};
