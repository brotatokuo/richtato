import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download, Edit, Trash2 } from 'lucide-react';
import { FileItem } from './types';
import {
  formatFileSize,
  getFileIcon,
  getFileTypeColor,
  getStatusInfo,
} from './utils';

// Column cell components
export const NameCell = ({ file }: { file: FileItem }) => {
  const IconComponent = getFileIcon(file.type);
  return (
    <div className="flex items-center gap-2 min-w-0">
      <IconComponent className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <span className="font-medium truncate" title={file.name}>
        {file.name}
      </span>
    </div>
  );
};

export const TypeCell = ({ type }: { type: string }) => (
  <Badge className={getFileTypeColor(type)}>
    {type.split('/')[1]?.toUpperCase() || 'UNKNOWN'}
  </Badge>
);

export const SizeCell = ({ size }: { size: number }) => (
  <span className="text-sm text-muted-foreground">{formatFileSize(size)}</span>
);

export const StatusCell = ({ file }: { file: FileItem }) => {
  const statusInfo = getStatusInfo(file.status);
  const IconComponent = statusInfo.icon;
  const showProgress =
    (file.status === 'uploading' || file.status === 'processing') &&
    (file.upload_progress !== undefined ||
      file.processing_progress !== undefined);

  return (
    <div className="flex flex-col gap-1">
      <Badge className={statusInfo.color}>
        <IconComponent
          className={`h-3 w-3 mr-1 ${statusInfo.animate ? 'animate-spin' : ''}`}
        />
        {statusInfo.label}
      </Badge>
      {showProgress && (
        <div className="flex items-center gap-1 text-xs">
          <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{
                width: `${
                  file.status === 'uploading'
                    ? file.upload_progress || 0
                    : file.processing_progress || 0
                }%`,
              }}
            />
          </div>
          <span className="text-gray-500 min-w-0">
            {file.status === 'uploading'
              ? `${file.upload_progress || 0}%`
              : `${file.processing_progress || 0}%`}
          </span>
        </div>
      )}
      {file.status === 'error' && file.error_message && (
        <div
          className="text-xs text-red-600 truncate max-w-32"
          title={file.error_message}
        >
          {file.error_message}
        </div>
      )}
    </div>
  );
};

export const UploaderCell = ({ uploader }: { uploader: string }) => (
  <span className="text-sm text-muted-foreground truncate" title={uploader}>
    {uploader}
  </span>
);

export const TagsCell = ({ tags }: { tags: string[] }) => (
  <div className="flex flex-wrap gap-1">
    {tags.slice(0, 1).map((tag, index) => (
      <Badge key={index} variant="outline" className="text-xs">
        {tag}
      </Badge>
    ))}
    {tags.length > 1 && (
      <Badge variant="outline" className="text-xs">
        +{tags.length - 1}
      </Badge>
    )}
  </div>
);

export const EquipmentCell = ({ equipment }: { equipment: string }) => (
  <span className="text-sm text-muted-foreground truncate" title={equipment}>
    {equipment}
  </span>
);

export const AccessGroupCell = ({ accessGroup }: { accessGroup: string }) => (
  <Badge variant="outline" className="text-xs">
    {accessGroup}
  </Badge>
);

export const UploadDateCell = ({ date }: { date: Date }) => (
  <span className="text-sm text-muted-foreground">
    {date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })}
  </span>
);

export const ActionsCell = ({
  file,
  onEdit,
  onDelete,
  onDownload,
  onRetry,
}: {
  file: FileItem;
  onEdit: (file: FileItem) => void;
  onDelete: (fileId: string) => void;
  onDownload: (file: FileItem) => void;
  onRetry?: (file: FileItem) => void;
}) => (
  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
    {file.status === 'vectorized' && (
      <Button
        variant="outline"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={() => onDownload(file)}
        title="Download file"
      >
        <Download className="h-4 w-4" />
      </Button>
    )}
    {file.status === 'error' && file.can_retry && onRetry && (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onRetry(file)}
        className="h-8 w-8 p-0 text-primary hover:text-primary/90"
        title="Retry upload"
      >
        Retry
      </Button>
    )}
    {(file.status === 'vectorized' || file.status === 'uploaded') && (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onEdit(file)}
        className="h-8 w-8 p-0"
        title="Edit file"
      >
        <Edit className="h-4 w-4" />
      </Button>
    )}
    <Button
      variant="outline"
      size="sm"
      onClick={() => onDelete(file.id)}
      className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
      title="Delete file"
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  </div>
);
