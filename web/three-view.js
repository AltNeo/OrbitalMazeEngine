import * as THREE from "three";

import {
  edgeKey,
  getNeighbors,
  getNode,
  getVisibleEdgeKeys,
  latLonToVector,
  pickBranch,
  slerpVectors,
} from "./maze.js";

const VIEW_CONFIG = {
  corridorRadius: 28,
  shellRadius: 38,
  corridorWidth: 2.8,
  wallHeight: 2.4,
  cameraHeight: 1.35,
  samplesPerEdge: 18,
  junctionRadius: 3.1,
};

function asVector3(vector) {
  return new THREE.Vector3(vector.x, vector.y, vector.z);
}

function projectTangent(vector, normal) {
  return vector.clone().sub(normal.clone().multiplyScalar(vector.dot(normal))).normalize();
}

function segmentLength(a, b) {
  return a.distanceTo(b);
}

function getWallTrim(degree) {
  return degree > 1 ? VIEW_CONFIG.junctionRadius : VIEW_CONFIG.corridorWidth * 0.65;
}

function getFloorTrim(degree) {
  return degree > 1 ? VIEW_CONFIG.corridorWidth * 0.22 : VIEW_CONFIG.corridorWidth * 0.42;
}

function getJunctionChamberRadius(degree) {
  return VIEW_CONFIG.junctionRadius * (degree >= 3 ? 1.06 : 0.94);
}

function buildTangentBasis(normal) {
  const reference =
    Math.abs(normal.y) < 0.94 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
  const tangentX = projectTangent(reference, normal);
  const tangentY = normal.clone().cross(tangentX).normalize();
  return { tangentX, tangentY };
}

function angleFromDirection(direction, basis) {
  return Math.atan2(direction.dot(basis.tangentY), direction.dot(basis.tangentX));
}

function pointOnJunctionArc(center, normal, basis, radius, angle, inset = 0) {
  const radial = basis.tangentX
    .clone()
    .multiplyScalar(Math.cos(angle))
    .add(basis.tangentY.clone().multiplyScalar(Math.sin(angle)))
    .normalize();
  return center
    .clone()
    .add(radial.multiplyScalar(radius))
    .add(normal.clone().multiplyScalar(inset));
}

function addJunctionWallArc(group, center, normal, basis, radius, startAngle, endAngle, material) {
  const span = endAngle - startAngle;
  if (span <= 0.08) {
    return;
  }

  const segments = Math.max(2, Math.ceil(span / 0.24));
  for (let index = 0; index < segments; index += 1) {
    const angleA = startAngle + (span * index) / segments;
    const angleB = startAngle + (span * (index + 1)) / segments;
    const floorA = pointOnJunctionArc(center, normal, basis, radius, angleA, -0.02);
    const floorB = pointOnJunctionArc(center, normal, basis, radius, angleB, -0.02);
    const topA = floorA.clone().add(normal.clone().multiplyScalar(-VIEW_CONFIG.wallHeight));
    const topB = floorB.clone().add(normal.clone().multiplyScalar(-VIEW_CONFIG.wallHeight));
    group.add(new THREE.Mesh(createQuadGeometry(floorA, floorB, topB, topA), material));
  }
}

