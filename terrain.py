#!/usr/bin/env python
import os

import gpxpy
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt

from pylab import *

from srtm import SRTMDownloader

# SF
# ne_corner = {
#     'lat': 37.836903,
#     'lng': -122.35611
# }
# sw_corner = {
#     'lat': 37.704467,
#     'lng': -122.520905
# }

# Marin
sw_corner = {
    'lat': 37.773429,
    'lng': -122.656174
}
ne_corner = {
    'lat': 37.956651,
    'lng': -122.45224
}

tile_count_lat = abs(sw_corner['lat'] - ne_corner['lat'])
tile_count_lng = abs(sw_corner['lng'] - ne_corner['lng'])

resolution = 500  # numer of samples we take of each hgt in each direction
pixels = resolution * resolution  # for calculating percent complete
divisor = resolution + 1.0  # for calculating the point to sample from

srtm_format = 1  # 3, 1

dpi = 100
width = 40  # inches
height = 40  # inches
output_resolution = {
    'x': width * dpi,
    'y': height * dpi
}
img_directory = "images/srtm%s" % srtm_format  # where to save the images


# Bresenham's line algorithm:
# http://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
# Code from:
# http://snipplr.com/view.php?codeview&id=22482
def bresenham_line((x, y), (x2, y2)):
    """Brensenham line algorithm"""
    steep = 0
    coords = []
    dx = abs(x2 - x)
    sx = 1 if (x2 - x) > 0 else -1
    dy = abs(y2 - y)
    sy = 1 if (y2 - y) > 0 else -1
    if dy > dx:
        steep = 1
        x, y = y, x
        dx, dy = dy, dx
        sx, sy = sy, sx
    d = (2 * dy) - dx
    for i in range(0, dx):
        if steep:
            coords.append((y, x))
        else:
            coords.append((x, y))
        while d >= 0:
            y = y + sy
            d = d - (2 * dx)
        x = x + sx
        d = d + (2 * dy)
    coords.append((x2, y2))
    return coords


def add_pixel(array, x, y, value, thickness=1):
    array[x, y] = value
    array[x + 1, y] = value
    array[x, y + 1] = value
    array[x + 1, y + 1] = value


def update_status(percent):
    sys.stdout.write("\r%3d%%" % percent)
    sys.stdout.flush()


