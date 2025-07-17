import React, { useState, useRef, useCallback } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { useDropzone } from 'react-dropzone';
import { PhotoIcon, FilmIcon, CodeBracketIcon, AdjustmentsHorizontalIcon, XMarkIcon } from '@heroicons/react/24/outline';
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
  const [codeTitle, setCodeTitle] = useState('');
  
  // Advanced media controls state
  const [imageSettings, setImageSettings] = useState({
    width: 'auto',
    height: 'auto',
    title: '',
    alt: '',
    alignment: 'center',
    caption: '',
    borderRadius: '0',
    border: false
  });
  
  const [videoSettings, setVideoSettings] = useState({
    width: '100%',
    height: '400px',
    title: '',
    autoplay: false,
    controls: true,
    muted: false,
    loop: false,
    alignment: 'center'
  });
  
  const quillRef = useRef(null);

  // Memoize handlers to prevent recreation on every render
  const handleImageInsert = useCallback(() => {
    setShowImageUpload(true);
  }, []);

  const handleVideoInsert = useCallback(() => {
    setShowVideoUpload(true);
  }, []);

  // Memoize modules to prevent recreation on every render
  const modules = React.useMemo(() => ({
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
  }), [handleImageInsert, handleVideoInsert]);

  // Memoize formats to prevent recreation on every render
  const formats = React.useMemo(() => [
    'header', 'bold', 'italic', 'underline', 'strike',
    'list', 'bullet', 'indent', 'align',
    'link', 'image', 'video', 'color', 'background',
    'blockquote', 'code-block'
  ], []);

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
      
      // Insert into editor with advanced styling
      const quill = quillRef.current.getEditor();
      const range = quill.getSelection();
      const index = range ? range.index : 0;
      
      if (file.type.startsWith('image/')) {
        // Create enhanced image HTML with advanced controls
        const imageHtml = createAdvancedImageHtml(fileUrl, imageSettings);
        quill.clipboard.dangerouslyPasteHTML(index, imageHtml);
      } else if (file.type.startsWith('video/')) {
        // Create enhanced video HTML with advanced controls  
        const videoHtml = createAdvancedVideoHtml(fileUrl, videoSettings);
        quill.clipboard.dangerouslyPasteHTML(index, videoHtml);
      }

      toast.success('File uploaded successfully!');
      setShowImageUpload(false);
      setShowVideoUpload(false);
      
      // Reset settings
      resetImageSettings();
      resetVideoSettings();
      
    } catch (error) {
      toast.error('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const createAdvancedImageHtml = (src, settings) => {
    const styles = [
      `width: ${settings.width === 'auto' ? 'auto' : settings.width + 'px'}`,
      `height: ${settings.height === 'auto' ? 'auto' : settings.height + 'px'}`,
      `border-radius: ${settings.borderRadius}px`,
      `display: block`,
      `margin: ${settings.alignment === 'center' ? '0 auto' : settings.alignment === 'left' ? '0 auto 0 0' : '0 0 0 auto'}`,
      settings.border ? 'border: 2px solid #e5e7eb' : '',
      'max-width: 100%'
    ].filter(Boolean).join('; ');

    return `
      <div style="margin: 20px 0; text-align: ${settings.alignment};">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <img src="${src}" 
             alt="${settings.alt || 'Uploaded image'}" 
             title="${settings.title || ''}"
             style="${styles}" />
        ${settings.caption ? `<p style="margin: 10px 0 0 0; font-size: 14px; color: #6b7280; font-style: italic;">${settings.caption}</p>` : ''}
      </div>
    `;
  };

  const createAdvancedVideoHtml = (src, settings) => {
    const videoAttributes = [
      `width="${settings.width}"`,
      `height="${settings.height}"`,
      settings.controls ? 'controls' : '',
      settings.autoplay ? 'autoplay' : '',
      settings.muted ? 'muted' : '',
      settings.loop ? 'loop' : '',
      'style="max-width: 100%; border-radius: 8px;"'
    ].filter(Boolean).join(' ');

    return `
      <div style="margin: 20px 0; text-align: ${settings.alignment};">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <video ${videoAttributes}>
          <source src="${src}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
    `;
  };

  const resetImageSettings = () => {
    setImageSettings({
      width: 'auto',
      height: 'auto',
      title: '',
      alt: '',
      alignment: 'center',
      caption: '',
      borderRadius: '0',
      border: false
    });
  };

  const resetVideoSettings = () => {
    setVideoSettings({
      width: '100%',
      height: '400px',
      title: '',
      autoplay: false,
      controls: true,
      muted: false,
      loop: false,
      alignment: 'center'
    });
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
    
    const codeHtml = createAdvancedCodeBlockHtml(codeContent, codeLanguage, codeTitle);
    
    quill.clipboard.dangerouslyPasteHTML(range ? range.index : 0, codeHtml);
    setShowCodeBlock(false);
    setCodeContent('');
    setCodeTitle('');
  };

  const createAdvancedCodeBlockHtml = (content, language, title) => {
    // Language-specific styling colors
    const languageColors = {
      javascript: '#f7df1e',
      python: '#3776ab',
      html: '#e34c26',
      css: '#1572b6',
      json: '#000000',
      sql: '#336791',
      bash: '#4eaa25',
      typescript: '#3178c6',
      java: '#ed8b00',
      cpp: '#00599c',
      csharp: '#239120',
      php: '#777bb4',
      ruby: '#cc342d',
      go: '#00add8',
      rust: '#000000',
      swift: '#fa7343'
    };

    const langColor = languageColors[language] || '#6b7280';
    const escapedContent = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    return `
      <div style="margin: 20px 0; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background-color: #f9fafb;">
        <div style="background-color: #f3f4f6; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 12px; height: 12px; background-color: ${langColor}; border-radius: 50%; display: inline-block;"></span>
            <span style="font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace; font-size: 14px; color: #374151; font-weight: 600;">${language.toUpperCase()}</span>
          </div>
          ${title ? `<span style="font-size: 14px; color: #6b7280; font-weight: 500;">${title}</span>` : ''}
        </div>
        <div style="padding: 16px; background-color: #1f2937; color: #f9fafb; font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace; font-size: 14px; line-height: 1.6; overflow-x: auto;">
          <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;"><code>${escapedContent}</code></pre>
        </div>
      </div>
    `;
  };

  const insertVideoEmbed = (url) => {
    const quill = quillRef.current.getEditor();
    const range = quill.getSelection();
    
    // Handle YouTube, Vimeo, etc.
    let embedUrl = url;
    let embedHtml = '';
    
    if (url.includes('youtube.com/watch?v=')) {
      const videoId = url.split('v=')[1].split('&')[0];
      embedUrl = `https://www.youtube.com/embed/${videoId}`;
      embedHtml = createAdvancedYouTubeEmbed(embedUrl, videoSettings);
    } else if (url.includes('vimeo.com/')) {
      const videoId = url.split('/').pop();
      embedUrl = `https://player.vimeo.com/video/${videoId}`;
      embedHtml = createAdvancedVimeoEmbed(embedUrl, videoSettings);
    } else {
      // Regular video URL
      embedHtml = createAdvancedVideoHtml(url, videoSettings);
    }
    
    quill.clipboard.dangerouslyPasteHTML(range ? range.index : 0, embedHtml);
    setShowVideoUpload(false);
    resetVideoSettings();
  };

  const createAdvancedYouTubeEmbed = (embedUrl, settings) => {
    const params = new URLSearchParams({
      autoplay: settings.autoplay ? '1' : '0',
      controls: settings.controls ? '1' : '0',
      mute: settings.muted ? '1' : '0',
      loop: settings.loop ? '1' : '0',
      rel: '0',
      modestbranding: '1'
    });

    return `
      <div style="margin: 20px 0; text-align: ${settings.alignment};">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: ${settings.width}; margin: 0 auto; border-radius: 8px;">
          <iframe 
            src="${embedUrl}?${params.toString()}" 
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 8px;"
            allowfullscreen>
          </iframe>
        </div>
      </div>
    `;
  };

  const createAdvancedVimeoEmbed = (embedUrl, settings) => {
    const params = new URLSearchParams({
      autoplay: settings.autoplay ? '1' : '0',
      controls: settings.controls ? '1' : '0',
      muted: settings.muted ? '1' : '0',
      loop: settings.loop ? '1' : '0',
      title: '0',
      byline: '0',
      portrait: '0'
    });

    return `
      <div style="margin: 20px 0; text-align: ${settings.alignment};">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: ${settings.width}; margin: 0 auto; border-radius: 8px;">
          <iframe 
            src="${embedUrl}?${params.toString()}" 
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 8px;"
            allowfullscreen>
          </iframe>
        </div>
      </div>
    `;
  };

  // Memoize the onChange handler to prevent unnecessary re-renders
  const handleChange = useCallback((content) => {
    onChange(content);
  }, [onChange]);

  return (
    <div className="space-y-4">
      {/* Rich Text Editor */}
      <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
        <ReactQuill
          ref={quillRef}
          theme="snow"
          value={value || ''}
          onChange={handleChange}
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

      {/* Enhanced Image Upload Modal */}
      {showImageUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Upload & Configure Image</h3>
              <button
                onClick={() => setShowImageUpload(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Upload Section */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Upload Image</h4>
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
                    <div className="space-y-2">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-gray-600 dark:text-gray-300">Uploading...</p>
                    </div>
                  ) : isDragActive ? (
                    <p className="text-gray-600 dark:text-gray-300">Drop the image here...</p>
                  ) : (
                    <div>
                      <p className="text-gray-600 dark:text-gray-300 mb-2">
                        Drag & drop an image here, or click to select
                      </p>
                      <p className="text-sm text-gray-500">
                        PNG, JPG, GIF, WebP up to 10MB
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Advanced Controls */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Image Settings</h4>
                <div className="space-y-4">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Title
                    </label>
                    <input
                      type="text"
                      value={imageSettings.title}
                      onChange={(e) => setImageSettings({...imageSettings, title: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Image title (optional)"
                    />
                  </div>

                  {/* Alt Text */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Alt Text
                    </label>
                    <input
                      type="text"
                      value={imageSettings.alt}
                      onChange={(e) => setImageSettings({...imageSettings, alt: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Alt text for accessibility"
                    />
                  </div>

                  {/* Caption */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Caption
                    </label>
                    <input
                      type="text"
                      value={imageSettings.caption}
                      onChange={(e) => setImageSettings({...imageSettings, caption: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Image caption (optional)"
                    />
                  </div>

                  {/* Dimensions */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Width
                      </label>
                      <input
                        type="text"
                        value={imageSettings.width}
                        onChange={(e) => setImageSettings({...imageSettings, width: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="auto or px value"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Height
                      </label>
                      <input
                        type="text"
                        value={imageSettings.height}
                        onChange={(e) => setImageSettings({...imageSettings, height: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="auto or px value"
                      />
                    </div>
                  </div>

                  {/* Alignment */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Alignment
                    </label>
                    <select
                      value={imageSettings.alignment}
                      onChange={(e) => setImageSettings({...imageSettings, alignment: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="left">Left</option>
                      <option value="center">Center</option>
                      <option value="right">Right</option>
                    </select>
                  </div>

                  {/* Border Radius */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Border Radius (px)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="50"
                      value={imageSettings.borderRadius}
                      onChange={(e) => setImageSettings({...imageSettings, borderRadius: e.target.value})}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 mt-1">{imageSettings.borderRadius}px</div>
                  </div>

                  {/* Border */}
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={imageSettings.border}
                        onChange={(e) => setImageSettings({...imageSettings, border: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Add border</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setShowImageUpload(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => resetImageSettings()}
                className="px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
              >
                Reset Settings
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

export default React.memo(RichTextEditor);