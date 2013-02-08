#!/usr/bin/env python
import gpxpy
import gpxpy.gpx

# Parsing an existing file:
# -------------------------

gpx_file = open('marin.gpx', 'r')

gpx = gpxpy.parse(gpx_file)

all_points = []

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            all_points.append(point)
            # print 'Point at ({0},{1}) -> {2}'.format(
            #     point.latitude, point.longitude, point.elevation)

print all_points