function createQuadGeometry(a, b, c, d) {
  const geometry = new THREE.BufferGeometry();
  const vertices = new Float32Array([
    a.x, a.y, a.z,
    b.x, b.y, b.z,
    c.x, c.y, c.z,
    a.x, a.y, a.z,
    c.x, c.y, c.z,
    d.x, d.y, d.z,
  ]);
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function buildEdgeSamples(maze, edge, radius) {
  const fromNode = getNode(maze, edge.a);
  const toNode = getNode(maze, edge.b);
  const fromUnit = asVector3(latLonToVector(fromNode.lat, fromNode.lon, 1));
  const toUnit = asVector3(latLonToVector(toNode.lat, toNode.lon, 1));
  const samples = [];

  for (let index = 0; index <= VIEW_CONFIG.samplesPerEdge; index += 1) {
    const fraction = index / VIEW_CONFIG.samplesPerEdge;
    samples.push(asVector3(slerpVectors(fromUnit, toUnit, fraction, radius)));
  }

  return samples;
}

function trimPolyline(samples, startTrim, endTrim) {
  const totalLength = samples.slice(1).reduce((sum, sample, index) => {
    return sum + segmentLength(samples[index], sample);
  }, 0);
  const trimmedStart = Math.min(startTrim, Math.max(0, totalLength - 0.25));
  const trimmedEnd = Math.min(endTrim, Math.max(0, totalLength - trimmedStart - 0.25));
  const startTarget = trimmedStart;
  const endTarget = totalLength - trimmedEnd;
  let traversed = 0;
  let startPoint = samples[0].clone();
  let endPoint = samples[samples.length - 1].clone();
  const points = [];

  for (let index = 1; index < samples.length; index += 1) {
    const pointA = samples[index - 1];
    const pointB = samples[index];
    const length = segmentLength(pointA, pointB);
    const segmentStart = traversed;
    const segmentEnd = traversed + length;

    if (segmentStart <= startTarget && segmentEnd >= startTarget) {
      const t = (startTarget - segmentStart) / length;
      startPoint = pointA.clone().lerp(pointB, t);
    }

    if (segmentStart <= endTarget && segmentEnd >= endTarget) {
      const t = (endTarget - segmentStart) / length;
      endPoint = pointA.clone().lerp(pointB, t);
    }

    traversed = segmentEnd;
  }

  points.push(startPoint);
  traversed = 0;
  for (let index = 1; index < samples.length; index += 1) {
    const pointA = samples[index - 1];
    const pointB = samples[index];
    const length = segmentLength(pointA, pointB);
    const segmentStart = traversed;
    const segmentEnd = traversed + length;

    if (segmentEnd > startTarget && segmentStart < endTarget) {
      if (segmentStart >= startTarget && segmentEnd <= endTarget) {
        points.push(pointB.clone());
      }
    }
    traversed = segmentEnd;
  }

  if (!points[points.length - 1]?.equals(endPoint)) {
    points.push(endPoint);
  }

  return points.filter((point, index, array) => {
    return index === 0 || point.distanceTo(array[index - 1]) > 0.001;
  });
}

function createPortalLintel(leftFloor, rightFloor, leftTop, rightTop, material) {
  const group = new THREE.Group();
  const columnHeight = 0.72;
  const columnWidth = 0.22;
  const leftDirection = leftTop.clone().sub(leftFloor).normalize();
  const rightDirection = rightTop.clone().sub(rightFloor).normalize();
  const horizontal = rightTop.clone().sub(leftTop).normalize();

  const topBandLeftBottom = leftTop.clone().add(leftDirection.clone().multiplyScalar(-0.24));
  const topBandRightBottom = rightTop.clone().add(rightDirection.clone().multiplyScalar(-0.24));
  group.add(
    new THREE.Mesh(
      createQuadGeometry(leftTop, rightTop, topBandRightBottom, topBandLeftBottom),
      material,
    ),
  );

  const leftInnerFloor = leftFloor.clone().add(horizontal.clone().multiplyScalar(columnWidth));
  const leftInnerTop = leftInnerFloor.clone().add(leftDirection.clone().multiplyScalar(columnHeight));
  group.add(
    new THREE.Mesh(
      createQuadGeometry(leftFloor, leftInnerFloor, leftInnerTop, leftTop),
      material,
    ),
  );

  const rightInnerFloor = rightFloor.clone().add(horizontal.clone().multiplyScalar(-columnWidth));
  const rightInnerTop = rightInnerFloor.clone().add(rightDirection.clone().multiplyScalar(columnHeight));
  group.add(
    new THREE.Mesh(
      createQuadGeometry(rightInnerFloor, rightFloor, rightTop, rightInnerTop),
      material,
    ),
  );

  return group;
}

function createEdgeGroup(maze, edge, materials) {
  const group = new THREE.Group();
  const samples = buildEdgeSamples(maze, edge, VIEW_CONFIG.corridorRadius);
  const startDegree = getNeighbors(maze, edge.a).length;
  const endDegree = getNeighbors(maze, edge.b).length;
  const allowPortals = startDegree <= 1 && endDegree <= 1;
  const wallSamples = trimPolyline(
    samples,
    getWallTrim(startDegree),
    getWallTrim(endDegree),
  );
  const floorSamples = trimPolyline(
    samples,
    getFloorTrim(startDegree),
    getFloorTrim(endDegree),
  );

  if (wallSamples.length < 2 && floorSamples.length < 2) {
    return group;
  }

  for (let index = 0; index < floorSamples.length - 1; index += 1) {
    const pointA = floorSamples[index];
    const pointB = floorSamples[index + 1];
    const normalA = pointA.clone().normalize();
    const normalB = pointB.clone().normalize();
    const delta = pointB.clone().sub(pointA);
    const tangentA = projectTangent(delta, normalA);
    const tangentB = projectTangent(delta, normalB);
    const rightA = tangentA.clone().cross(normalA).normalize();
    const rightB = tangentB.clone().cross(normalB).normalize();
    const halfWidth = VIEW_CONFIG.corridorWidth / 2;

    const leftA = pointA.clone().add(rightA.clone().multiplyScalar(halfWidth));
    const rightAEdge = pointA.clone().add(rightA.clone().multiplyScalar(-halfWidth));
    const leftB = pointB.clone().add(rightB.clone().multiplyScalar(halfWidth));
    const rightBEdge = pointB.clone().add(rightB.clone().multiplyScalar(-halfWidth));

    group.add(
      new THREE.Mesh(
        createQuadGeometry(leftA, rightAEdge, rightBEdge, leftB),
        materials.floor,
      ),
    );
  }

  for (let index = 0; index < wallSamples.length - 1; index += 1) {
    const pointA = wallSamples[index];
    const pointB = wallSamples[index + 1];
    const normalA = pointA.clone().normalize();
    const normalB = pointB.clone().normalize();
    const delta = pointB.clone().sub(pointA);
    const tangentA = projectTangent(delta, normalA);
    const tangentB = projectTangent(delta, normalB);
    const rightA = tangentA.clone().cross(normalA).normalize();
    const rightB = tangentB.clone().cross(normalB).normalize();
    const halfWidth = VIEW_CONFIG.corridorWidth / 2;

    const leftA = pointA.clone().add(rightA.clone().multiplyScalar(halfWidth));
    const rightAEdge = pointA.clone().add(rightA.clone().multiplyScalar(-halfWidth));
    const leftB = pointB.clone().add(rightB.clone().multiplyScalar(halfWidth));
    const rightBEdge = pointB.clone().add(rightB.clone().multiplyScalar(-halfWidth));

    const liftA = normalA.clone().multiplyScalar(-VIEW_CONFIG.wallHeight);
    const liftB = normalB.clone().multiplyScalar(-VIEW_CONFIG.wallHeight);
    const leftTopA = leftA.clone().add(liftA);
    const rightTopA = rightAEdge.clone().add(liftA);
    const leftTopB = leftB.clone().add(liftB);
    const rightTopB = rightBEdge.clone().add(liftB);

    group.add(
      new THREE.Mesh(
        createQuadGeometry(leftA, leftB, leftTopB, leftTopA),
        materials.wall,
      ),
    );
    group.add(
      new THREE.Mesh(
        createQuadGeometry(rightBEdge, rightAEdge, rightTopA, rightTopB),
        materials.wall,
      ),
    );

    const shouldAddPortal =
      allowPortals &&
      index > 1 &&
      index < wallSamples.length - 3 &&
      index % 5 === 0;
    if (shouldAddPortal) {
      group.add(createPortalLintel(leftA, rightAEdge, leftTopA, rightTopA, materials.portal));
    }
  }

  return group;
}

function createJunctionGroup(maze, node, materials) {
  const group = new THREE.Group();
  const neighbors = getNeighbors(maze, node.id);
  const degree = neighbors.length;
  const radius = getJunctionChamberRadius(degree);
  const basePoint = asVector3(latLonToVector(node.lat, node.lon, VIEW_CONFIG.corridorRadius));
  const normal = basePoint.clone().normalize();
  const planePosition = basePoint.clone().add(normal.clone().multiplyScalar(-0.16));
  const basis = buildTangentBasis(normal);
  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(radius * 0.92, 40),
    materials.junctionFloor,
  );
  floor.position.copy(planePosition);
  floor.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
  group.add(floor);

  const coreRing = new THREE.Mesh(
    new THREE.RingGeometry(radius * 0.22, radius * 0.34, 32),
    materials.junctionRing,
  );
  coreRing.position.copy(planePosition.clone().add(normal.clone().multiplyScalar(-0.02)));
  coreRing.quaternion.copy(floor.quaternion);
  group.add(coreRing);

  const exits = neighbors
    .map((neighborId) => {
      const neighbor = getNode(maze, neighborId);
      const neighborPoint = asVector3(
        latLonToVector(neighbor.lat, neighbor.lon, VIEW_CONFIG.corridorRadius),
      );
      const direction = projectTangent(neighborPoint.clone().sub(basePoint), normal);
      return {
        neighborId,
        angle: angleFromDirection(direction, basis),
      };
    })
    .sort((left, right) => left.angle - right.angle);

  const halfOpening = Math.min(0.42, (VIEW_CONFIG.corridorWidth * 0.64) / radius);
  for (let index = 0; index < exits.length; index += 1) {
    const currentExit = exits[index];
    const nextExit = exits[(index + 1) % exits.length];
    const startAngle = currentExit.angle + halfOpening;
    const endAngle =
      index === exits.length - 1
        ? nextExit.angle + Math.PI * 2 - halfOpening
        : nextExit.angle - halfOpening;
    addJunctionWallArc(group, planePosition, normal, basis, radius, startAngle, endAngle, materials.wall);
  }

  return group;
}

