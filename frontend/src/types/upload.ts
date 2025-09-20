export interface Upload {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  upload_url: string;
  custom_name?: string;
  domain_id?: number;
  view_count: number;
  is_public: boolean;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadListResponse {
  uploads: Upload[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface UploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  result?: Upload;
  error?: string;
}