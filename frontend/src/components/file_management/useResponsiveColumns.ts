import { useMemo, useState } from 'react';
import { FileTableConfig } from './types';

export const useResponsiveColumns = (baseConfig: FileTableConfig) => {
  const [showAllColumns, setShowAllColumns] = useState(true); // Always show all columns by default

  const responsiveConfig = useMemo(() => {
    // Always return the base config since we want to show all columns
    return baseConfig;
  }, [baseConfig]);

  return {
    config: responsiveConfig,
    showAllColumns,
    setShowAllColumns,
    screenWidth: typeof window !== 'undefined' ? window.innerWidth : 1024,
  };
};
