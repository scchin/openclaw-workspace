---
name: feishu-calendar
description: Manage Feishu (Lark) calendars by listing calendars/events, searching schedules, and creating/syncing events.
metadata: {"openclaw":{"skillKey":"feishu-calendar","requires":{"env":["FEISHU_APP_ID","FEISHU_APP_SECRET"]},"primaryEnv":"FEISHU_APP_SECRET"}}
---

# feishu-calendar

Manage Feishu (Lark) Calendars. Use this skill to list calendars, check schedules, and sync events.

## Usage

### List Calendars
Check available calendars and their IDs.
```bash
node {baseDir}/list_test.js
```

### Search Calendar
Find a calendar by name/summary.
```bash
node {baseDir}/search_cal.js
```

### Check Master's Calendar
Specific check for the Master's calendar status.
```bash
node {baseDir}/check_master.js
```

### Sync Routine
Run the calendar synchronization routine (syncs events to local state/memory).
```bash
node {baseDir}/sync_routine.js
```

## Setup
Requires `FEISHU_APP_ID` and `FEISHU_APP_SECRET` in `.env`.

## Standard Protocol: Task Marking
**Trigger**: User says "Mark this task" or "Remind me to...".
**Action**:
1. **Analyze**: Extract date/time (e.g., "Feb 4th" -> YYYY-MM-04).
2. **Execute**: Run `create.js` with `--attendees` set to the requester's ID.
3. **Format**:
   ```bash
   node {baseDir}/create.js --summary "Task: <Title>" --desc "<Context>" --start "<ISO>" --end "<ISO+1h>" --attendees "<User_ID>"
   ```

### Setup Shared Calendar
Create a shared calendar for a project and add members.
```bash
node {baseDir}/setup_shared.js --name "Project Name" --desc "Description" --members "ou_1,ou_2" --role "writer"
```
