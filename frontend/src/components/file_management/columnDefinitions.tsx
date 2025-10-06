import { ColumnDef } from '@tanstack/react-table';
import {
  AccessGroupCell,
  ActionsCell,
  EquipmentCell,
  NameCell,
  SizeCell,
  StatusCell,
  TagsCell,
  TypeCell,
  UploadDateCell,
  UploaderCell,
} from './tableCells';
import { ColumnConfig, ColumnId, FileItem } from './types';

// Column definitions factory
export const createColumnDefinitions = (
  config: ColumnConfig[],
  onEdit: (file: FileItem) => void,
  onDelete: (fileId: string) => void,
  onDownload: (file: FileItem) => void,
  onRetry?: (file: FileItem) => void
): ColumnDef<FileItem>[] => {
  const columnMap: Record<ColumnId, () => ColumnDef<FileItem>> = {
    name: () => ({
      accessorKey: 'name',
      header: 'Name',
      size: config.find(c => c.id === 'name')?.size || 250,
      minSize: config.find(c => c.id === 'name')?.minSize || 200,
      cell: ({ row }) => <NameCell file={row.original} />,
    }),
    type: () => ({
      accessorKey: 'type',
      header: 'Type',
      size: config.find(c => c.id === 'type')?.size || 80,
      cell: ({ row }) => <TypeCell type={row.getValue('type')} />,
    }),
    size: () => ({
      accessorKey: 'size',
      header: 'Size',
      size: config.find(c => c.id === 'size')?.size || 80,
      cell: ({ row }) => <SizeCell size={row.getValue('size')} />,
    }),
    status: () => ({
      accessorKey: 'status',
      header: 'Status',
      size: config.find(c => c.id === 'status')?.size || 120,
      cell: ({ row }) => <StatusCell file={row.original} />,
    }),
    uploader: () => ({
      accessorKey: 'uploader',
      header: 'Uploader',
      size: config.find(c => c.id === 'uploader')?.size || 120,
      cell: ({ row }) => <UploaderCell uploader={row.getValue('uploader')} />,
    }),
    tags: () => ({
      accessorKey: 'tags',
      header: 'Tags',
      size: config.find(c => c.id === 'tags')?.size || 150,
      cell: ({ row }) => <TagsCell tags={row.getValue('tags')} />,
    }),
    equipment: () => ({
      accessorKey: 'equipment',
      header: 'Equipment',
      size: config.find(c => c.id === 'equipment')?.size || 150,
      cell: ({ row }) => (
        <EquipmentCell equipment={row.getValue('equipment')} />
      ),
    }),
    accessGroup: () => ({
      accessorKey: 'accessGroup',
      header: 'Access Group',
      size: config.find(c => c.id === 'accessGroup')?.size || 100,
      cell: ({ row }) => (
        <AccessGroupCell accessGroup={row.getValue('accessGroup')} />
      ),
    }),
    uploadDate: () => ({
      accessorKey: 'uploadDate',
      header: 'Upload Date',
      size: config.find(c => c.id === 'uploadDate')?.size || 100,
      cell: ({ row }) => <UploadDateCell date={row.getValue('uploadDate')} />,
    }),
    actions: () => ({
      id: 'actions',
      header: 'Actions',
      size: config.find(c => c.id === 'actions')?.size || 120,
      cell: ({ row }) => (
        <ActionsCell
          file={row.original}
          onEdit={onEdit}
          onDelete={onDelete}
          onDownload={onDownload}
          onRetry={onRetry}
        />
      ),
    }),
  };

  // Sort columns by order and create definitions
  return config
    .sort((a, b) => a.order - b.order)
    .map(columnConfig => columnMap[columnConfig.id]());
};
