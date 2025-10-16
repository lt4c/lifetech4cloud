'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  permission?: string;
  children?: NavItem[];
}

interface SidebarProps {
  items: NavItem[];
  currentPath: string;
  collapsed?: boolean;
  onToggle?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  items,
  currentPath,
  collapsed = false,
  onToggle,
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const renderNavItem = (item: NavItem, level = 0) => {
    const isActive = currentPath === item.href;
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;
    const indentClass = level > 0 ? `ml-${level * 4}` : '';

    return (
      <div key={item.id}>
        <a
          href={item.href}
          className={cn(
            'flex items-center px-3 py-2 text-sm font-medium transition-all duration-200 ease-in-out rounded-md mx-2',
            isActive
              ? 'bg-primary text-white shadow-md'
              : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary',
            level > 0 && 'text-sm',
            indentClass
          )}
          onClick={(e) => {
            if (hasChildren) {
              e.preventDefault();
              toggleExpanded(item.id);
            }
          }}
        >
          <span className="flex items-center justify-center w-5 h-5 mr-3 text-lg">
            {item.icon}
          </span>
          {!collapsed && (
            <>
              <span className="flex-1 truncate">{item.label}</span>
              {hasChildren && (
                <span className={`ml-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                  ▶
                </span>
              )}
            </>
          )}
        </a>
        {!collapsed && hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map((child) => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={cn(
        'bg-surface border-r border-gray-700 flex flex-col transition-all duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        {!collapsed && (
          <h1 className="text-xl font-bold gradient-primary bg-clip-text text-transparent">
            LTC4C Admin
          </h1>
        )}
        <button
          onClick={onToggle}
          className="p-1 text-text-secondary hover:text-text-primary hover:bg-surface-hover rounded-md transition-colors focus-ring"
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {items.map((item) => renderNavItem(item))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        {!collapsed && (
          <div className="text-xs text-text-muted">
            © 2025 LifeTech4Code
          </div>
        )}
      </div>
    </div>
  );
};
