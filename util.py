import math

from pylab import *


# Bresenham's circle algorithm:
# http://www.daniweb.com/software-development/python/threads/321181/python-bresenham-circle-arc-algorithm#
# Returns set of points of the circle [(x,y),(x,y)...]
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
# Returns list of coords [(x,y),(x,y)...]
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


def overlay_gps(region, gpx, srtm_format=1):
    from srtm_manager import SRTMManager

    s = SRTMManager(srtm_format)

    gpx_overlay = region.outfile.copy()

    prev_pixel = None
    prev_alt = 0

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                p_lat, p_lng = point.latitude, point.longitude

                alt = s.get_altitude(p_lat, p_lng)

                if not alt:
                    alt = prev_alt
                else:
                    prev_alt = alt

                # we need to get the percentage of the map where the
                # point is and convert it to number of pixels
                lat_pt = abs(p_lat - region.south_lat)
                lng_pt = abs(region.east_lng - p_lng)

                if lat_pt < region.lat_delta and lng_pt < region.lng_delta:
                    lat_pct = lat_pt / region.lat_delta
                    lng_pct = lng_pt / region.lng_delta
                    pixel_lat = int(math.floor(lat_pct *
                                    region.lat_sample_points))
                    pixel_lng = int(math.floor(lng_pct *
                                    region.lng_sample_points))

                    # draw a line between the pixels
                    if prev_pixel:
                        coords = bresenham_line(
                            (pixel_lat, pixel_lng),
                            (prev_pixel['lat'], prev_pixel['lng']))
                        for pixel in coords:
                            x, y = pixel

                            pixel_x = region.lat_sample_points - x  # + (
                                #lat_margin / 2)
                            pixel_y = region.lng_sample_points - y  # + (
                                #lng_margin / 2)

                            # draw a circle at every point
                            circ = circle(int(4))

                            # print region.lng_sample_points, region.lat_sample_points

                            for point in circ:
                                x, y = point
                                circle_x = pixel_x + x
                                circle_y = pixel_y + y
                                #print circle_x, circle_y
                                if circle_x >= region.lng_sample_points:
                                    circle_x = region.lng_sample_points - 1
                                if circle_y >= region.lat_sample_points:
                                    circle_y = region.lat_sample_points - 1
                                #print circle_x, circle_y
                                gpx_overlay[circle_x, circle_y] = alt + 100

                    prev_pixel = {'lat': pixel_lat, 'lng': pixel_lng}

    return gpx_overlay


# http://stackoverflow.com/a/14034507/1145332
def get_xy(lat, lng, map_width, map_height):
    x = ((lng + 180) * (map_width / 360))
    y = (((lat * -1) + 90) * (map_width / 180))
    return x, y


# http://stackoverflow.com/a/4913653/1145332
# haversine formula for calculating distances between 2 coordinates
def haversine(lng1, lat1, lng2, lat2):
    from math import radians, cos, sin, asin, sqrt
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    # haversine formula
    dlon = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km
