import React, { useState, useRef, useCallback } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import './EnhancedEditor.css';
import { useDropzone } from 'react-dropzone';
import { 
  PhotoIcon, 
  FilmIcon, 
  CodeBracketIcon, 
  AdjustmentsHorizontalIcon, 
  XMarkIcon,
  ClipboardDocumentIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon
} from '@heroicons/react/24/outline';
import api from '../utils/api';
import { toast } from 'react-hot-toast';

const EnhancedRichTextEditor = ({ 
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
  const [videoUrl, setVideoUrl] = useState('');
  
  // Enhanced media controls state
  const [imageSettings, setImageSettings] = useState({
    width: 'auto',
    height: 'auto',
    title: '',
    alt: '',
    alignment: 'center',
    caption: '',
    borderRadius: '8',
    border: false,
    shadow: false,
    float: 'none',
    margin: '20',
    aspectRatio: 'auto',
    sizePreset: 'custom'
  });
  
  const [videoSettings, setVideoSettings] = useState({
    width: '100%',
    height: '400px',
    title: '',
    autoplay: false,
    controls: true,
    muted: false,
    loop: false,
    alignment: 'center',
    aspectRatio: '16:9',
    quality: 'auto',
    thumbnail: '',
    float: 'none',
    margin: '20',
    shadow: false,
    borderRadius: '8'
  });

  const [codeBlockSettings, setCodeBlockSettings] = useState({
    theme: 'dark',
    showLineNumbers: true,
    copyButton: true,
    collapsible: false,
    maxHeight: 'auto',
    fontSize: '14',
    fontFamily: 'SF Mono',
    borderRadius: '8',
    showHeader: true,
    customTitle: ''
  });
  
  const quillRef = useRef(null);

  // Size presets
  const sizePresets = {
    small: { width: '300px', height: 'auto' },
    medium: { width: '500px', height: 'auto' },
    large: { width: '800px', height: 'auto' },
    'full-width': { width: '100%', height: 'auto' },
    thumbnail: { width: '150px', height: '150px' },
    banner: { width: '100%', height: '200px' }
  };

  // Aspect ratios
  const aspectRatios = {
    'auto': null,
    '16:9': 1.777,
    '4:3': 1.333,
    '1:1': 1,
    '3:2': 1.5,
    '21:9': 2.333
  };

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

      const response = await api.post('/api/user/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const fileUrl = response.data.file_url;
      
      // Insert into editor with advanced styling
      const quill = quillRef.current.getEditor();
      const range = quill.getSelection();
      const index = range ? range.index : 0;
      
      if (file.type.startsWith('image/')) {
        const imageHtml = createEnhancedImageHtml(fileUrl, imageSettings);
        quill.clipboard.dangerouslyPasteHTML(index, imageHtml);
      } else if (file.type.startsWith('video/')) {
        const videoHtml = createEnhancedVideoHtml(fileUrl, videoSettings);
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

  const createEnhancedImageHtml = (src, settings) => {
    const preset = sizePresets[settings.sizePreset] || { width: settings.width, height: settings.height };
    const aspectRatio = aspectRatios[settings.aspectRatio];
    
    let width = preset.width;
    let height = preset.height;
    
    // Apply aspect ratio if specified
    if (aspectRatio && width !== 'auto') {
      const numWidth = typeof width === 'string' ? parseInt(width) : width;
      height = `${Math.round(numWidth / aspectRatio)}px`;
    }

    const containerStyles = [
      `margin: ${settings.margin}px ${settings.alignment === 'center' ? 'auto' : '0'}`,
      `text-align: ${settings.alignment}`,
      settings.float !== 'none' ? `float: ${settings.float}` : '',
      settings.float !== 'none' ? `margin: ${settings.margin}px` : '',
      'clear: both',
      'position: relative'
    ].filter(Boolean).join('; ');

    const imageStyles = [
      `width: ${width}`,
      `height: ${height}`,
      `border-radius: ${settings.borderRadius}px`,
      `display: block`,
      settings.border ? 'border: 2px solid #e5e7eb' : '',
      settings.shadow ? 'box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1)' : '',
      'max-width: 100%',
      'transition: all 0.3s ease',
      'cursor: grab'
    ].filter(Boolean).join('; ');

    // Create unique ID for this image
    const imageId = `resizable-image-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return `
      <div style="${containerStyles}" class="enhanced-image-container resizable-image-wrapper" data-image-id="${imageId}">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <div class="resizable-image-container" style="position: relative; display: inline-block;">
          <img src="${src}" 
               alt="${settings.alt || 'Uploaded image'}" 
               title="${settings.title || ''}"
               style="${imageStyles}" 
               class="enhanced-image resizable-image" 
               data-width="${width}"
               data-height="${height}"
               data-settings='${JSON.stringify(settings)}' />
          <div class="image-controls" style="position: absolute; top: 8px; right: 8px; opacity: 0; transition: opacity 0.3s ease;">
            <button class="resize-handle" style="background: #3b82f6; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: nw-resize; margin-left: 4px;" title="Resize">⤡</button>
            <button class="settings-handle" style="background: #6b7280; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; margin-left: 4px;" title="Settings">⚙</button>
          </div>
        </div>
        ${settings.caption ? `<p style="margin: 10px 0 0 0; font-size: 14px; color: #6b7280; font-style: italic; text-align: ${settings.alignment};">${settings.caption}</p>` : ''}
      </div>
      <script>
        (function() {
          const container = document.querySelector('[data-image-id="${imageId}"]');
          if (!container) return;
          
          const img = container.querySelector('.resizable-image');
          const controls = container.querySelector('.image-controls');
          const resizeHandle = container.querySelector('.resize-handle');
          
          // Show/hide controls on hover
          container.addEventListener('mouseenter', () => {
            controls.style.opacity = '1';
          });
          
          container.addEventListener('mouseleave', () => {
            controls.style.opacity = '0';
          });
          
          // Make image draggable
          let isDragging = false;
          let startX, startY, startLeft, startTop;
          
          img.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('resize-handle') || e.target.classList.contains('settings-handle')) return;
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = container.getBoundingClientRect();
            startLeft = rect.left;
            startTop = rect.top;
            
            img.style.cursor = 'grabbing';
            e.preventDefault();
          });
          
          document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            container.style.transform = \`translate(\${deltaX}px, \${deltaY}px)\`;
          });
          
          document.addEventListener('mouseup', () => {
            if (isDragging) {
              isDragging = false;
              img.style.cursor = 'grab';
            }
          });
          
          // Handle resize
          let isResizing = false;
          let startWidth, startHeight;
          
          resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startY = e.clientY;
            startWidth = img.offsetWidth;
            startHeight = img.offsetHeight;
            e.preventDefault();
            e.stopPropagation();
          });
          
          document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const deltaX = e.clientX - startX;
            const newWidth = Math.max(100, startWidth + deltaX);
            const aspectRatio = startHeight / startWidth;
            const newHeight = newWidth * aspectRatio;
            
            img.style.width = newWidth + 'px';
            img.style.height = newHeight + 'px';
          });
          
          document.addEventListener('mouseup', () => {
            isResizing = false;
          });
        })();
      </script>
    `;
  };

  const createEnhancedVideoHtml = (src, settings) => {
    const aspectRatio = aspectRatios[settings.aspectRatio];
    const isEmbedded = src.includes('youtube.com') || src.includes('vimeo.com');
    
    const containerStyles = [
      `margin: ${settings.margin}px ${settings.alignment === 'center' ? 'auto' : '0'}`,
      `text-align: ${settings.alignment}`,
      settings.float !== 'none' ? `float: ${settings.float}` : '',
      settings.float !== 'none' ? `margin: ${settings.margin}px` : '',
      'clear: both'
    ].filter(Boolean).join('; ');

    const videoStyles = [
      `width: ${settings.width}`,
      `height: ${settings.height}`,
      `border-radius: ${settings.borderRadius}px`,
      settings.shadow ? 'box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1)' : '',
      'max-width: 100%'
    ].filter(Boolean).join('; ');

    if (isEmbedded) {
      return createEmbeddedVideoHtml(src, settings);
    }

    const videoAttributes = [
      `width="${settings.width}"`,
      `height="${settings.height}"`,
      settings.controls ? 'controls' : '',
      settings.autoplay ? 'autoplay' : '',
      settings.muted ? 'muted' : '',
      settings.loop ? 'loop' : '',
      settings.thumbnail ? `poster="${settings.thumbnail}"` : '',
      `style="${videoStyles}"`
    ].filter(Boolean).join(' ');

    return `
      <div style="${containerStyles}" class="enhanced-video-container">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <video ${videoAttributes} class="enhanced-video">
          <source src="${src}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </div>
    `;
  };

  const createEmbeddedVideoHtml = (url, settings) => {
    let embedUrl = url;
    
    if (url.includes('youtube.com/watch?v=')) {
      const videoId = url.split('v=')[1].split('&')[0];
      embedUrl = `https://www.youtube.com/embed/${videoId}`;
    } else if (url.includes('vimeo.com/')) {
      const videoId = url.split('/').pop();
      embedUrl = `https://player.vimeo.com/video/${videoId}`;
    }

    const aspectRatio = aspectRatios[settings.aspectRatio] || 1.777;
    const paddingBottom = `${(1 / aspectRatio) * 100}%`;

    const containerStyles = [
      `margin: ${settings.margin}px ${settings.alignment === 'center' ? 'auto' : '0'}`,
      `text-align: ${settings.alignment}`,
      settings.float !== 'none' ? `float: ${settings.float}` : '',
      settings.float !== 'none' ? `margin: ${settings.margin}px` : '',
      'clear: both'
    ].filter(Boolean).join('; ');

    return `
      <div style="${containerStyles}" class="enhanced-video-container">
        ${settings.title ? `<h4 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 600; color: #374151;">${settings.title}</h4>` : ''}
        <div style="position: relative; padding-bottom: ${paddingBottom}; height: 0; overflow: hidden; max-width: ${settings.width}; margin: 0 auto; border-radius: ${settings.borderRadius}px; ${settings.shadow ? 'box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);' : ''}">
          <iframe 
            src="${embedUrl}" 
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: ${settings.borderRadius}px;"
            allowfullscreen>
          </iframe>
        </div>
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
      borderRadius: '8',
      border: false,
      shadow: false,
      float: 'none',
      margin: '20',
      aspectRatio: 'auto',
      sizePreset: 'custom'
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
      alignment: 'center',
      aspectRatio: '16:9',
      quality: 'auto',
      thumbnail: '',
      float: 'none',
      margin: '20',
      shadow: false,
      borderRadius: '8'
    });
  };

  const resetCodeBlockSettings = () => {
    setCodeBlockSettings({
      theme: 'dark',
      showLineNumbers: true,
      copyButton: true,
      collapsible: false,
      maxHeight: 'auto',
      fontSize: '14',
      fontFamily: 'SF Mono',
      borderRadius: '8',
      showHeader: true,
      customTitle: ''
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
    
    const codeHtml = createEnhancedCodeBlockHtml(codeContent, codeLanguage, codeBlockSettings);
    
    quill.clipboard.dangerouslyPasteHTML(range ? range.index : 0, codeHtml);
    setShowCodeBlock(false);
    setCodeContent('');
    setCodeTitle('');
  };

  const createEnhancedCodeBlockHtml = (content, language, settings) => {
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
    const codeId = `code-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const lines = escapedContent.split('\n');
    const lineNumbersHtml = settings.showLineNumbers ? 
      lines.map((_, i) => `<span class="line-number">${i + 1}</span>`).join('') : '';
    
    const codeWithLineNumbers = settings.showLineNumbers ? 
      lines.map((line, i) => `<span class="code-line" data-line="${i + 1}">${line}</span>`).join('\n') : 
      escapedContent;

    const containerStyles = [
      `margin: 20px 0`,
      `border: 1px solid #e5e7eb`,
      `border-radius: ${settings.borderRadius}px`,
      `overflow: hidden`,
      `background-color: #f9fafb`,
      settings.maxHeight !== 'auto' ? `max-height: ${settings.maxHeight}px` : '',
      `font-family: ${settings.fontFamily}, Monaco, 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace`
    ].filter(Boolean).join('; ');

    const headerStyle = settings.showHeader ? `
      <div style="background-color: #f3f4f6; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 12px; height: 12px; background-color: ${langColor}; border-radius: 50%; display: inline-block;"></span>
          <span style="font-size: 14px; color: #374151; font-weight: 600;">${language.toUpperCase()}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          ${settings.customTitle || codeTitle ? `<span style="font-size: 14px; color: #6b7280; font-weight: 500;">${settings.customTitle || codeTitle}</span>` : ''}
          ${settings.copyButton ? `<button onclick="copyCode('${codeId}')" style="padding: 4px 8px; background: #e5e7eb; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; color: #374151;">Copy</button>` : ''}
          ${settings.collapsible ? `<button onclick="toggleCode('${codeId}')" style="padding: 4px 8px; background: #e5e7eb; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; color: #374151;">Toggle</button>` : ''}
        </div>
      </div>
    ` : '';

    const codeBodyStyle = `
      padding: 16px; 
      background-color: ${settings.theme === 'dark' ? '#1f2937' : '#ffffff'}; 
      color: ${settings.theme === 'dark' ? '#f9fafb' : '#1f2937'}; 
      font-size: ${settings.fontSize}px; 
      line-height: 1.6; 
      overflow-x: auto;
      ${settings.maxHeight !== 'auto' ? 'overflow-y: auto;' : ''}
    `;

    return `
      <div style="${containerStyles}" class="enhanced-code-block" id="${codeId}">
        ${headerStyle}
        <div style="${codeBodyStyle}">
          ${settings.showLineNumbers ? `
            <div style="display: flex;">
              <div style="min-width: 40px; padding-right: 16px; color: #6b7280; user-select: none; border-right: 1px solid #e5e7eb; margin-right: 16px;">
                ${lineNumbersHtml}
              </div>
              <div style="flex: 1;">
                <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;"><code>${codeWithLineNumbers}</code></pre>
              </div>
            </div>
          ` : `
            <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;"><code>${escapedContent}</code></pre>
          `}
        </div>
      </div>
      <script>
        function copyCode(id) {
          const codeBlock = document.getElementById(id);
          const code = codeBlock.querySelector('code').textContent;
          navigator.clipboard.writeText(code);
          // Show toast notification
          const button = event.target;
          const originalText = button.textContent;
          button.textContent = 'Copied!';
          setTimeout(() => { button.textContent = originalText; }, 2000);
        }
        
        function toggleCode(id) {
          const codeBlock = document.getElementById(id);
          const codeBody = codeBlock.querySelector('div:last-child');
          const button = event.target;
          if (codeBody.style.display === 'none') {
            codeBody.style.display = 'block';
            button.textContent = 'Collapse';
          } else {
            codeBody.style.display = 'none';
            button.textContent = 'Expand';
          }
        }
      </script>
    `;
  };

  const insertVideoEmbed = (url) => {
    const quill = quillRef.current.getEditor();
    const range = quill.getSelection();
    
    const embedHtml = createEmbeddedVideoHtml(url, videoSettings);
    
    quill.clipboard.dangerouslyPasteHTML(range ? range.index : 0, embedHtml);
    setShowVideoUpload(false);
    setVideoUrl('');
    resetVideoSettings();
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
          <span>Enhanced Image</span>
        </button>
        
        <button
          onClick={() => setShowVideoUpload(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <FilmIcon className="h-5 w-5" />
          <span>Enhanced Video</span>
        </button>
        
        <button
          onClick={() => setShowCodeBlock(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          <CodeBracketIcon className="h-5 w-5" />
          <span>Enhanced Code Block</span>
        </button>
      </div>

      {/* Enhanced Image Upload Modal */}
      {showImageUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Enhanced Image Upload & Configuration</h3>
              <button
                onClick={() => setShowImageUpload(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

              {/* Basic Settings */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Basic Settings</h4>
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

                  {/* Size Preset */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Size Preset
                    </label>
                    <select
                      value={imageSettings.sizePreset}
                      onChange={(e) => {
                        const preset = e.target.value;
                        const presetValues = sizePresets[preset];
                        setImageSettings({
                          ...imageSettings, 
                          sizePreset: preset,
                          width: presetValues?.width || imageSettings.width,
                          height: presetValues?.height || imageSettings.height
                        });
                      }}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="custom">Custom</option>
                      <option value="small">Small (300px)</option>
                      <option value="medium">Medium (500px)</option>
                      <option value="large">Large (800px)</option>
                      <option value="full-width">Full Width</option>
                      <option value="thumbnail">Thumbnail (150px)</option>
                      <option value="banner">Banner (100% x 200px)</option>
                    </select>
                  </div>

                  {/* Aspect Ratio */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Aspect Ratio
                    </label>
                    <select
                      value={imageSettings.aspectRatio}
                      onChange={(e) => setImageSettings({...imageSettings, aspectRatio: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="auto">Auto</option>
                      <option value="16:9">16:9 (Widescreen)</option>
                      <option value="4:3">4:3 (Standard)</option>
                      <option value="1:1">1:1 (Square)</option>
                      <option value="3:2">3:2 (Photography)</option>
                      <option value="21:9">21:9 (Ultrawide)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Advanced Settings */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Advanced Settings</h4>
                <div className="space-y-4">
                  {/* Custom Dimensions */}
                  {imageSettings.sizePreset === 'custom' && (
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
                          placeholder="auto, 300px, 50%"
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
                          placeholder="auto, 200px, 50%"
                        />
                      </div>
                    </div>
                  )}

                  {/* Layout Controls */}
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

                  {/* Float */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Float (Text Wrap)
                    </label>
                    <select
                      value={imageSettings.float}
                      onChange={(e) => setImageSettings({...imageSettings, float: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="none">None</option>
                      <option value="left">Float Left</option>
                      <option value="right">Float Right</option>
                    </select>
                  </div>

                  {/* Margin */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Margin: {imageSettings.margin}px
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={imageSettings.margin}
                      onChange={(e) => setImageSettings({...imageSettings, margin: e.target.value})}
                      className="w-full"
                    />
                  </div>

                  {/* Border Radius */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Border Radius: {imageSettings.borderRadius}px
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="50"
                      value={imageSettings.borderRadius}
                      onChange={(e) => setImageSettings({...imageSettings, borderRadius: e.target.value})}
                      className="w-full"
                    />
                  </div>

                  {/* Visual Effects */}
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={imageSettings.border}
                        onChange={(e) => setImageSettings({...imageSettings, border: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Add border</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={imageSettings.shadow}
                        onChange={(e) => setImageSettings({...imageSettings, shadow: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Add shadow</span>
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

      {/* Enhanced Video Upload/Embed Modal */}
      {showVideoUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Enhanced Video Upload & Configuration</h3>
              <button
                onClick={() => setShowVideoUpload(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Upload/Embed Section */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Video Source</h4>
                
                <div className="space-y-4">
                  {/* Video URL Input */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Video URL (YouTube, Vimeo, etc.)
                    </label>
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      placeholder="https://youtube.com/watch?v=..."
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                    <button
                      onClick={() => videoUrl && insertVideoEmbed(videoUrl)}
                      disabled={!videoUrl}
                      className="mt-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Embed Video
                    </button>
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
              </div>

              {/* Video Settings */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Video Settings</h4>
                <div className="space-y-4">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Title
                    </label>
                    <input
                      type="text"
                      value={videoSettings.title}
                      onChange={(e) => setVideoSettings({...videoSettings, title: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Video title (optional)"
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
                        value={videoSettings.width}
                        onChange={(e) => setVideoSettings({...videoSettings, width: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="100%, 500px"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Height
                      </label>
                      <input
                        type="text"
                        value={videoSettings.height}
                        onChange={(e) => setVideoSettings({...videoSettings, height: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="400px, auto"
                      />
                    </div>
                  </div>

                  {/* Aspect Ratio */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Aspect Ratio
                    </label>
                    <select
                      value={videoSettings.aspectRatio}
                      onChange={(e) => setVideoSettings({...videoSettings, aspectRatio: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="16:9">16:9 (Widescreen)</option>
                      <option value="4:3">4:3 (Standard)</option>
                      <option value="1:1">1:1 (Square)</option>
                      <option value="21:9">21:9 (Ultrawide)</option>
                    </select>
                  </div>

                  {/* Alignment */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Alignment
                    </label>
                    <select
                      value={videoSettings.alignment}
                      onChange={(e) => setVideoSettings({...videoSettings, alignment: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="left">Left</option>
                      <option value="center">Center</option>
                      <option value="right">Right</option>
                    </select>
                  </div>

                  {/* Float */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Float (Text Wrap)
                    </label>
                    <select
                      value={videoSettings.float}
                      onChange={(e) => setVideoSettings({...videoSettings, float: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="none">None</option>
                      <option value="left">Float Left</option>
                      <option value="right">Float Right</option>
                    </select>
                  </div>

                  {/* Video Controls */}
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={videoSettings.controls}
                        onChange={(e) => setVideoSettings({...videoSettings, controls: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Show controls</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={videoSettings.autoplay}
                        onChange={(e) => setVideoSettings({...videoSettings, autoplay: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Autoplay</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={videoSettings.muted}
                        onChange={(e) => setVideoSettings({...videoSettings, muted: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Muted</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={videoSettings.loop}
                        onChange={(e) => setVideoSettings({...videoSettings, loop: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Loop</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={videoSettings.shadow}
                        onChange={(e) => setVideoSettings({...videoSettings, shadow: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Add shadow</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setShowVideoUpload(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => resetVideoSettings()}
                className="px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
              >
                Reset Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Code Block Modal */}
      {showCodeBlock && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Enhanced Code Block</h3>
              <button
                onClick={() => setShowCodeBlock(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Code Input */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Code Content</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Language</label>
                    <select
                      value={codeLanguage}
                      onChange={(e) => setCodeLanguage(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="javascript">JavaScript</option>
                      <option value="python">Python</option>
                      <option value="html">HTML</option>
                      <option value="css">CSS</option>
                      <option value="json">JSON</option>
                      <option value="sql">SQL</option>
                      <option value="bash">Bash</option>
                      <option value="typescript">TypeScript</option>
                      <option value="java">Java</option>
                      <option value="cpp">C++</option>
                      <option value="csharp">C#</option>
                      <option value="php">PHP</option>
                      <option value="ruby">Ruby</option>
                      <option value="go">Go</option>
                      <option value="rust">Rust</option>
                      <option value="swift">Swift</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Title (Optional)</label>
                    <input
                      type="text"
                      value={codeTitle}
                      onChange={(e) => setCodeTitle(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Code block title..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Code</label>
                    <textarea
                      value={codeContent}
                      onChange={(e) => setCodeContent(e.target.value)}
                      rows={12}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Paste your code here..."
                    />
                  </div>
                </div>
              </div>

              {/* Code Block Settings */}
              <div>
                <h4 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Code Block Settings</h4>
                <div className="space-y-4">
                  {/* Theme */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Theme</label>
                    <select
                      value={codeBlockSettings.theme}
                      onChange={(e) => setCodeBlockSettings({...codeBlockSettings, theme: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="dark">Dark</option>
                      <option value="light">Light</option>
                    </select>
                  </div>

                  {/* Font Size */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Font Size: {codeBlockSettings.fontSize}px
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="20"
                      value={codeBlockSettings.fontSize}
                      onChange={(e) => setCodeBlockSettings({...codeBlockSettings, fontSize: e.target.value})}
                      className="w-full"
                    />
                  </div>

                  {/* Max Height */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Max Height</label>
                    <select
                      value={codeBlockSettings.maxHeight}
                      onChange={(e) => setCodeBlockSettings({...codeBlockSettings, maxHeight: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="auto">Auto</option>
                      <option value="200">200px</option>
                      <option value="300">300px</option>
                      <option value="400">400px</option>
                      <option value="500">500px</option>
                    </select>
                  </div>

                  {/* Font Family */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Font Family</label>
                    <select
                      value={codeBlockSettings.fontFamily}
                      onChange={(e) => setCodeBlockSettings({...codeBlockSettings, fontFamily: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="SF Mono">SF Mono</option>
                      <option value="Monaco">Monaco</option>
                      <option value="Inconsolata">Inconsolata</option>
                      <option value="Roboto Mono">Roboto Mono</option>
                      <option value="Source Code Pro">Source Code Pro</option>
                      <option value="Fira Code">Fira Code</option>
                    </select>
                  </div>

                  {/* Features */}
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={codeBlockSettings.showLineNumbers}
                        onChange={(e) => setCodeBlockSettings({...codeBlockSettings, showLineNumbers: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Show line numbers</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={codeBlockSettings.copyButton}
                        onChange={(e) => setCodeBlockSettings({...codeBlockSettings, copyButton: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Copy button</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={codeBlockSettings.collapsible}
                        onChange={(e) => setCodeBlockSettings({...codeBlockSettings, collapsible: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Collapsible</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={codeBlockSettings.showHeader}
                        onChange={(e) => setCodeBlockSettings({...codeBlockSettings, showHeader: e.target.checked})}
                        className="mr-2 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Show header</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setShowCodeBlock(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => resetCodeBlockSettings()}
                className="px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
              >
                Reset Settings
              </button>
              <button
                onClick={insertCodeBlock}
                disabled={!codeContent.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Insert Code Block
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(EnhancedRichTextEditor);