import { UploadStatus } from '@/lib/api/documents';
import {
  AlertCircle,
  Archive,
  Archive as ArchiveIcon,
  CheckCircle,
  Clock,
  Code,
  File,
  FileText,
  Image,
  Loader2,
  Music,
  Trash2,
  Video,
} from 'lucide-react';

// Helper functions for file management
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return Image;
  if (type.startsWith('video/')) return Video;
  if (type.startsWith('audio/')) return Music;
  if (type.includes('text') || type.includes('document')) return FileText;
  if (type.includes('zip') || type.includes('rar') || type.includes('7z'))
    return Archive;
  if (type.includes('code') || type.includes('script')) return Code;
  return File;
};

export const getFileTypeColor = (type: string): string => {
  if (type.startsWith('image/')) return 'bg-green-100 text-green-800';
  if (type.startsWith('video/'))
    return 'bg-secondary text-secondary-foreground';
  if (type.startsWith('audio/')) return 'bg-pink-100 text-pink-800';
  if (type.includes('text') || type.includes('document'))
    return 'bg-primary/15 text-primary';
  if (type.includes('zip') || type.includes('rar') || type.includes('7z'))
    return 'bg-orange-100 text-orange-800';
  if (type.includes('code') || type.includes('script'))
    return 'bg-gray-100 text-gray-800';
  return 'bg-gray-100 text-gray-800';
};

export const getStatusInfo = (status: UploadStatus) => {
  switch (status) {
    case 'pending':
      return {
        icon: Clock,
        color: 'bg-gray-100 text-gray-800',
        label: 'Pending',
      };
    case 'uploading':
      return {
        icon: Loader2,
        color: 'bg-primary/15 text-primary',
        label: 'Uploading',
        animate: true,
      };
    case 'uploaded':
      return {
        icon: CheckCircle,
        color: 'bg-green-100 text-green-800',
        label: 'Uploaded',
      };
    case 'processing':
      return {
        icon: Loader2,
        color: 'bg-yellow-100 text-yellow-800',
        label: 'Processing',
        animate: true,
      };
    case 'vectorized':
      return {
        icon: CheckCircle,
        color: 'bg-green-100 text-green-800',
        label: 'Complete',
      };
    case 'error':
      return {
        icon: AlertCircle,
        color: 'bg-red-100 text-red-800',
        label: 'Error',
      };
    case 'archived':
      return {
        icon: ArchiveIcon,
        color: 'bg-gray-100 text-gray-800',
        label: 'Archived',
      };
    case 'deleted':
      return {
        icon: Trash2,
        color: 'bg-gray-100 text-gray-800',
        label: 'Deleted',
      };
    default:
      return {
        icon: Clock,
        color: 'bg-gray-100 text-gray-800',
        label: 'Unknown',
      };
  }
};
