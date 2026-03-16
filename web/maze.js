const TEMPLATE_NODES = [
  { id: "n0", lat: 35, lon: -120 },
  { id: "n1", lat: 42, lon: -35 },
  { id: "n2", lat: 33, lon: 55 },
  { id: "n3", lat: 8, lon: 128 },
  { id: "n4", lat: -20, lon: 105 },
  { id: "n5", lat: -38, lon: 42 },
  { id: "n6", lat: -46, lon: -28 },
  { id: "n7", lat: -30, lon: -104 },
  { id: "n8", lat: -6, lon: -148 },
  { id: "n9", lat: 12, lon: -78 },
  { id: "n10", lat: 7, lon: -4 },
  { id: "n11", lat: -12, lon: -58 },
  { id: "n12", lat: 28, lon: -156 },
  { id: "n13", lat: 26, lon: 102 },
  { id: "n14", lat: -4, lon: 76 },
  { id: "n15", lat: -26, lon: 152 },
  { id: "n16", lat: -46, lon: -144 },
  { id: "n17", lat: 2, lon: -112 },
];

const TEMPLATE_EDGES = [
  ["n0", "n1"],
  ["n1", "n2"],
  ["n2", "n3"],
  ["n3", "n4"],
  ["n4", "n5"],
  ["n5", "n6"],
  ["n6", "n7"],
  ["n7", "n8"],
  ["n8", "n9"],
  ["n9", "n0"],
  ["n1", "n10"],
  ["n10", "n4"],
  ["n10", "n11"],
  ["n11", "n7"],
  ["n9", "n11"],
  ["n0", "n12"],
  ["n12", "n8"],
  ["n2", "n13"],
  ["n13", "n4"],
  ["n4", "n14"],
  ["n14", "n10"],
  ["n14", "n15"],
  ["n15", "n5"],
  ["n7", "n16"],
  ["n16", "n12"],
  ["n17", "n9"],
  ["n17", "n1"],
  ["n17", "n11"],
];

function createRng(seed) {
  let value = seed % 2147483647;
  if (value <= 0) {
    value += 2147483646;
  }
  return () => {
    value = (value * 16807) % 2147483647;
    return (value - 1) / 2147483646;
  };
}

export function edgeKey(a, b) {
  return [a, b].sort().join(":");
}

export function cycleCount(maze) {
  return maze.edges.length - maze.nodeList.length + 1;
}

export function latLonToVector(lat, lon, radius = 1) {
  const latRad = (lat * Math.PI) / 180;
  const lonRad = (lon * Math.PI) / 180;
  return {
    x: radius * Math.cos(latRad) * Math.cos(lonRad),
    y: radius * Math.sin(latRad),
    z: radius * Math.cos(latRad) * Math.sin(lonRad),
  };
}

export function slerpVectors(a, b, t, radius = 1) {
  const dotProduct = Math.max(-1, Math.min(1, a.x * b.x + a.y * b.y + a.z * b.z));
  const omega = Math.acos(dotProduct);
  if (omega < 1e-6) {
    return {
      x: a.x * radius,
      y: a.y * radius,
      z: a.z * radius,
    };
  }

  const sinOmega = Math.sin(omega);
  const factorA = Math.sin((1 - t) * omega) / sinOmega;
  const factorB = Math.sin(t * omega) / sinOmega;
  return {
    x: (a.x * factorA + b.x * factorB) * radius,
    y: (a.y * factorA + b.y * factorB) * radius,
    z: (a.z * factorA + b.z * factorB) * radius,
  };
}

export function createMaze(seed = 1) {
  const random = createRng(seed);
  const nodes = new Map();
  const adjacency = new Map();

  TEMPLATE_NODES.forEach((node, index) => {
    const jitterLat = (random() - 0.5) * 6;
    const jitterLon = (random() - 0.5) * 10;
    const metadata = {
      ...node,
      lat: node.lat + jitterLat,
      lon: node.lon + jitterLon + index * 0.15,
    };
    nodes.set(node.id, metadata);
    adjacency.set(node.id, []);
  });

  const edges = TEMPLATE_EDGES.map(([a, b]) => {
    const id = edgeKey(a, b);
    adjacency.get(a).push(b);
    adjacency.get(b).push(a);
    return { id, a, b };
  });

  return {
    seed,
    nodes,
    edges,
    adjacency,
    nodeList: [...nodes.values()],
  };
}

export function getNode(maze, id) {
  return maze.nodes.get(id);
}

export function getNeighbors(maze, id) {
  return maze.adjacency.get(id) ?? [];
}

export function bearingBetween(maze, fromId, toId) {
  const from = getNode(maze, fromId);
  const to = getNode(maze, toId);
  const lat1 = (from.lat * Math.PI) / 180;
  const lat2 = (to.lat * Math.PI) / 180;
  const dLon = ((to.lon - from.lon) * Math.PI) / 180;
  const x = Math.sin(dLon) * Math.cos(lat2);
  const y =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return Math.atan2(x, y);
}

