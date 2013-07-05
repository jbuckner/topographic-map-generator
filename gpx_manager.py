import os

import gpxpy

from util import haversine


class GPXManager:
    def __init__(self, gpx_filepath):
        if not gpx_filepath:
            raise ValueError("You must provide a path to a gpx file.")

        if not os.path.exists(gpx_filepath):
            raise ValueError("Invalid path to gpx file.")

        gpx_file = open(gpx_filepath, 'r')
        gpx = gpxpy.parse(gpx_file)
        self.gpx = gpx

        self.distance = []
        self.elevation = []

        self.north_lat = -300
        self.west_lng = 300
        self.south_lat = 300
        self.east_lng = -300

        self.parse()

    def _set_bounds(self, point):
        if point.latitude > self.north_lat:
            self.north_lat = point.latitude
        if point.latitude < self.south_lat:
            self.south_lat = point.latitude
        if point.longitude > self.east_lng:
            self.east_lng = point.longitude
        if point.longitude < self.west_lng:
            self.west_lng = point.longitude

    def parse(self):
        # returns ne, sw dictionary: {"ne": (x,y), "sw": (x,y)}

        prev_point = None
        distance = 0

        for track in self.gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    self._set_bounds(point)
                    if prev_point:
                        distance += haversine(
                            prev_point.longitude, prev_point.latitude,
                            point.longitude, point.latitude)
                        self.distance.append(distance)
                    else:
                        self.distance.append(0)
                    self.elevation.append(point.elevation)

                    prev_point = point

    def get_boundaries(self):
        return {'ne': {'lat': self.north_lat, 'lng': self.east_lng},
                'sw': {'lat': self.south_lat, 'lng': self.west_lng}}

    def get_elevation_profile(self):
        import matplotlib.pyplot as plt
        import numpy as np

        from scipy.interpolate import spline, interp1d

        T = np.array(self.distance)
        elevation = np.array(self.elevation)

        #plt.plot(T, elevation)
        #plt.show()

        print T.min(), T.max(), T.size
        print elevation.min(), elevation.max(), elevation.size

        print "linspace"
        xnew = np.linspace(0, T.size - 1, 50)
        print "linspace done"

        print T

        print np.floor(xnew)

        xnewnew = []
        ynewnew = []
        for x in np.floor(xnew):
            print x, T[x], elevation[x]
            xnewnew.append(T[x])
            ynewnew.append(elevation[x])

        #print [T[x] for x in np.floor(xnew)]

        xnew2 = np.array(xnewnew)
        ynew2 = np.array(ynewnew)

        print xnew2

        print "interp1d"
        # f = interp1d(T, elevation)
        print "interp1d complete, starting second"
        f2 = interp1d(T, elevation, kind='cubic')
        print "interp1d 2 complete"

        #elevation_smooth = spline(T, elevation, np.floor(xnew))

        #plt.plot(xnew, elevation_smooth)
        plt.plot(T, elevation, '-', xnew2, f2(xnew2), '-')
        print "plot done"
        #plt.legend(['data', 'linear', 'cubic'], loc='best')
        print "legend done"
        plt.show()
        print "show done"
