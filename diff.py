from __future__ import unicode_literals
import sys, os, difflib, argparse, re, argparse, io, logging
from PIL import Image, ImageChops, PngImagePlugin, TiffImagePlugin

PY3K = sys.version_info >= (3, 0)

if PY3K:
    unicode = str

LOG = logging.getLogger(__name__)

def read(filename):
    with io.open(filename, mode="r", encoding="utf-8") as f:
        body = f.read()
        # diff doesn't handle a file without a trailing \n on last line correctly
        if len(body)>0 and not body.endswith("\n"):
            body+="\n"
        return body.splitlines(True)

def ftime(path):
    return os.stat(path).st_mtime

def find_differ(differs, file):
    for pattern, differ in differs.items():
        if re.match(pattern, file):
            return differ
    return None

def find_mods(modded, original, differs, excl):
    result = []
    for root, subdirs, files in os.walk(modded):
        for file in files:
            d = find_differ(differs, file)
            if not d:
                continue
            m = os.path.join(root, file)
            r = os.path.relpath(m,modded).replace("\\","/")
            if re.match(excl, r):
                continue
            o = os.path.join(original, r)
            if not os.path.isfile(o):
                LOG.debug("No original   : {}".format(r))
                pass
            elif ftime(m)<=ftime(o):
                LOG.debug("Newer original: {}".format(r))
                pass
            else:
                LOG.debug("Change in     : {}".format(r))
                print("Change        : {}".format(r))
                result.append((m,o,r,d))
    return result

def flatten_diffs(diffs):
    return [l for diff in diffs for l in diff]

def arg_is_dir(value):
    value = os.path.abspath(value)
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError("%s is not a directory" % value)
    return unicode(value)

def write_lines(diffs, out):
    for line in diffs:
        # patch non-unicode that difflib generates in some lines
        if isinstance(line, str):
            line = unicode(line)
        out.write(line)

def write_diff(f, diff):
    if f:
        with io.open(f, mode="w", encoding="utf-8") as out:
            write_lines(diff, out)
    else:
        write_lines(diff, sys.stdout)


def diff_txt(modded, original, relative, out):
    write_diff(out+".diff", difflib.unified_diff(read(original), read(modded), relative, relative, "", "", n=3))


def diff_png(p2modded, p2original, relative, out):

    # open original and mod
    original = Image.open(p2original)
    mod = Image.open(p2modded)

    LOG.info("Original {} is mode={}, width={}, height={}".format(p2original, original.mode, original.width, original.height))
    LOG.info("Modded {} is mode={}, width={}, height={}".format(p2modded, mod.mode, mod.width, mod.height))

    # create a 1bit mask out of differences, converting grayscale in 0/1
    diff = ImageChops.difference(mod, original)
    mask = diff.convert(mode="L").point( lambda x: 0 if x==0 else 1, mode="1")

    # create final mod reduced to mask
    masked_mod = Image.composite(mod, Image.new(mod.mode, mod.size), mask)
    masked_mod.putalpha(mask)

    masked_original = Image.composite(original, Image.new(original.mode, original.size), mask)
    masked_original.putalpha(mask)

    # prepare meta information of original relative path
    ifd = TiffImagePlugin.ImageFileDirectory_v2()
    ifd[269] = relative
    ifd.tagtype[269] = TiffImagePlugin.TiffTags.ASCII

    with TiffImagePlugin.AppendingTiffWriter(out+".tiff",True) as tf:
        masked_original.save(tf, compression="tiff_deflate", tiffinfo=ifd)
        tf.newFrame()
        masked_mod.save(tf, compression="tiff_deflate", tiffinfo=ifd)




DIFFS = {'.*\.txt': diff_txt, '.*\.acf': diff_txt, '.*\.obj': diff_txt, '.*\.lua': diff_txt, '.*\.png': diff_png }

def main(args):
    parser = argparse.ArgumentParser(description='Create diff for two directories')
    parser.add_argument("--a", required=True, default=None, type=arg_is_dir, help="Directory to compare against")
    parser.add_argument("--b", required=False, default='.', type=arg_is_dir, help="Directory with changes or current directory")
    parser.add_argument("--o", required=True, default=None, type=arg_is_dir, help="Output folder")
    parser.add_argument("--x", default="^$", help="Exclude file specification")

    args = parser.parse_args(args)

    print("Original      : {}".format(args.a))
    print("Modifications : {}".format(args.b))
    print("Output        : {}".format(args.o))

    for (m,o,r,d) in find_mods(args.b, args.a, DIFFS, args.x):
        d(m, o, r, os.path.join(args.o, os.path.basename(r)))

    print("Diff result in: {}".format(args.o))

if __name__ == '__main__':
    main(sys.argv)