export function normalizeAngle(angle) {
  let value = angle;
  while (value > Math.PI) {
    value -= Math.PI * 2;
  }
  while (value < -Math.PI) {
    value += Math.PI * 2;
  }
  return value;
}

export function relativeTurn(maze, fromId, atId, candidateId) {
  const incoming = bearingBetween(maze, fromId, atId);
  const outgoing = bearingBetween(maze, atId, candidateId);
  return normalizeAngle(outgoing - incoming);
}

export function pickBranch(maze, fromId, atId, branchBias) {
  const candidates = getNeighbors(maze, atId).filter((candidate) => candidate !== fromId);
  if (!candidates.length) {
    return fromId;
  }
  if (candidates.length === 1) {
    return candidates[0];
  }

  const targetTurn = branchBias * (Math.PI / 2.4);
  return candidates.reduce((bestId, candidateId) => {
    const candidateTurn = relativeTurn(maze, fromId, atId, candidateId);
    const bestTurn = relativeTurn(maze, fromId, atId, bestId);
    const candidateScore = Math.abs(candidateTurn - targetTurn);
    const bestScore = Math.abs(bestTurn - targetTurn);
    return candidateScore < bestScore ? candidateId : bestId;
  }, candidates[0]);
}

export function classifyVisibleBranches(maze, fromId, atId) {
  return getNeighbors(maze, atId)
    .filter((candidate) => candidate !== fromId)
    .map((candidateId) => {
      const turn = relativeTurn(maze, fromId, atId, candidateId);
      const direction =
        Math.abs(turn) < 0.38 ? "forward" : turn < 0 ? "left" : "right";
      return { candidateId, turn, direction };
    });
}

export function createInitialState(maze) {
  return {
    fromNode: "n1",
    toNode: "n10",
    progress: 0.08,
    branchBias: 0,
    lookBias: 0,
    visibleHops: 2,
    radarVisible: true,
    steps: 0,
    pulse: 0,
    targetNode: "n15",
    reachedTarget: false,
    maze,
  };
}

export function advanceState(state, movement, deltaTime) {
  if (state.reachedTarget) {
    return;
  }
  const speed = 0.42;
  const step = movement * speed * deltaTime;
  if (Math.abs(step) < 1e-5) {
    return;
  }

  state.progress += step;

  while (state.progress >= 1) {
    const nextNode = pickBranch(state.maze, state.fromNode, state.toNode, state.branchBias);
    state.fromNode = state.toNode;
    state.toNode = nextNode;
    state.progress -= 1;
    state.steps += 1;
    if (state.toNode === state.targetNode) {
      state.reachedTarget = true;
      state.progress = 1;
      break;
    }
  }

  while (state.progress <= 0) {
    const previousNode = state.fromNode;
    state.fromNode = state.toNode;
    state.toNode = previousNode;
    state.progress = 1 + state.progress;
    state.steps += 1;
  }

  state.pulse += Math.abs(step) * 4.2;
}

export function getPlayerNodeAhead(state) {
  return state.toNode;
}

export function getHeadingLabel(maze, fromId, toId) {
  const bearing = bearingBetween(maze, fromId, toId);
  const degrees = ((bearing * 180) / Math.PI + 360) % 360;
  if (degrees > 315 || degrees <= 45) {
    return "Orbital North";
  }
  if (degrees <= 135) {
    return "Orbital East";
  }
  if (degrees <= 225) {
    return "Orbital South";
  }
  return "Orbital West";
}

export function getBranchLabel(state) {
  if (state.reachedTarget) {
    return "Target reached";
  }
  if (state.branchBias < -0.4) {
    return "Left arc";
  }
  if (state.branchBias > 0.4) {
    return "Right arc";
  }
  return "Forward arc";
}

export function getVisibleEdgeKeys(maze, state) {
  const visited = new Set([edgeKey(state.fromNode, state.toNode)]);
  let frontier = [{ from: state.fromNode, at: state.toNode }];

  for (let hop = 0; hop < state.visibleHops; hop += 1) {
    const nextFrontier = [];
    frontier.forEach(({ from, at }) => {
      getNeighbors(maze, at)
        .filter((candidate) => candidate !== from)
        .forEach((candidate) => {
          const key = edgeKey(at, candidate);
          if (!visited.has(key)) {
            visited.add(key);
            nextFrontier.push({ from: at, at: candidate });
          }
        });
    });
    frontier = nextFrontier;
  }

  return visited;
}

export function estimateTargetDistance(maze, state) {
  const visited = new Set([state.toNode]);
  let frontier = [state.toNode];
  let depth = 0;

  while (frontier.length) {
    if (frontier.includes(state.targetNode)) {
      return depth;
    }
    const next = [];
    frontier.forEach((nodeId) => {
      getNeighbors(maze, nodeId).forEach((neighborId) => {
        if (!visited.has(neighborId)) {
          visited.add(neighborId);
          next.push(neighborId);
        }
      });
    });
    frontier = next;
    depth += 1;
  }

  return null;
}
