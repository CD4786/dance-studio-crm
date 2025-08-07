// WebSocket connection for real-time updates
class WebSocketManager {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.pingInterval = null;
  }

  connect(userId) {
    if (this.socket) {
      this.disconnect();
    }

    try {
      // Get backend URL from environment
      const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;
      
      // Convert to WebSocket URL
      let wsUrl;
      if (backendUrl.includes('railway.app')) {
        // For Railway, use the same domain with wss
        wsUrl = backendUrl.replace('https://', 'wss://') + `/ws/${userId}`;
      } else if (backendUrl.includes('localhost')) {
        // For local development
        wsUrl = backendUrl.replace('http://', 'ws://') + `/ws/${userId}`;
      } else {
        // Default fallback
        wsUrl = `wss://${backendUrl.replace(/^https?:\/\//, '')}/ws/${userId}`;
      }

      console.log('Attempting WebSocket connection to:', wsUrl);

      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Send periodic ping to keep connection alive
        this.pingInterval = setInterval(() => {
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send('ping');
          }
        }, 30000);

        // Notify listeners of connection
        this.notifyListeners('connection', { status: 'connected' });
      };

      this.socket.onmessage = (event) => {
        try {
          if (event.data === 'pong') return; // Handle ping/pong

          const message = JSON.parse(event.data);
          console.log('📡 WebSocket message received:', message.type);
          
          // Notify all listeners for this message type
          const typeListeners = this.listeners.get(message.type) || [];
          typeListeners.forEach(callback => {
            try {
              callback(message);
            } catch (error) {
              console.error('Error in message listener:', error);
            }
          });
          
          // Notify global listeners
          const globalListeners = this.listeners.get('*') || [];
          globalListeners.forEach(callback => {
            try {
              callback(message);
            } catch (error) {
              console.error('Error in global listener:', error);
            }
          });
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }

        // Attempt to reconnect unless it's a deliberate close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          
          setTimeout(() => {
            this.connect(userId);
          }, this.reconnectDelay * this.reconnectAttempts);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('❌ Max reconnect attempts reached');
          this.notifyListeners('connection', { status: 'failed', reason: 'max_attempts_reached' });
        }
      };

      this.socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.notifyListeners('connection', { status: 'error', error: error });
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.notifyListeners('connection', { status: 'error', error: error });
    }
  }

  disconnect() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.socket) {
      this.socket.close(1000); // Normal closure
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
      return true;
    } else {
      console.warn('⚠️ WebSocket not connected, message not sent:', message);
      return false;
    }
  }

  // Helper method to notify listeners
  notifyListeners(type, data) {
    const listeners = this.listeners.get(type) || [];
    listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${type} listener:`, error);
      }
    });
  }

  // Get connection status
  getStatus() {
    return {
      connected: this.isConnected,
      readyState: this.socket ? this.socket.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Create singleton instance
const wsManager = new WebSocketManager();

// Make it available globally for debugging
if (typeof window !== 'undefined') {
  window.wsManager = wsManager;
}

export default wsManager;