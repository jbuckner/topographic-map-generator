#!/usr/bin/env python
import os
import argparse

import datetime

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

srtm_format = 1  # 3, 1
srtm_samples = 1201 if srtm_format == 3 else 3601

dpi = 72
width = 40  # inches
output_resolution = {
    'x': width * dpi,
}
img_directory = "images/srtm%s" % srtm_format  # where to save the images


# Bresenham's circle algorithm:
# http://www.daniweb.com/software-development/python/threads/321181/python-bresenham-circle-arc-algorithm#
def circle(radius):
    "Bresenham complete circle algorithm in Python"
    # init vars
    switch = 3 - (2 * radius)
    points = set()
    # first quarter/octant starts clockwise at 12 o'clock
    x = 0
    y = radius
    while x <= y:
        # first quarter first octant
        points.add((x, -y))
        # first quarter 2nd octant
        points.add((y, -x))
        # second quarter 3rd octant
        points.add((y, x))
        # second quarter 4.octant
        points.add((x, y))
        # third quarter 5.octant
        points.add((-x, y))
        # third quarter 6.octant
        points.add((-y, x))
        # fourth quarter 7.octant
        points.add((-y, -x))
        # fourth quarter 8.octant
        points.add((-x, -y))
        if switch < 0:
            switch = switch + (4 * x) + 6
        else:
            switch = switch + (4 * (x - y)) + 10
            y = y - 1
        x = x + 1
    return points


# Bresenham's line algorithm (calculates the pixels between 2 points):
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


def add_pixel(array, x, y, value, thickness=2):
    # this just draws a basic pixel and some surrounding points
    # it has been superceded by the circle drawing

    array[x, y] = value
    # left
    array[x - 1, y] = value
    # right
    array[x + 1, y] = value
    # top
    array[x, y + 1] = value
    # top-right
    array[x + 1, y + 1] = value
    # top-left
    array[x - 1, y + 1] = value
    # bottom
    array[x, y - 1] = value
    # bottom-left
    array[x - 1, y - 1] = value
    # bottom-right
    array[x + 1, y - 1] = value


def get_altitude(lat, lng):
    pass


def update_status(percent):
    """ Update status bar when processing GPX data

    """
    sys.stdout.write("\r%3d%%" % percent)
    sys.stdout.flush()


