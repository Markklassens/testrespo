import React, { useState, useRef, useEffect } from 'react';
import { 
  ArrowsPointingOutIcon, 
  ArrowsPointingInIcon,
  XMarkIcon,
  Cog6ToothIcon 
} from '@heroicons/react/24/outline';

const ResizableImage = ({ 
  src, 
  alt = "Blog image", 
  initialWidth = 400,
  initialHeight = 300,
  onDelete,
  onUpdate,
  settings = {}
}) => {
  const [isResizing, setIsResizing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [dimensions, setDimensions] = useState({
    width: initialWidth,
    height: initialHeight
  });
  const [position, setPosition] = useState({ x: 0, y: 0 });
  
  const [imageSettings, setImageSettings] = useState({
    borderRadius: 8,
    shadow: false,
    border: false,
    opacity: 100,
    brightness: 100,
    contrast: 100,
    saturation: 100,
    alignment: 'center',
    caption: settings.caption || '',
    ...settings
  });

  const imageRef = useRef(null);
  const containerRef = useRef(null);
  const resizeStartRef = useRef({ x: 0, y: 0, width: 0, height: 0 });
  const dragStartRef = useRef({ x: 0, y: 0, startX: 0, startY: 0 });

  // Handle resize start
  const handleResizeStart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    
    const rect = imageRef.current.getBoundingClientRect();
    resizeStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      width: rect.width,
      height: rect.height
    };

    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', handleResizeEnd);
  };

  // Handle resize
  const handleResize = (e) => {
    if (!isResizing) return;

    const deltaX = e.clientX - resizeStartRef.current.x;
    const deltaY = e.clientY - resizeStartRef.current.y;
    
    const newWidth = Math.max(100, resizeStartRef.current.width + deltaX);
    const aspectRatio = resizeStartRef.current.height / resizeStartRef.current.width;
    const newHeight = newWidth * aspectRatio;
    
    setDimensions({
      width: newWidth,
      height: newHeight
    });
  };

  // Handle resize end
  const handleResizeEnd = () => {
    setIsResizing(false);
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', handleResizeEnd);
    
    if (onUpdate) {
      onUpdate({ dimensions, position, settings: imageSettings });
    }
  };

  // Handle drag start
  const handleDragStart = (e) => {
    if (e.target.classList.contains('resize-handle')) return;
    
    e.preventDefault();
    setIsDragging(true);
    
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      startX: position.x,
      startY: position.y
    };

    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };

  // Handle drag
  const handleDrag = (e) => {
    if (!isDragging) return;

    const deltaX = e.clientX - dragStartRef.current.x;
    const deltaY = e.clientY - dragStartRef.current.y;
    
    setPosition({
      x: dragStartRef.current.startX + deltaX,
      y: dragStartRef.current.startY + deltaY
    });
  };

  // Handle drag end
  const handleDragEnd = () => {
    setIsDragging(false);
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', handleDragEnd);
    
    if (onUpdate) {
      onUpdate({ dimensions, position, settings: imageSettings });
    }
  };

  // Apply image filters
  const getImageStyle = () => {
    const filters = [
      `brightness(${imageSettings.brightness}%)`,
      `contrast(${imageSettings.contrast}%)`,
      `saturate(${imageSettings.saturation}%)`,
      `opacity(${imageSettings.opacity}%)`
    ].join(' ');

    return {
      width: `${dimensions.width}px`,
      height: `${dimensions.height}px`,
      borderRadius: `${imageSettings.borderRadius}px`,
      border: imageSettings.border ? '2px solid #e5e7eb' : 'none',
      boxShadow: imageSettings.shadow ? '0 10px 25px rgba(0, 0, 0, 0.15)' : 'none',
      filter: filters,
      cursor: isDragging ? 'grabbing' : 'grab',
      transform: `translate(${position.x}px, ${position.y}px)`,
      transition: isResizing || isDragging ? 'none' : 'all 0.3s ease',
      userSelect: 'none',
      display: 'block',
      margin: imageSettings.alignment === 'center' ? '0 auto' : 
              imageSettings.alignment === 'right' ? '0 0 0 auto' : '0'
    };
  };

  // Handle settings update
  const handleSettingChange = (key, value) => {
    const newSettings = { ...imageSettings, [key]: value };
    setImageSettings(newSettings);
    
    if (onUpdate) {
      onUpdate({ dimensions, position, settings: newSettings });
    }
  };

  // Cleanup event listeners on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleResize);
      document.removeEventListener('mouseup', handleResizeEnd);
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', handleDragEnd);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative inline-block my-4"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => !showSettings && setShowControls(false)}
    >
      {/* Image */}
      <img
        ref={imageRef}
        src={src}
        alt={alt}
        style={getImageStyle()}
        onMouseDown={handleDragStart}
        className="relative z-10"
        draggable={false}
      />

      {/* Control Panel */}
      {showControls && (
        <div className="absolute top-2 right-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-2 flex space-x-2 z-20">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1 text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-gray-100 transition-colors"
            title="Image settings"
          >
            <Cog6ToothIcon className="h-4 w-4" />
          </button>
          
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
              title="Delete image"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {/* Resize Handles */}
      {showControls && (
        <>
          {/* Corner resize handle */}
          <div
            className="resize-handle absolute bottom-0 right-0 w-4 h-4 bg-blue-500 border-2 border-white rounded-full cursor-nw-resize z-20 transform translate-x-1/2 translate-y-1/2"
            onMouseDown={handleResizeStart}
            title="Resize image"
          />
          
          {/* Size indicator */}
          <div className="absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded z-20">
            {Math.round(dimensions.width)} × {Math.round(dimensions.height)}
          </div>
        </>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-12 right-0 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-30 w-64">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Image Settings</h4>
            <button
              onClick={() => setShowSettings(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3">
            {/* Caption */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Caption
              </label>
              <input
                type="text"
                value={imageSettings.caption}
                onChange={(e) => handleSettingChange('caption', e.target.value)}
                className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Image caption..."
              />
            </div>

            {/* Alignment */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Alignment
              </label>
              <select
                value={imageSettings.alignment}
                onChange={(e) => handleSettingChange('alignment', e.target.value)}
                className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>

            {/* Border Radius */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Border Radius: {imageSettings.borderRadius}px
              </label>
              <input
                type="range"
                min="0"
                max="50"
                value={imageSettings.borderRadius}
                onChange={(e) => handleSettingChange('borderRadius', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Opacity */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Opacity: {imageSettings.opacity}%
              </label>
              <input
                type="range"
                min="10"
                max="100"
                value={imageSettings.opacity}
                onChange={(e) => handleSettingChange('opacity', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Brightness */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Brightness: {imageSettings.brightness}%
              </label>
              <input
                type="range"
                min="50"
                max="150"
                value={imageSettings.brightness}
                onChange={(e) => handleSettingChange('brightness', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Contrast */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Contrast: {imageSettings.contrast}%
              </label>
              <input
                type="range"
                min="50"
                max="150"
                value={imageSettings.contrast}
                onChange={(e) => handleSettingChange('contrast', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Visual Effects */}
            <div className="space-y-2">
              <label className="flex items-center text-xs">
                <input
                  type="checkbox"
                  checked={imageSettings.border}
                  onChange={(e) => handleSettingChange('border', e.target.checked)}
                  className="mr-2"
                />
                <span className="text-gray-700 dark:text-gray-300">Add border</span>
              </label>
              <label className="flex items-center text-xs">
                <input
                  type="checkbox"
                  checked={imageSettings.shadow}
                  onChange={(e) => handleSettingChange('shadow', e.target.checked)}
                  className="mr-2"
                />
                <span className="text-gray-700 dark:text-gray-300">Add shadow</span>
              </label>
            </div>

            {/* Reset Button */}
            <button
              onClick={() => {
                setImageSettings({
                  borderRadius: 8,
                  shadow: false,
                  border: false,
                  opacity: 100,
                  brightness: 100,
                  contrast: 100,
                  saturation: 100,
                  alignment: 'center',
                  caption: ''
                });
                setDimensions({ width: initialWidth, height: initialHeight });
                setPosition({ x: 0, y: 0 });
              }}
              className="w-full px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Reset All
            </button>
          </div>
        </div>
      )}

      {/* Caption */}
      {imageSettings.caption && (
        <p 
          className="text-sm text-gray-600 dark:text-gray-400 italic mt-2"
          style={{ textAlign: imageSettings.alignment }}
        >
          {imageSettings.caption}
        </p>
      )}
    </div>
  );
};

export default ResizableImage;