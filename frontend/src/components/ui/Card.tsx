'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'elevated';
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'default',
  hover = false,
  padding = 'md',
}) => {
  const baseClasses = 'rounded-lg border transition-all duration-300 ease-in-out';

  const variantClasses = {
    default: 'bg-surface border-gray-700',
    glass: 'glass',
    elevated: 'bg-surface border-gray-700 shadow-lg',
  };

  const hoverClasses = hover ? 'glass-hover' : '';

  const paddingClasses = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-12',
  };

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        hoverClasses,
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
};
