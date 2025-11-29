import React, { useEffect, useRef, useState } from 'react';

/**
 * HumanoidRobotVisual - 2D visualization of humanoid robot with real-time joint updates
 * Shows all 18 joints with position, velocity, and status
 * Supports 4 modes: sitting, standing, walking, running
 */
const HumanoidRobotVisual = ({ joints = [], mode = 'standing', className = '' }) => {
  const canvasRef = useRef(null);
  const [selectedJoint, setSelectedJoint] = useState(null);
  const [showLabels, setShowLabels] = useState(false); // Labels hidden by default

  // Joint positions on canvas (x, y) - base pose template
  const jointPositions = {
    // HEAD
    'neck': { x: 200, y: 80, radius: 8, color: '#60a5fa' },

    // ARMS
    'left_shoulder': { x: 170, y: 110, radius: 7, color: '#34d399' },
    'right_shoulder': { x: 230, y: 110, radius: 7, color: '#34d399' },
    'left_elbow': { x: 150, y: 160, radius: 6, color: '#34d399' },
    'right_elbow': { x: 250, y: 160, radius: 6, color: '#34d399' },
    'left_wrist': { x: 140, y: 200, radius: 5, color: '#34d399' },
    'right_wrist': { x: 260, y: 200, radius: 5, color: '#34d399' },
    'left_gripper': { x: 135, y: 220, radius: 4, color: '#34d399' },
    'right_gripper': { x: 265, y: 220, radius: 4, color: '#34d399' },

    // TORSO
    'hip': { x: 200, y: 180, radius: 9, color: '#f59e0b' },

    // LEGS
    'left_hip': { x: 185, y: 220, radius: 7, color: '#8b5cf6' },
    'right_hip': { x: 215, y: 220, radius: 7, color: '#8b5cf6' },
    'left_knee': { x: 180, y: 290, radius: 6, color: '#8b5cf6' },
    'right_knee': { x: 220, y: 290, radius: 6, color: '#8b5cf6' },
    'left_ankle': { x: 175, y: 350, radius: 5, color: '#8b5cf6' },
    'right_ankle': { x: 225, y: 350, radius: 5, color: '#8b5cf6' },
    'left_foot': { x: 170, y: 380, radius: 5, color: '#8b5cf6' },
    'right_foot': { x: 230, y: 380, radius: 5, color: '#8b5cf6' },
  };

  // Mode-specific pose adjustments
  const getModeAdjustments = (mode) => {
    const adjustments = {
      sitting: {
        'hip': { y: 40 },
        'left_hip': { y: 50 },
        'right_hip': { y: 50 },
        'left_knee': { y: -20 },
        'right_knee': { y: -20 },
        'left_ankle': { y: -50 },
        'right_ankle': { y: -50 },
        'left_foot': { y: -50 },
        'right_foot': { y: -50 },
        'left_shoulder': { y: 10 },
        'right_shoulder': { y: 10 },
      },
      standing: {},
      walking: {
        'left_shoulder': { x: -5, y: -5 },
        'right_shoulder': { x: 5, y: -5 },
        'left_hip': { x: -3 },
        'right_hip': { x: 3 },
      },
      running: {
        'left_shoulder': { x: -10, y: -10 },
        'right_shoulder': { x: 10, y: -10 },
        'left_elbow': { x: -15, y: -10 },
        'right_elbow': { x: 15, y: -10 },
        'left_hip': { x: -5 },
        'right_hip': { x: 5 },
        'neck': { y: -5 },
      }
    };
    return adjustments[mode] || {};
  };

  // Apply mode adjustments to joint positions
  const getAdjustedPosition = (jointName) => {
    const basePos = jointPositions[jointName];
    if (!basePos) return null;

    const modeAdj = getModeAdjustments(mode)[jointName] || {};
    return {
      x: (basePos.x || 0) + (modeAdj.x || 0),
      y: (basePos.y || 0) + (modeAdj.y || 0),
      radius: basePos.radius,
      color: basePos.color,
    };
  };

  // Get joint status color
  const getJointStatusColor = (joint) => {
    if (!joint) return '#6b7280'; // gray for missing
    if (joint.status === 'ERROR') return '#ef4444'; // red
    if (joint.velocity && Math.abs(joint.velocity) > 0.5) return '#f59e0b'; // orange for high velocity
    return '#10b981'; // green for OK
  };

  // Draw the robot
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw skeleton connections (limbs)
    ctx.strokeStyle = '#4b5563';
    ctx.lineWidth = 3;
    const connections = [
      // Spine
      ['neck', 'hip'],
      // Left arm
      ['neck', 'left_shoulder'],
      ['left_shoulder', 'left_elbow'],
      ['left_elbow', 'left_wrist'],
      ['left_wrist', 'left_gripper'],
      // Right arm
      ['neck', 'right_shoulder'],
      ['right_shoulder', 'right_elbow'],
      ['right_elbow', 'right_wrist'],
      ['right_wrist', 'right_gripper'],
      // Left leg
      ['hip', 'left_hip'],
      ['left_hip', 'left_knee'],
      ['left_knee', 'left_ankle'],
      ['left_ankle', 'left_foot'],
      // Right leg
      ['hip', 'right_hip'],
      ['right_hip', 'right_knee'],
      ['right_knee', 'right_ankle'],
      ['right_ankle', 'right_foot'],
    ];

    connections.forEach(([start, end]) => {
      const startPos = getAdjustedPosition(start);
      const endPos = getAdjustedPosition(end);
      if (startPos && endPos) {
        ctx.beginPath();
        ctx.moveTo(startPos.x, startPos.y);
        ctx.lineTo(endPos.x, endPos.y);
        ctx.stroke();
      }
    });

    // Draw joints
    Object.keys(jointPositions).forEach((jointName) => {
      const pos = getAdjustedPosition(jointName);
      if (!pos) return;

      const jointData = joints.find(j => j.name === jointName);
      const statusColor = getJointStatusColor(jointData);

      // Joint circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pos.radius, 0, 2 * Math.PI);
      ctx.fillStyle = statusColor;
      ctx.fill();
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Velocity indicator (motion blur effect)
      if (jointData && jointData.velocity && Math.abs(jointData.velocity) > 0.1) {
        ctx.strokeStyle = `rgba(245, 158, 11, ${Math.min(Math.abs(jointData.velocity), 1)})`;
        ctx.lineWidth = 3;
        ctx.beginPath();
        const velocityLength = jointData.velocity * 20;
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(pos.x + velocityLength, pos.y - velocityLength / 2);
        ctx.stroke();
      }

      // Labels
      if (showLabels) {
        ctx.fillStyle = '#e5e7eb';
        ctx.font = '10px monospace';
        ctx.fillText(jointName.replace('_', ' '), pos.x + 12, pos.y + 4);
      }

      // Selection highlight
      if (selectedJoint === jointName) {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, pos.radius + 4, 0, 2 * Math.PI);
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });

    // Mode indicator
    ctx.fillStyle = '#e5e7eb';
    ctx.font = 'bold 16px sans-serif';
    ctx.fillText(`Mode: ${mode.toUpperCase()}`, 10, 30);

    // Joint count
    ctx.font = '12px sans-serif';
    ctx.fillText(`Joints: ${joints.length}/18`, 10, 50);

  }, [joints, mode, selectedJoint, showLabels]);

  // Handle canvas click for joint selection
  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find clicked joint
    let clickedJoint = null;
    Object.keys(jointPositions).forEach((jointName) => {
      const pos = getAdjustedPosition(jointName);
      if (!pos) return;

      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance <= pos.radius + 5) {
        clickedJoint = jointName;
      }
    });

    setSelectedJoint(clickedJoint);
  };

  // Get selected joint data
  const selectedJointData = selectedJoint ? joints.find(j => j.name === selectedJoint) : null;

  return (
    <div className={`relative ${className}`}>
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={400}
        height={420}
        className="bg-slate-900 rounded-lg cursor-pointer border-2 border-slate-700"
        onClick={handleCanvasClick}
      />

      {/* Controls */}
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => setShowLabels(!showLabels)}
          className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm"
        >
          {showLabels ? 'Hide Labels' : 'Show Labels'}
        </button>
        {selectedJoint && (
          <button
            onClick={() => setSelectedJoint(null)}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm"
          >
            Clear Selection
          </button>
        )}
      </div>

      {/* Joint Details Panel */}
      {selectedJointData && (
        <div className="mt-4 p-4 bg-slate-800 rounded-lg border border-slate-700">
          <h3 className="text-lg font-bold text-cyan-400 mb-2">
            {selectedJoint.replace('_', ' ').toUpperCase()}
          </h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-400">DOF:</span>
              <span className="ml-2 text-white font-mono">{selectedJointData.dof}</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>
              <span className={`ml-2 font-bold ${
                selectedJointData.status === 'OK' ? 'text-green-400' :
                selectedJointData.status === 'ERROR' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {selectedJointData.status}
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-gray-400">Position:</span>
              <span className="ml-2 text-white font-mono">
                [{selectedJointData.position.map(p => p.toFixed(2)).join(', ')}]
              </span>
            </div>
            <div>
              <span className="text-gray-400">Velocity:</span>
              <span className="ml-2 text-white font-mono">
                {selectedJointData.velocity.toFixed(3)} rad/s
              </span>
            </div>
            <div>
              <span className="text-gray-400">Torque:</span>
              <span className="ml-2 text-white font-mono">
                {selectedJointData.torque.toFixed(3)} Nm
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 p-3 bg-slate-800 rounded-lg border border-slate-700">
        <div className="text-xs font-bold text-gray-400 mb-2">LEGEND</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-300">OK</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-gray-300">Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-300">Error</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-500"></div>
            <span className="text-gray-300">Missing</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HumanoidRobotVisual;
