import sys
import json
import os
from datetime import datetime

# Read stdin
try:
    payload = json.load(sys.stdin)
    transcript_path = payload.get("transcriptPath") or payload.get("transcript_path")
except Exception as e:
    print(f"Error reading stdin: {e}", file=sys.stderr)
    sys.exit(0)  # Exit 0 so we don't block/crash the CLI loop

if not transcript_path or not os.path.exists(transcript_path):
    print(f"Transcript path not found: {transcript_path}", file=sys.stderr)
    sys.exit(0)

# Find the last MODEL PLANNER_RESPONSE in transcript
last_assistant_content = None
try:
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get("source") == "MODEL" and obj.get("type") == "PLANNER_RESPONSE":
                    content = obj.get("content", "")
                    if content:
                        last_assistant_content = content.strip()
            except Exception:
                continue
except Exception as e:
    print(f"Error reading transcript: {e}", file=sys.stderr)
    sys.exit(0)

if last_assistant_content:
    # Summarize or truncate to 600 chars
    summary = last_assistant_content[:600]
    if len(last_assistant_content) > 600:
        summary += "..."
    # Collapse newlines to single line
    summary_sanitized = summary.replace('\n', ' ')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workspaces = payload.get("workspacePaths") or []
    if workspaces:
        log_dir = os.path.join(workspaces[0], "logs")
    else:
        log_dir = "logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "session.log")
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"[{timestamp}] AGY: {summary_sanitized}\n")
            lf.write("---\n")
    except Exception as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
else:
    # Fallback if no response captured
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workspaces = payload.get("workspacePaths") or []
    if workspaces:
        log_dir = os.path.join(workspaces[0], "logs")
    else:
        log_dir = "logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "session.log")
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"[{timestamp}] AGY: [session ended - no response captured]\n")
            lf.write("---\n")
    except Exception as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
