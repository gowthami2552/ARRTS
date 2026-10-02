import json
from pathlib import Path

transcript_path = Path(r"C:\Users\gowthami\.gemini\antigravity\brain\957edd73-0131-4ff7-b7f6-88e42dfa8730\.system_generated\logs\transcript_full.jsonl")
if not transcript_path.exists():
    transcript_path = Path(r"C:\Users\gowthami\.gemini\antigravity\brain\957edd73-0131-4ff7-b7f6-88e42dfa8730\.system_generated\logs\transcript.jsonl")

found = False
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            content = step.get("content", "")
            if isinstance(content, str) and "stations" in content and "train_name,train_number" in content:
                Path("data").mkdir(exist_ok=True)
                with open("data/raw_user_payload.txt", "w", encoding="utf-8") as out:
                    out.write(content)
                print(f"Extracted payload length: {len(content)}")
                found = True
        except Exception as e:
            pass

if not found:
    print("Payload not found in transcript lines.")
else:
    print("Successfully extracted payload to data/raw_user_payload.txt")