def contour(matrix, interval=50):
    # break up the map into interval height contour lines
    contoured = matrix.copy()

    min_alt = 999999
    max_alt = 0

    # first run through, we're just getting the min and max altitude
    for (x, y), value in np.ndenumerate(contoured):
        if value > max_alt:
            max_alt = value
        if value < min_alt:
            min_alt = value

    alt_range = max_alt - min_alt
    steps = math.ceil(alt_range / interval)
    grey_delta = 256 / steps  # 256 shades of grey

    print "max_alt: %s, min_alt: %s, alt_range: %s, steps: %s" % (
        max_alt, min_alt, alt_range, steps)

    for (x, y), value in np.ndenumerate(contoured):
        new_shade = math.floor(value / alt_range) * grey_delta
        # if value > 0.0:
        #     print "value: %s, new_shade: %s" % (value, new_shade)
        contoured[x][y] = new_shade

    return contoured

    # compress the color range of the output
    # color_scale = np.log1p(outfile)
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a GPS file.')
    parser.add_argument('--gpx_filename', '-f',
                        help='GPX file for processing')
    parser.add_argument('--overlay_gps', '-g', action='store_true',
                        default=False, help='Overlay GPX file')
    parser.add_argument('--gps_only', '-p', action='store_true',
                        default=False, help='Only show GPS track, no height '
                        'map')
    parser.add_argument('--color_map', '-c', default="gray",
                        help='Colormap to use, defaults to gray')
    parser.add_argument('--resolution', '-r', default="1000",
                        help='Resolution to read SRTM files at')
    parser.add_argument('--thickness', '-t', default="2",
                        help='Line thickness')
    parser.add_argument('--bounds', '-b',
                        help='Map boundaries in the form: sw_lat,sw_lngxne_lat'
                        ',ne_lng for instance -b "37.704467,-122.520905x37.83'
                        '6903,-122.35611"')

    args = parser.parse_args()
    print args

    if not (args.gpx_filename or args.bounds):
        parser.error('You must specify --bounds and/or --gpx_filename.')

    if args.gps_only:
        args.overlay_gps = True
        if not args.gpx_filename:
            parser.error('You must specify --gpx_filename if you specify '
                         'gps_only')

    if args.overlay_gps and not args.gpx_filename:
        parser.error('You must specify --gpx_filename if you specify overlay_'
                     'gps.')

    if args.gpx_filename:
        gpx_filename = args.gpx_filename
        gpx_file = open(gpx_filename, 'r')
        gpx = gpxpy.parse(gpx_file)

    resolution = int(args.resolution)

    # calculate boundaries by either passed boundaries or gpx file
    if args.bounds:
        sw, ne = args.bounds.split('x')
        if sw and ne:
            south_lat, west_lng = sw.split(',')
            north_lat, east_lng = ne.split(',')
            south_lat = float(south_lat)
            north_lat = float(north_lat)
            west_lng = float(west_lng)
            east_lng = float(east_lng)
    elif args.gpx_filename:
        north_lat = -300
        west_lng = 300
        south_lat = 300
        east_lng = -300

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

    print "SW: %s, %s NE: %s, %s" % (south_lat, west_lng, north_lat,
                                     east_lng)

    lat_margin = 0.000833575539568
    lng_margin = 0.000832888

    # add some padding to the view
    sw_corner = {
        'lat': south_lat - lat_margin,
        'lng': west_lng - lng_margin
    }
    ne_corner = {
        'lat': north_lat + lat_margin,
        'lng': east_lng + lng_margin
    }

    # the delta is how far it is from one side to the other of the visible
    # area
    lng_delta = abs(ne_corner['lng'] - sw_corner['lng'])
    lat_delta = abs(ne_corner['lat'] - sw_corner['lat'])
    if lng_delta > lat_delta:
        aspect_ratio = lat_delta / lng_delta
        lat_sample_points = int(resolution * aspect_ratio)
        lng_sample_points = resolution
        height = width * aspect_ratio
    else:
        aspect_ratio = lng_delta / lat_delta
        lat_sample_points = resolution
        lng_sample_points = int(resolution * aspect_ratio)
        height = width / aspect_ratio

    #aspect_ratio = lng_delta / lat_delta

    print ne_corner
    print sw_corner
    print lat_delta, lng_delta, aspect_ratio

    #height = width / aspect_ratio

    print width
    print height

    # sample points is how many sample points we're going to take from each
    # of the lat and lng
    #lng_sample_points = int(resolution * aspect_ratio)
    #lat_sample_points = int(resolution)

    print lng_sample_points
    print lat_sample_points

    # the distance in lat and lng between each sample point
    lng_interval = lng_delta / lng_sample_points * 1.0
    lat_interval = lat_delta / lat_sample_points * 1.0

    total_sample_resolution = lng_sample_points * lat_sample_points

    print total_sample_resolution

    downloader = SRTMDownloader(
        directory="/srtm/version2_1/SRTM%s/" % srtm_format,
        cachedir="cache/srtm%s" % srtm_format)
    downloader.loadFileList()

    pd = None  # processing decision whether to process all or skip all

    highest_peak = {"alt": 0}
    lowest_valley = {"alt": 32767}

    cache_dir = "cache/parsed_data"
    cache_file = "%s/%sx%s_%sx%s_%s.npy" % (
        cache_dir, south_lat, west_lng, north_lat,
        east_lng, resolution)

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

    outfile = zeros((lat_sample_points, lng_sample_points))
    if not args.gps_only:
        if reprocess:
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
                        outfile[(lat_sample_points - lat_i) - 1][lng_i] = \
                            float(alt)
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

            np.save(cache_file, outfile)

            print peak, valley
        else:
            outfile = np.load(cache_file)

    prev_alt = None

    if args.overlay_gps:
        prev_pixel = None
        print "overlaying GPS"
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    p_lat, p_lng = point.latitude, point.longitude

                    tile_lat = int(math.floor(p_lat))
                    tile_lng = int(math.floor(p_lng))
                    if not tile or tile.lat != tile_lat or tile.lon != tile_lng:
                        tile = downloader.getTile(tile_lat, tile_lng)
                    alt = tile.getAltitudeFromLatLon(p_lat, p_lng)

                    if not alt:
                        alt = prev_alt
                    else:
                        prev_alt = alt

                    # we need to get the percentage of the map where the
                    # point is and convert it to number of pixels
                    lat_pt = abs(p_lat - sw_corner['lat'])
                    lng_pt = abs(ne_corner['lng'] - p_lng)

                    if lat_pt < lat_delta and lng_pt < lng_delta:
                        lat_pct = lat_pt / lat_delta
                        lng_pct = lng_pt / lng_delta
                        pixel_lat = int(math.floor(lat_pct *
                                        lat_sample_points))
                        pixel_lng = int(math.floor(lng_pct *
                                        lng_sample_points))

                        # draw a line between the pixels
                        if prev_pixel:
                            coords = bresenham_line(
                                (pixel_lat, pixel_lng),
                                (prev_pixel['lat'], prev_pixel['lng']))
                            for pixel in coords:
                                x, y = pixel

                                pixel_x = lat_sample_points - x + (
                                    lat_margin / 2)
                                pixel_y = lng_sample_points - y + (
                                    lng_margin / 2)

                                # draw a circle at every point
                                circ = circle(int(args.thickness))

                                for point in circ:
                                    x, y = point
                                    outfile[pixel_x + x, pixel_y + y] = alt + 100

                                # add_pixel(outfile, pixel_x, pixel_y, alt +
                                #           50)
                        prev_pixel = {'lat': pixel_lat, 'lng': pixel_lng}

    vmin = None
    vmax = None

    contoured = contour(outfile)

    fig = plt.figure(frameon=False)
    fig.set_size_inches(width, height)
    fig.set_dpi(dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    colormaps = [m for m in cm.datad if not m.endswith("_r")]
    colormap = cm.get_cmap(args.color_map)
    ax.imshow(outfile, aspect='normal', interpolation='bilinear',
              cmap=colormap, alpha=1.0)
    filename = "%s-%s,%s_%s,%s_%s_%s_%s.png" % (
        datetime.datetime.strftime(datetime.datetime.now(), "%y%m%d%H%M%S"),
        sw_corner["lat"], sw_corner["lng"], ne_corner["lat"], ne_corner["lng"],
        resolution, "gps" if args.overlay_gps else "nogps", colormap.name)
    fig.savefig("images/merged/%s" % filename)
