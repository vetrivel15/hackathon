import { io } from 'socket.io-client';

class WebSocketService {
  constructor(url = 'http://localhost:5001') {
    this.url = url;
    this.socket = null;
    this.listeners = new Map();
    this.isConnecting = false;
  }

  connect() {
    if (this.socket && this.socket.connected) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true;
      try {
        this.socket = io(this.url, {
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionDelayMax: 5000,
          reconnectionAttempts: 10,
          transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
          console.log('✅ WebSocket connected');
          this.isConnecting = false;
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

        // Listen for all Socket.IO events
        this.socket.onAny((event, data) => {
          this.emit(event, data);
        });

        this.socket.on('error', (error) => {
          console.error('❌ WebSocket error:', error);
          this.emit('error', error);
          this.isConnecting = false;
          reject(error);
        });

        this.socket.on('disconnect', () => {
          console.log('🔌 WebSocket disconnected');
          this.emit('connection', { status: 'disconnected' });
          this.isConnecting = false;
        });
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  send(type, data) {
    if (this.socket && this.socket.connected) {
      const message = { type, timestamp: Date.now(), ...data };
      this.socket.emit('message', message);
      return true;
    } else {
      console.warn('⚠️ WebSocket not connected. Cannot send:', type);
      return false;
    }
  }

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

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected() {
    return this.socket && this.socket.connected;
  }
}

export default new WebSocketService();
