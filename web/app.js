import { advanceState, createInitialState, createMaze } from "./maze.js";
import { renderRadar, updateHud } from "./render.js";
import { ThreeMazeView } from "./three-view.js";

const viewportCanvas = document.getElementById("viewport");
const radarCanvas = document.getElementById("radar");
const radarCtx = radarCanvas.getContext("2d");
const threeView = new ThreeMazeView(
  viewportCanvas,
  document.getElementById("viewportOverlay"),
);

const elements = {
  nodesStat: document.getElementById("nodesStat"),
  loopsStat: document.getElementById("loopsStat"),
  headingStat: document.getElementById("headingStat"),
  branchStat: document.getElementById("branchStat"),
  targetStat: document.getElementById("targetStat"),
  radarPanel: document.getElementById("radarPanel"),
  regenerateButton: document.getElementById("regenerateButton"),
  recenterButton: document.getElementById("recenterButton"),
  radarButton: document.getElementById("radarButton"),
};

let seed = 4;
let maze = createMaze(seed);
const state = createInitialState(maze);
const input = {
  forward: 0,
  bias: 0,
};

function regenerate() {
  seed += 1;
  maze = createMaze(seed);
  state.maze = maze;
  state.fromNode = "n1";
  state.toNode = "n10";
  state.progress = 0.08;
  state.branchBias = 0;
  state.lookBias = 0;
  state.steps = 0;
  state.targetNode = "n15";
  state.reachedTarget = false;
}

elements.regenerateButton.addEventListener("click", regenerate);
elements.recenterButton.addEventListener("click", () => {
  state.branchBias = 0;
  state.lookBias = 0;
});
elements.radarButton.addEventListener("click", () => {
  state.radarVisible = !state.radarVisible;
  elements.radarPanel.classList.toggle("is-hidden", !state.radarVisible);
  elements.radarButton.textContent = state.radarVisible ? "Hide Radar" : "Show Radar";
});

window.addEventListener("keydown", (event) => {
  if (event.key === "w") {
    input.forward = 1;
  }
  if (event.key === "s") {
    input.forward = -1;
  }
  if (event.key === "a") {
    input.bias = -1;
  }
  if (event.key === "d") {
    input.bias = 1;
  }
  if (event.key === "m") {
    elements.radarButton.click();
  }
  if (event.key === "r") {
    regenerate();
  }
});

window.addEventListener("keyup", (event) => {
  if ((event.key === "w" && input.forward === 1) || (event.key === "s" && input.forward === -1)) {
    input.forward = 0;
  }
  if ((event.key === "a" && input.bias === -1) || (event.key === "d" && input.bias === 1)) {
    input.bias = 0;
  }
});

let previous = performance.now();

function animate(now) {
  const deltaTime = Math.min(0.032, (now - previous) / 1000);
  previous = now;

  state.branchBias += (input.bias - state.branchBias) * Math.min(1, deltaTime * 8);
  state.lookBias += (input.bias - state.lookBias) * Math.min(1, deltaTime * 6);
  if (Math.abs(state.lookBias) < 0.001 && input.bias === 0) {
    state.lookBias = 0;
  }

  advanceState(state, input.forward, deltaTime);
  threeView.render(maze, state, deltaTime);
  renderRadar({
    radarCtx,
    state,
    maze,
    radarCanvas,
  });
  updateHud(elements, state, maze);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
