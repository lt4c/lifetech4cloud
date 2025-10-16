'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  permission?: string;
  children?: NavItem[];
}

interface AdminLayoutProps {
  children: React.ReactNode;
  title?: string;
  navigationItems: NavItem[];
  currentPath: string;
  user?: {
    name: string;
    avatar?: string;
    email?: string;
  };
  navbarActions?: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({
  children,
  title,
  navigationItems,
  currentPath,
  user,
  navbarActions,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <div className="flex">
        {/* Sidebar */}
        <Sidebar
          items={navigationItems}
          currentPath={currentPath}
          collapsed={sidebarCollapsed}
          onToggle={toggleSidebar}
        />

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Navbar */}
          <Navbar
            title={title}
            user={user}
            onToggleSidebar={toggleSidebar}
            sidebarCollapsed={sidebarCollapsed}
          >
            {navbarActions}
          </Navbar>

          {/* Page content */}
          <main className="flex-1 p-6 overflow-auto">
            <div className="max-w-7xl mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};
