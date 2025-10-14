import { FileTableConfig } from './types';

export const defaultFileTableConfig: FileTableConfig = {
  columns: [
    {
      id: 'name',
      label: 'Name',
      size: 250,
      minSize: 200,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 1,
    },
    {
      id: 'equipment',
      label: 'Equipment',
      size: 150,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 2,
    },
    {
      id: 'accessGroup',
      label: 'Group',
      size: 100,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 3,
    },
    {
      id: 'uploadDate',
      label: 'Date',
      size: 100,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 4,
    },
    {
      id: 'size',
      label: 'Size',
      size: 80,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 5,
    },
    {
      id: 'uploader',
      label: 'Uploader',
      size: 120,
      priority: 'low',
      responsive: {
        mobile: false,
        tablet: false,
        desktop: false,
      },
      order: 6,
    },
    {
      id: 'status',
      label: 'Status',
      size: 100,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 7,
    },

    {
      id: 'actions',
      label: 'Actions',
      size: 120,
      priority: 'high',
      responsive: {
        mobile: true,
        tablet: true,
        desktop: true,
      },
      order: 8,
    },
  ],
  defaultView: 'detailed',
  responsiveBreakpoints: {
    mobile: 640,
    tablet: 768,
    desktop: 1024,
  },
};

// Preset configurations for different screen sizes - now all show all columns
export const mobileConfig: FileTableConfig = {
  ...defaultFileTableConfig,
  columns: defaultFileTableConfig.columns.map((col, index) => ({
    ...col,
    order: index + 1,
  })),
};

export const tabletConfig: FileTableConfig = {
  ...defaultFileTableConfig,
  columns: defaultFileTableConfig.columns.map((col, index) => ({
    ...col,
    order: index + 1,
  })),
};

export const desktopConfig: FileTableConfig = {
  ...defaultFileTableConfig,
  columns: defaultFileTableConfig.columns.map((col, index) => ({
    ...col,
    order: index + 1,
  })),
};

// Utility functions - filter to show only visible columns
export const getConfigForScreenSize = (_width: number): FileTableConfig => {
  // Filter to show only columns that are responsive for the current screen size
  const visibleColumns = defaultFileTableConfig.columns.filter(
    col =>
      col.responsive.mobile && col.responsive.tablet && col.responsive.desktop
  );

  return {
    ...defaultFileTableConfig,
    columns: visibleColumns,
  };
};

export const createCustomConfig = (
  baseConfig: FileTableConfig,
  visibleColumns: string[],
  columnOrder: string[] = []
): FileTableConfig => {
  const filteredColumns = baseConfig.columns
    .filter(col => visibleColumns.includes(col.id))
    .map((col, index) => ({
      ...col,
      order: columnOrder.includes(col.id)
        ? columnOrder.indexOf(col.id) + 1
        : index + 1,
    }));

  return {
    ...baseConfig,
    columns: filteredColumns,
  };
};
