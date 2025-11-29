import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  Map,
  TrendingUp,
  RotateCw,
  Download,
  Play,
  Pause
} from 'lucide-react';
import websocketService from '../services/websocketService';

/**
 * Path Logging & Kinematics Panel - Trajectory Tracking & Analysis
 * Displays:
 * - Robot trajectory visualization on 2D grid
 * - Path statistics (distance, duration, velocity)
 * - Heatmap visualization (high activity areas)
 * - Playback timeline
 * - Path export functionality
 */
export default function PathLoggingPanel() {
  const [pathData, setPathData] = useState([]);
  const [statistics, setStatistics] = useState({
    total_distance: 0,
    duration_seconds: 0,
    point_count: 0,
    average_velocity: 0,
    max_velocity: 0,
    bounding_box: { min_x: 0, max_x: 0, min_y: 0, max_y: 0 }
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [currentSegment, setCurrentSegment] = useState(null);

  useEffect(() => {
    // Request initial path data
    websocketService.requestPath();

    // Listen for path segment updates
    const unsubPath = websocketService.on('path_segment', (data) => {
      setPathData((prev) => [...prev, {
        x: data.x,
        y: data.y,
        heading: data.heading,
        timestamp: data.timestamp
      }]);
      setCurrentSegment(data);
    });

    // Listen for full path updates
    const unsubPathUpdate = websocketService.on('path_update', (data) => {
      setPathData(data.path || []);
      setStatistics(data.statistics || {});
    });

    return () => {
      unsubPath();
      unsubPathUpdate();
    };
  }, []);

  const handleClearPath = async () => {
    try {
      await fetch('http://localhost:5001/api/robot/reset', { method: 'POST' });
      setPathData([]);
      setPlaybackIndex(0);
      setIsPlaying(false);
    } catch (error) {
      console.error('Failed to clear path:', error);
    }
  };

  const handleExportPath = () => {
    const csv = [
      ['X', 'Y', 'Heading', 'Timestamp'],
      ...pathData.map(p => [p.x, p.y, p.heading, p.timestamp])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `robot-path-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Playback simulation
  useEffect(() => {
    if (!isPlaying || pathData.length === 0) return;

    const interval = setInterval(() => {
      setPlaybackIndex((prev) => {
        if (prev >= pathData.length - 1) {
          setIsPlaying(false);
          return pathData.length - 1;
        }
        return prev + 1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, pathData.length]);

  // Generate heatmap data (grid-based frequency)
  const generateHeatmapData = () => {
    if (pathData.length === 0) return [];
    
    const gridSize = 0.2; // 20cm grid
    const heatmap = {};

    pathData.forEach(point => {
      const gridX = Math.round(point.x / gridSize) * gridSize;
      const gridY = Math.round(point.y / gridSize) * gridSize;
      const key = `${gridX},${gridY}`;
      heatmap[key] = (heatmap[key] || 0) + 1;
    });

    return Object.entries(heatmap).map(([key, count]) => {
      const [x, y] = key.split(',').map(Number);
      return { x, y, intensity: count };
    });
  };

  const heatmapData = generateHeatmapData();
  const playbackPath = pathData.slice(0, playbackIndex + 1);

  return (
    <div className="space-y-6">
      {/* Path Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Total Distance</div>
          <div className="text-2xl font-bold text-emerald-400">
            {statistics.total_distance?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-slate-500">meters</div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Duration</div>
          <div className="text-2xl font-bold text-blue-400">
            {(statistics.duration_seconds / 60)?.toFixed(1) || '0.0'}
          </div>
          <div className="text-xs text-slate-500">minutes</div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Avg Velocity</div>
          <div className="text-2xl font-bold text-cyan-400">
            {statistics.average_velocity?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-slate-500">m/s</div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Max Velocity</div>
          <div className="text-2xl font-bold text-orange-400">
            {statistics.max_velocity?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-slate-500">m/s</div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Path Points</div>
          <div className="text-2xl font-bold text-purple-400">
            {statistics.point_count || '0'}
          </div>
          <div className="text-xs text-slate-500">recorded</div>
        </div>

        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-sm text-slate-400 mb-1">Bounding Box</div>
          <div className="text-sm font-bold text-yellow-400">
            {(statistics.bounding_box?.max_x - statistics.bounding_box?.min_x)?.toFixed(2)}
            {' '} x {' '}
            {(statistics.bounding_box?.max_y - statistics.bounding_box?.min_y)?.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">meters</div>
        </div>
      </div>

      {/* Path Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trajectory Map */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Map className="w-5 h-5" />
            Trajectory Visualization
          </h3>

          {pathData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                data={playbackPath}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="x"
                  type="number"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  domain="dataMin - 0.5"
                  label={{ value: 'X (meters)', position: 'insideBottomRight', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  dataKey="y"
                  type="number"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  domain="dataMin - 0.5"
                  label={{ value: 'Y (meters)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#e2e8f0' }}
                  cursor={{ strokeDasharray: '3 3' }}
                />
                <Scatter
                  name="Path"
                  data={playbackPath}
                  fill="#06b6d4"
                  line
                  isAnimationActive={false}
                />
                {currentSegment && (
                  <Scatter
                    name="Current"
                    data={[currentSegment]}
                    fill="#10b981"
                    shape="diamond"
                  />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-72 flex items-center justify-center text-slate-500">
              No path data yet. Drive the robot to record trajectory.
            </div>
          )}
        </div>

        {/* Heatmap */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Activity Heatmap
          </h3>

          {heatmapData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="x"
                  type="number"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  label={{ value: 'X (meters)', position: 'insideBottomRight', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  dataKey="y"
                  type="number"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  label={{ value: 'Y (meters)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#e2e8f0' }}
                  cursor={{ strokeDasharray: '3 3' }}
                />
                <Scatter
                  name="Activity"
                  data={heatmapData}
                  fill="#fbbf24"
                  shape="circle"
                  isAnimationActive={false}
                />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-72 flex items-center justify-center text-slate-500">
              No heatmap data available yet.
            </div>
          )}
        </div>
      </div>

      {/* Playback Controls */}
      {pathData.length > 0 && (
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Play className="w-5 h-5" />
            Path Playback
          </h3>

          <div className="space-y-4">
            {/* Playback Progress */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">
                  Frame {playbackIndex + 1} / {pathData.length}
                </span>
                <span className="text-sm text-slate-400">
                  {((playbackIndex / pathData.length) * 100).toFixed(1)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max={pathData.length - 1}
                value={playbackIndex}
                onChange={(e) => setPlaybackIndex(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-full appearance-none cursor-pointer"
              />
            </div>

            {/* Playback Controls */}
            <div className="flex gap-3">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="flex-1 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 px-4 py-2 rounded-lg font-semibold text-white transition-all flex items-center justify-center gap-2"
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-4 h-4" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Play
                  </>
                )}
              </button>

              <button
                onClick={() => setPlaybackIndex(0)}
                className="flex-1 bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg font-semibold text-slate-300 transition-all flex items-center justify-center gap-2"
              >
                <RotateCw className="w-4 h-4" />
                Reset
              </button>

              <button
                onClick={handleExportPath}
                className="flex-1 bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg font-semibold text-slate-300 transition-all flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>

            {/* Clear Path Button */}
            <button
              onClick={handleClearPath}
              className="w-full bg-red-900/40 hover:bg-red-900/60 border border-red-600/50 px-4 py-2 rounded-lg font-semibold text-red-300 transition-all"
            >
              Clear Path History
            </button>
          </div>
        </div>
      )}

      {/* Current Position */}
      {currentSegment && (
        <div className="bg-gradient-to-br from-emerald-900/20 to-cyan-900/20 border border-emerald-600/50 rounded-lg p-4 shadow-lg">
          <h3 className="font-semibold mb-3 text-emerald-300">Current Position</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-slate-400">X</div>
              <div className="text-2xl font-bold text-cyan-400">
                {currentSegment.x?.toFixed(3) || '0.000'}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">Y</div>
              <div className="text-2xl font-bold text-cyan-400">
                {currentSegment.y?.toFixed(3) || '0.000'}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">Heading</div>
              <div className="text-2xl font-bold text-yellow-400">
                {currentSegment.heading?.toFixed(1) || '0.0'}°
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
