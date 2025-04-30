import React, { useState } from 'react';
import { ChevronDown, ChevronUp, X, Move, Settings } from 'lucide-react';
import TranscriptItem from './TranscriptItem';
import { TranscriptData } from '../types';

interface OverlayWindowProps {
  transcriptData: TranscriptData[];
}

const OverlayWindow: React.FC<OverlayWindowProps> = ({ transcriptData }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  
  return (
    <div 
      className="group rounded-lg overflow-hidden backdrop-blur-md"
      style={{ 
        width: '700px',
        maxWidth: '90vw',
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Header bar with controls */}
      <div className="bg-gradient-to-r from-blue-900/70 to-indigo-900/70 px-3 py-2 flex items-center justify-between">
        <div className="text-white font-medium text-sm flex items-center">
          <Move size={14} className="mr-2 opacity-50" />
          Italian Overlay
        </div>
        
        <div className={`flex items-center space-x-1 transition-opacity ${isHovering ? 'opacity-100' : 'opacity-0'}`}>
          <button className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white">
            <Settings size={14} />
          </button>
          <button 
            className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white"
            onClick={() => setIsMinimized(!isMinimized)}
          >
            {isMinimized ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white">
            <X size={14} />
          </button>
        </div>
      </div>
      
      {/* Transcript content area */}
      {!isMinimized && (
        <div className="p-4 max-h-[70vh] overflow-y-auto space-y-3">
          {transcriptData.map(item => (
            <TranscriptItem key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export default OverlayWindow;