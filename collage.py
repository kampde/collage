#-*- coding: utf-8 -*-
u"""

"""
from argparse import ArgumentParser
from glob import glob
from decimal import Decimal
import os
import sys
from PIL import Image

MM_PER_INCH = Decimal("25.4")

DEFAULT_WIDTH = Decimal("3050")
DEFAULT_HEIGHT = Decimal("2350")
DEFAULT_RESOLUTION = 200
DEFAULT_COLUMNS = 12
DEFAULT_ROWS = 6
DEFAULT_MODE = "CMYK"

def collage(
    image_files,
    output_file,
    width = DEFAULT_WIDTH,
    height = DEFAULT_HEIGHT,
    resolution = DEFAULT_RESOLUTION,
    mode = DEFAULT_MODE,
    columns = DEFAULT_COLUMNS,
    rows = DEFAULT_ROWS,
    verbose = False
):
    canvas_width = int(width / MM_PER_INCH * resolution)
    canvas_height = int(height / MM_PER_INCH * resolution)
    cell_width = canvas_width / columns
    cell_height = canvas_height / rows

    canvas = Image.new(
        mode,
        (canvas_width, canvas_height)
    )

    images = []
    for image_file in image_files:
        if verbose:
            print "Redimensionant", image_file
        thumb = thumbnail(
            image_file,
            cell_width,
            cell_height,
            mode = mode
        )
        images.append(thumb)

    if verbose:
        print "Enganxant imatges"

    i = 0

    for row in xrange(rows):
        for column in xrange(columns):
            image = images[i % len(images)]
            x = cell_width * column
            y = cell_height * row
            canvas.paste(image, (x, y, ))
            i += 1

    if verbose:
        print "Desant", output_file

    canvas.save(output_file)

def thumbnail(
    image_file,
    width,
    height,
    horizontal_alignment = "center",
    vertical_alignment = "center",
    upscale = True,
    filter = Image.ANTIALIAS,
    mode = DEFAULT_MODE,
    cache_folder = "/tmp"
):
    if cache_folder:
        cache_path = os.path.join(
            cache_folder,
            "%s-%d-%d-%s-%s-%d-%d-%s%s" % (
                os.path.splitext(os.path.basename(image_file))[0],
                width,
                height,
                horizontal_alignment,
                vertical_alignment,
                upscale,
                filter,
                mode,
                os.path.splitext(image_file)[1]
            )
        )
        if os.path.exists(cache_path):
            return Image.open(cache_path)

    image = Image.open(image_file)
    if image.mode != mode:
        image = image.convert(mode)

    source_width, source_height = image.size
    source_ratio = float(source_width) / source_height

    resize_ratio = max(
        float(width) / source_width,
        float(height) / source_height
    )
    target_width = int(source_width * resize_ratio)
    target_height = int(source_height * resize_ratio)

    if upscale and (
        target_width > source_width
        or target_height > source_height
    ):
        image = image.resize((target_width, target_height), filter)
    else:
        width = min(source_width, width)
        height = min(source_height, height)
        target_width = min(source_width, target_width)
        target_height = min(source_height, target_height)
        image.thumbnail((target_width, target_height), filter)

    if horizontal_alignment == "center":
        offset_x = (target_width - width) / 2
    elif horizontal_alignment == "left":
        offset_x = 0
    elif horizontal_alignment == "right":
        offset_x = target_width - width
    else:
        raise ValueError(
            "horizontal_alignment = %s not implemented"
            % horizontal_alignment
        )

    if vertical_alignment == "center":
        offset_y = (target_height - height) / 2
    elif vertical_alignment == "top":
        offset_y = 0
    elif vertical_alignment == "bottom":
        offset_y = target_height - height
    else:
        raise ValueError(
            "vertical_alignment = %s not implemented"
            % self.horizontal_alignment
        )

    thumbnail_width, thumbnail_height = image.size

    image = image.crop((
        min(offset_x, thumbnail_width),
        min(offset_y, thumbnail_height),
        min(width + offset_x, thumbnail_width),
        min(height + offset_y, thumbnail_height)
    ))

    if cache_folder:
        image.save(cache_path)

    return image

def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--width", type = Decimal, default = DEFAULT_WIDTH,
        help = u"Amplada de la imatge final, en mm."
    )

    parser.add_argument(
        "--height", type = Decimal, default = DEFAULT_HEIGHT,
        help = u"Alçada de la imatge final, en mm."
    )

    parser.add_argument(
        "--resolution", type = int, default = DEFAULT_RESOLUTION,
        help = u"Píxels per polzada de la imatge final."
    )

    parser.add_argument(
        "--mode", default = DEFAULT_MODE,
        choices = ["RGB", "CMYK"],
        help = u"Mode de la imatge."
    )

    parser.add_argument(
        "--columns", type = int, default = DEFAULT_COLUMNS,
        help = u"Número de columnes de la graella."
    )

    parser.add_argument(
        "--rows", type = int, default = DEFAULT_ROWS,
        help = u"Número de files de la graella."
    )

    parser.add_argument(
        "--verbose", "-v", action = "store_true",
        help = u"Mostrar informació sobre el progrés de l'script."
    )

    parser.add_argument(
        "image_files", nargs = "+",
        help = u"Patrons de fitxers d'imatge que s'utilitzaran per omplir la "
               u"graella"
    )

    parser.add_argument(
        "output_file",
        help = u"Fitxer on es desarà la imatge final."
    )

    args = parser.parse_args()

    image_files = []
    for pattern in args.image_files:
        image_files.extend(glob(pattern))

    if not image_files:
        sys.stderr.write(u"No s'ha seleccionat cap imatge\n")
        sys.exit(2)

    collage(
        image_files,
        args.output_file,
        width = args.width,
        height = args.height,
        resolution = args.resolution,
        mode = args.mode,
        columns = args.columns,
        rows = args.rows,
        verbose = args.verbose
    )

if __name__ == "__main__":
    main()

