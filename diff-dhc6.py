from __future__ import unicode_literals
import diff, sys, logging, os, shutil, time, fileinput, re

LOG = logging.getLogger(__name__)

def makedir(path):
    if not os.path.isdir(path):
        h,t = os.path.split(path)
        if h and not os.path.isdir(h):
            makedir(h)
        os.mkdir(os.path.join(h,t))
    return path

def get_version(source):
    with open(source, 'r') as file :
        txt = file.read()
    match = re.search("Tweak Version: ([0-9]\.[0-9]\.[0-9]\.[0-9])", txt)
    if not match:
        raise ValueError("Can't determine tweak version from "+source)
    return match.group(1)


DOC = "DHC6-v2-tweaks.txt"
ASSETS = [DOC, "patch.py", "tweak-dhc6.py"]

if __name__ == '__main__':

    print("Diff'ing modifications to Aircraft")

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    version = get_version(DOC)

    out = makedir("build/build-"+version)

    args = [
       "--a=C:/Users/nmeier/Downloads/twotter/original",
	   "--b=C:/Users/nmeier/Downloads/twotter/modded",
	   "--o="+makedir(out+"/tweaks/"+version),
	   "--x=.*fmod.*"
    ]
    diff.main(args)

    for asset in ASSETS:
        shutil.copy(asset, os.path.join(out, asset))









