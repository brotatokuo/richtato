import { documentsApi, DocumentUploadCreate } from '@/lib/api/documents';
import { useCallback, useState } from 'react';
import { FileUploadState } from './types';

export const useFileUploads = () => {
  const [uploads, setUploads] = useState<FileUploadState[]>([]);

  const addUpload = useCallback(
    (file: File) => {
      const newUpload: FileUploadState = {
        file,
        status: 'pending',
        progress: 0,
      };

      setUploads(prev => [...prev, newUpload]);
      return uploads.length; // Return index for tracking
    },
    [uploads.length]
  );

  const updateUpload = useCallback(
    (index: number, updates: Partial<FileUploadState>) => {
      setUploads(prev =>
        prev.map((upload, i) =>
          i === index ? { ...upload, ...updates } : upload
        )
      );
    },
    []
  );

  const removeUpload = useCallback((index: number) => {
    setUploads(prev => prev.filter((_, i) => i !== index));
  }, []);

  const pollProcessingStatus = useCallback(
    async (index: number, documentId: string) => {
      const pollInterval = setInterval(async () => {
        try {
          const document = await documentsApi.getDocument(documentId);

          if (document.status === 'processing') {
            updateUpload(index, {
              status: 'processing',
              progress: document.processing_progress || 0,
            });
          } else if (document.status === 'vectorized') {
            updateUpload(index, {
              status: 'vectorized',
              progress: 100,
              documentUpload: document,
            });
            clearInterval(pollInterval);
          } else if (document.status === 'error') {
            updateUpload(index, {
              status: 'error',
              error: document.error_message || 'Processing failed',
            });
            clearInterval(pollInterval);
          }
        } catch (error) {
          console.error('Error polling processing status:', error);
          clearInterval(pollInterval);
        }
      }, 2000); // Poll every 2 seconds

      // Clear interval after 5 minutes to prevent infinite polling
      setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000);
    },
    [updateUpload]
  );

  const startUpload = useCallback(
    async (
      index: number,
      uploadData: Omit<
        DocumentUploadCreate,
        'original_filename' | 'file_size' | 'mime_type' | 'file_extension'
      >
    ) => {
      const upload = uploads[index];
      if (!upload) return;

      try {
        updateUpload(index, { status: 'uploading', progress: 0 });

        const documentUpload = await documentsApi.uploadFile(
          upload.file,
          uploadData,
          progress => {
            updateUpload(index, { progress });
          }
        );

        updateUpload(index, {
          status: 'uploaded',
          progress: 100,
          documentUpload,
          id: documentUpload.id,
        });

        // Start polling for processing status
        pollProcessingStatus(index, documentUpload.id);
      } catch (error) {
        updateUpload(index, {
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed',
        });
      }
    },
    [uploads, updateUpload, pollProcessingStatus]
  );

  const retryUpload = useCallback(
    async (index: number) => {
      const upload = uploads[index];
      if (!upload || !upload.documentUpload) return;

      try {
        updateUpload(index, {
          status: 'uploading',
          progress: 0,
          error: undefined,
        });

        await documentsApi.retryDocument(upload.documentUpload.id);

        // Start polling again
        pollProcessingStatus(index, upload.documentUpload.id);
      } catch (error) {
        updateUpload(index, {
          status: 'error',
          error: error instanceof Error ? error.message : 'Retry failed',
        });
      }
    },
    [uploads, updateUpload, pollProcessingStatus]
  );

  const cancelUpload = useCallback(
    (index: number) => {
      const upload = uploads[index];
      if (!upload) return;

      // If upload has started and we have a document ID, we might want to delete it
      if (upload.id && upload.status !== 'vectorized') {
        documentsApi.deleteDocument(upload.id).catch(console.error);
      }

      removeUpload(index);
    },
    [uploads, removeUpload]
  );

  const uploadFiles = useCallback(
    async (
      files: File[],
      documentData: Omit<
        DocumentUploadCreate,
        'original_filename' | 'file_size' | 'mime_type' | 'file_extension'
      >
    ) => {
      const uploadPromises = files.map(async file => {
        const index = addUpload(file);
        await startUpload(index, documentData);
      });

      await Promise.allSettled(uploadPromises);
    },
    [addUpload, startUpload]
  );

  const clearCompleted = useCallback(() => {
    setUploads(prev =>
      prev.filter(
        upload => upload.status !== 'vectorized' && upload.status !== 'error'
      )
    );
  }, []);

  const clearAll = useCallback(() => {
    setUploads([]);
  }, []);

  return {
    uploads,
    addUpload,
    updateUpload,
    removeUpload,
    startUpload,
    retryUpload,
    cancelUpload,
    uploadFiles,
    clearCompleted,
    clearAll,
  };
};

export default useFileUploads;
