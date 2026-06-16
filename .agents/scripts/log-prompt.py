import sys
import json
import os
import re
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

# Find the last USER_INPUT in transcript
last_user_prompt = None
try:
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get("type") == "USER_INPUT":
                    content = obj.get("content", "")
                    # Extract USER_REQUEST if present
                    match = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', content, re.DOTALL)
                    if match:
                        last_user_prompt = match.group(1).strip()
                    else:
                        last_user_prompt = content.strip()
            except Exception:
                continue
except Exception as e:
    print(f"Error reading transcript: {e}", file=sys.stderr)
    sys.exit(0)

if last_user_prompt:
    # Single line log, collapse newlines
    prompt_sanitized = last_user_prompt.replace('\n', ' ')
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
            lf.write(f"[{timestamp}] USER: {prompt_sanitized}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)
