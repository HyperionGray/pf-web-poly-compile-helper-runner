import json

for line in open("issues_lines.txt"):
    print(json.loads(line))