function createGuideShell() {
  const shellGroup = new THREE.Group();
  const lineMaterial = new THREE.LineBasicMaterial({
    color: "#2c4458",
    transparent: true,
    opacity: 0.28,
  });

  for (let latitude = -50; latitude <= 50; latitude += 25) {
    const points = [];
    for (let step = 0; step <= 64; step += 1) {
      const longitude = -180 + (360 * step) / 64;
      points.push(asVector3(latLonToVector(latitude, longitude, VIEW_CONFIG.shellRadius)));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    shellGroup.add(new THREE.Line(geometry, lineMaterial));
  }

  for (let longitude = -150; longitude <= 150; longitude += 30) {
    const points = [];
    for (let step = 0; step <= 64; step += 1) {
      const latitude = -75 + (150 * step) / 64;
      points.push(asVector3(latLonToVector(latitude, longitude, VIEW_CONFIG.shellRadius)));
    }
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    shellGroup.add(new THREE.Line(geometry, lineMaterial));
  }

  return shellGroup;
}

function createStarField() {
  const geometry = new THREE.BufferGeometry();
  const stars = [];

  for (let index = 0; index < 1000; index += 1) {
    const radius = 180 + Math.random() * 120;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    stars.push(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta),
    );
  }

  geometry.setAttribute("position", new THREE.Float32BufferAttribute(stars, 3));
  return new THREE.Points(
    geometry,
    new THREE.PointsMaterial({
      color: "#d9e5ef",
      size: 0.8,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.7,
    }),
  );
}

