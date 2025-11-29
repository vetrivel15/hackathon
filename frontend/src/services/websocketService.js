/**
 * WebSocket Service for MQTT Integration
 * Connects to FastAPI WebSocket endpoint and handles MQTT topic routing
 */
class WebSocketService {
  constructor(url = null) {
    // Auto-detect WebSocket URL based on current location
    if (!url) {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const host = window.location.hostname;
      const port = 8001; // FastAPI backend port
      url = `${protocol}://${host}:${port}/ws`;
    }
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 3000;
    this.isOnline = false;
  }

  /**
   * Establish WebSocket connection
   * @returns {Promise<void>}
   */
  connect() {
    return new Promise((resolve, reject) => {
      try {
        console.log(`🔌 Connecting to WebSocket: ${this.url}`);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          this.isOnline = true;
          this.reconnectAttempts = 0;
          this.emit('connection', { status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Emit to type-specific listeners (e.g., 'joints', 'telemetry', 'pose')
            if (data.type) {
              this.emit(data.type, data);
            }

            // Also emit to general message listener
            this.emit('message', data);
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error);
            console.log('Raw message:', event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log(`🔌 WebSocket disconnected (code: ${event.code}, reason: ${event.reason})`);
          this.isOnline = false;
          this.emit('connection', { status: 'disconnected' });

          // Auto-reconnect with exponential backoff
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30000);
            console.log(`⏳ Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
          } else {
            console.error('❌ Max reconnection attempts reached');
            this.emit('connection', { status: 'failed' });
          }
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Send message to server
   * @param {object} data - Message data
   * @returns {boolean} - Success status
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        return true;
      } catch (error) {
        console.error('❌ Failed to send message:', error);
        return false;
      }
    } else {
      console.warn('⚠️ WebSocket not connected. Message not sent:', data.type);
      return false;
    }
  }

  /**
   * Send velocity command (joystick control)
   * @param {string} robotId - Robot identifier
   * @param {number} linear - Linear velocity (-1 to 1)
   * @param {number} angular - Angular velocity (-1 to 1)
   */
  sendCmdVel(robotId, linear, angular) {
    return this.send({
      type: 'cmd_vel',
      robot_id: robotId,
      linear: parseFloat(linear),
      angular: parseFloat(angular),
      timestamp: Date.now()
    });
  }

  /**
   * Send teleop command
   * @param {string} robotId - Robot identifier
   * @param {string} command - Command (sit, stand, walk, run, stop, etc.)
   * @param {object} params - Optional parameters
   */
  sendTeleop(robotId, command, params = {}) {
    return this.send({
      type: 'teleop',
      robot_id: robotId,
      command: command,
      params: params,
      timestamp: Date.now()
    });
  }

  /**
   * Send mode change command
   * @param {string} robotId - Robot identifier
   * @param {string} mode - Mode (sitting, standing, walking, running)
   */
  sendMode(robotId, mode) {
    return this.send({
      type: 'mode',
      robot_id: robotId,
      mode: mode,
      timestamp: Date.now()
    });
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
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
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
          console.error(`❌ Error in listener for event '${event}':`, error);
        }
      });
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isOnline = false;
    }
  }

  /**
   * Check connection status
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN && this.isOnline;
  }

  /**
   * Get connection metrics
   * @returns {object}
   */
  getConnectionMetrics() {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      url: this.url,
      readyState: this.ws ? this.ws.readyState : -1
    };
  }
}

// Export singleton instance
export default new WebSocketService();
