import { useEffect, useState } from 'react';
import {
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  HardDrive,
  TrendingUp
} from 'lucide-react';
import websocketService from '../services/websocketService';

/**
 * OTA Update Management Panel - Remote Software Updates
 * Displays:
 * - Current software version
 * - Available updates
 * - Update progress simulation
 * - Update history log
 * - File download info
 */
export default function OTAUpdatePanel() {
  const [updateState, setUpdateState] = useState({
    currentVersion: '1.0.0',
    latestVersion: '1.2.0',
    inProgress: false,
    progress: 0,
    availableUpdates: [],
    history: []
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState('');

  useEffect(() => {
    // Fetch initial update status
    fetch('http://localhost:5001/api/updates')
      .then(res => res.json())
      .then(data => {
        setUpdateState(data);
        if (data.available_updates.length > 0) {
          setSelectedVersion(data.available_updates[0].version);
        }
      })
      .catch(err => console.error('Failed to fetch updates:', err));

    // Poll for update progress
    const progressInterval = setInterval(() => {
      fetch('http://localhost:5001/api/updates/progress')
        .then(res => res.json())
        .then(data => {
          setUpdateState(prev => ({
            ...prev,
            inProgress: data.in_progress,
            progress: data.progress,
            currentVersion: data.current_version
          }));
        })
        .catch(err => console.error('Failed to fetch progress:', err));
    }, 1000);

    return () => clearInterval(progressInterval);
  }, []);

  const handleStartUpdate = async () => {
    if (!selectedVersion) return;

    try {
      const response = await fetch('http://localhost:5001/api/updates/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: selectedVersion })
      });

      const result = await response.json();
      if (result.success) {
        setIsUpdating(true);
        setUpdateState(prev => ({
          ...prev,
          inProgress: true,
          progress: 0
        }));
      } else {
        alert(`Error: ${result.error}`);
      }
    } catch (error) {
      console.error('Failed to start update:', error);
      alert('Failed to start update');
    }
  };

  const getUpdateInfo = () => {
    return updateState.availableUpdates.find(u => u.version === selectedVersion);
  };

  const updateInfo = getUpdateInfo();

  return (
    <div className="space-y-6">
      {/* Current Version Status */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm text-slate-400 mb-2">Current Version</h3>
            <div className="text-3xl font-bold text-cyan-400">{updateState.currentVersion}</div>
            <div className="text-xs text-slate-500 mt-1">Currently Running</div>
          </div>

          <div>
            <h3 className="text-sm text-slate-400 mb-2">Latest Version</h3>
            <div className="text-3xl font-bold text-emerald-400">{updateState.latestVersion}</div>
            <div className={`text-xs mt-1 ${
              updateState.currentVersion !== updateState.latestVersion
                ? 'text-yellow-400'
                : 'text-emerald-400'
            }`}>
              {updateState.currentVersion !== updateState.latestVersion
                ? 'Update Available ✓'
                : 'Up to Date ✓'}
            </div>
          </div>

          <div>
            <h3 className="text-sm text-slate-400 mb-2">Status</h3>
            <div className={`inline-block px-4 py-2 rounded-lg font-semibold text-sm ${
              updateState.inProgress
                ? 'bg-blue-900/40 text-blue-300 border border-blue-600/50'
                : updateState.currentVersion === updateState.latestVersion
                  ? 'bg-emerald-900/40 text-emerald-300 border border-emerald-600/50'
                  : 'bg-yellow-900/40 text-yellow-300 border border-yellow-600/50'
            }`}>
              {updateState.inProgress
                ? 'Updating...'
                : updateState.currentVersion === updateState.latestVersion
                  ? 'Up to Date'
                  : 'Update Available'}
            </div>
          </div>
        </div>
      </div>

      {/* Update Progress */}
      {updateState.inProgress && (
        <div className="bg-blue-900/20 border border-blue-600/50 rounded-lg p-6 shadow-lg">
          <h3 className="font-semibold mb-4 text-blue-300 flex items-center gap-2">
            <Download className="w-5 h-5" />
            Update in Progress
          </h3>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-blue-300">{selectedVersion}</span>
                <span className="text-blue-400 font-bold">{updateState.progress.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-slate-700/50 rounded-full h-4 overflow-hidden border border-blue-600/50">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all"
                  style={{ width: `${updateState.progress}%` }}
                ></div>
              </div>
            </div>

            {updateState.progress < 100 && (
              <div className="text-sm text-blue-300 flex items-center gap-2">
                <Clock className="w-4 h-4 animate-spin" />
                Downloading and installing update...
              </div>
            )}

            {updateState.progress === 100 && (
              <div className="text-sm text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Update completed successfully!
              </div>
            )}
          </div>
        </div>
      )}

      {/* Available Updates */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
        <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
          <Download className="w-5 h-5" />
          Available Updates
        </h3>

        {updateState.availableUpdates.length > 0 ? (
          <div className="space-y-4">
            {/* Version Selection */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Select Version to Update</label>
              <select
                value={selectedVersion}
                onChange={(e) => setSelectedVersion(e.target.value)}
                disabled={updateState.inProgress}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-400 disabled:bg-slate-700 disabled:cursor-not-allowed"
              >
                {updateState.availableUpdates.map((update) => (
                  <option key={update.version} value={update.version}>
                    v{update.version} - {update.release_date}
                  </option>
                ))}
              </select>
            </div>

            {/* Update Details */}
            {updateInfo && (
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-slate-400">Version</div>
                    <div className="text-lg font-bold text-cyan-400">v{updateInfo.version}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Size</div>
                    <div className="text-lg font-bold text-blue-400">{updateInfo.size_mb} MB</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Release Date</div>
                    <div className="text-lg font-bold text-yellow-400">{updateInfo.release_date}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">Status</div>
                    <div className="text-lg font-bold text-emerald-400">Available</div>
                  </div>
                </div>

                <div>
                  <div className="text-sm text-slate-400 mb-2">Changes</div>
                  <div className="text-sm text-slate-300 bg-slate-900/50 rounded p-3">
                    📝 {updateInfo.changes}
                  </div>
                </div>
              </div>
            )}

            {/* Update Button */}
            <button
              onClick={handleStartUpdate}
              disabled={updateState.inProgress || updateState.currentVersion === selectedVersion}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed px-4 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 active:scale-95 shadow-lg flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              {updateState.inProgress
                ? 'Updating...'
                : updateState.currentVersion === selectedVersion
                  ? 'Already Running'
                  : `Update to v${selectedVersion}`}
            </button>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No updates available</p>
          </div>
        )}
      </div>

      {/* Update History */}
      {updateState.history.length > 0 && (
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Update History
          </h3>

          <div className="space-y-3 max-h-48 overflow-y-auto">
            {updateState.history.map((entry, idx) => (
              <div key={idx} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-cyan-300">v{entry.version}</span>
                  <div className="flex items-center gap-2">
                    {entry.status === 'SUCCESS' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-400" />
                    )}
                    <span className={`text-xs font-bold ${
                      entry.status === 'SUCCESS'
                        ? 'text-emerald-400'
                        : 'text-red-400'
                    }`}>
                      {entry.status}
                    </span>
                  </div>
                </div>
                <div className="text-xs text-slate-400">
                  {new Date(entry.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