export class ThreeMazeView {
  constructor(canvas, overlayElement) {
    this.canvas = canvas;
    this.overlayElement = overlayElement;
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#081018");
    this.scene.fog = new THREE.Fog("#081018", 18, 76);

    this.camera = new THREE.PerspectiveCamera(68, 16 / 9, 0.1, 320);
    this.camera.position.set(0, 0, 10);

    this.edgeGroups = new Map();
    this.junctionGroups = new Map();
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.scene.add(createGuideShell());
    this.scene.add(createStarField());

    this.materials = {
      floor: new THREE.MeshStandardMaterial({
        color: "#51687f",
        roughness: 0.94,
        metalness: 0.06,
        side: THREE.DoubleSide,
      }),
      wall: new THREE.MeshStandardMaterial({
        color: "#8ea2b0",
        roughness: 0.84,
        metalness: 0.12,
        side: THREE.DoubleSide,
      }),
      portal: new THREE.MeshStandardMaterial({
        color: "#9f6425",
        emissive: "#5f2c0a",
        emissiveIntensity: 0.12,
        roughness: 0.52,
        metalness: 0.28,
        side: THREE.DoubleSide,
      }),
      junctionFloor: new THREE.MeshStandardMaterial({
        color: "#4f6679",
        roughness: 0.9,
        metalness: 0.06,
        side: THREE.DoubleSide,
      }),
      junctionRing: new THREE.MeshStandardMaterial({
        color: "#7dd7cf",
        emissive: "#184448",
        emissiveIntensity: 0.2,
        roughness: 0.34,
        metalness: 0.18,
        side: THREE.DoubleSide,
      }),
    };

    const ambient = new THREE.AmbientLight("#8fb2c9", 0.9);
    const key = new THREE.DirectionalLight("#f7c58c", 1.1);
    key.position.set(40, 50, 20);
    const fill = new THREE.PointLight("#74d5cf", 18, 120, 2);
    fill.position.set(0, 0, 0);
    this.scene.add(ambient, key, fill);

    this.beacon = null;
    this.beaconLight = null;
    this.currentMazeSeed = null;
    this.resize();
    window.addEventListener("resize", () => this.resize());
  }

