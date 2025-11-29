from __future__ import annotations

import asyncio
import json
import threading
from collections import deque
from datetime import datetime
from random import uniform
from typing import Deque, Dict, List, Optional, Callable

import paho.mqtt.client as mqtt

from .config import settings


# MQTT Connection Return Codes
MQTT_ERROR_CODES = {
    0: "Connection successful",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorized",
}


class MQTTManager:
    """Wraps the MQTT client providing publish/subscribe helpers and event storage."""

    def __init__(self) -> None:
        self._client = mqtt.Client(client_id=settings.mqtt_client_id, clean_session=True)
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message
        self._client.on_disconnect = self._handle_disconnect

        self._events: Deque[Dict[str, object]] = deque(maxlen=settings.max_recorded_events)
        self._subscriptions: set[str] = set(settings.mqtt_default_subscriptions)
        self._loop_thread: Optional[threading.Thread] = None
        self._connected = threading.Event()
        self._lock = threading.Lock()
        self._connection_error: Optional[str] = None
        self._last_connection_time: Optional[float] = None
        self._reconnection_count: int = 0

        # Message handlers for specific topics
        self._message_handlers: Dict[str, Callable] = {}
        self._asyncio_loop: Optional[asyncio.AbstractEventLoop] = None

    def set_asyncio_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the asyncio event loop for async message handlers."""
        self._asyncio_loop = loop

    def register_handler(self, topic_pattern: str, handler: Callable) -> None:
        """Register a handler for messages matching a topic pattern."""
        self._message_handlers[topic_pattern] = handler

    def start(self) -> None:
        """Start MQTT client with proper async connection handling."""
        if self._loop_thread and self._loop_thread.is_alive():
            return

        import time
        import logging
        logger = logging.getLogger(__name__)

        max_retries = 5
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MQTT broker at {settings.mqtt_host}:{settings.mqtt_port} (attempt {attempt + 1}/{max_retries})")

                # Use connect_async to avoid blocking
                self._client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)

                # Start network loop FIRST - critical for callbacks to work
                self._loop_thread = threading.Thread(target=self._client.loop_forever, daemon=True)
                self._loop_thread.start()

                # Brief pause to let thread start
                time.sleep(0.1)

                # Now wait for connection callback
                if self._connected.wait(timeout=30):
                    logger.info(f"Successfully connected to MQTT broker")
                    return
                else:
                    logger.warning(f"Connection timeout on attempt {attempt + 1}")
                    self._client.disconnect()
                    if self._loop_thread:
                        self._loop_thread.join(timeout=2)
                    self._loop_thread = None
                    self._connected.clear()

                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise TimeoutError(f"MQTT connection could not be established after {max_retries} attempts")

            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if self._loop_thread:
                    self._client.disconnect()
                    self._loop_thread.join(timeout=2)
                    self._loop_thread = None

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    def stop(self) -> None:
        if self._loop_thread and self._loop_thread.is_alive():
            self._client.disconnect()
            self._loop_thread.join(timeout=2)
        self._loop_thread = None
        self._connected.clear()

    def is_connected(self) -> bool:
        """Check if MQTT client is currently connected."""
        return self._connected.is_set()

    def get_connection_status(self) -> Dict[str, object]:
        """Get detailed connection status for health checks."""
        import time
        return {
            "connected": self._connected.is_set(),
            "connection_error": self._connection_error,
            "last_connection_time": self._last_connection_time,
            "uptime_seconds": time.time() - self._last_connection_time if self._last_connection_time else 0,
            "reconnection_count": self._reconnection_count,
            "thread_alive": self._loop_thread.is_alive() if self._loop_thread else False,
        }

    def publish_event(self, topic: str, payload: Dict[str, object], qos: int = 0) -> None:
        message = json.dumps(payload)
        info = self._client.publish(topic, message, qos=qos, retain=False)
        info.wait_for_publish(timeout=5)

    def subscribe(self, topic: str, qos: int = 0) -> None:
        if topic not in self._subscriptions:
            self._subscriptions.add(topic)
        self._client.subscribe(topic, qos=qos)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, object]]:
        limit = max(1, min(limit, settings.max_recorded_events))
        with self._lock:
            return list(list(self._events)[-limit:])

    def publish_dummy_payload(self, source: str = "device-A") -> Dict[str, object]:
        payload = {
            "device": source,
            "temperature_c": round(uniform(18.0, 32.0), 2),
            "humidity_pct": round(uniform(35.0, 65.0), 2),
            "status": "OK",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        topic = f"{settings.mqtt_dummy_topic}/{source}"
        self.publish_event(topic, payload)
        return payload

    # MQTT callbacks -----------------------------------------------------
    def _handle_connect(self, client: mqtt.Client, _userdata, _flags, rc: int) -> None:
        """Handle connection callback with comprehensive error logging."""
        import logging
        import time
        logger = logging.getLogger(__name__)

        if rc == 0:
            logger.info(f"MQTT connection established successfully")
            logger.info(f"Subscribing to {len(self._subscriptions)} topic patterns...")

            for topic in self._subscriptions:
                result, mid = client.subscribe(topic)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"  - Subscribed to: {topic}")
                else:
                    logger.warning(f"  - Failed to subscribe to {topic}: error code {result}")

            self._last_connection_time = time.time()
            if self._reconnection_count > 0:
                logger.info(f"MQTT reconnected successfully (reconnection #{self._reconnection_count})")
            self._reconnection_count = 0
            self._connection_error = None
            self._connected.set()
            logger.info("MQTT client ready to publish/receive messages")

        else:
            error_msg = MQTT_ERROR_CODES.get(rc, f"Unknown error code: {rc}")
            self._connection_error = error_msg
            logger.error(f"MQTT connection failed: {error_msg} (code: {rc})")
            logger.error(f"Connection parameters: host={settings.mqtt_host}, port={settings.mqtt_port}, client_id={settings.mqtt_client_id}")

            if rc == 1:
                logger.error("HINT: The broker may not support the MQTT protocol version.")
            elif rc == 2:
                logger.error("HINT: The client ID may be rejected. Try a different client ID.")
            elif rc == 3:
                logger.error("HINT: The broker may not be running. Check broker status and logs.")
            elif rc == 4:
                logger.error("HINT: Check MQTT_USERNAME and MQTT_PASSWORD in .env file.")
            elif rc == 5:
                logger.error("HINT: The broker may have ACLs enabled. Check allow_anonymous setting.")

            self._connected.clear()

    def _handle_message(self, _client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        decoded_payload: object
        try:
            decoded_payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            decoded_payload = message.payload.decode("utf-8", errors="ignore")

        event = {
            "topic": message.topic,
            "qos": message.qos,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": decoded_payload,
        }
        with self._lock:
            self._events.append(event)

        # Call registered handlers
        self._dispatch_to_handlers(message.topic, decoded_payload)

    def _dispatch_to_handlers(self, topic: str, payload: object) -> None:
        """Dispatch message to registered handlers."""
        import fnmatch
        import logging
        logger = logging.getLogger(__name__)
        
        matched = False
        for pattern, handler in self._message_handlers.items():
            if fnmatch.fnmatch(topic, pattern):
                matched = True
                logger.debug(f"Dispatching {topic} to handler for pattern {pattern}")
                # Schedule async handler if asyncio loop is available
                if self._asyncio_loop and asyncio.iscoroutinefunction(handler):
                    asyncio.run_coroutine_threadsafe(
                        handler(topic, payload),
                        self._asyncio_loop
                    )
                else:
                    # Call sync handler directly
                    try:
                        handler(topic, payload)
                    except Exception as e:
                        logger.error(
                            f"Error in message handler for {topic}: {e}"
                        )
        
        if not matched:
            logger.debug(f"No handler matched for topic: {topic}")

    def _handle_disconnect(self, _client: mqtt.Client, _userdata, rc: int) -> None:
        """Handle disconnection with reconnection tracking."""
        import logging
        logger = logging.getLogger(__name__)

        self._connected.clear()

        if rc == 0:
            logger.info("MQTT client disconnected cleanly")
        else:
            self._reconnection_count += 1
            logger.warning(f"MQTT client disconnected unexpectedly (rc={rc})")
            logger.warning(f"Reconnection attempt #{self._reconnection_count} (automatic via loop_forever)")


mqtt_manager = MQTTManager()
