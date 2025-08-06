// WebSocket connection for real-time updates
let socket = null;
let reconnectInterval = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  connect(userId) {
    if (this.socket) {
      this.disconnect();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_BACKEND_URL || window.location.origin;
    const wsUrl = `${protocol}//${host.replace(/^https?:\/\//, '')}/ws/${userId}`;

    console.log('Connecting to WebSocket:', wsUrl);

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
      // Send periodic ping to keep connection alive
      this.pingInterval = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send('ping');
        }
      }, 30000);
    };

    this.socket.onmessage = (event) => {
      try {
        if (event.data === 'pong') return; // Handle ping/pong

        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // Notify all listeners for this message type
        const typeListeners = this.listeners.get(message.type) || [];
        typeListeners.forEach(callback => callback(message));
        
        // Notify global listeners
        const globalListeners = this.listeners.get('*') || [];
        globalListeners.forEach(callback => callback(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
      this.isConnected = false;
      
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
      }

      // Attempt to reconnect
      if (this.reconnectAttempts < maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${maxReconnectAttempts})`);
        
        setTimeout(() => {
          this.connect(userId);
        }, reconnectDelay * this.reconnectAttempts);
      } else {
        console.error('Max reconnect attempts reached');
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    this.isConnected = false;
    this.listeners.clear();
  }

  // Add listener for specific message type
  on(messageType, callback) {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, []);
    }
    this.listeners.get(messageType).push(callback);
  }

  // Remove listener
  off(messageType, callback) {
    const listeners = this.listeners.get(messageType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  // Send message to server
  send(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(typeof message === 'string' ? message : JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }
}

// Create singleton instance
const wsManager = new WebSocketManager();

export default wsManager;