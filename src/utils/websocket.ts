let wsInstance: WebSocket | null = null;

// Define a type for the message handler callback
type MessageHandler = (data: any) => void;

export const connectWebSocket = (onMessageCallback: MessageHandler): WebSocket | null => {
  if (wsInstance) {
    console.log("WebSocket already connected or connecting.");
    return wsInstance;
  }

  const newWs = new WebSocket('ws://localhost:8765');
  wsInstance = newWs;
  console.log("Attempting to connect WebSocket...");

  newWs.onopen = () => {
    console.log('Connected to WebSocket server');
  };

  newWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessageCallback(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', event.data, error);
    }
  };

  newWs.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  newWs.onclose = (event) => {
    console.log(`Disconnected from WebSocket server. Code: ${event.code}, Reason: ${event.reason}`);
    if (wsInstance === newWs) {
      wsInstance = null;
    }
  };

  return newWs;
};

export const disconnectWebSocket = (wsToDisconnect: WebSocket | null) => {
  // Check if the instance to disconnect is valid and is the current shared instance
  if (wsToDisconnect && wsToDisconnect === wsInstance) {
    console.log('Closing WebSocket connection...', wsToDisconnect.url);
    // Only close if the connection is open or in the process of closing.
    if (wsToDisconnect.readyState === WebSocket.OPEN || wsToDisconnect.readyState === WebSocket.CLOSING) {
      wsToDisconnect.close();
    } else {
      console.log('WebSocket is not open or closing, skipping close() call. State:', wsToDisconnect.readyState);
    }
    // Only nullify the shared instance if we are closing the active shared one
    wsInstance = null;
  } else if (wsToDisconnect) {
    // If it's a valid instance but not the shared one (e.g., from a previous StrictMode render), still try to close it carefully
    console.log('Closing potentially stale WebSocket instance...', wsToDisconnect.url);
     // Only close if the connection is open or in the process of closing.
    if (wsToDisconnect.readyState === WebSocket.OPEN || wsToDisconnect.readyState === WebSocket.CLOSING) {
      wsToDisconnect.close();
    } else {
      console.log('Stale WebSocket is not open or closing, skipping close() call. State:', wsToDisconnect.readyState);
    }
  } else {
    console.log('Disconnect called with null WebSocket instance.');
  }
};

export const sendMessage = (message: object) => {
  if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
    wsInstance.send(JSON.stringify(message));
  } else {
    console.error('WebSocket not connected or not open.');
  }
};