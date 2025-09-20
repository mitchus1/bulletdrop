import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  animate = true,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'circular':
        return 'rounded-full';
      case 'rectangular':
        return 'rounded-md';
      case 'text':
      default:
        return 'rounded';
    }
  };

  const getDefaultHeight = () => {
    if (height) return height;
    switch (variant) {
      case 'text':
        return '1rem';
      default:
        return '100%';
    }
  };

  return (
    <div
      className={`
        ${animate ? 'animate-pulse' : ''}
        bg-gray-300 dark:bg-gray-700
        ${getVariantStyles()}
        ${className}
      `}
      style={{
        width: width || '100%',
        height: getDefaultHeight(),
      }}
      aria-hidden="true"
    />
  );
};

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 1,
  className = '',
}) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, index) => (
      <Skeleton
        key={index}
        variant="text"
        width={index === lines - 1 ? '75%' : '100%'}
        className="h-4"
      />
    ))}
  </div>
);

export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
    <div className="space-y-4">
      <Skeleton variant="rectangular" height="200px" />
      <div className="space-y-2">
        <Skeleton variant="text" className="h-6" width="60%" />
        <SkeletonText lines={2} />
      </div>
    </div>
  </div>
);

export const SkeletonTable: React.FC<{
  rows?: number;
  columns?: number;
  className?: string;
}> = ({
  rows = 5,
  columns = 4,
  className = ''
}) => (
  <div className={`bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden ${className}`}>
    {/* Table Header */}
    <div className="bg-gray-50 dark:bg-gray-700 px-6 py-3">
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} variant="text" className="h-4" width="80%" />
        ))}
      </div>
    </div>

    {/* Table Rows */}
    <div className="divide-y divide-gray-200 dark:divide-gray-700">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="px-6 py-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div key={colIndex} className="flex items-center space-x-3">
                {colIndex === 0 && (
                  <Skeleton variant="circular" width="40px" height="40px" />
                )}
                <div className="flex-1">
                  <Skeleton variant="text" className="h-4" width="90%" />
                  {colIndex === 0 && (
                    <Skeleton variant="text" className="h-3 mt-1" width="70%" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonProfile: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8 ${className}`}>
    {/* Header */}
    <div className="relative h-64 rounded-xl mb-6 overflow-hidden">
      <Skeleton variant="rectangular" className="w-full h-full" />
      <div className="absolute bottom-6 left-6 flex items-center space-x-6">
        <Skeleton variant="circular" width="80px" height="80px" />
        <div className="space-y-2">
          <Skeleton variant="text" width="200px" className="h-8" />
          <Skeleton variant="text" width="150px" className="h-4" />
        </div>
      </div>
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Content */}
      <div className="lg:col-span-2 space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  </div>
);

export const SkeletonDashboard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 space-y-6 ${className}`}>
    {/* Header */}
    <div className="space-y-2">
      <Skeleton variant="text" width="300px" className="h-8" />
      <Skeleton variant="text" width="200px" className="h-4" />
    </div>

    {/* Stats Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Skeleton variant="circular" width="48px" height="48px" />
              <Skeleton variant="text" width="60px" className="h-8" />
            </div>
            <div className="space-y-2">
              <Skeleton variant="text" width="80%" className="h-4" />
              <Skeleton variant="text" width="60%" className="h-3" />
            </div>
          </div>
        </div>
      ))}
    </div>

    {/* Content Area */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <SkeletonCard />
      </div>
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>
  </div>
);