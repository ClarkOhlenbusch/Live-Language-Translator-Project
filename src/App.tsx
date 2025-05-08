import React, { useState, useEffect, useRef } from 'react';
import OverlayWindow from './components/OverlayWindow';
import { connectWebSocket, disconnectWebSocket } from './utils/websocket';
import { Settings as SettingsType, defaultSettings } from './components/SettingsModal';

// Define the structure for transcript items - align with TranscriptData from types
// No longer need a separate interface here if it matches the imported one
// We can import TranscriptData directly later if needed, but for now matching structure
interface TranscriptItem {
  id: string;
  original: string;  // Changed from italian
  english: string; // Make required
  replies: { original: string; english: string }[]; // Make required
  detected_language?: string; // The language code detected by the backend
}

function App() {
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 20 });
  const [transcriptData, setTranscriptData] = useState<TranscriptItem[]>([]);
  const [settings, setSettings] = useState<SettingsType>(() => {
    // Try to load settings from localStorage
    const savedSettings = localStorage.getItem('translator-settings');
    if (savedSettings) {
      try {
        return JSON.parse(savedSettings) as SettingsType;
      } catch (e) {
        console.error('Failed to parse saved settings:', e);
      }
    }
    return defaultSettings;
  });
  
  const [isBackendProcessing, setIsBackendProcessing] = useState(true); // Default to ON
  const [isBackendTransitioning, setIsBackendTransitioning] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null); // Create a ref for the WebSocket instance

  // Effect to save settings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('translator-settings', JSON.stringify(settings));
  }, [settings]);

  // WebSocket message handler
  const handleWebSocketMessage = (data: any) => {
    if (data && data.type === 'transcript_data' && data.transcript) {
      const newItem: TranscriptItem = {
        id: Date.now().toString(),
        original: data.transcript,
        english: data.english || "",
        replies: data.replies || [],
        detected_language: data.detected_language
      };
      setTranscriptData((prevData) => [newItem, ...prevData].slice(0, 10));
    } else if (data && data.type === 'transcript_data') {
      console.debug("Received transcript_data message with empty content.");
    } else if (data && data.type === 'backend_status') {
      setIsBackendProcessing(data.isActive);
      setIsBackendTransitioning(false); // Transition finished
      console.log(`Backend status updated: Processing ${data.isActive ? 'ON' : 'OFF'}`);
    }
  };

  // Function to send WebSocket messages safely
  const sendWsMessage = (message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not open. Message not sent:", message);
    }
  };

  // Send settings to backend
  const sendSettingsToBackend = () => {
    sendWsMessage({ type: 'settings', settings: settings });
  };
  
  // Toggle backend processing
  const handleToggleBackendProcessing = () => {
    if (isBackendTransitioning) return; // Prevent rapid toggling
    
    setIsBackendTransitioning(true);
    const newProcessingState = !isBackendProcessing;
    // Optimistically update UI, will be confirmed by backend_status
    // setIsBackendProcessing(newProcessingState); 
    
    if (newProcessingState) {
      sendWsMessage({ type: 'start_processing' });
    } else {
      sendWsMessage({ type: 'stop_processing' });
    }
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
          wsRef.current = connectWebSocket(handleWebSocketMessage);
          
          // Send initial settings and request current processing state
          setTimeout(() => {
            sendSettingsToBackend();
            // Request initial status from backend after connection
            sendWsMessage({ type: 'request_backend_status' });
          }, 1000); // Delay a bit to ensure connection is established
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
  
  // Send settings to backend whenever they change
  useEffect(() => {
    sendSettingsToBackend();
  }, [settings]);

  const handleSettingsChange = (newSettings: SettingsType) => {
    setSettings(newSettings);
  };

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
        <OverlayWindow 
          transcriptData={transcriptData} 
          settings={settings}
          onSettingsChange={handleSettingsChange}
          isBackendProcessing={isBackendProcessing}
          onToggleBackendProcessing={handleToggleBackendProcessing}
          isBackendTransitioning={isBackendTransitioning}
        />
      </div>
    </div>
  );
}

export default App;