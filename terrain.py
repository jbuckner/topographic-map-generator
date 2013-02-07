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
    'lat': 38,
    'lng': -121
}

tile_count_lat = abs(sw_corner['lat'] - ne_corner['lat'])
tile_count_lng = abs(sw_corner['lng'] - ne_corner['lng'])

resolution = 99  # numer of samples we take of each hgt in each direction
pixels = resolution * resolution  # for calculating percent complete
divisor = resolution + 1.0  # for calculating the point to sample from

srtm_format = 3  # 3, 1

dpi = 100
width = 40  # inches
height = 40  # inches
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


def parse_tile(tile):
    outfile = zeros((resolution, resolution))
    valley = {"lat": None, "lng": None, "alt": 32767}
    peak = {"lat": None, "lng": None, "alt": 0}
    c = 0  # just a counter to track completion

    print "Processing: %s, %s" % (tile.lat, tile.lon)
    for lat_i in range(0, resolution):
        for lng_i in range(0, resolution):
            lat_point = tile.lat + (lat_i / divisor)
            lng_point = tile.lon + (lng_i / divisor)
            alt = tile.getAltitudeFromLatLon(lat_point, lng_point)
            if alt:
                outfile[lat_i][lng_i] = float(alt)
                if alt < valley["alt"]:
                    valley["alt"] = alt
                    valley["lat"] = lat_point
                    valley["lng"] = lng_point
                if alt > peak["alt"]:
                    peak["alt"] = alt
                    peak["lat"] = lat_point
                    peak["lng"] = lng_point
            c = c + 1.0
            if (c % 1000) == 0:
                percent_complete = (c / pixels) * 100.0
                update_status(percent_complete)
    print "\n"
    return outfile, valley, peak

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

    highest_peak = {"alt": 0}
    lowest_valley = {"alt": 32767}

    cache_dir = "cache/parsed_data"
    cache_file = "%s/%sx%s_%sx%s_%s.npy" % (
        cache_dir, sw_corner["lat"], sw_corner["lng"], ne_corner["lat"],
        ne_corner["lng"], resolution)

    sample_resolution_lat = tile_count_lat * resolution
    sample_resolution_lng = tile_count_lng * resolution
    total_sample_resolution = sample_resolution_lat * sample_resolution_lng

    tile = None
    valley = {"lat": None, "lng": None, "alt": 32767}
    peak = {"lat": None, "lng": None, "alt": 0}
    c = 0  # just a counter to track completion

    reprocess = True
    if os.path.exists("%s" % cache_file):
        pd = raw_input("Cache already exists for %s. \n"
                       "Reprocess? Y/N\n" % cache_file)
        pd = pd.lower()
        if pd == "n":
            reprocess = False

    if reprocess:
        outfile = zeros((sample_resolution_lat, sample_resolution_lng))
        for lat_i in range(0, sample_resolution_lat):
            for lng_i in range(0, sample_resolution_lng):
                lat_point = sw_corner["lat"] + (lat_i / divisor)
                lng_point = sw_corner["lng"] + (lng_i / divisor)
                tile_lat = floor(lat_point)
                tile_lng = floor(lng_point)
                if not tile or tile.lat != tile_lat or tile.lon != tile_lng:
                    tile = downloader.getTile(tile_lat, tile_lng)
                alt = tile.getAltitudeFromLatLon(lat_point, lng_point)
                if alt:
                    outfile[lat_i][lng_i] = float(alt)
                    if alt < valley["alt"]:
                        valley["alt"] = alt
                        valley["lat"] = lat_point
                        valley["lng"] = lng_point
                    if alt > peak["alt"]:
                        peak["alt"] = alt
                        peak["lat"] = lat_point
                        peak["lng"] = lng_point
                c = c + 1.0
                if (c % 1000) == 0:
                    percent_complete = (c / total_sample_resolution) * 100.0
                    update_status(percent_complete)
        np.save(cache_file, outfile)

        # compress the color range of the output
        # color_scale = np.log1p(outfile)
        color_compressed = zeros((sample_resolution_lat,
                                  sample_resolution_lng))
        grey_max = 200
        grey_min = 100
        for (x, y), value in np.ndenumerate(outfile):
            # compress colors, found here: http://stackoverflow.com/a/929107
            color_compressed[x][y] = ((
                (value - valley["alt"]) * (grey_max - grey_min)) /
                (peak["alt"] - valley["alt"])) + grey_min
    else:
        outfile = np.load(cache_file)

    #for vmin in range(-100, 200, 100):
    #    for vmax in range(1000, 2500, 500):
    vmin = None
    vmax = None
    ax.imshow(outfile, aspect='normal', interpolation='bilinear',
              cmap=cm.gray, alpha=1.0, norm=None, vmin=vmin, vmax=vmax)
    filename = "%s,%s_%s,%s_%s_%s_%s" % (
        sw_corner["lat"], sw_corner["lng"], ne_corner["lat"],
        ne_corner["lng"], resolution, vmin, vmax)
    print "processing vmin: %s, vmax: %s" % (vmin, vmax)
    fig.savefig("images/merged/%s" % filename)
