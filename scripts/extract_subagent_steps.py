import json

filepath = '/usr/local/google/home/shacharb/.gemini/jetski/brain/aa8521f9-5699-4284-a1ac-243df51ca049/.system_generated/logs/transcript.jsonl'

with open(filepath, 'r') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'BROWSER_SUBAGENT':
            content = obj.get('content', '')
            if "find_lab_images" in content:
                # Let's split the content by Step headers
                steps = content.split("### Step ")
                for step in steps:
                    if "execute_browser_javascript" in step:
                        print("=================================")
                        print("Found JS execute step:")
                        print(step[:1500])
