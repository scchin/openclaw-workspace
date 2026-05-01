# MemPalace v5 Secure Upgrade Best Practice Guide

## 1. Overview
The transition from MemPalace v4 to v5 introduces a fundamental shift from "Flat Search" to "Cognitive Routing." This guide ensures a zero-risk migration with full data integrity.

## 2. Pre-Upgrade Requirements
- **Environment**: Python 3.13+
- **Dependencies**: `chromadb >= 1.5.4`, `pyyaml >= 6.0`
- **Backup**: A full snapshot of the `.mempalace` directory is mandatory.

## 3. The 'Immortal' Upgrade Workflow
To achieve zero-risk, we utilize the **Sandbox-Verify-Switch** pattern:

### Step 1: Isolated Sandbox Setup
- Create a temporary directory (e.g., `/tmp/mempalace_v5_sandbox`).
- Clone the production data into the sandbox.
- Install the `develop` branch of MemPalace.

### Step 2: Logic Alignment
Apply the v5 core optimizations:
- **Relational Wake-up**: Implement entity-linked context expansion.
- **Heterogeneous Indexing**: Map queries to specific Rooms (skills, memory, etc.).
- **Temporal Validity**: Implement validity windows for dynamic facts.
- **Intelligent Routing**: Deploy the LLM-level room dispatcher.

### Step 3: Empirical Verification
Run a statistical battery of tests (min 100 queries) measuring:
- **Safety**: Zero crashes during heavy retrieval.
- **Routing Accuracy**: Ensuring queries hit the correct isolated indices.
- **Latency**: Verifying that routed search remains sub-100ms.

### Step 4: Atomic Pointer-Switch
Once verified, the production system is updated via an idempotent script that:
1. Locks critical config files (`chflags uchg`).
2. Performs an atomic directory swap or symlink update.
3. Verifies health via `mempalace status` before releasing the lock.

## 4. Rollback Procedure
If `mempalace status` fails post-switch:
1. Restore the `.mempalace` backup.
2. Revert the binary to the v4 stable version.
3. Analyze the sandbox logs to identify the regression.

## 5. Synergy: Temporal KG & Sutra Library
v5 leverages the **Sutra Library (藏經閣)** for advanced time-reasoning. When a query involves a time-state transition, v5 routes to the Temporal KG to retrieve the "State-at-Time-T" before returning the final result.
