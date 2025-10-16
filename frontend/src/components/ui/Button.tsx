'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  className,
  disabled,
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium transition-all duration-200 ease-in-out focus-ring rounded-md disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-primary hover:bg-primary/90 text-white shadow-md hover:shadow-lg',
    secondary: 'bg-secondary hover:bg-secondary/90 text-white shadow-md hover:shadow-lg',
    outline:
      'border border-primary text-primary hover:bg-primary hover:text-white bg-transparent',
    ghost: 'text-primary hover:bg-surface-hover bg-transparent',
    danger: 'bg-error hover:bg-error/90 text-white shadow-md hover:shadow-lg',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2',
    xl: 'px-8 py-4 text-xl gap-3',
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        loading && 'cursor-wait',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
      )}
      {!loading && leftIcon && <span className="mr-1.5">{leftIcon}</span>}
      {children}
      {!loading && rightIcon && <span className="ml-1.5">{rightIcon}</span>}
    </button>
  );
};
