import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useDropzone } from 'react-dropzone';
import { 
  DocumentArrowUpIcon, 
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { bulkUploadTools, downloadCsvTemplate, clearCsvUploadResult } from '../store/slices/toolsSlice';
import { toast } from 'react-hot-toast';

const BulkUpload = ({ isOpen, onClose, onSuccess }) => {
  const dispatch = useDispatch();
  const { csvUpload } = useSelector(state => state.tools);
  const [dragActive, setDragActive] = useState(false);

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file');
      return;
    }

    try {
      const result = await dispatch(bulkUploadTools(file)).unwrap();
      toast.success(`Successfully uploaded ${result.tools_created} tools!`);
      if (onSuccess) onSuccess();
    } catch (error) {
      toast.error('Upload failed: ' + error.message);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    multiple: false,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false)
  });

  const handleDownloadTemplate = async () => {
    try {
      const result = await dispatch(downloadCsvTemplate()).unwrap();
      
      // Create and download CSV file directly from blob
      const blob = new Blob([result], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'tools_template.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('Template downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const handleClose = () => {
    dispatch(clearCsvUploadResult());
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <DocumentArrowUpIcon className="h-6 w-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Bulk Upload Tools
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!csvUpload.result ? (
            <>
              {/* Instructions */}
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                  Upload Instructions
                </h3>
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800 dark:text-blue-300">
                    <li>Download the CSV template to see the required format</li>
                    <li>Fill in your tool data following the template structure</li>
                    <li>Make sure all required fields are populated (name, description, category_id, slug)</li>
                    <li>Upload your completed CSV file</li>
                  </ol>
                </div>
              </div>

              {/* Download Template */}
              <div className="mb-6">
                <button
                  onClick={handleDownloadTemplate}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <DocumentArrowDownIcon className="h-5 w-5" />
                  <span>Download CSV Template</span>
                </button>
              </div>

              {/* Upload Area */}
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                  Upload CSV File
                </h3>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                    isDragActive || dragActive
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-purple-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <input {...getInputProps()} />
                  <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  
                  {csvUpload.loading ? (
                    <div className="space-y-2">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                      <p className="text-gray-600 dark:text-gray-300">
                        Uploading and processing CSV...
                      </p>
                    </div>
                  ) : isDragActive ? (
                    <p className="text-purple-600 dark:text-purple-400 font-medium">
                      Drop the CSV file here...
                    </p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-gray-600 dark:text-gray-300">
                        Drag & drop a CSV file here, or click to select
                      </p>
                      <p className="text-sm text-gray-500">
                        Only CSV files are supported
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Error Display */}
              {csvUpload.error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
                    <h4 className="font-medium text-red-800 dark:text-red-300">
                      Upload Error
                    </h4>
                  </div>
                  <p className="mt-2 text-sm text-red-700 dark:text-red-400">
                    {csvUpload.error}
                  </p>
                </div>
              )}
            </>
          ) : (
            /* Upload Results */
            <div className="space-y-6">
              {/* Success Summary */}
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  <h3 className="text-lg font-medium text-green-800 dark:text-green-300">
                    Upload Completed!
                  </h3>
                </div>
                <p className="mt-2 text-green-700 dark:text-green-400">
                  Successfully created {csvUpload.result.tools_created} tools
                </p>
              </div>

              {/* Errors (if any) */}
              {csvUpload.result.errors && csvUpload.result.errors.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-300">
                      Some rows had errors
                    </h4>
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    <ul className="space-y-1 text-sm text-yellow-700 dark:text-yellow-400">
                      {csvUpload.result.errors.map((error, index) => (
                        <li key={index} className="font-mono text-xs">
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-4">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => dispatch(clearCsvUploadResult())}
                  className="px-4 py-2 text-purple-600 border border-purple-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
                >
                  Upload Another File
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkUpload;