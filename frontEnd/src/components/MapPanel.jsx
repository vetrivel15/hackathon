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

  const [robotPos, setRobotPos] = useState({ lat: 12.9352, lon: 77.6245, heading: 0 });
  const [currentMode, setCurrentMode] = useState('Walk');
  const [isFollowingRobot, setIsFollowingRobot] = useState(false);
  const followingTimeoutRef = useRef(null);

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    // BTM, Bangalore coordinates
    map.current = L.map(mapContainer.current).setView([12.9352, 77.6245], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(map.current);

    // Create a modern, sleek robot icon
    const robotIcon = L.divIcon({
      html: `<div style="position: relative; width: 70px; height: 70px; display: flex; align-items: center; justify-content: center;">
        <div style="position: absolute; width: 68px; height: 68px; background: radial-gradient(circle, rgba(0, 217, 255, 0.3) 0%, rgba(0, 217, 255, 0.1) 70%, transparent 100%); border-radius: 50%; animation: pulse 2s infinite;"></div>
        <div style="position: absolute; width: 42px; height: 48px; background: linear-gradient(135deg, #0891b2 0%, #06b6d4 50%, #0ea5e9 100%); border: 2px solid #00d9ff; border-radius: 10px; box-shadow: 0 0 16px rgba(0, 217, 255, 0.6), inset 0 2px 6px rgba(255, 255, 255, 0.2); z-index: 5;"></div>
        <div style="position: absolute; top: -15px; width: 28px; height: 28px; background: linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%); border: 2px solid #00d9ff; border-radius: 50%; box-shadow: 0 0 12px rgba(34, 211, 238, 0.8);"></div>
        <div style="position: absolute; top: -25px; width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-bottom: 10px solid #fbbf24; filter: drop-shadow(0 0 2px #f59e0b); z-index: 10;"></div>
        <div style="position: absolute; top: -10px; left: -12px; width: 10px; height: 10px; background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6); border: 1px solid #1e40af; border-radius: 50%; box-shadow: 0 0 6px #3b82f6;"></div>
        <div style="position: absolute; top: -10px; right: -12px; width: 10px; height: 10px; background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6); border: 1px solid #1e40af; border-radius: 50%; box-shadow: 0 0 6px #3b82f6;"></div>
        <div style="position: absolute; width: 32px; height: 20px; background: linear-gradient(135deg, #064e3b 0%, #047857 100%); border: 1px solid #10b981; border-radius: 4px; box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.5);"></div>
        <div style="position: absolute; width: 4px; height: 4px; background: #10b981; border-radius: 50%; top: 6px; left: 6px; box-shadow: 0 0 4px #10b981;"></div>
        <div style="position: absolute; width: 4px; height: 4px; background: #10b981; border-radius: 50%; top: 6px; left: 16px; box-shadow: 0 0 4px #10b981;"></div>
        <div style="position: absolute; width: 4px; height: 4px; background: #10b981; border-radius: 50%; top: 6px; right: 6px; box-shadow: 0 0 4px #10b981;"></div>
        <div style="position: absolute; width: 12px; height: 8px; background: #0ea5e9; border: 1px solid #00d9ff; border-radius: 3px; left: -10px; top: 8px;"></div>
        <div style="position: absolute; width: 12px; height: 8px; background: #0ea5e9; border: 1px solid #00d9ff; border-radius: 3px; right: -10px; top: 8px;"></div>
        <div style="position: absolute; width: 6px; height: 12px; background: linear-gradient(90deg, #0ea5e9 0%, #06b6d4 100%); border: 1px solid #00d9ff; border-radius: 3px; left: 0px; top: 10px;"></div>
        <div style="position: absolute; width: 6px; height: 12px; background: linear-gradient(90deg, #06b6d4 0%, #0ea5e9 100%); border: 1px solid #00d9ff; border-radius: 3px; right: 0px; top: 10px;"></div>
        <div style="position: absolute; width: 8px; height: 14px; background: #0891b2; border: 1px solid #0ea5e9; border-radius: 2px; left: 10px; bottom: -10px;"></div>
        <div style="position: absolute; width: 8px; height: 14px; background: #0891b2; border: 1px solid #0ea5e9; border-radius: 2px; right: 10px; bottom: -10px;"></div>
        <div style="position: absolute; width: 38px; height: 2px; background: linear-gradient(90deg, transparent, #fbbf24, transparent); bottom: 6px; box-shadow: 0 0 4px #fbbf24;"></div>
        <style>@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.05); opacity: 0.8; } }</style>
      </div>`,
      iconSize: [70, 70],
      iconAnchor: [35, 35],
      popupAnchor: [0, -35]
    });

    robotMarker.current = L.marker([12.9352, 77.6245], { icon: robotIcon }).addTo(map.current);
    robotMarker.current.bindPopup('<div class="text-center"><strong>zeeno</strong><br>Humanoid Robot<br><em>Status: Active</em></div>');

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
          robotMarker.current._icon.style.transform = `rotate(${heading}deg) scale(1.1)`;
          robotMarker.current._icon.style.transition = 'transform 0.2s ease-out';
        }

        // Update heading arrow - make it more prominent
        if (headingArrow.current) {
          map.current.removeLayer(headingArrow.current);
        }
        
        const arrowLength = 0.0004; // Larger arrow
        headingArrow.current = L.polyline([
          [lat, lon],
          [lat + arrowLength * Math.sin(heading * Math.PI / 180), 
           lon + arrowLength * Math.cos(heading * Math.PI / 180)]
        ], {
          color: '#fbbf24',
          weight: 4,
          opacity: 0.9,
          lineCap: 'round'
        }).addTo(map.current);

        // Auto-pan to robot only during continuous movement, not during spot
        if (isFollowingRobot && !followingTimeoutRef.current) {
          map.current.panTo(newPos, { animate: true, duration: 0.5 });
        }
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
            <div class="w-4 h-4 bg-green-400 rounded-full border-2 border-green-600 shadow-lg shadow-green-500/50"></div>
          </div>`,
          iconSize: [16, 16],
          className: 'waypoint-marker'
        });

        const marker = L.marker([data.lat, data.lon], { icon }).addTo(map.current);
        marker.bindPopup(`<strong>Waypoint</strong><br>${data.name || 'Target'}`);
        waypointMarkers.current.push(marker);
      }
    });

    return () => {
      unsubPose();
      unsubMode();
      unsubObstacle();
      unsubWaypoint();
    };
  }, [isFollowingRobot]);

  const getModeIndicatorColor = () => {
    return currentMode === 'Run' ? 'bg-orange-900/50 border-orange-500' : 'bg-blue-900/50 border-blue-500';
  };

  const spotRobot = () => {
    if (map.current && robotMarker.current) {
      // Disable following during the centering animation
      setIsFollowingRobot(false);
      
      // Center and zoom on robot
      map.current.setView(robotMarker.current.getLatLng(), 17, { 
        animate: true, 
        duration: 0.8 
      });
      
      // Open popup
      robotMarker.current.openPopup();
      
      // Clear any existing timeout
      if (followingTimeoutRef.current) {
        clearTimeout(followingTimeoutRef.current);
      }
      
      // After animation completes, keep following disabled unless user wants it
      followingTimeoutRef.current = setTimeout(() => {
        followingTimeoutRef.current = null;
      }, 1000);
    }
  };

  const toggleAutoFollow = () => {
    setIsFollowingRobot(prev => !prev);
  };

  return (
    <section className="bg-slate-900 rounded-xl p-4 border border-slate-700 shadow-lg h-[600px] flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-cyan-300 flex items-center gap-2">
          <span className="flex items-center gap-2">
            📍 Live Map
            <span className={`text-xs px-2 py-1 rounded border ${getModeIndicatorColor()}`}>
              {currentMode === 'Run' ? '🏃' : '🚶'} {currentMode}
            </span>
          </span>
        </h2>
        
        <div className="flex items-center gap-2">
          <button
            onClick={toggleAutoFollow}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold text-white transition-all transform shadow-lg ${
              isFollowingRobot
                ? 'bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 active:from-green-700 active:to-green-600 hover:shadow-green-500/50'
                : 'bg-gradient-to-r from-gray-600 to-gray-500 hover:from-gray-500 hover:to-gray-400 active:from-gray-700 active:to-gray-600 hover:shadow-gray-500/50'
            }`}
            title="Toggle auto-follow"
          >
            {isFollowingRobot ? '🔒 Auto-Follow On' : '🔓 Auto-Follow Off'}
          </button>
          <button
            onClick={spotRobot}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 active:from-cyan-700 active:to-cyan-600 px-3 py-1.5 rounded-lg text-sm font-semibold text-white transition-all transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-cyan-500/50"
            title="Center on robot"
          >
            🎯 Spot Robot
          </button>
        </div>
      </div>

      {/* Coordinates and heading display */}
      <div className="text-xs bg-slate-800 px-3 py-1.5 rounded border border-slate-600 mb-3 font-mono text-slate-300">
        <span className="text-cyan-400 font-semibold">Pos:</span> {robotPos.lat.toFixed(4)}, {robotPos.lon.toFixed(4)} | 
        <span className="text-yellow-400 font-semibold ml-2">Heading:</span> {robotPos.heading.toFixed(1)}°
      </div>

      <div 
        ref={mapContainer} 
        className="flex-1 w-full rounded-lg border border-slate-700 overflow-hidden"
      />

      {/* Map legend */}
      <div className="mt-3 text-xs text-slate-400 grid grid-cols-3 gap-2 bg-slate-800/50 p-2 rounded border border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse"></div>
          <span>Robot</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400"></div>
          <span>Waypoint</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          <span>Obstacle</span>
        </div>
      </div>
    </section>
  );
}
