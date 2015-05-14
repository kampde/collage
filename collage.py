#!/usr/bin/env python
#-*- coding: utf-8 -*-
u"""

"""
import argparse
import textwrap
from glob import glob
from decimal import Decimal
import os
import re
import sys
from PIL import Image

MM_PER_INCH = Decimal("25.4")

DEFAULT_WIDTH = Decimal("3050")
DEFAULT_HEIGHT = Decimal("2350")
DEFAULT_RESOLUTION = 200
DEFAULT_COLUMNS = 12
DEFAULT_ROWS = 6
DEFAULT_MODE = "CMYK"
DEFAULT_PADDING = 0
DEFAULT_HSPACE = 0
DEFAULT_VSPACE = 0
DEFAULT_ALIGNMENT = ("center", 0, "center", 0)

def collage(
    image_files,
    output_file,
    width = DEFAULT_WIDTH,
    height = DEFAULT_HEIGHT,
    resolution = DEFAULT_RESOLUTION,
    mode = DEFAULT_MODE,
    columns = DEFAULT_COLUMNS,
    rows = DEFAULT_ROWS,
    padding = DEFAULT_PADDING,
    hspace = DEFAULT_HSPACE,
    vspace = DEFAULT_VSPACE,
    alignment_rules = None,
    verbose = False
):
    # Convert all units from mm to pixels
    pixels = lambda mm: int(mm / MM_PER_INCH * resolution)
    width_px = pixels(width)
    height_px = pixels(height)
    hspace_px = pixels(hspace)
    vspace_px = pixels(vspace)
    padding_px = pixels(padding)

    if verbose:
        print "Mida de la imatge: %d x %d" % (width_px, height_px)

    # Calculate cell size
    cell_width_px = (width_px - padding_px * 2 - (columns - 1) * hspace_px) / columns
    cell_height_px = (height_px - padding_px * 2 - (rows - 1) * vspace_px) / rows

    if verbose:
        print "Mida de les cel·les: %d x %d" % (cell_width_px, cell_height_px)

    # Create an empty canvas
    canvas = Image.new(mode, (width_px, height_px))

    # Load and resize the source images
    images = []
    for image_file in image_files:
        if verbose:
            print "Redimensionant %s" % image_file

        halign, offset_x, valign, offset_y = get_image_alignment(
            image_file,
            alignment_rules,
            verbose = verbose
        )

        thumb = thumbnail(
            image_file,
            cell_width_px,
            cell_height_px,
            horizontal_alignment = halign,
            vertical_alignment = valign,
            offset_x = pixels(offset_x),
            offset_y = pixels(offset_y),
            mode = mode
        )
        images.append(thumb)

    # Compose the grid
    if verbose:
        print "Enganxant imatges"

    i = 0

    for row in xrange(rows):
        for column in xrange(columns):
            image = images[i % len(images)]
            x = cell_width_px * column + padding_px + (column * hspace_px)
            y = cell_height_px * row + padding_px + (row * vspace_px)
            if verbose:
                print "Enganxant a (%d, %d)" % (x, y)
            canvas.paste(image, (x, y))
            i += 1

    # Save the resulting image
    if verbose:
        print "Desant", output_file

    canvas.save(output_file)

def get_image_alignment(image_file, alignment_rules, verbose = False):

    if alignment_rules is not None:
        image_name = os.path.splitext(os.path.basename(image_file))[0]
        image_alignment = alignment_rules.get(os.path.basename(image_name))

        if image_alignment:
            if verbose:
                print u"Aplicant alineament %r a la imatge %r" % (
                    image_file,
                    image_alignment
                )
            return image_alignment

    return DEFAULT_ALIGNMENT

def thumbnail(
    image_file,
    width,
    height,
    horizontal_alignment = "center",
    vertical_alignment = "center",
    offset_x = 0,
    offset_y = 0,
    upscale = True,
    filter = Image.ANTIALIAS,
    mode = DEFAULT_MODE,
    cache_folder = "/tmp"
):
    if cache_folder:
        cache_path = os.path.join(
            cache_folder,
            "%s-%d-%d-%s%d-%s%d-%d-%d-%s%s" % (
                os.path.splitext(os.path.basename(image_file))[0],
                width,
                height,
                horizontal_alignment,
                offset_x,
                vertical_alignment,
                offset_y,
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
        offset_x += (target_width - width) / 2
    elif horizontal_alignment == "left":
        pass
    elif horizontal_alignment == "right":
        offset_x += target_width - width
    else:
        raise ValueError(
            "horizontal_alignment = %s not implemented"
            % horizontal_alignment
        )

    if vertical_alignment == "center":
        offset_y += (target_height - height) / 2
    elif vertical_alignment == "top":
        pass
    elif vertical_alignment == "bottom":
        offset_y += target_height - height
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

_alignment_regexp = re.compile(
    r"(?P<pattern>[^:]+)"
    r":(?P<halign>left|center|right)(?P<hoffset>[-+]\d+)?"
    r":(?P<valign>top|center|bottom)(?P<voffset>[-+]\d+)?"
)

def parse_alignment(alignment_string):

    match = _alignment_regexp.match(alignment_string)

    if not match:
        raise ValueError(u"Invalid alignment string: %r" % alignment_string)

    normalize_int = lambda value: int(value) if value else 0

    return (
        match.group("pattern"),
        match.group("halign"),
        normalize_int(match.group("hoffset")),
        match.group("valign"),
        normalize_int(match.group("voffset"))
    )

def main():
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
    )

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

    parser.add_argument(
        "--padding", type = int, default = DEFAULT_PADDING,
        help = u"Marge de la imatge (en mm)."
    )

    parser.add_argument(
        "--hspace", type = int, default = DEFAULT_HSPACE,
        help = u"Espaiat horitzontal entre imatges (en mm)."
    )

    parser.add_argument(
        "--alignment", "-a", nargs = "*", type = parse_alignment,
        help = textwrap.dedent(u"""\
            Permet controlar el retallat de les imatges que satisfan el patró
            indicat.

            Cada regla pren la forma següent:
                image_name:halign[+-offset]:valign[+-offset]

                image_name:
                    El nom del fitxer imatge al que s'aplica la regla (sense
                    ruta ni extensió).

                halign:
                    left, center o right, segons es vulgui alinear la imatge a
                    l'esquerra, centre o dreta, respectivament.

                valign:
                    top, center o bottom, segons es vulgui alinear la imatge a
                    l'esquerra, centre o dreat, respectivament.

                offset:
                    Un valor numèric que es combina amb l'alineament per
                    aplicar un despleçament en mm sobre el posicionament
                    indicat. Es pot indicar un valor positiu o negatiu.

                exemple:
                    mad-monkey:center:top+10
            """
        )
    )

    parser.add_argument(
        "--vspace", type = int, default = DEFAULT_VSPACE,
        help = u"Espaiat vertical entre imatges (en mm)."
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
        padding = args.padding,
        hspace = args.hspace,
        vspace = args.vspace,
        alignment_rules =
            dict(
                (item[0], item[1:])
                for item in args.alignment
            )
            if args.alignment
            else None,
        verbose = args.verbose
    )

if __name__ == "__main__":
    main()

# vim: et sts=4 sw=4 ts=4
