import { io } from 'socket.io-client';

/**
 * WebSocket Service for S4 Remote Robot Management System
 * Handles real-time communication with backend services:
 * - Control commands transmission
 * - Health telemetry reception
 * - Path logging updates
 * - Maintenance alerts
 * - Event streaming
 */
class WebSocketService {
  constructor(url = null) {
    // Use current host if no URL provided (works for network access)
    if (!url) {
      const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
      const host = window.location.hostname;
      const port = 5001;
      url = `${protocol}://${host}:${port}`;
    }
    this.url = url;
    this.socket = null;
    this.listeners = new Map();
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.messageQueue = [];
    this.isOnline = false;
  }

  /**
   * Establish WebSocket connection with automatic reconnection
   * @returns {Promise<void>}
   */
  connect() {
    if (this.socket && this.socket.connected) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true;
      try {
        this.socket = io(this.url, {
          reconnection: true,
          reconnectionDelay: this.reconnectDelay,
          reconnectionDelayMax: 5000,
          reconnectionAttempts: this.maxReconnectAttempts,
          transports: ['websocket', 'polling'],
          autoConnect: true
        });

        this.socket.on('connect', () => {
          console.log('✅ WebSocket connected to:', this.url);
          this.isConnecting = false;
          this.isOnline = true;
          this.reconnectAttempts = 0;
          
          // Process queued messages
          this.processMessageQueue();
          
          this.emit('connection', { status: 'connected' });
          resolve();
        });

        this.socket.on('message', (data) => {
          try {
            this.emit('message', data);
            if (data.type) {
              this.emit(data.type, data);
            }
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        });

        // Listen for all Socket.IO events dynamically
        this.socket.onAny((event, data) => {
          this.emit(event, data);
        });

        this.socket.on('error', (error) => {
          console.error('❌ WebSocket error:', error);
          this.emit('error', error);
          this.isConnecting = false;
        });

        this.socket.on('disconnect', (reason) => {
          console.log('🔌 WebSocket disconnected:', reason);
          this.isOnline = false;
          this.emit('connection', { status: 'disconnected' });
          this.isConnecting = false;
        });

        this.socket.on('connect_error', (error) => {
          console.error('Connection error:', error);
          this.reconnectAttempts++;
          this.isConnecting = false;
        });

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Send message to server, with queuing if disconnected
   * @param {string} type - Message type
   * @param {object} data - Message payload
   * @returns {boolean} - Success status
   */
  send(type, data) {
    const message = { type, timestamp: Date.now(), ...data };

    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
      return true;
    } else {
      // Queue message for later delivery
      this.messageQueue.push(message);
      console.warn('⚠️ WebSocket not connected. Message queued:', type);
      return false;
    }
  }

  /**
   * Process queued messages when connection is restored
   * @private
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0 && this.isOnline) {
      const message = this.messageQueue.shift();
      this.socket.emit('message', message);
      console.log('📤 Processed queued message:', message.type);
    }
  }

  /**
   * Register event listener
   * @param {string} event - Event name
   * @param {function} callback - Handler function
   * @returns {function} - Unsubscribe function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Emit event to all listeners
   * @param {string} event - Event name
   * @param {*} data - Event data
   * @private
   */
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for event ${event}:`, error);
        }
      });
    }
  }

  /**
   * Request path data from server
   */
  requestPath() {
    if (this.socket && this.socket.connected) {
      this.socket.emit('request_path');
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isOnline = false;
    }
  }

  /**
   * Check connection status
   * @returns {boolean}
   */
  isConnected() {
    return this.socket && this.socket.connected && this.isOnline;
  }

  /**
   * Get connection metrics
   * @returns {object}
   */
  getConnectionMetrics() {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length,
      socketId: this.socket?.id || null
    };
  }
}

export default new WebSocketService();
