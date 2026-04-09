import os
import shutil
import re

base_dir = "static/images/Traps"
folders = {
    "Bomb": "Bomb",
    "SpringTrap": "Spring_Trap",
    "GiantBomb": "Giant_Bomb",
    "AirBomb": "Air_Bomb",
    "SeekingAirMine": "Seeking_Air_Mine",
    "SkeletonTrap": "SkeletonTrap",
    "TornadoTrap": "Tornado_Trap"
}

for folder, prefix in folders.items():
    path = os.path.join(base_dir, folder)
    if not os.path.exists(path):
        print(f"Skipping {folder}, path not found.")
        continue
    
    # 1. Clean existing filenames
    files = os.listdir(path)
    for f in files:
        if f == ".DS_Store": continue
        clean_name = f.replace('\n', '').replace(' ', '').strip()
        if clean_name != f:
            print(f"Renaming {f} -> {clean_name}")
            os.rename(os.path.join(path, f), os.path.join(path, clean_name))
    
    # Refresh file list
    files = os.listdir(path)
    
    # 2. Duplicate range-based files
    for f in files:
        if f == ".DS_Store": continue
        # Matches patterns like Name1_2.webp or Name1_2_Suffix.webp
        match = re.search(r'(\d+)_(\d+)', f)
        if match:
            v1, v2 = match.groups()
            suffix = ""
            if "_Ground" in f:
                suffix = "_Ground"
            
            # Construct new names
            # We want to match the prefix used in script.js
            target1 = f"{prefix}{v1}{suffix}.webp"
            target2 = f"{prefix}{v2}{suffix}.webp"
            
            print(f"Duplicating {f} into {target1} and {target2}")
            shutil.copy2(os.path.join(path, f), os.path.join(path, target1))
            shutil.copy2(os.path.join(path, f), os.path.join(path, target2))
            
            # Optional: remove the range file
            os.remove(os.path.join(path, f))

# Special case for Tornado Trap 2-3 if needed
# (Already handled by the regex pattern)

print("Done cleaning and duplicating trap images.")
