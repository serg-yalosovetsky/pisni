import json

with open('progress.json', 'r') as file:
    lines = json.load(file)
    
print(lines)