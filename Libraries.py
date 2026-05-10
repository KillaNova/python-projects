from datetime import datetime

nu = datetime.now()
print(nu)


import os

print(os.getcwd())  # Print the current working directory

import json

profiel = {"naam": "Hamza", "leeftijd": 25}
with open("profiel.json", "w", encoding="utf-8") as f:
    json.dump(profiel, f)

with open("profiel.json", "r") as f:
    content = json.load(f)
    print(content)

import json

profiel = {"naam": "Hamza", "leeftijd": 25}
with open("profiel.json", "w") as f:
    json.dump(profiel, f)

with open("profiel.json", "r") as f:
    inhoud = json.load(f)
    print(inhoud)
