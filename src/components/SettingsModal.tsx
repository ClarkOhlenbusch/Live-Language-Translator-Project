import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

// Define the settings structure
export interface Settings {
  conversationContext: string;
  personalInfo: string;
  responseLanguage: 'detected' | 'english';
  userName: string;
}

// Default settings
export const defaultSettings: Settings = {
  conversationContext: 'Casual conversation with a friend.',
  personalInfo: 'My name is [Your Name]. I am a [Your Profession]. I speak [Languages].',
  responseLanguage: 'detected',
  userName: 'User'
};

// Preset conversation contexts
const presetContexts = [
  {value: 'Casual conversation with a friend.', label: 'Casual conversation'},
  {value: 'Business meeting with colleagues.', label: 'Business meeting'},
  {value: 'Academic lecture or class.', label: 'Academic lecture'},
  {value: 'Travel conversation with locals.', label: 'Travel conversation'},
  {value: 'Technical discussion about work.', label: 'Technical discussion'},
  {value: 'Medical appointment with a doctor.', label: 'Medical appointment'},
];

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: Settings;
  onSave: (settings: Settings) => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, settings, onSave }) => {
  const [localSettings, setLocalSettings] = useState<Settings>(settings);
  const [useCustomContext, setUseCustomContext] = useState(
    !presetContexts.some(preset => preset.value === settings.conversationContext)
  );

  useEffect(() => {
    setLocalSettings(settings);
    setUseCustomContext(!presetContexts.some(preset => preset.value === settings.conversationContext));
  }, [settings]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setLocalSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleContextTypeChange = (isCustom: boolean) => {
    setUseCustomContext(isCustom);
    // If switching to preset and the current value isn't a preset, set to the first preset
    if (!isCustom && !presetContexts.some(preset => preset.value === localSettings.conversationContext)) {
      setLocalSettings(prev => ({
        ...prev,
        conversationContext: presetContexts[0].value
      }));
    }
  };

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div 
        className="bg-slate-800 rounded-lg w-full max-w-md max-h-[60vh] overflow-y-auto"
        style={{
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)',
        }}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-3 border-b border-slate-700">
          <h2 className="text-white text-base font-medium">Settings</h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4 space-y-4">
          {/* User Name */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-200">Your Name</label>
            <input
              type="text"
              name="userName"
              value={localSettings.userName}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Your name"
            />
          </div>
          
          {/* Conversation Context */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-200">Conversation Context</label>
            
            {/* Context type selection */}
            <div className="flex items-center space-x-4 mb-2">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="contextType"
                  checked={!useCustomContext}
                  onChange={() => handleContextTypeChange(false)}
                  className="text-blue-500 focus:ring-blue-500 h-4 w-4 bg-slate-700 border-slate-600"
                />
                <span className="ml-2 text-sm text-gray-200">Use preset</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="contextType"
                  checked={useCustomContext}
                  onChange={() => handleContextTypeChange(true)}
                  className="text-blue-500 focus:ring-blue-500 h-4 w-4 bg-slate-700 border-slate-600"
                />
                <span className="ml-2 text-sm text-gray-200">Custom context</span>
              </label>
            </div>
            
            {/* Show select or textarea based on the context type */}
            {!useCustomContext ? (
              <select
                name="conversationContext"
                value={localSettings.conversationContext}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {presetContexts.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            ) : (
              <textarea
                name="conversationContext"
                value={localSettings.conversationContext}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the conversation context..."
                rows={2}
              />
            )}
            <p className="text-xs text-gray-400">Describe the context of your conversations to help the AI generate more relevant responses.</p>
          </div>
          
          {/* Personal Info */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-200">Personal Information</label>
            <textarea
              name="personalInfo"
              value={localSettings.personalInfo}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Share some information about yourself..."
              rows={3}
            />
            <p className="text-xs text-gray-400">Add personal details to help the AI generate more personalized responses. This information stays on your device.</p>
          </div>

          {/* Response Language */}
          <div className="space-y-1">
            <label className="block text-sm font-medium text-gray-200">Response Language</label>
            <div className="flex items-center space-x-4">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="responseLanguage"
                  value="detected"
                  checked={localSettings.responseLanguage === 'detected'}
                  onChange={handleChange}
                  className="text-blue-500 focus:ring-blue-500 h-4 w-4 bg-slate-700 border-slate-600"
                />
                <span className="ml-2 text-sm text-gray-200">Match detected language</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="responseLanguage"
                  value="english"
                  checked={localSettings.responseLanguage === 'english'}
                  onChange={handleChange}
                  className="text-blue-500 focus:ring-blue-500 h-4 w-4 bg-slate-700 border-slate-600"
                />
                <span className="ml-2 text-sm text-gray-200">Always English</span>
              </label>
            </div>
            <p className="text-xs text-gray-400">Choose whether AI responses should match the detected language or always be in English.</p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex justify-end p-3 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="ml-2 px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal; 