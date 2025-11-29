import React, { useState } from 'react';

/**
 * RobotJointsPanel - Displays detailed information about all robot joints
 * Organized by body part with real-time updates
 */
const RobotJointsPanel = ({ joints = [], className = '' }) => {
  const [filter, setFilter] = useState('all'); // all, head, arms, torso, legs
  const [sortBy, setSortBy] = useState('name'); // name, velocity, torque, status

  // Group joints by body part
  const groupJoints = () => {
    const groups = {
      head: joints.filter(j => j.name.includes('neck')),
      arms: joints.filter(j =>
        j.name.includes('shoulder') ||
        j.name.includes('elbow') ||
        j.name.includes('wrist') ||
        j.name.includes('gripper')
      ),
      torso: joints.filter(j => j.name === 'hip'),
      legs: joints.filter(j =>
        j.name.includes('hip') && j.name !== 'hip' ||
        j.name.includes('knee') ||
        j.name.includes('ankle') ||
        j.name.includes('foot')
      ),
    };
    return groups;
  };

  const groups = groupJoints();

  // Get joints to display based on filter
  const getFilteredJoints = () => {
    if (filter === 'all') return joints;
    return groups[filter] || [];
  };

  // Sort joints
  const getSortedJoints = (jointsToSort) => {
    const sorted = [...jointsToSort];
    switch (sortBy) {
      case 'velocity':
        return sorted.sort((a, b) => Math.abs(b.velocity) - Math.abs(a.velocity));
      case 'torque':
        return sorted.sort((a, b) => Math.abs(b.torque) - Math.abs(a.torque));
      case 'status':
        return sorted.sort((a, b) => {
          const statusOrder = { 'ERROR': 0, 'WARNING': 1, 'OK': 2 };
          return statusOrder[a.status] - statusOrder[b.status];
        });
      default: // name
        return sorted.sort((a, b) => a.name.localeCompare(b.name));
    }
  };

  const displayJoints = getSortedJoints(getFilteredJoints());

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case 'OK': return 'bg-green-500/20 text-green-400 border-green-500';
      case 'WARNING': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500';
      case 'ERROR': return 'bg-red-500/20 text-red-400 border-red-500';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500';
    }
  };

  // Get velocity indicator
  const getVelocityIndicator = (velocity) => {
    const absVel = Math.abs(velocity);
    if (absVel < 0.1) return { color: 'text-gray-400', label: 'Idle' };
    if (absVel < 0.3) return { color: 'text-green-400', label: 'Slow' };
    if (absVel < 0.6) return { color: 'text-yellow-400', label: 'Moderate' };
    return { color: 'text-orange-400', label: 'Fast' };
  };

  // Get torque bar width
  const getTorqueWidth = (torque) => {
    const maxTorque = 2.0; // Assume max 2.0 Nm
    return Math.min((Math.abs(torque) / maxTorque) * 100, 100);
  };

  return (
    <div className={`${className}`}>
      {/* Header */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Robot Joints Monitor</h2>
          <p className="text-sm text-gray-400 mt-1">
            Total: {joints.length} joints | Active: {joints.filter(j => Math.abs(j.velocity) > 0.1).length}
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          {['all', 'head', 'arms', 'torso', 'legs'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === f
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== 'all' && ` (${groups[f]?.length || 0})`}
            </button>
          ))}
        </div>
      </div>

      {/* Sort Controls */}
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm text-gray-400">Sort by:</span>
        {['name', 'velocity', 'torque', 'status'].map((sort) => (
          <button
            key={sort}
            onClick={() => setSortBy(sort)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              sortBy === sort
                ? 'bg-slate-600 text-white'
                : 'bg-slate-800 text-gray-400 hover:bg-slate-700'
            }`}
          >
            {sort.charAt(0).toUpperCase() + sort.slice(1)}
          </button>
        ))}
      </div>

      {/* Joints Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-4 text-gray-400 font-medium">Joint Name</th>
              <th className="text-center py-3 px-4 text-gray-400 font-medium">DOF</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">Position</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">Velocity</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium">Torque</th>
              <th className="text-center py-3 px-4 text-gray-400 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {displayJoints.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-8 text-gray-500">
                  No joint data available
                </td>
              </tr>
            ) : (
              displayJoints.map((joint, idx) => {
                const velIndicator = getVelocityIndicator(joint.velocity);
                const torqueWidth = getTorqueWidth(joint.torque);

                return (
                  <tr
                    key={joint.name}
                    className={`border-b border-slate-800 hover:bg-slate-800/50 transition-colors ${
                      idx % 2 === 0 ? 'bg-slate-900/30' : ''
                    }`}
                  >
                    {/* Joint Name */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${
                          Math.abs(joint.velocity) > 0.1 ? 'bg-orange-500 animate-pulse' : 'bg-gray-600'
                        }`}></div>
                        <span className="text-white font-mono">
                          {joint.name.replace('_', ' ')}
                        </span>
                      </div>
                    </td>

                    {/* DOF */}
                    <td className="py-3 px-4 text-center">
                      <span className="inline-block px-2 py-1 bg-slate-700 rounded text-cyan-400 font-mono text-xs">
                        {joint.dof}
                      </span>
                    </td>

                    {/* Position */}
                    <td className="py-3 px-4">
                      <span className="font-mono text-gray-300 text-xs">
                        [{joint.position.map(p => p.toFixed(2)).join(', ')}]
                      </span>
                    </td>

                    {/* Velocity */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono ${velIndicator.color}`}>
                          {joint.velocity.toFixed(3)}
                        </span>
                        <span className="text-xs text-gray-500">{velIndicator.label}</span>
                      </div>
                    </td>

                    {/* Torque */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                            style={{ width: `${torqueWidth}%` }}
                          />
                        </div>
                        <span className="font-mono text-gray-300 text-xs w-12 text-right">
                          {joint.torque.toFixed(2)}
                        </span>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4 text-center">
                      <span className={`inline-block px-2 py-1 rounded border text-xs font-bold ${getStatusColor(joint.status)}`}>
                        {joint.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-gray-400 text-xs mb-1">Total Joints</div>
          <div className="text-2xl font-bold text-white">{joints.length}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-gray-400 text-xs mb-1">Active</div>
          <div className="text-2xl font-bold text-green-400">
            {joints.filter(j => Math.abs(j.velocity) > 0.1).length}
          </div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-gray-400 text-xs mb-1">Avg Torque</div>
          <div className="text-2xl font-bold text-cyan-400">
            {joints.length > 0
              ? (joints.reduce((sum, j) => sum + Math.abs(j.torque), 0) / joints.length).toFixed(2)
              : '0.00'}
          </div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-gray-400 text-xs mb-1">Errors</div>
          <div className={`text-2xl font-bold ${
            joints.filter(j => j.status === 'ERROR').length > 0 ? 'text-red-400' : 'text-green-400'
          }`}>
            {joints.filter(j => j.status === 'ERROR').length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RobotJointsPanel;
