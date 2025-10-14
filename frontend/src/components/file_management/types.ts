import { DocumentUpload, UploadStatus } from '@/lib/api/documents';
import { OnChangeFn, SortingState } from '@tanstack/react-table';

// File type interface - updated to match DocumentUpload
export interface FileItem {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadDate: Date;
  lastModified: Date;
  uploader: string;
  tags: string[];
  accessGroup: string;
  equipment: string;
  status: UploadStatus;
  description?: string;
  upload_progress?: number;
  processing_progress?: number;
  error_message?: string;
  can_retry?: boolean;
}

// Upload state for tracking file uploads
export interface FileUploadState {
  file: File;
  id?: string;
  status: UploadStatus;
  progress: number;
  error?: string;
  documentUpload?: DocumentUpload;
}

export type ColumnId =
  | 'name'
  | 'type'
  | 'size'
  | 'status'
  | 'uploader'
  | 'tags'
  | 'equipment'
  | 'accessGroup'
  | 'uploadDate'
  | 'actions';

export interface ColumnConfig {
  id: ColumnId;
  label: string;
  size: number;
  minSize?: number;
  priority: 'high' | 'medium' | 'low';
  responsive: {
    mobile: boolean;
    tablet: boolean;
    desktop: boolean;
  };
  order: number;
}

export interface FileTableConfig {
  columns: ColumnConfig[];
  defaultView: 'compact' | 'detailed';
  responsiveBreakpoints: {
    mobile: number;
    tablet: number;
    desktop: number;
  };
}

export type FileTableProps = {
  files: FileItem[];
  config: FileTableConfig;
  onEditFile: (file: FileItem) => void;
  onDeleteFile: (fileId: string) => void;
  onDownloadFile: (file: FileItem) => void;
  onRetry?: (file: FileItem) => void;
  sorting?: SortingState;
  onSortingChange?: OnChangeFn<SortingState>;
  globalFilter?: string;
  onGlobalFilterChange?: (filter: string) => void;
};
