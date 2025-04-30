import React, { useState, useEffect, useRef } from 'react';
import OverlayWindow from './components/OverlayWindow';
import { connectWebSocket, disconnectWebSocket } from './utils/websocket';

// Define the structure for transcript items - align with TranscriptData from types
// No longer need a separate interface here if it matches the imported one
// We can import TranscriptData directly later if needed, but for now matching structure
interface TranscriptItem {
  id: string;
  italian: string;
  english: string; // Make required
  replies: { italian: string; english: string }[]; // Make required
}

function App() {
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [transcriptData, setTranscriptData] = useState<TranscriptItem[]>([]);
  const wsRef = useRef<WebSocket | null>(null); // Create a ref for the WebSocket instance

  // WebSocket message handler
  const handleNewTranscript = (data: any) => {
    // Check if it's a transcript message with content
    if (data && data.type === 'transcript' && data.transcript) {
      const newItem: TranscriptItem = {
        id: Date.now().toString(), // Simple unique ID
        italian: data.transcript,
        english: data.english || "", 
        // Use the received replies array, default to empty array if not present or LLM failed
        replies: data.replies || [], 
      };
      // Prepend new item and keep max length (e.g., 10 items)
      setTranscriptData((prevData: TranscriptItem[]) => [newItem, ...prevData].slice(0, 10));
    } else if (data && data.type === 'transcript') {
        // Handle cases where we might get an empty transcript back (e.g., end of utterance)
        // We might not want to display these, or handle them differently.
        // For now, we just log it.
        console.debug("Received transcript message with empty content.");
    }
    // Can add handling for other message types here later (e.g., errors, status updates)
  };

  // Effect to connect and disconnect WebSocket
  useEffect(() => {
    // Only attempt connection if the ref is currently null
    if (!wsRef.current) { 
      console.log("App mounting, scheduling WebSocket connection attempt...");
      // Add a small delay to potentially avoid React Strict Mode double-invocation issues
      const timeoutId = setTimeout(() => {
          console.log("Attempting to connect WebSocket... (after delay)");
          // Connect and store the instance in the ref *inside* the timeout callback
          wsRef.current = connectWebSocket(handleNewTranscript);
      }, 100); // 100ms delay

      // Cleanup function on unmount
      return () => {
        console.log("App unmounting, cleaning up WebSocket connection attempt...");
        clearTimeout(timeoutId); // Clear the timeout if component unmounts before it fires
        if (wsRef.current) {
          disconnectWebSocket(wsRef.current);
          // Explicitly nullify the ref after requesting disconnect
          wsRef.current = null; 
        }
      };
    } else {
        console.log("App mounting, WebSocket ref already exists, not connecting again.");
        // If the ref already exists (e.g., due to HMR without full unmount), 
        // we still need a cleanup function for the *existing* connection when this effect instance unmounts.
        return () => {
            console.log("App unmounting effect instance, but leaving existing WebSocket ref.");
            // We don't disconnect here because the ref belongs to a previous effect run that might still be active.
            // The disconnect should happen when the component *truly* unmounts.
            // However, this branch might indicate complex state scenarios. Consider refining state management if this occurs often.
        }
    }
  }, []); // Empty dependency array means run only on mount and unmount

  const handleDragStart = (e: React.MouseEvent) => {
    setIsDragging(true);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  const handleDrag = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: position.x + e.movementX,
        y: position.y + e.movementY
      });
    }
  };

  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 2147483647 }}>
      <div 
        style={{ 
          position: 'absolute', 
          left: `${position.x}px`, 
          top: `${position.y}px`,
          pointerEvents: 'auto',
          cursor: isDragging ? 'grabbing' : 'grab' 
        }}
        onMouseDown={handleDragStart}
        onMouseUp={handleDragEnd}
        onMouseMove={handleDrag}
        onMouseLeave={handleDragEnd}
      >
        <OverlayWindow transcriptData={transcriptData} />
      </div>
    </div>
  );
}

export default App;