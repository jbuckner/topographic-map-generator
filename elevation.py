#!/usr/bin/env python
import logging
import argparse
import gpxpy

import matplotlib.cm as cm
import matplotlib.pyplot as plt

from pylab import *

from srtm_manager import Region
from gpx_manager import GPXManager

srtm_format = 1

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a GPS file.')
    parser.add_argument('--gpx_filename', '-f',
                        help='GPX file for processing')
    parser.add_argument('--overlay_gps', '-g', action='store_true',
                        default=False, help='Overlay GPX file')
    parser.add_argument('--resolution', '-r', default="500",
                        help='Resolution to read SRTM files at')
    parser.add_argument('--dpi', '-d', default="72",
                        help='DPI of output file')
    parser.add_argument('--width', '-w', default="20",
                        help='Width in inches of output file')
    parser.add_argument('--color_map', '-c', default="gray",
                        help='Colormap to use, defaults to gray')
    parser.add_argument('--contour', '-e', default="-1",
                        help='Elevation in meters of contour lines')
    parser.add_argument('--bounds', '-b',
                        help='Map boundaries in the form: sw_lat,sw_lngxne_lat'
                        ',ne_lng for instance -b "37.704467,-122.520905x37.83'
                        '6903,-122.35611"')
    parser.add_argument('--no_cache', '-n', default=False,
                        action='store_true', help="Don't use cache, always "
                        "reprocess data")
    parser.add_argument('--thickness', '-t', default=2,
                        help='Line thickness for GPS Overlay')

    args = parser.parse_args()

    resolution = int(args.resolution)
    width = int(args.width)  # we will calculate height after the aspect ratio
    dpi = int(args.dpi)
    valley = {"lat": None, "lng": None, "alt": 32767}
    peak = {"lat": None, "lng": None, "alt": 0}

    if not (args.gpx_filename or args.bounds):
        parser.error('You must specify --bounds and/or --gpx_filename.')

    if args.overlay_gps and not args.gpx_filename:
        parser.error('You must specify --gpx_filename if you specify overlay_'
                     'gps.')

    if args.gpx_filename:
        gpx_filename = args.gpx_filename
        gpx_file = open(gpx_filename, 'r')
        gpx = gpxpy.parse(gpx_file)

        g = GPXManager(gpx)

        bounds = g.get_boundaries()

        north_lat = bounds['ne']['lat']
        south_lat = bounds['sw']['lat']
        east_lng = bounds['ne']['lng']
        west_lng = bounds['sw']['lng']

    if args.bounds:
        sw, ne = args.bounds.split('x')
        if sw and ne:
            south_lat, west_lng = sw.split(',')
            north_lat, east_lng = ne.split(',')
            south_lat = float(south_lat)
            north_lat = float(north_lat)
            west_lng = float(west_lng)
            east_lng = float(east_lng)

    region = Region(north_lat, east_lng, south_lat, west_lng,
                    resolution=int(args.resolution), no_cache=args.no_cache)

    contour_filename_suffix = ""
    if int(args.contour) > 0:
        region.contour(int(args.contour))
        contour_filename_suffix = "-contour-%s" % args.contour

    if args.overlay_gps:
        region.overlay_gps(gpx, thickness=int(args.thickness))

    if region.aspect_ratio < 0:
        height = width / region.aspect_ratio
    else:
        height = width * region.aspect_ratio

    height = height / region.distance_ratio  # correct for lng distance diff

    fig = plt.figure(frameon=False)
    fig.set_size_inches(width, height)
    fig.set_dpi(dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    colormaps = [m for m in cm.datad if not m.endswith("_r")]
    colormap = cm.get_cmap(args.color_map)
    ax.imshow(region.outfile, aspect='normal', interpolation='bilinear',
              cmap=colormap, alpha=1.0)

    name_source = ""  # append to filename either the source gpx or the bounds
    if args.gpx_filename:
        name_source = gpx_filename.split('/')[-1]
    else:
        name_source = "%s,%sx%s,%s" % (
            str(south_lat)[0:7], str(west_lng)[0:7],
            str(north_lat)[0:7], str(east_lng)[0:7])

    filename = "%s-%s-%s-%s%s.png" % (
        datetime.datetime.strftime(datetime.datetime.now(),
                                   "%y%m%d%H%M%S"),
        resolution, colormap.name, name_source,
        contour_filename_suffix)
    fig.savefig("images/merged/%s" % filename)