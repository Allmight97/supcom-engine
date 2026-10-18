# /// script
# dependencies = ["numpy", "pillow"]
# ///
"""Compare a reference screenshot of the original with one of ours.

    uv run -q tools/image-compare/compare.py REF OURS [--region X0 Y0 X1 Y1] [--search N] [--diff OUT.png]

REF may be a raw tools/ref-shot capture (3360x2156 Retina window with title bar): it is cropped to rows
56-2155 and box-downscaled by 2 to OURS's 1680x1050 first. Within the region (default: the whole image minus a
4 px margin) the best offset of OURS within +-N px (default 4) is searched; the line printed is the mean absolute
difference over RGB (of 255), that offset, and the share of pixels whose largest channel difference is within 8
and within 16. --diff writes the per-pixel largest channel difference, scaled x4, as a grey image.
"""
import argparse

import numpy as np
from PIL import Image


def load_reference(path, size):
    image = Image.open(path).convert('RGB')
    if image.size == size:
        return image
    if image.size == (size[0] * 2, size[1] * 2 + 56):
        return image.crop((0, 56, image.width, image.height)).reduce(2)
    raise SystemExit(f'{path}: {image.size[0]}x{image.size[1]} is neither {size[0]}x{size[1]} nor its Retina capture')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reference')
    parser.add_argument('ours')
    parser.add_argument('--region', type=int, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'))
    parser.add_argument('--search', type=int, default=4)
    parser.add_argument('--diff')
    args = parser.parse_args()
    ours_image = Image.open(args.ours).convert('RGB')
    a = np.asarray(load_reference(args.reference, ours_image.size), dtype=float)
    b = np.asarray(ours_image, dtype=float)
    n = args.search
    x0, y0, x1, y1 = args.region or (n, n, b.shape[1] - n, b.shape[0] - n)
    if x0 - n < 0 or y0 - n < 0 or x1 + n > b.shape[1] or y1 + n > b.shape[0]:
        raise SystemExit('region plus search margin leaves the image')
    ref = a[y0:y1, x0:x1]
    mean, dx, dy = min((np.abs(ref - b[y0 + dy:y1 + dy, x0 + dx:x1 + dx]).mean(), dx, dy)
                       for dy in range(-n, n + 1) for dx in range(-n, n + 1))
    largest = np.abs(ref - b[y0 + dy:y1 + dy, x0 + dx:x1 + dx]).max(axis=2)
    print('mean |diff| %.2f/255 at dx %d dy %d; within 8: %.1f%%, within 16: %.1f%%'
          % (mean, dx, dy, (largest <= 8).mean() * 100, (largest <= 16).mean() * 100))
    if args.diff:
        Image.fromarray(np.clip(largest * 4, 0, 255).astype(np.uint8)).save(args.diff)


main()
