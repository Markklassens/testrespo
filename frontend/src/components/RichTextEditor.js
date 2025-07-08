import React, { useState, useRef } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { useDropzone } from 'react-dropzone';
import { PhotoIcon, FilmIcon, CodeBracketIcon } from '@heroicons/react/24/outline';
import api from '../utils/api';
import { toast } from 'react-hot-toast';

const RichTextEditor = ({ 
  value, 
  onChange, 
  placeholder = "Start writing...",
  height = "300px",
  showPreview = false 
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [showVideoUpload, setShowVideoUpload] = useState(false);
  const [showCodeBlock, setShowCodeBlock] = useState(false);
  const [codeLanguage, setCodeLanguage] = useState('javascript');
  const [codeContent, setCodeContent] = useState('');
  const quillRef = useRef(null);

  // Custom toolbar configuration
  const modules = {
    toolbar: {
      container: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'indent': '-1'}, { 'indent': '+1' }],
        [{ 'align': [] }],
        ['link', 'image', 'video'],
        [{ 'color': [] }, { 'background': [] }],
        ['blockquote', 'code-block'],
        ['clean']
      ],
      handlers: {
        image: handleImageInsert,
        video: handleVideoInsert
      }
    },
    clipboard: {
      matchVisual: false,
    }
  };

  const formats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'list', 'bullet', 'indent', 'align',
    'link', 'image', 'video', 'color', 'background',
    'blockquote', 'code-block'
  ];

  async function handleImageInsert() {
    setShowImageUpload(true);
  }

  function handleVideoInsert() {
    setShowVideoUpload(true);
  }

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);
    try {
      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const fileUrl = response.data.file_url;
      
      // Insert into editor
      const quill = quillRef.current.getEditor();
      const range = quill.getSelection();
      
      if (file.type.startsWith('image/')) {
        quill.insertEmbed(range ? range.index : 0, 'image', fileUrl);
      } else if (file.type.startsWith('video/')) {
        quill.insertEmbed(range ? range.index : 0, 'video', fileUrl);
      }

      toast.success('File uploaded successfully!');
      setShowImageUpload(false);
      setShowVideoUpload(false);
    } catch (error) {
      toast.error('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'video/*': ['.mp4', '.avi', '.mov', '.wmv']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false
  });

  const insertCodeBlock = () => {
    const quill = quillRef.current.getEditor();
    const range = quill.getSelection();
    
    const codeHtml = `
      <pre class="ql-syntax" data-language="${codeLanguage}">
        <code>${codeContent}</code>
      </pre>
    `;
    
    quill.clipboard.dangerouslyPasteHTML(range ? range.index : 0, codeHtml);
    setShowCodeBlock(false);
    setCodeContent('');
  };

  const insertVideoEmbed = (url) => {
    const quill = quillRef.current.getEditor();
    const range = quill.getSelection();
    
    // Handle YouTube, Vimeo, etc.
    let embedUrl = url;
    if (url.includes('youtube.com/watch?v=')) {
      const videoId = url.split('v=')[1].split('&')[0];
      embedUrl = `https://www.youtube.com/embed/${videoId}`;
    } else if (url.includes('vimeo.com/')) {
      const videoId = url.split('/').pop();
      embedUrl = `https://player.vimeo.com/video/${videoId}`;
    }
    
    quill.insertEmbed(range ? range.index : 0, 'video', embedUrl);
    setShowVideoUpload(false);
  };

  return (
    <div className="space-y-4">
      {/* Rich Text Editor */}
      <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
        <ReactQuill
          ref={quillRef}
          theme="snow"
          value={value}
          onChange={onChange}
          modules={modules}
          formats={formats}
          placeholder={placeholder}
          style={{ height }}
          className="bg-white dark:bg-gray-800"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={() => setShowImageUpload(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PhotoIcon className="h-5 w-5" />
          <span>Add Image</span>
        </button>
        
        <button
          onClick={() => setShowVideoUpload(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <FilmIcon className="h-5 w-5" />
          <span>Add Video</span>
        </button>
        
        <button
          onClick={() => setShowCodeBlock(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          <CodeBracketIcon className="h-5 w-5" />
          <span>Code Block</span>
        </button>
      </div>

      {/* Image Upload Modal */}
      {showImageUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Upload Image</h3>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive 
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                  : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
              }`}
            >
              <input {...getInputProps()} />
              <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              {isUploading ? (
                <p>Uploading...</p>
              ) : isDragActive ? (
                <p>Drop the image here...</p>
              ) : (
                <div>
                  <p className="text-gray-600 dark:text-gray-300">
                    Drag & drop an image here, or click to select
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    PNG, JPG, GIF up to 10MB
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowImageUpload(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Upload/Embed Modal */}
      {showVideoUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Add Video</h3>
            
            <div className="space-y-4">
              {/* Video URL Input */}
              <div>
                <label className="block text-sm font-medium mb-2">Video URL</label>
                <input
                  type="url"
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.target.value) {
                      insertVideoEmbed(e.target.value);
                    }
                  }}
                />
              </div>
              
              <div className="text-center text-gray-500">or</div>
              
              {/* File Upload */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  isDragActive 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                <FilmIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                {isUploading ? (
                  <p>Uploading...</p>
                ) : (
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Upload video file (MP4, AVI, MOV)
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowVideoUpload(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Code Block Modal */}
      {showCodeBlock && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-2xl w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Insert Code Block</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Language</label>
                <select
                  value={codeLanguage}
                  onChange={(e) => setCodeLanguage(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                >
                  <option value="javascript">JavaScript</option>
                  <option value="python">Python</option>
                  <option value="html">HTML</option>
                  <option value="css">CSS</option>
                  <option value="json">JSON</option>
                  <option value="sql">SQL</option>
                  <option value="bash">Bash</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Code</label>
                <textarea
                  value={codeContent}
                  onChange={(e) => setCodeContent(e.target.value)}
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm"
                  placeholder="Paste your code here..."
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowCodeBlock(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={insertCodeBlock}
                disabled={!codeContent.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Insert Code
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RichTextEditor;