  resize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  clearMaze() {
    while (this.root.children.length) {
      const child = this.root.children[this.root.children.length - 1];
      this.root.remove(child);
      child.traverse?.((node) => {
        if (node.geometry) {
          node.geometry.dispose();
        }
        if (node.material) {
          if (Array.isArray(node.material)) {
            node.material.forEach((material) => material.dispose());
          } else {
            node.material.dispose();
          }
        }
      });
    }
    this.edgeGroups.clear();
    this.junctionGroups.clear();
    this.beacon = null;
    this.beaconLight = null;
  }

  buildMaze(maze, state) {
    this.clearMaze();
    this.currentMazeSeed = maze.seed;

    maze.edges.forEach((edge) => {
      const group = createEdgeGroup(maze, edge, this.materials);
      this.edgeGroups.set(edge.id, group);
      this.root.add(group);
    });

    maze.nodeList.forEach((node) => {
      if (getNeighbors(maze, node.id).length > 1) {
        const junction = createJunctionGroup(maze, node, this.materials);
        this.junctionGroups.set(node.id, junction);
        this.root.add(junction);
      }
    });

    const targetNode = getNode(maze, state.targetNode);
    const targetPoint = asVector3(
      latLonToVector(targetNode.lat, targetNode.lon, VIEW_CONFIG.corridorRadius - 0.35),
    );
    this.beacon = new THREE.Mesh(
      new THREE.SphereGeometry(0.42, 20, 20),
      new THREE.MeshStandardMaterial({
        color: "#f26a55",
        emissive: "#7f130f",
        emissiveIntensity: 1.1,
        roughness: 0.28,
        metalness: 0.12,
      }),
    );
    this.beacon.position.copy(targetPoint);
    this.beaconLight = new THREE.PointLight("#f26a55", 8, 20, 2);
    this.beaconLight.position.copy(targetPoint);
    this.root.add(this.beacon, this.beaconLight);
  }

