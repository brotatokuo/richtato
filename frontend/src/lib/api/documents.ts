/**
 * Documents API service for handling document uploads with progress tracking
 */

export interface DocumentUpload {
  id: string;
  organization: string;
  organization_name: string;
  name: string;
  document_type: string;
  description: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  file_extension: string;
  s3_bucket: string;
  s3_key: string;
  s3_url: string;
  s3_etag: string;
  status: UploadStatus;
  upload_progress: number;
  processing_progress: number;
  error_message: string;
  error_code: string;
  retry_count: number;
  max_retries: number;
  uploaded_by: string;
  uploaded_by_name: string;
  equipment: string[];
  equipment_names: string[];
  facility: string | null;
  facility_name: string | null;
  processing_metadata: Record<string, unknown>;
  tags: string[];
  access_groups: string[];
  created_at: string;
  updated_at: string;
  uploaded_at: string | null;
  processed_at: string | null;
  archived_at: string | null;
  processing_jobs: DocumentProcessingJob[];
  versions: DocumentVersion[];
  access_logs: DocumentAccessLog[];
  is_upload_complete: boolean;
  is_processing_complete: boolean;
  can_retry: boolean;
}

export interface DocumentProcessingJob {
  id: string;
  job_type: string;
  status: string;
  job_id: string;
  started_at: string | null;
  completed_at: string | null;
  result_data: Record<string, unknown>;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  version_number: number;
  is_current: boolean;
  s3_key: string;
  s3_url: string;
  file_size: number;
  mime_type: string;
  change_description: string;
  created_by: string;
  created_by_name: string;
  created_at: string;
}

export interface DocumentAccessLog {
  id: string;
  action: string;
  ip_address: string;
  user_agent: string;
  user_name: string;
  timestamp: string;
}

export type UploadStatus =
  | 'pending'
  | 'uploading'
  | 'uploaded'
  | 'processing'
  | 'vectorized'
  | 'error'
  | 'archived'
  | 'deleted';

export type DocumentType =
  | 'manual'
  | 'datasheet'
  | 'warranty'
  | 'certificate'
  | 'diagram'
  | 'photo'
  | 'drawing'
  | 'specification'
  | 'configuration'
  | 'log'
  | 'other';

export interface DocumentUploadCreate {
  name: string;
  document_type: DocumentType;
  description?: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  file_extension: string;
  equipment_ids?: string[];
  tags?: string[];
  access_groups?: string[];
  facility?: string;
}

export interface DocumentStatusUpdate {
  status: UploadStatus;
  upload_progress?: number;
  processing_progress?: number;
  error_message?: string;
  error_code?: string;
}

export interface DocumentSearchParams {
  query?: string;
  document_type?: DocumentType;
  status?: UploadStatus;
  equipment_id?: string;
  facility_id?: string;
  uploaded_by_id?: number;
  tags?: string[];
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface DocumentSearchResponse {
  results: DocumentUpload[];
  count: number;
  page: number;
  page_size: number;
}

export interface UploadProgressCallback {
  (progress: number): void;
}

export interface ApiError {
  success: false;
  message: string;
  details?: unknown;
}

class DocumentsApiService {
  private baseUrl: string;

  constructor() {
    // Use environment variable or default to in-cluster /api
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  }

  private getToken(): string | null {
    try {
      return localStorage.getItem('auth_token');
    } catch {
      return null;
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({
        success: false,
        message: 'An error occurred',
      }));
      throw new Error(
        errorData.message || `HTTP error! status: ${response.status}`
      );
    }

    return response.json();
  }

  /**
   * List document uploads with filtering and pagination
   */
  async listDocuments(params?: {
    search?: string;
    ordering?: string;
    page?: number;
  }): Promise<DocumentUpload[]> {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.ordering) searchParams.set('ordering', params.ordering);
    if (params?.page) searchParams.set('page', params.page.toString());

    const response = await fetch(
      `${this.baseUrl}/documents/uploads/?${searchParams}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    const data = await this.handleResponse<{ results: DocumentUpload[] }>(
      response
    );
    return data.results;
  }

  /**
   * Get a specific document upload by ID
   */
  async getDocument(id: string): Promise<DocumentUpload> {
    const response = await fetch(`${this.baseUrl}/documents/uploads/${id}/`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    return this.handleResponse<DocumentUpload>(response);
  }

  /**
   * Create a new document upload entry
   */
  async createDocumentUpload(
    data: DocumentUploadCreate
  ): Promise<DocumentUpload> {
    const response = await fetch(`${this.baseUrl}/documents/uploads/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<DocumentUpload>(response);
  }

