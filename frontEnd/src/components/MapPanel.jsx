import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import websocketService from '../services/websocketService';

export default function MapPanel() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const robotMarker = useRef(null);
  const pathPolyline = useRef(null);
  const headingArrow = useRef(null);
  const waypointMarkers = useRef([]);
  const obstacleCircles = useRef([]);
  const pathCoordinates = useRef([]);

  const [robotPos, setRobotPos] = useState({ lat: 37.7749, lon: -122.4194, heading: 0 });
  const [currentMode, setCurrentMode] = useState('Walk');

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    map.current = L.map(mapContainer.current).setView([37.7749, -122.4194], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
      className: 'grayscale opacity-60'
    }).addTo(map.current);

    // Custom robot icon SVG
    const robotIcon = L.divIcon({
      html: `<div class="flex items-center justify-center">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="12" fill="#22d3ee" stroke="#06b6d4" stroke-width="2"/>
          <circle cx="16" cy="16" r="8" fill="#0369a1"/>
          <polygon points="16,6 20,14 12,14" fill="#22d3ee"/>
        </svg>
      </div>`,
      iconSize: [32, 32],
      className: 'robot-marker'
    });

    robotMarker.current = L.marker([37.7749, -122.4194], { icon: robotIcon }).addTo(map.current);
    robotMarker.current.bindPopup('HUM-01<br>Status: Active');

    // Initialize path polyline
    pathPolyline.current = L.polyline([], {
      color: '#06b6d4',
      weight: 2,
      opacity: 0.6,
      dashArray: '5, 5'
    }).addTo(map.current);

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Handle pose updates and mode changes
  useEffect(() => {
    const unsubPose = websocketService.on('pose_update', (data) => {
      const { lat, lon, heading } = data;
      setRobotPos({ lat, lon, heading });

      if (map.current && robotMarker.current) {
        const newPos = [lat, lon];
        robotMarker.current.setLatLng(newPos);

        // Update path trail
        if (pathCoordinates.current.length === 0 || 
            Math.hypot(lat - pathCoordinates.current[pathCoordinates.current.length - 1][0],
                      lon - pathCoordinates.current[pathCoordinates.current.length - 1][1]) > 0.0001) {
          pathCoordinates.current.push([lat, lon]);
          pathPolyline.current.setLatLngs(pathCoordinates.current);
        }

        // Rotate robot marker based on heading
        if (robotMarker.current._icon) {
          robotMarker.current._icon.style.transform = `rotate(${heading}deg)`;
        }

        // Update heading arrow
        if (headingArrow.current) {
          map.current.removeLayer(headingArrow.current);
        }
        headingArrow.current = L.polyline([
          [lat, lon],
          [lat + 0.0002 * Math.sin(heading * Math.PI / 180), 
           lon + 0.0002 * Math.cos(heading * Math.PI / 180)]
        ], {
          color: '#f59e0b',
          weight: 3,
          opacity: 0.8
        }).addTo(map.current);

        map.current.panTo(newPos, { animate: true });
      }
    });

    const unsubMode = websocketService.on('mode_update', (data) => {
      const { mode } = data;
      setCurrentMode(mode || 'Walk');
    });

    const unsubObstacle = websocketService.on('obstacle_detected', (data) => {
      if (map.current && data.lat && data.lon) {
        // Remove old obstacle circles if too many
        if (obstacleCircles.current.length > 20) {
          const old = obstacleCircles.current.shift();
          map.current.removeLayer(old);
        }

        const circle = L.circle([data.lat, data.lon], {
          radius: data.radius || 1,
          color: '#ef4444',
          fill: true,
          fillColor: '#dc2626',
          fillOpacity: 0.5,
          weight: 2
        }).addTo(map.current);

        obstacleCircles.current.push(circle);
      }
    });

    const unsubWaypoint = websocketService.on('waypoint_set', (data) => {
      if (map.current && data.lat && data.lon) {
        const icon = L.divIcon({
          html: `<div class="flex items-center justify-center">
            <div class="w-3 h-3 bg-green-400 rounded-full border-2 border-green-600"></div>
          </div>`,
          iconSize: [12, 12],
          className: 'waypoint-marker'
        });

        const marker = L.marker([data.lat, data.lon], { icon }).addTo(map.current);
        marker.bindPopup(`Waypoint<br>${data.name || 'Target'}`);
        waypointMarkers.current.push(marker);
      }
    });

    return () => {
      unsubPose();
      unsubMode();
      unsubObstacle();
      unsubWaypoint();
    };
  }, []);

  const getModeIndicatorColor = () => {
    return currentMode === 'Run' ? 'bg-orange-900/50 border-orange-500' : 'bg-blue-900/50 border-blue-500';
  };

  return (
    <section className="bg-slate-900 rounded-xl p-4 border border-slate-700 shadow-lg h-[600px]">
      <h2 className="font-semibold mb-3 text-cyan-300 flex items-center gap-2 justify-between">
        <span className="flex items-center gap-2">
          📍 Live Map
          <span className={`text-xs px-2 py-1 rounded border ${getModeIndicatorColor()}`}>
            {currentMode === 'Run' ? '🏃' : '🚶'} {currentMode}
          </span>
        </span>
        <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">
          Pos: {robotPos.lat.toFixed(4)}, {robotPos.lon.toFixed(4)} | Heading: {robotPos.heading.toFixed(1)}°
        </span>
      </h2>
      <div 
        ref={mapContainer} 
        className="w-full h-[calc(100%-3rem)] rounded-lg border border-slate-700 overflow-hidden"
      />
    </section>
  );
}
