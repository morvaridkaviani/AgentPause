/* AgentPause in-browser engine (used by the static online demo).
 *
 * Runs the real AgentPause REST API (FastAPI + SQLite in memory) inside Pyodide, Python compiled
 * to WebAssembly, in this Web Worker. The page sends {id, method, path, query, body}; the worker
 * answers {id, result: {status, contentType, body}}. Nothing leaves the browser.
 */
// Loaded as a module worker: new Worker(url, { type: "module" }).
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

const version = new URL(self.location.href).searchParams.get("v") || "dev";
const status = (state, text) => self.postMessage({ type: "status", state, text });
let handle = null;

const ready = (async () => {
  status("loading", "Downloading the Python runtime…");
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  status("loading", "Loading Python libraries…");
  await pyodide.loadPackage(["fastapi", "sqlalchemy", "pydantic"], { messageCallback: () => {} });
  status("loading", "Starting AgentPause…");
  const zipUrl = new URL(`py/agentpause-py.zip?v=${encodeURIComponent(version)}`, self.location.href);
  const response = await fetch(zipUrl);
  if (!response.ok) throw new Error(`Could not download the AgentPause bundle (${response.status})`);
  pyodide.unpackArchive(new Uint8Array(await response.arrayBuffer()), "zip", { extractDir: "/home/pyodide/agentpause" });
  await pyodide.runPythonAsync('import sys\nsys.path.insert(0, "/home/pyodide/agentpause")\nimport agentpause_web');
  handle = pyodide.globals.get("agentpause_web").handle;
  status("ready", "");
})().catch((error) => {
  status("failed", String((error && error.message) || error));
});

self.onmessage = async (event) => {
  const { id, method, path, query, body } = event.data;
  try {
    await ready;
    if (!handle) throw new Error("The in-browser engine failed to start.");
    const raw = await handle(method, path, query || "", body ?? null);
    self.postMessage({ id, result: JSON.parse(raw) });
  } catch (error) {
    self.postMessage({ id, error: String((error && error.message) || error) });
  }
};
