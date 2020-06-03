from __future__ import unicode_literals
import patch, sys, os, re, logging, glob
from PIL import Image, ImageChops, PngImagePlugin, TiffImagePlugin

# set up stdout and file logging
logger = logging.getLogger()
handler = logging.FileHandler("tweaks.log")
handler.setFormatter(logging.Formatter("%(asctime)s;%(levelname)-5s:%(name)s:%(message)s"))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger = logging.getLogger("tweak")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# remove patch module's direct logging
logging.getLogger("patch").handlers = []

# global constants
PREV5_PATCH_PATTERN = "DHC6-300 Twin Otter V([\d.]*).diff"
VERSION_PATTERN = "([\d.]*)"

TWEAKS_DIR = "tweaks"
TWEAK_VERSION = TWEAKS_DIR+"/version"
AIRCRAFT_VERSION = "version.txt"
SUPPORTED_VERSION = "Current Version: V2.02"

def sort_versions(vs, key=lambda x: x):
    vs.sort(key=lambda s: list(map(int, key(s).split('.'))))
    return vs

def read_line(file, n=1):
    line = None
    try:
        with open(file) as f:
            for i in range(0,n):
                line = f.readline().strip()
    except:
        pass
    return line


def find_tweaks():
    def dir2version(f):
        if not os.path.isdir(os.path.join(TWEAKS_DIR, f)):
            return None
        match = re.match(VERSION_PATTERN, f)
        return match.group(1) if match else None

    version = None
    tweaks = []
    if os.path.isdir(TWEAKS_DIR):
        tweaks = sort_versions(list(filter(None, map(dir2version, os.listdir(TWEAKS_DIR)))))
        version = read_line(TWEAK_VERSION)
    if not tweaks:
        raise RuntimeError("No tweaks in "+os.path.abspath(TWEAKS_DIR))

    logger.debug("Tweaks found: "+', '.join(tweaks))

    return version, tweaks

def revert_prev5_diff():
    def file2version(f):
        match = re.match(PREV5_PATCH_PATTERN, f)
        return match.group(1) if match else None

    tweaks = sort_versions(list(filter(None, map(file2version, os.listdir(".")))))
    if len(tweaks) > 1:
        raise RuntimeError("Found more than one pre 2.0.2.5 diff file")
    elif len(tweaks) == 1:
        version = tweaks[0]
        logger.info("Reverting previous tweaks version %s" % version)
        diff = PREV5_PATCH_PATTERN.replace(VERSION_PATTERN, version)
        patch_diff(diff, True)
        os.remove(diff)


def patch_diff(diff, revert):
    if revert:
        logger.info("< "+diff);
        patch.main([ "-d", ".", "--revert", diff])
    else:
        logger.info("> "+diff);
        patch.main([ "-d", ".", diff])

def patch_tiff(tiff, revert):

    patch_img = Image.open(tiff)

    try:
        if not revert:
            patch_img.seek(1)
        relative = patch_img.tag_v2[269]
    except:
        raise RuntimeError("%s is not a valid tiff" % tiff)

    logger.debug("%s with relative path %s" % (tiff, relative))

    if revert:
        logger.info("< "+tiff);
    else:
        logger.info("> "+tiff);

    try:
        target_img = Image.open(relative)
    except:
        raise RuntimeError("Can't find %s to modify" % relative)

    mask_img = patch_img.split()[3]

    # Create a new image with an opaque black background
    target_img.paste(patch_img, mask=mask_img)
    target_img.save(relative)


def extension(diff):
    return os.path.splitext(diff)[1][1:]

def apply(diff, revert):
    try:
        globals()["patch_"+extension(diff)](diff, revert)
    except KeyError as ke:
        raise RuntimeError("Unknown diff %s: %s" % (diff, ke.message))

def patch_version(version, revert=False):

    if revert:
        logger.info("Reverting to version %s" % version)
    else:
        logger.info("Patching to version %s" % version)

    # got version directory?
    dir = os.path.join(TWEAKS_DIR, version)
    if not os.path.isdir(dir):
        raise RuntimeError("Version folder %s is missing" % version)

    # look for diffs
    diffs = [os.path.join(dir, f) for f in os.listdir(dir)]

    # apply
    applied = []
    try:
        for diff in diffs:
            apply(diff, revert)
            applied.append(diff)
    except:
        if applied and not revert:
            for diff in applied:
                apply(diff, True)
        raise

    # mark version
    if revert:
        os.remove(TWEAK_VERSION)
    else:
        with open(TWEAK_VERSION, 'a') as f:
            f.write(version)


if __name__ == '__main__':

    logger.debug("Tweak DHC6 started")

    try:
        # verify we're looking at RWDesign's V2.02
        av = read_line(AIRCRAFT_VERSION, 2)
        if av != SUPPORTED_VERSION:
            raise RuntimeError("Unsupported aircraft version %s (should be %s)" % (av, SUPPORTED_VERSION))

        # Look for pre 2.0.2.5 diff file to revert
        revert_prev5_diff()

        # look for tweak versions (current, avail)
        version, tweaks = find_tweaks()

        # look for current version to revert
        if version:
            patch_version(version, True)

        # apply latest
        patch_version(tweaks[-1]);

    except Exception as e:
        logger.info("Caught exception", exc_info=True)
        logger.warn("%s - Aborting" % str(e))










