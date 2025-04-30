import React from 'react';
import { TranscriptData } from '../types';

interface TranscriptItemProps {
  item: TranscriptData;
}

const TranscriptItem: React.FC<TranscriptItemProps> = ({ item }) => {
  return (
    <div 
      className="rounded-md overflow-hidden animate-fadeIn"
      style={{
        borderLeft: '3px solid rgba(56, 189, 248, 0.7)',
        backgroundColor: 'rgba(30, 41, 59, 0.5)',
        animationDuration: '0.3s'
      }}
    >
      <div className="grid grid-cols-3 gap-2 p-3">
        {/* Italian transcript column */}
        <div className="space-y-1">
          <div className="text-xs text-sky-400 font-medium">Italian</div>
          <p className="text-white text-sm">{item.italian}</p>
        </div>
        
        {/* English translation column */}
        <div className="space-y-1">
          <div className="text-xs text-emerald-400 font-medium">English</div>
          <p className="text-gray-200 text-sm">{item.english}</p>
        </div>
        
        {/* Suggested replies column */}
        <div className="space-y-1">
          <div className="text-xs text-purple-400 font-medium">Suggested Replies</div>
          <div className="space-y-2">
            {item.replies.map((reply, index) => (
              <div 
                key={index} 
                className="cursor-pointer hover:bg-white/10 rounded p-1 transition-colors"
              >
                <p className="text-white text-sm">{reply.italian}</p>
                <p className="text-gray-400 text-xs">{reply.english}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscriptItem;