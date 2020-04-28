# patch-xaircraft
A patching mechanism that allows to distribute X-Plane modifications to aircraft as a self-contained patch

# howto
There are five phases to patching an aircraft

1. Keep a copy of the unedited original aircraft as installed
2. make changes on disk to files in the aircraft folder (text and image files)
3. configure and run diff-dhc6.py (it currently contains hardcoded paths to the folder with the original airacraft and folder containing mods) - it will generate a build based on a version string in *tweaks.txt, including all files needed for someone applying the patch
4. distribute the files in build/build-x.x.x.x
5. run tweak-dhc6.py on the destination machine (again currently hardcoded to that one specific plane this started for)

# Prerequisites

Python 2.7.15 or 3.8.x
Pillow (c:/python/scripts/pip install pillow)
