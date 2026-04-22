# Technical Report: OpenClaw Window Stability & Session Corruption Analysis

## 1. Root Cause Analysis (RCA)
The window lagging and crashing observed during the loading of corrupted session files (e.g., `8caeebda...jsonl`) is caused by a **Blocking-Parsing Memory Exhaustion** chain.

### The Failure Chain
`Corrupted JSONL (Missing Newline/Quote)` $\rightarrow$ `Parser consumes multiple lines as one giant string` $\rightarrow$ `Synchronous JSON.parse() blocks the Event Loop` $\rightarrow$ `Heap Memory Spike` $\rightarrow$ `V8 OOM Crash`.

### Key Technical Impacts
- **Memory**: V8 heap is exhausted by attempting to parse a massive, malformed string, leading to `FATAL ERROR: Allocation failed`.
- **Threads**: The main UI thread is blocked during the parsing process, resulting in a complete window freeze (unresponsive to user input).
- **Stability**: Because the corruption occurs at the "Session Loading" (boot) phase, the application becomes unlaunchable or crashes immediately upon session selection.

## 2. Technical References (Patterns)
Research was based on 20 industry patterns across Electron, Node.js, and V8:
- **Parsing**: OOM on large strings, ReDoS, and `readline` buffer overflows.
- **Memory**: V8 heap limits (Renderer vs Main), GC pauses, and Buffer allocation overhead.
- **Threading**: Event loop blocking, Sync I/O bottlenecks, and IPC saturation.
- **Electron**: IPC buffer limits, Renderer process crashes, and GPU process lag.

## 3. Concrete Repair Path (The Solution)

### Priority 1: Defensive Parsing (Immediate)
- **Stream Reading**: Replace bulk file reads with `readline` or `json-stream`.
- **Hard Line Limit**: Enforce a `MAX_LINE_LENGTH` (e.g., 1MB). Discard any line exceeding this limit.
- **Isolated Parsing**: Wrap `JSON.parse` in a `try-catch` block **per line** to prevent a single corrupt record from failing the entire session.

### Priority 2: Thread Offloading (Structural)
- **Worker Threads**: Move all session loading and parsing logic to a dedicated `Worker Thread` to ensure the main UI thread remains responsive.
- **Async Communication**: Use non-blocking IPC to stream session data from the worker to the renderer.

### Priority 3: Integrity Assurance (Preventative)
- **Atomic Saves**: Implement `write` $\rightarrow$ `temp file` $\rightarrow$ `rename` to eliminate "torn writes".
- **Auto-Quarantine**: Implement a failure counter; move sessions that fail to load 3+ times to a `.corrupt` backup folder automatically.

## 4. Conclusion
The instability is not a random bug but a structural vulnerability to malformed input. By implementing **Streaming + Line-Limits + Worker Threads**, OpenClaw can achieve "Crash-Proof" session loading.
