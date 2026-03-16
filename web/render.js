import {
  cycleCount,
  edgeKey,
  estimateTargetDistance,
  getBranchLabel,
  getHeadingLabel,
  getNode,
  getVisibleEdgeKeys,
  latLonToVector,
  slerpVectors,
} from "./maze.js";

function projectGlobe(node, rotation, radius, center) {
  const lat = (node.lat * Math.PI) / 180;
  const lon = ((node.lon + rotation) * Math.PI) / 180;
  const x = radius * Math.cos(lat) * Math.sin(lon);
  const y = radius * Math.sin(lat);
  const z = radius * Math.cos(lat) * Math.cos(lon);
  return {
    x: center.x + x,
    y: center.y - y,
    z,
  };
}

function projectVector(vector, rotation, radius, center) {
  const baseRadius = Math.sqrt(
    vector.x * vector.x + vector.y * vector.y + vector.z * vector.z,
  );
  const safeRadius = baseRadius || 1;
  const normalized = {
    x: vector.x / safeRadius,
    y: vector.y / safeRadius,
    z: vector.z / safeRadius,
  };
  const rotatedX =
    normalized.x * Math.cos((rotation * Math.PI) / 180) -
    normalized.z * Math.sin((rotation * Math.PI) / 180);
  const rotatedZ =
    normalized.x * Math.sin((rotation * Math.PI) / 180) +
    normalized.z * Math.cos((rotation * Math.PI) / 180);
  return {
    x: center.x + rotatedZ * radius,
    y: center.y - normalized.y * radius,
    z: rotatedX * radius,
  };
}

export function renderRadar({ radarCtx, state, maze, radarCanvas }) {
  radarCtx.clearRect(0, 0, radarCanvas.width, radarCanvas.height);
  const center = { x: radarCanvas.width / 2, y: radarCanvas.height / 2 };
  const radius = radarCanvas.width * 0.36;
  const headingRotation = -(getNode(maze, state.toNode).lon + state.lookBias * 24);
  const visibleEdgeKeys = getVisibleEdgeKeys(maze, state);

  const gradient = radarCtx.createRadialGradient(
    center.x,
    center.y,
    radius * 0.2,
    center.x,
    center.y,
    radius,
  );
  gradient.addColorStop(0, "rgba(116, 213, 207, 0.13)");
  gradient.addColorStop(1, "rgba(7, 11, 17, 0.1)");
  radarCtx.fillStyle = gradient;
  radarCtx.beginPath();
  radarCtx.arc(center.x, center.y, radius, 0, Math.PI * 2);
  radarCtx.fill();

  radarCtx.strokeStyle = "rgba(255, 225, 182, 0.18)";
  radarCtx.lineWidth = 1.4;
  radarCtx.beginPath();
  radarCtx.arc(center.x, center.y, radius, 0, Math.PI * 2);
  radarCtx.stroke();

  const projected = new Map();
  maze.nodeList.forEach((node) => {
    projected.set(node.id, projectGlobe(node, headingRotation, radius, center));
  });

  maze.edges.forEach((edge) => {
    const a = projected.get(edge.a);
    const b = projected.get(edge.b);
    const key = edgeKey(edge.a, edge.b);
    const visible = visibleEdgeKeys.has(key);
    radarCtx.strokeStyle = visible
      ? "rgba(116, 213, 207, 0.78)"
      : a.z < 0 && b.z < 0
        ? "rgba(255, 242, 233, 0.08)"
        : "rgba(255, 242, 233, 0.18)";
    radarCtx.lineWidth = visible ? 2.6 : 1.2;
    radarCtx.beginPath();
    radarCtx.moveTo(a.x, a.y);
    radarCtx.lineTo(b.x, b.y);
    radarCtx.stroke();
  });

  const fromNode = getNode(maze, state.fromNode);
  const toNode = getNode(maze, state.toNode);
  const fromVector = latLonToVector(fromNode.lat, fromNode.lon, 1);
  const toVector = latLonToVector(toNode.lat, toNode.lon, 1);
  const playerVector = slerpVectors(fromVector, toVector, state.progress, 1);
  const fromPoint = projected.get(state.fromNode);
  const toPoint = projected.get(state.toNode);
  const playerPoint = projectVector(playerVector, headingRotation, radius, center);

  radarCtx.strokeStyle = "rgba(245, 155, 72, 0.92)";
  radarCtx.lineWidth = 3.2;
  radarCtx.beginPath();
  radarCtx.moveTo(fromPoint.x, fromPoint.y);
  radarCtx.lineTo(playerPoint.x, playerPoint.y);
  radarCtx.stroke();

  radarCtx.strokeStyle = "rgba(116, 213, 207, 0.8)";
  radarCtx.lineWidth = 3;
  radarCtx.beginPath();
  radarCtx.moveTo(playerPoint.x, playerPoint.y);
  radarCtx.lineTo(toPoint.x, toPoint.y);
  radarCtx.stroke();

  maze.nodeList.forEach((node) => {
    const point = projected.get(node.id);
    radarCtx.fillStyle =
      node.id === state.targetNode
        ? "#f26a55"
        : node.id === state.toNode
          ? "#f2f0e7"
        : node.id === state.fromNode
          ? "#74d5cf"
          : point.z < 0
            ? "rgba(255, 242, 233, 0.22)"
            : "rgba(255, 242, 233, 0.56)";
    radarCtx.beginPath();
    radarCtx.arc(point.x, point.y, node.id === state.toNode ? 6 : 4, 0, Math.PI * 2);
    radarCtx.fill();
  });

  radarCtx.fillStyle = "#f59b48";
  radarCtx.strokeStyle = "rgba(255, 244, 228, 0.6)";
  radarCtx.lineWidth = 2;
  radarCtx.beginPath();
  radarCtx.arc(playerPoint.x, playerPoint.y, 8, 0, Math.PI * 2);
  radarCtx.fill();
  radarCtx.stroke();
}

export function updateHud(elements, state, maze) {
  elements.nodesStat.textContent = `${maze.nodeList.length} nodes`;
  elements.loopsStat.textContent = `${cycleCount(maze)} cycles`;
  elements.headingStat.textContent = getHeadingLabel(maze, state.fromNode, state.toNode);
  const distance = estimateTargetDistance(maze, state);
  const nodesLeft = state.reachedTarget ? 0 : distance === null ? null : distance + 1;
  elements.branchStat.textContent = state.reachedTarget
    ? "Beacon secured"
    : distance === null
      ? getBranchLabel(state)
      : `${getBranchLabel(state)} / ${distance} hops to target`;
  elements.nodesLeftStat.textContent =
    nodesLeft === null ? "Unknown" : `${nodesLeft} node${nodesLeft === 1 ? "" : "s"}`;
  elements.targetStat.textContent = state.reachedTarget
    ? "Target reached"
    : `Beacon node ${state.targetNode.toUpperCase()}`;
}
