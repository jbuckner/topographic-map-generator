#!/usr/bin/env python
import os

import Image
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt

from pylab import *

from srtm import SRTMDownloader

sw_corner = {
    'lat': 36,
    'lng': -123
}
ne_corner = {
    'lat': 39,
    'lng': -120
}

tile_count_lat = abs(sw_corner['lat'] - ne_corner['lat'])
tile_count_lng = abs(sw_corner['lng'] - ne_corner['lng'])

resolution = 999  # numer of samples we take of each hgt in each direction
pixels = resolution * resolution  # for calculating percent complete
divisor = resolution + 1.0  # for calculating the point to sample from

srtm_format = 3  # 3, 1

dpi = 100
width = 20  # inches
height = 20  # inches
output_resolution = {
    'x': width * dpi,
    'y': height * dpi
}
img_directory = "images/srtm%s" % srtm_format  # where to save the images


def merge_images():
    # images = os.listdir(img_directory)

    stitched_dimensions = {
        "x": output_resolution["x"] * tile_count_lng,
        "y": output_resolution["y"] * tile_count_lat
    }

    print stitched_dimensions

    blank_image = Image.new("RGBA",
                            (stitched_dimensions["x"],
                                stitched_dimensions["y"]),
                            "black")

    for lat_i, lat in enumerate(range(sw_corner['lat'], ne_corner['lat'])):
        for lng_i, lng in enumerate(range(sw_corner['lng'], ne_corner['lng'])):
            filename = "%sx%s.png" % (lat, lng)
            try:
                filepath = os.path.join(img_directory, filename)
                im = Image.open(filepath)
                print filename, im.format, "%dx%d" % im.size, im.mode
                blank_image.paste(im, (2000 * lng_i, 2000 * lat_i))
            except IOError:
                pass
    blank_image.save("merged_file.png")


def update_status(percent):
    sys.stdout.write("\r%3d%%" % percent)
    sys.stdout.flush()

if __name__ == '__main__':
    fig = plt.figure(frameon=False)
    fig.set_size_inches(width, height)
    fig.set_dpi(dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    downloader = SRTMDownloader(
        directory="/srtm/version2_1/SRTM%s/" % srtm_format,
        cachedir="cache/srtm%s" % srtm_format)
    downloader.loadFileList()

    pd = None  # processing decision whether to process all or skip all

    for lat in range(sw_corner['lat'], ne_corner['lat']):
        for lng in range(sw_corner['lng'], ne_corner['lng']):
            tile = downloader.getTile(lat, lng)
            outfile = zeros((resolution, resolution))
            img_filename = "%sx%s.png" % (lat, lng)
            img_path = os.path.join(img_directory, img_filename)

            if os.path.exists(img_path):
                if pd == "s":
                    continue
                if pd != "p":
                    pd = raw_input("Image %s already exists. Process again? "
                                   "Y/N/(P)rocess All/(S)kip All: " %
                                   img_filename)
                    pd = pd.lower()
                    if pd == "n" or pd == "s":
                        continue

            print "Processing: %s, %s" % (tile.lat, tile.lon)

            c = 0  # just a counter to track completion
            for lat_i in range(0, resolution):
                for lng_i in range(0, resolution):
                    lat_point = lat + (lat_i / divisor)
                    lng_point = lng + (lng_i / divisor)
                    alt = tile.getAltitudeFromLatLon(lat_point, lng_point)
                    if alt:
                        outfile[lat_i][lng_i] = float(alt)
                    c = c + 1.0
                    if (c % 1000) == 0:
                        percent_complete = (c / pixels) * 100.0
                        update_status(percent_complete)
            # logarithm color scale
            color_scale = np.log1p(outfile)
            ax.imshow(outfile, aspect='normal',
                      interpolation='bilinear', cmap=cm.gray, alpha=1.0)
            fig.savefig(img_path)
    merge_images()
