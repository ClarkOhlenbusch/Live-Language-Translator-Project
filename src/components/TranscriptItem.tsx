import React from 'react';
import { TranscriptData } from '../types';

interface TranscriptItemProps {
  item: TranscriptData;
}

const TranscriptItem: React.FC<TranscriptItemProps> = ({ item }) => {
  // Get detected language from the item or use our fallback detection
  const getLanguageLabel = (text: string, detectedLanguage?: string): string => {
    // If we have detected language from the backend, use it
    if (detectedLanguage) {
      // Map language codes to full names
      const languageMap: Record<string, string> = {
        "EN": "English",
        "DE": "German",
        "FR": "French", 
        "ES": "Spanish",
        "IT": "Italian",
        "NL": "Dutch",
        "PT": "Portuguese",
        "RU": "Russian",
        "JA": "Japanese"
      };
      return languageMap[detectedLanguage] || detectedLanguage;
    }
    
    // Fallback client-side detection (simple heuristic)
    if (!text) return "Unknown";
    if (/[àèéìòù]/i.test(text)) return "Italian";
    if (/[áéíóúñ¿¡]/i.test(text)) return "Spanish";
    if (/[äöüß]/i.test(text)) return "German";
    if (/[àâçéèêëîïôùûüÿ]/i.test(text)) return "French";
    if (/[а-яА-Я]/i.test(text)) return "Russian";
    
    return "Auto-detected";
  };

  const languageLabel = getLanguageLabel(item.original, item.detected_language);
  
  return (
    <div 
      className="rounded-md overflow-hidden animate-fadeIn mb-2.5"
      style={{
        borderLeft: '3px solid rgba(56, 189, 248, 0.7)',
        backgroundColor: 'rgba(30, 41, 59, 0.5)',
        animationDuration: '0.3s'
      }}
    >
      <div className="grid grid-cols-3 gap-2 p-2.5">
        {/* Original transcript column */}
        <div className="space-y-1">
          <div className="text-xs font-medium flex items-center">
            <span className="text-sky-400">Original</span>
            <span className="text-gray-400 text-xs ml-1 opacity-75">({languageLabel})</span>
          </div>
          <p className="text-white text-sm leading-snug">{item.original}</p>
        </div>
        
        {/* English translation column */}
        <div className="space-y-1">
          <div className="text-xs text-emerald-400 font-medium">English</div>
          <p className="text-gray-200 text-sm leading-snug">{item.english}</p>
        </div>
        
        {/* Suggested replies column */}
        <div className="space-y-1">
          <div className="text-xs text-purple-400 font-medium">Suggested Replies</div>
          <div className="space-y-1.5">
            {item.replies && item.replies.length > 0 ? (
              item.replies.map((reply, index) => (
                <div 
                  key={index} 
                  className="cursor-pointer hover:bg-white/10 rounded p-1 transition-colors"
                >
                  <p className="text-white text-sm leading-snug">{reply.original}</p>
                  <p className="text-gray-400 text-xs">{reply.english}</p>
                </div>
              ))
            ) : (
              <div className="text-gray-400 text-xs italic">No suggestions available</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscriptItem;