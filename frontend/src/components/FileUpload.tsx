/**
 * @fileoverview File Upload Component
 *
 * A comprehensive drag-and-drop file upload component for the BulletDrop platform.
 * Supports multiple file uploads, progress tracking, domain selection, and automatic
 * clipboard copying of upload URLs.
 *
 * Features:
 * - Drag and drop file upload
 * - File selection via click
 * - Upload progress tracking
 * - Domain selection for custom URLs
 * - Automatic URL copying to clipboard
 * - File type validation
 * - Dark/light theme support
 *
 * @author BulletDrop Team
 * @version 1.0.0
 */

import React, { useState, useRef, useCallback } from 'react';
import { apiService } from '../services/api';
import { Upload, UploadProgress } from '../types/upload';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../contexts/ToastContext';

/**
 * Props for the FileUpload component.
 */
interface FileUploadProps {
  /** Callback function called when an upload completes successfully */
  onUploadComplete?: (upload: Upload) => void;
  /** Maximum number of files that can be uploaded at once */
  maxFiles?: number;
  /** Additional CSS classes to apply to the component */
  className?: string;
}

/**
 * FileUpload component provides drag-and-drop file upload functionality.
 *
 * This component handles the complete file upload workflow including:
 * - File selection via drag-and-drop or file picker
 * - Domain selection for custom upload URLs
 * - Progress tracking for each upload
 * - Error handling and user feedback
 * - Automatic URL copying to clipboard
 *
 * @param props - Component props
 * @returns JSX element representing the file upload interface
 *
 * @example
 * ```tsx
 * <FileUpload
 *   maxFiles={10}
 *   onUploadComplete={(upload) => console.log('Uploaded:', upload.upload_url)}
 *   className="my-custom-class"
 * />
 * ```
 */
export const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  maxFiles = 5,
  className = ''
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [domains, setDomains] = useState<any[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<number | undefined>();
  const inputRef = useRef<HTMLInputElement>(null);
  const { isAuthenticated, refreshUser, user } = useAuth();
  const { success, error } = useToast();

  // Load domains on component mount
  React.useEffect(() => {
    if (isAuthenticated) {
      loadDomains();
    }
  }, [isAuthenticated]);

  const loadDomains = async () => {
    try {
      const response = await apiService.getAvailableDomains();
      setDomains(response.domains);
      
      // Auto-select user's preferred domain if available and accessible
      if (response.domains.length > 0 && !selectedDomain) {
        let domainToSelect = response.domains[0].id; // fallback to first domain
        
        // If user has a preferred domain, try to use it
        if (user?.preferred_domain_id) {
          const preferredDomain = response.domains.find(d => d.id === user.preferred_domain_id);
          if (preferredDomain) {
            domainToSelect = preferredDomain.id;
          }
        }
        
        setSelectedDomain(domainToSelect);
      }
    } catch (error) {
      console.error('Failed to load domains:', error);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

    const handleFiles = async (files: FileList | File[]) => {
    const fileArray = Array.isArray(files) ? files : Array.from(files);
    if (!fileArray.length) return;

    // Check if a domain is selected
    if (!selectedDomain) {
      error('Please select a domain before uploading');
      return;
    }

    const filesToUpload = fileArray.slice(0, maxFiles || 10);

    // Create upload entries
    const newUploads: UploadProgress[] = filesToUpload.map(file => ({
      file,
      progress: 0,
      status: 'pending' as const,
    }));

    setUploads(prev => [...prev, ...newUploads]);

    // Start uploading files
    filesToUpload.forEach((file, index) => {
      uploadFile(file, uploads.length + index);
    });
  };

  const uploadFile = async (file: File, index: number) => {
    try {
      setUploads(prev => prev.map((upload, i) =>
        i === index
          ? { ...upload, status: 'uploading' as const }
          : upload
      ));

      const result = await apiService.uploadFile(
        file,
        undefined, // custom name
        selectedDomain,
        true, // is public
        (progress) => {
          setUploads(prev => prev.map((upload, i) =>
            i === index
              ? { ...upload, progress }
              : upload
          ));
        }
      );

      setUploads(prev => prev.map((upload, i) =>
        i === index
          ? { ...upload, status: 'completed', result }
          : upload
      ));

      if (onUploadComplete) {
        onUploadComplete(result);
      }

      // Refresh user data to update storage/upload counts
      refreshUser().catch(console.error);

      // Copy URL to clipboard
      navigator.clipboard.writeText(result.upload_url).then(() => {
        success('File uploaded successfully!', 'URL copied to clipboard');
      }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = result.upload_url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        success('File uploaded successfully!', 'URL copied to clipboard');
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setUploads(prev => prev.map((upload, i) =>
        i === index
          ? {
              ...upload,
              status: 'error',
              error: errorMessage
            }
          : upload
      ));
      error('Upload failed', errorMessage);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const removeUpload = (index: number) => {
    setUploads(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const copyToClipboard = (url: string) => {
    navigator.clipboard.writeText(url).then(() => {
      success('URL copied to clipboard!');
    }).catch(() => {
      error('Failed to copy URL', 'Please copy manually from the address bar');
    });
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center p-8 bg-gray-50 rounded-lg">
        <p className="text-gray-600">Please log in to upload files.</p>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {/* Domain Selection */}
      {domains.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Upload Domain
          </label>
          <select
            value={selectedDomain || ''}
            onChange={(e) => setSelectedDomain(e.target.value ? parseInt(e.target.value) : undefined)}
            className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition-colors duration-300"
          >
            {!selectedDomain && <option value="">Select a domain...</option>}
            {domains.map(domain => (
              <option key={domain.id} value={domain.id}>
                {domain.display_name} ({domain.domain_name})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500 bg-white dark:bg-gray-800'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleChange}
          className="hidden"
          accept="image/*,video/*,.pdf,.txt,.md"
        />

        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div className="mt-4">
            <button
              type="button"
              onClick={onButtonClick}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-300"
            >
              Select files
            </button>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              or drag and drop files here
            </p>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            PNG, JPG, GIF, PDF up to 10MB
          </p>
        </div>
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Uploads</h3>
          {uploads.map((upload, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {upload.file.name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatFileSize(upload.file.size)}
                  </p>
                </div>
                <div className="ml-4 flex items-center space-x-2">
                  {upload.status === 'completed' && upload.result && (
                    <>
                      <button
                        onClick={() => copyToClipboard(upload.result!.upload_url)}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 dark:text-blue-300 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 transition-colors duration-300"
                      >
                        Copy URL
                      </button>
                      <a
                        href={upload.result.upload_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 dark:text-green-300 dark:bg-green-900/30 dark:hover:bg-green-900/50 transition-colors duration-300"
                      >
                        View
                      </a>
                    </>
                  )}
                  <button
                    onClick={() => removeUpload(index)}
                    className="inline-flex items-center p-1 border border-transparent rounded-full text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors duration-300"
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Progress Bar */}
              {upload.status === 'uploading' && (
                <div className="mt-2">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {Math.round(upload.progress)}% uploaded
                  </p>
                </div>
              )}

              {/* Success State */}
              {upload.status === 'completed' && (
                <div className="mt-2 flex items-center text-sm text-green-600 dark:text-green-400">
                  <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Uploaded successfully - URL copied to clipboard!
                </div>
              )}

              {/* Error State */}
              {upload.status === 'error' && (
                <div className="mt-2 flex items-center text-sm text-red-600 dark:text-red-400">
                  <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {upload.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;