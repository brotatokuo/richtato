import {
  defaultFileTableConfig,
  FileEditModal,
  FileItem,
  FileTable,
  FileUploadArea,
  FilterSelect,
  useFileUploads,
  useResponsiveColumns,
} from '@/components/file-management';
import { documentsApi, DocumentUpload } from '@/lib/api/documents';
import { OnChangeFn, SortingState } from '@tanstack/react-table';
import { useCallback, useEffect, useState } from 'react';

export function FileManagement() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [editingFile, setEditingFile] = useState<FileItem | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    equipment: '',
    group: '',
    status: '',
  });
  const [isDragOver, setIsDragOver] = useState(false);
  const [showDropNotification, setShowDropNotification] = useState(false);

  // Use responsive columns hook and file uploads hook
  const { config } = useResponsiveColumns(defaultFileTableConfig);
  const { uploads, uploadFiles, retryUpload, cancelUpload } = useFileUploads();

  // Convert DocumentUpload to FileItem
  const convertDocumentToFileItem = (doc: DocumentUpload): FileItem => ({
    id: doc.id,
    name: doc.name,
    size: doc.file_size,
    type: doc.mime_type,
    uploadDate: new Date(doc.uploaded_at || doc.created_at),
    lastModified: new Date(doc.updated_at),
    uploader: doc.uploaded_by_name || 'Unknown',
    tags: doc.tags || [],
    accessGroup: doc.access_groups?.[0] || 'General',
    equipment: doc.equipment_names?.join(', ') || 'None',
    status: doc.status,
    description: doc.description,
    upload_progress: doc.upload_progress,
    processing_progress: doc.processing_progress,
    error_message: doc.error_message,
    can_retry: doc.can_retry,
  });

  // Load files from API
  const loadFiles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const documents = await documentsApi.listDocuments({
        search: globalFilter,
        ordering:
          sorting.length > 0
            ? `${sorting[0].desc ? '-' : ''}${sorting[0].id}`
            : '-created_at',
      });

      const fileItems = documents.map(convertDocumentToFileItem);
      setFiles(fileItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files');
      console.error('Failed to load files:', err);
    } finally {
      setLoading(false);
    }
  }, [globalFilter, sorting]);

  // Load files on component mount and when filters change
  useEffect(() => {
    loadFiles();
  }, [globalFilter, sorting, loadFiles]);

  // Refresh files periodically to get status updates
  useEffect(() => {
    const interval = setInterval(() => {
      loadFiles();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [globalFilter, sorting, loadFiles]);

  // Handle file input change - now uploads via API
  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    try {
      await uploadFiles(selectedFiles, {
        name: selectedFiles[0].name, // Use first file's name, could be improved
        document_type: 'other', // Default type, could be inferred from file extension
        description: '',
        tags: [],
        access_groups: [],
      });

      // Refresh files after upload
      setTimeout(() => loadFiles(), 2000);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // Handle file deletion
  const handleDeleteFile = async (fileId: string) => {
    try {
      await documentsApi.deleteDocument(fileId);
      // Remove from local state immediately for better UX
      setFiles(prev => prev.filter(file => file.id !== fileId));
    } catch (error) {
      console.error('Delete failed:', error);
      // Optionally show error message to user
    }
  };

  // Handle retry file upload
  const handleRetryFile = async (file: FileItem) => {
    try {
      await documentsApi.retryDocument(file.id);
      // Refresh files to get updated status
      loadFiles();
    } catch (error) {
      console.error('Retry failed:', error);
    }
  };

  // Handle edit file metadata
  const handleEditFile = (file: FileItem) => {
    setEditingFile(file);
    setIsEditModalOpen(true);
  };

  // Handle save edited file
  const handleSaveEdit = async (updatedFile: FileItem) => {
    try {
      // Update file metadata via API
      await documentsApi.updateDocumentStatus(updatedFile.id, {
        // Convert FileItem back to update format - this is a simplified version
        status: updatedFile.status,
      });

      // Update local state
      setFiles(prev =>
        prev.map(file => (file.id === updatedFile.id ? updatedFile : file))
      );
      setIsEditModalOpen(false);
      setEditingFile(null);
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  // File action handlers
  const handleDownloadFile = async (file: FileItem) => {
    try {
      // Get the document to access its S3 URL
      const document = await documentsApi.getDocument(file.id);
      if (document.s3_url) {
        // Open the S3 URL in a new window/tab for download
        window.open(document.s3_url, '_blank');
      } else {
        console.error('No download URL available for file:', file.name);
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // Filter handlers
  const handleFilterChange = (filterType: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value,
    }));
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
    setShowDropNotification(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
    setShowDropNotification(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    setShowDropNotification(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length === 0) return;

    try {
      await uploadFiles(droppedFiles, {
        name: droppedFiles[0].name,
        document_type: 'other',
        description: '',
        tags: [],
        access_groups: [],
      });

      // Refresh files after upload
      setTimeout(() => loadFiles(), 2000);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // Filter options
  const filterOptions = {
    equipment: [
      { value: 'main-server-rack-a', label: 'Main Server Rack A' },
      { value: 'network-switch-b', label: 'Network Switch B' },
      { value: 'database-server-c', label: 'Database Server C' },
      { value: 'conference-room-display', label: 'Conference Room Display' },
      { value: 'automation-controller-d', label: 'Automation Controller D' },
    ],
    group: [
      { value: 'engineering', label: 'Engineering' },
      { value: 'operations', label: 'Operations' },
      { value: 'analytics', label: 'Analytics' },
      { value: 'management', label: 'Management' },
      { value: 'devops', label: 'DevOps' },
    ],
    status: [
      { value: 'uploaded', label: 'Uploaded' },
      { value: 'processing', label: 'Processing' },
      { value: 'vectorized', label: 'Vectorized' },
      { value: 'error', label: 'Error' },
      { value: 'archived', label: 'Archived' },
    ],
  };

  // Show loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome to Memory Bank
          </h1>
        </div>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome to Memory Bank
          </h1>
        </div>
        <div className="text-center py-12">
          <div className="text-red-600 mb-4">Error loading files: {error}</div>
          <button
            onClick={loadFiles}
            className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show empty state with upload area
  if (files.length === 0 && uploads.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome to Memory Bank
          </h1>
          <p className="text-muted-foreground mt-2">
            Upload your first documents to get started
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <FileUploadArea
            isDragOver={isDragOver}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onFileSelect={handleFileInput}
            uploads={uploads}
            onCancelUpload={cancelUpload}
            onRetryUpload={retryUpload}
          />
        </div>
      </div>
    );
  }

  // Show full interface with files
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome to Memory Bank
        </h1>
      </div>

      {/* Search Bar and Filters */}
      <div className="space-y-4">
        {/* Search Bar with Upload Button */}
        <div className="flex items-center justify-center gap-3 max-w-md mx-auto">
          <input
            type="file"
            id="file-upload"
            multiple
            onChange={handleFileInput}
            className="hidden"
          />
          <label
            htmlFor="file-upload"
            className="bg-primary text-primary-foreground hover:bg-primary/90 p-2 rounded-md cursor-pointer transition-colors flex items-center justify-center"
            title="Upload Files"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </label>
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search files..."
              value={globalFilter}
              onChange={e => setGlobalFilter(e.target.value)}
              className="w-full px-4 py-3 pl-10 pr-4 border border-input bg-background text-foreground placeholder:text-muted-foreground rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg
                className="h-5 w-5 text-muted-foreground"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Filter Options */}
        <div className="flex flex-wrap gap-4 justify-center">
          <FilterSelect
            value={filters.equipment}
            onChange={value => handleFilterChange('equipment', value)}
            options={filterOptions.equipment}
            placeholder="All Equipment"
          />
          <FilterSelect
            value={filters.group}
            onChange={value => handleFilterChange('group', value)}
            options={filterOptions.group}
            placeholder="All Groups"
          />
          <FilterSelect
            value={filters.status}
            onChange={value => handleFilterChange('status', value)}
            options={filterOptions.status}
            placeholder="All Status"
          />
        </div>
      </div>

      {/* Show upload progress if any uploads are in progress */}
      {uploads.length > 0 && (
        <div className="max-w-2xl mx-auto">
          <FileUploadArea
            isDragOver={false}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onFileSelect={handleFileInput}
            uploads={uploads}
            onCancelUpload={cancelUpload}
            onRetryUpload={retryUpload}
          />
        </div>
      )}

      {/* Files Table with Drag and Drop */}
      <div
        className={`relative transition-all duration-200 ${
          isDragOver
            ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-400 border-dashed rounded-lg'
            : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <FileTable
          files={files}
          config={config}
          onEditFile={handleEditFile}
          onDeleteFile={handleDeleteFile}
          onDownloadFile={handleDownloadFile}
          onRetry={handleRetryFile}
          sorting={sorting}
          onSortingChange={setSorting as OnChangeFn<SortingState>}
          globalFilter={globalFilter}
          onGlobalFilterChange={setGlobalFilter}
        />

        {/* Drop Notification Popup */}
        {showDropNotification && (
          <div className="absolute inset-0 flex items-center justify-center bg-blue-500/10 backdrop-blur-sm rounded-lg z-10">
            <div className="bg-blue-500 text-white px-6 py-4 rounded-lg shadow-lg text-center">
              <div className="flex items-center gap-3">
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <div>
                  <p className="font-semibold">Drop files to upload</p>
                  <p className="text-sm opacity-90">
                    Release to add files to Memory Bank
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Edit File Metadata Modal */}
      <FileEditModal
        file={editingFile}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={handleSaveEdit}
      />
    </div>
  );
}
