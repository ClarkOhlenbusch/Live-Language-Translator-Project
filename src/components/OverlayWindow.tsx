import React, { useState } from 'react';
import { ChevronDown, ChevronUp, X, Move, Settings, Power, Loader2 } from 'lucide-react';
import TranscriptItem from './TranscriptItem';
import { TranscriptData } from '../types';
import SettingsModal, { Settings as SettingsType, defaultSettings } from './SettingsModal';

interface OverlayWindowProps {
  transcriptData: TranscriptData[];
  settings: SettingsType;
  onSettingsChange: (settings: SettingsType) => void;
  isBackendProcessing: boolean;
  onToggleBackendProcessing: () => void;
  isBackendTransitioning: boolean;
}

const OverlayWindow: React.FC<OverlayWindowProps> = ({ 
  transcriptData, 
  settings,
  onSettingsChange,
  isBackendProcessing,
  onToggleBackendProcessing,
  isBackendTransitioning
}) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  return (
    <div 
      className="group rounded-lg overflow-hidden backdrop-blur-md"
      style={{ 
        width: '650px',
        maxWidth: '95vw',
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        borderRadius: '10px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
        transition: 'all 0.2s ease'
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Header bar with controls */}
      <div className="bg-gradient-to-r from-blue-900/70 to-indigo-900/70 px-3 py-1.5 flex items-center justify-between">
        <div className="text-white font-medium text-sm flex items-center">
          <Move size={14} className="mr-2 opacity-50" />
          Live Language Translator
          {isBackendTransitioning && <Loader2 size={16} className="ml-2 animate-spin text-sky-400" />}
        </div>
        
        <div className={`flex items-center space-x-1 transition-opacity ${isHovering ? 'opacity-100' : 'opacity-0'}`}>
          <button 
            className={`p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white 
                        ${isBackendProcessing ? 'text-green-400' : 'text-red-400'}`}
            onClick={onToggleBackendProcessing}
            disabled={isBackendTransitioning}
            aria-label={isBackendProcessing ? "Turn Off Processing" : "Turn On Processing"}
          >
            {isBackendTransitioning ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Power size={14} />
            )}
          </button>
          <button 
            className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white"
            onClick={() => setIsSettingsOpen(true)}
            aria-label="Settings"
            disabled={isBackendTransitioning}
          >
            <Settings size={14} />
          </button>
          <button 
            className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white"
            onClick={() => setIsMinimized(!isMinimized)}
            aria-label={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button 
            className="p-1 hover:bg-white/10 rounded text-gray-300 hover:text-white"
            aria-label="Close"
            onClick={() => window.close()}
          >
            <X size={14} />
          </button>
        </div>
      </div>
      
      {/* Transcript content area */}
      {!isMinimized && (
        <div className="p-3 max-h-[65vh] overflow-y-auto space-y-2">
          {/* User information banner */}
          <div className="bg-slate-700/50 rounded p-2 text-xs text-gray-300 mb-2">
            <span className="font-medium text-blue-400">{settings.userName}</span>
            <span className="mx-1">|</span>
            <span className="italic">{settings.conversationContext}</span>
            <span className="mx-1">|</span>
            <span className={isBackendProcessing ? 'text-green-400' : 'text-red-400'}>
              {isBackendProcessing ? 'Processing ON' : 'Processing OFF'}
            </span>
          </div>
          
          {transcriptData.map(item => (
            <TranscriptItem key={item.id} item={item} />
          ))}
          
          {transcriptData.length === 0 && (
            <div className="text-center p-6 text-gray-400">
              {isBackendProcessing ? 
                'Start speaking to see transcriptions appear here.' : 
                'Processing is OFF. Click the power button to start.'
              }
              <p className="text-xs mt-2">Configure your settings by clicking the gear icon.</p>
            </div>
          )}
        </div>
      )}
      
      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        onSave={onSettingsChange}
      />
    </div>
  );
};

export default OverlayWindow;