  /**
   * Upload file with progress tracking
   */
  async uploadFile(
    file: File,
    documentData: Omit<
      DocumentUploadCreate,
      'original_filename' | 'file_size' | 'mime_type' | 'file_extension'
    >,
    onProgress?: UploadProgressCallback
  ): Promise<DocumentUpload> {
    // First create the document upload entry
    const uploadData: DocumentUploadCreate = {
      ...documentData,
      original_filename: file.name,
      file_size: file.size,
      mime_type: file.type,
      file_extension: file.name.split('.').pop()?.toLowerCase() || '',
    };

    const documentUpload = await this.createDocumentUpload(uploadData);

    // Then upload the file using FormData for proper file handling
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_id', documentUpload.id);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', event => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            onProgress(progress);

            // Update document status
            this.updateDocumentStatus(documentUpload.id, {
              status: 'uploading',
              upload_progress: progress,
            }).catch(console.error);
          }
        });
      }

      xhr.addEventListener('load', async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            // Update status to uploaded
            const updatedDocument = await this.updateDocumentStatus(
              documentUpload.id,
              {
                status: 'uploaded',
                upload_progress: 100,
              }
            );
            resolve(updatedDocument);
          } catch (error) {
            reject(error);
          }
        } else {
          reject(new Error(`Upload failed with status: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        this.updateDocumentStatus(documentUpload.id, {
          status: 'error',
          error_message: 'Upload failed',
        }).catch(console.error);
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${this.baseUrl}/documents/upload-file/`);

      const token = this.getToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Token ${token}`);
      }

      xhr.send(formData);
    });
  }

  /**
   * Update document upload status and progress
   */
  async updateDocumentStatus(
    id: string,
    status: DocumentStatusUpdate
  ): Promise<DocumentUpload> {
    const response = await fetch(
      `${this.baseUrl}/documents/uploads/${id}/update_status/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(status),
      }
    );

    return this.handleResponse<DocumentUpload>(response);
  }

  /**
   * Retry a failed document upload
   */
  async retryDocument(
    id: string,
    resetForRetry: boolean = true
  ): Promise<DocumentUpload> {
    const response = await fetch(
      `${this.baseUrl}/documents/uploads/${id}/retry/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ reset_for_retry: resetForRetry }),
      }
    );

    return this.handleResponse<DocumentUpload>(response);
  }

  /**
   * Delete a document upload
   */
  async deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/documents/uploads/${id}/`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Delete failed with status: ${response.status}`);
    }
  }

  /**
   * Search documents with advanced filtering
   */
  async searchDocuments(
    params: DocumentSearchParams
  ): Promise<DocumentSearchResponse> {
    const response = await fetch(`${this.baseUrl}/documents/uploads/search/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(params),
    });

    return this.handleResponse<DocumentSearchResponse>(response);
  }

  /**
   * Get processing jobs for a document
   */
  async getProcessingJobs(id: string): Promise<DocumentProcessingJob[]> {
    const response = await fetch(
      `${this.baseUrl}/documents/uploads/${id}/processing_jobs/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    return this.handleResponse<DocumentProcessingJob[]>(response);
  }

  /**
   * Get versions for a document
   */
  async getDocumentVersions(id: string): Promise<DocumentVersion[]> {
    const response = await fetch(
      `${this.baseUrl}/documents/uploads/${id}/versions/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    return this.handleResponse<DocumentVersion[]>(response);
  }

  /**
   * Get access logs for a document
   */
  async getAccessLogs(id: string): Promise<DocumentAccessLog[]> {
    const response = await fetch(
      `${this.baseUrl}/documents/uploads/${id}/access_logs/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    return this.handleResponse<DocumentAccessLog[]>(response);
  }

  /**
   * Get available document types
   */
  async getDocumentTypes(): Promise<{ value: string; label: string }[]> {
    const response = await fetch(
      `${this.baseUrl}/documents/metadata/document_types/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    return this.handleResponse<{ value: string; label: string }[]>(response);
  }

  /**
   * Get available upload statuses
   */
  async getUploadStatuses(): Promise<{ value: string; label: string }[]> {
    const response = await fetch(
      `${this.baseUrl}/documents/metadata/upload_statuses/`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    return this.handleResponse<{ value: string; label: string }[]>(response);
  }
}

// Export singleton instance
export const documentsApi = new DocumentsApiService();
