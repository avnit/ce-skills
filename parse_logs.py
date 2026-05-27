import json

filepath = '/usr/local/google/home/shacharb/.gemini/jetski/brain/aa8521f9-5699-4284-a1ac-243df51ca049/.system_generated/logs/transcript.jsonl'

with open(filepath, 'r') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'BROWSER_SUBAGENT':
            content = obj.get('content', '')
            if "find_lab_images" in content:
                print("--- FOUND find_lab_images subagent output ---")
                print(content[:3000])
                print("... [truncated] ...")
                print(content[-3000:])