if __name__ == '__main__':
    gpx_file = open('marin.gpx', 'r')

    north_lat = -300
    west_lng = 300
    south_lat = 300
    east_lng = -300

    gpx = gpxpy.parse(gpx_file)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.latitude > north_lat:
                    north_lat = point.latitude
                if point.latitude < south_lat:
                    south_lat = point.latitude
                if point.longitude > east_lng:
                    east_lng = point.longitude
                if point.longitude < west_lng:
                    west_lng = point.longitude

    print "SW: %s, %s NE: %s, %s" % (south_lat, west_lng, north_lat, east_lng)

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
        lat_margin = 0.000733575539568
        lng_margin = 0.000732888

        print lat_margin, lng_margin

        sw_corner = {
            'lat': south_lat - lat_margin,
            'lng': west_lng - lng_margin
        }
        ne_corner = {
            'lat': north_lat + lat_margin,
            'lng': east_lng + lng_margin
        }

        gps_sw_corner = {
            'lat': south_lat,
            'lng': west_lng
        }
        gps_ne_corner = {
            'lat': north_lat,
            'lng': east_lng
        }

        lng_delta = abs(ne_corner['lng'] - sw_corner['lng'])
        lat_delta = abs(ne_corner['lat'] - sw_corner['lat'])
        aspect_ratio = lng_delta / lat_delta
        lng_sample_points = int(resolution * aspect_ratio)
        lat_sample_points = int(resolution)

        lng_interval = lng_delta / lng_sample_points * 1.0
        lat_interval = lat_delta / lat_sample_points * 1.0

        total_sample_resolution = lng_sample_points * lat_sample_points

        print aspect_ratio, lng_delta, lat_delta, lng_interval, lat_interval, lng_sample_points, lat_sample_points, total_sample_resolution

        outfile = zeros((lat_sample_points, lng_sample_points))

        check_point = sw_corner.copy()
        for lat_i in range(0, lat_sample_points):
            for lng_i in range(0, lng_sample_points):
                tile_lat = int(math.floor(check_point['lat']))
                tile_lng = int(math.floor(check_point['lng']))
                if not tile or tile.lat != tile_lat or tile.lon != tile_lng:
                    tile = downloader.getTile(tile_lat, tile_lng)
                alt = tile.getAltitudeFromLatLon(check_point["lat"],
                                                 check_point["lng"])
                if alt:
                    outfile[(lat_sample_points - lat_i) - 1][lng_i] = float(alt)
                    if alt < valley["alt"]:
                        valley["alt"] = alt
                        valley["lat"] = check_point["lat"]
                        valley["lng"] = check_point["lng"]
                    if alt > peak["alt"]:
                        peak["alt"] = alt
                        peak["lat"] = check_point["lat"]
                        peak["lng"] = check_point["lng"]

                check_point["lng"] += lng_interval
                if check_point["lng"] > ne_corner["lng"]:
                    check_point["lng"] = sw_corner["lng"]
                    check_point["lat"] = check_point["lat"] + lat_interval
                c += 1.0
                if (c % 1000) == 0:
                    percent_complete = (c / total_sample_resolution) * 100.0
                    update_status(percent_complete)

        prev_pixel = None
        print "overlaying GPS"
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    p_lat, p_lng = point.latitude, point.longitude

                    # we need to get the percentage of the map where the point is
                    # and convert it to number of pixels
                    lat_pt = abs(p_lat - sw_corner['lat'])
                    lng_pt = abs(p_lng - ne_corner['lng'])
                    lat_pct = lat_pt / lat_delta
                    lng_pct = lng_pt / lng_delta
                    pixel_lat = int(math.floor(lat_pct * lat_sample_points))
                    pixel_lng = int(math.floor(lng_pct * lng_sample_points))

                    #outfile[lat_sample_points - pixel_lat][lng_sample_points - pixel_lng] = peak["alt"] + 100
                    add_pixel(outfile, lat_sample_points - pixel_lat + (lat_margin / 2), lng_sample_points - pixel_lng + (lng_margin / 2), peak["alt"] + 100)
                    if prev_pixel:
                        coords = bresenham_line((pixel_lat, pixel_lng), (prev_pixel['lat'], prev_pixel['lng']))
                        for pixel in coords:
                            x, y = pixel
                            add_pixel(outfile, lat_sample_points - x + (lat_margin / 2), lng_sample_points - y + (lng_margin / 2), peak["alt"] + 100)
                    prev_pixel = {'lat': pixel_lat, 'lng': pixel_lng}

        np.save(cache_file, outfile)

        print peak, valley
    else:
        outfile = np.load(cache_file)

    # compress the color range of the output
    color_scale = np.log1p(outfile)
    # color_compressed = zeros((lat_sample_points,
    #                          lng_sample_points))
    # grey_max = 200
    # grey_min = 100
    # for (x, y), value in np.ndenumerate(outfile):
    #     # compress colors, found here: http://stackoverflow.com/a/929107
    #     color_compressed[x][y] = ((
    #         (value - valley["alt"]) * (grey_max - grey_min)) /
    #         (peak["alt"] - valley["alt"])) + grey_min

    #for vmin in range(-100, 200, 100):
    #    for vmax in range(1000, 2500, 500):
    vmin = None
    vmax = None

    fig = plt.figure(frameon=False)
    fig.set_size_inches(width, height)
    fig.set_dpi(dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    colormaps = [m for m in cm.datad if not m.endswith("_r")]
    colormap = cm.Paired
    ax.imshow(color_scale, aspect='normal', interpolation='bilinear',
              cmap=colormap, alpha=1.0)
    filename = "%s,%s_%s,%s_%s_%s.png" % (
        sw_corner["lat"], sw_corner["lng"], ne_corner["lat"],
        ne_corner["lng"], resolution, colormap.name)
    fig.savefig("images/merged/%s" % filename)