  updateVisibility(maze, state) {
    const visibleEdgeKeys = getVisibleEdgeKeys(maze, state);
    const visibleNodes = new Set([state.fromNode, state.toNode, state.targetNode]);
    const currentKey = edgeKey(state.fromNode, state.toNode);
    const previewThreshold = 0.58;
    const revealAllThreshold = 0.86;
    const previewNode =
      state.progress > previewThreshold
        ? pickBranch(maze, state.fromNode, state.toNode, state.branchBias)
        : null;
    const previewKey =
      previewNode && previewNode !== state.fromNode
        ? edgeKey(state.toNode, previewNode)
        : currentKey;

    maze.edges.forEach((edge) => {
      let visible = visibleEdgeKeys.has(edge.id);
      const touchesCurrentJunction = edge.a === state.toNode || edge.b === state.toNode;
      if (visible && touchesCurrentJunction) {
        if (state.progress > revealAllThreshold) {
          visible = true;
        } else if (state.progress > previewThreshold) {
          visible = edge.id === currentKey || edge.id === previewKey;
        }
      }
      const group = this.edgeGroups.get(edge.id);
      if (group) {
        group.visible = visible;
      }
      if (visible) {
        visibleNodes.add(edge.a);
        visibleNodes.add(edge.b);
      }
    });

    this.junctionGroups.forEach((group, nodeId) => {
      group.visible = visibleNodes.has(nodeId);
    });

    if (this.beacon && this.beaconLight) {
      const targetVisible = visibleNodes.has(state.targetNode) || state.reachedTarget;
      this.beacon.visible = targetVisible;
      this.beaconLight.visible = targetVisible;
    }
  }

  updateCamera(maze, state, deltaTime) {
    const fromNode = getNode(maze, state.fromNode);
    const toNode = getNode(maze, state.toNode);
    const fromUnit = asVector3(latLonToVector(fromNode.lat, fromNode.lon, 1));
    const toUnit = asVector3(latLonToVector(toNode.lat, toNode.lon, 1));
    const t = THREE.MathUtils.clamp(state.progress, 0.001, 0.999);
    const position = asVector3(
      slerpVectors(fromUnit, toUnit, t, VIEW_CONFIG.corridorRadius),
    );
    const pointAhead = asVector3(
      slerpVectors(fromUnit, toUnit, Math.min(0.999, t + 0.02), VIEW_CONFIG.corridorRadius),
    );
    const pointBehind = asVector3(
      slerpVectors(fromUnit, toUnit, Math.max(0.001, t - 0.02), VIEW_CONFIG.corridorRadius),
    );
    const normal = position.clone().normalize();
    const up = normal.clone().negate();
    const tangent = projectTangent(pointAhead.clone().sub(pointBehind), normal);
    const right = tangent.clone().cross(normal).normalize();
    const lookDirection = tangent
      .clone()
      .applyAxisAngle(up, state.lookBias * 0.42)
      .normalize();
    const lateralOffset = right.clone().multiplyScalar(state.branchBias * 0.55);
    const cameraPosition = position
      .clone()
      .add(up.clone().multiplyScalar(VIEW_CONFIG.cameraHeight))
      .add(lateralOffset);
    const lookTarget = cameraPosition
      .clone()
      .add(lookDirection.multiplyScalar(9.5))
      .add(up.clone().multiplyScalar(0.18));

    const smoothing = 1 - Math.exp(-deltaTime * 10);
    this.camera.position.lerp(cameraPosition, smoothing);
    this.camera.up.lerp(up, smoothing).normalize();
    this.camera.lookAt(lookTarget);

    if (this.beacon && this.beaconLight) {
      const pulse = 1 + Math.sin(performance.now() * 0.004) * 0.16;
      this.beacon.scale.setScalar(pulse);
      this.beaconLight.intensity = state.reachedTarget ? 12 : 7 + Math.sin(performance.now() * 0.003) * 1.2;
    }
  }

  render(maze, state, deltaTime) {
    if (this.currentMazeSeed !== maze.seed) {
      this.buildMaze(maze, state);
    }

    this.updateVisibility(maze, state);
    this.updateCamera(maze, state, deltaTime);
    this.overlayElement.hidden = !state.reachedTarget;
    this.renderer.render(this.scene, this.camera);
  }
}
