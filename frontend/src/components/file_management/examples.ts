import { createCustomConfig, defaultFileTableConfig } from './config';
import { FileTableConfig } from './types';

// Example: Custom configuration for a mobile-first design
export const mobileFirstConfig: FileTableConfig = createCustomConfig(
  defaultFileTableConfig,
  ['name', 'type', 'size', 'status', 'actions'], // Only show essential columns
  ['name', 'status', 'type', 'size', 'actions'] // Reorder with status second
);

// Example: Custom configuration for a detailed view
export const detailedConfig: FileTableConfig = createCustomConfig(
  defaultFileTableConfig,
  [
    'name',
    'type',
    'size',
    'status',
    'uploader',
    'tags',
    'equipment',
    'accessGroup',
    'uploadDate',
    'actions',
  ],
  [
    'name',
    'type',
    'size',
    'status',
    'uploader',
    'uploadDate',
    'tags',
    'equipment',
    'accessGroup',
    'actions',
  ]
);

// Example: Custom configuration for admin view
export const adminConfig: FileTableConfig = createCustomConfig(
  defaultFileTableConfig,
  ['name', 'uploader', 'accessGroup', 'status', 'uploadDate', 'actions'],
  ['name', 'uploader', 'accessGroup', 'status', 'uploadDate', 'actions']
);

// Example: Custom configuration for equipment-focused view
export const equipmentConfig: FileTableConfig = createCustomConfig(
  defaultFileTableConfig,
  ['name', 'equipment', 'type', 'size', 'status', 'actions'],
  ['name', 'equipment', 'type', 'size', 'status', 'actions']
);
