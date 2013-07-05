import sys


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


def update_status(percent):
    """ Update status bar

    """
    sys.stdout.write("\r%3d%%" % percent)
    sys.stdout.flush()
