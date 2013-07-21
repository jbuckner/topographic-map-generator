import os
import math
import json

from pylab import *

from srtm import SRTMManager

from util import haversine, bresenham_line, circle, update_status


class Region:
    def __init__(self, north_lat, east_lng, south_lat, west_lng,
                 resolution=500, base_cache_dir='cache/parsed_data',
                 no_cache=False, padding_pct=20, srtm_format=1,
                 patch_mode='auto', auto_parse=True):
        self.north_lat = north_lat
        self.east_lng = east_lng
        self.south_lat = south_lat
        self.west_lng = west_lng
        self.padding_pct = float(padding_pct)

        self._calculate_aspect_ratio()
        self._add_coordinate_padding()

        self.peak = {"lat": None, "lng": None, "alt": 0}
        self.valley = {"lat": None, "lng": None, "alt": 32767}
        self.resolution = resolution
        self.cache_dir = None
        self.parsed_data_filepath = None
        self.metadata_filepath = None
        self.outfile = None
        self.distance_ratio = 1.0  # the lng/lat distance ratio of the region
        self.no_cache = no_cache
        self.midpoint = {"lat": None, "lng": None}
        self.lat_km = 0
        self.lng_km = 0

        self.srtm_format = srtm_format
        self.patch_mode = patch_mode

        self._set_cache_filenames(base_cache_dir)
        self._setup_outfile()
        if auto_parse:
            if self.no_cache:
                self.overlay_map()
            else:
                self._load_cache()

    def _set_cache_filenames(self, base_cache_dir):
        parsed_data_filename = "parsed_data.npy"
        metadata_filename = "metadata.json"

        patch_mode_filename = ''

        if self.patch_mode not in ['auto', 'reprocess']:
            patch_mode_filename = '_patch_%s' % str(self.patch_mode)

        self.cache_dir = os.path.join(
            base_cache_dir, "%s,%s_%s,%s_%s_srtm%s%s" % (
                str(self.south_lat)[0:7], str(self.west_lng)[0:7],
                str(self.north_lat)[0:7], str(self.east_lng)[0:7],
                self.resolution, str(self.srtm_format), patch_mode_filename))
        self.parsed_data_filepath = os.path.join(
            self.cache_dir, parsed_data_filename)
        self.metadata_filepath = os.path.join(
            self.cache_dir, metadata_filename)

    def _save_cache(self):
        try:
            os.makedirs(self.cache_dir)
        except:
            pass

        metadata = {
            "north_lat": self.north_lat,
            "east_lng": self.east_lng,
            "south_lat": self.south_lat,
            "west_lng": self.west_lng,
            "peak": self.peak,
            "valley": self.valley,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "distance_ratio": self.distance_ratio,
            "lat_delta": self.lat_delta,
            "lng_delta": self.lng_delta,
            "lng_sample_points": self.lng_sample_points,
            "lat_sample_points": self.lat_sample_points,
            "lng_interval": self.lng_interval,
            "lat_interval": self.lat_interval,
            "midpoint": self.midpoint,
            "lat_km": self.lat_km,
            "lng_km": self.lng_km,
            "padding_pct": self.padding_pct,
            "padding": self.padding
        }
        f = open(self.metadata_filepath, 'w')
        f.write(json.dumps(metadata))
        f.close()
        np.save(self.parsed_data_filepath, self.outfile)

    def _calculate_distance_ratio(self):
        # Latitude is a fairly consistent ~111km per parallel, whereas
        # longitude distance changes with latitude. This approximates
        # the lng/lat ratio at the closest parallel and meridian lines.

        # In case a whole number is passed in, we offset it by 0.0001 so we
        # can get a proper ceil and floor.
        # Yes, someone could pass in 73.0009 and ruin everything, but they are
        # bad people. Okay, maybe they're not bad people, I just don't want to
        # check for this right now
        north_parallel = math.ceil(self.north_lat + 0.0001)
        south_parallel = math.floor(self.north_lat + 0.0001)
        west_meridian = math.ceil(self.east_lng + 0.0001)
        east_meridian = math.floor(self.east_lng + 0.0001)

        lat_distance = haversine(east_meridian, north_parallel,
                                 east_meridian, south_parallel)
        lng_distance = haversine(east_meridian, north_parallel,
                                 west_meridian, north_parallel)

        self.distance_ratio = lng_distance / lat_distance
        return self.distance_ratio

    def _calculate_aspect_ratio(self):
        self.lat_delta = abs(self.north_lat - self.south_lat)
        self.lng_delta = abs(self.east_lng - self.west_lng)
        self.aspect_ratio = self.lat_delta / self.lng_delta
        return self.aspect_ratio

    def _calculate_area_size(self):
        half_lat = (self.north_lat - self.south_lat) / 2
        half_lng = (self.west_lng - self.east_lng) / 2

        self.midpoint = {
            "lat": self.south_lat + half_lat,
            "lng": self.east_lng + half_lng
        }

        self.lat_km = haversine(self.midpoint["lng"], self.north_lat,
                                self.midpoint["lng"], self.south_lat)
        self.lng_km = haversine(self.west_lng, self.midpoint["lat"],
                                self.east_lng, self.midpoint["lat"])
        return self.lat_km, self.lng_km

    def _add_coordinate_padding(self):
        if self.lat_delta < self.lng_delta:
            self.padding = self.lat_delta * (self.padding_pct / 100.0)
        else:
            self.padding = self.lng_delta * (self.padding_pct / 100.0)

        self.north_lat = self.north_lat + (self.padding / 2.0)
        self.south_lat = self.south_lat - (self.padding / 2.0)
        self.west_lng = self.west_lng - (self.padding / 2.0)
        self.east_lng = self.east_lng + (self.padding / 2.0)

        self._calculate_aspect_ratio()
        return self.padding

    def _setup_outfile(self):
        # an aspect ratio greater than 1 means it's wider than it is tall
        if self.aspect_ratio > 1:
            self.lng_sample_points = self.resolution
            self.lat_sample_points = int(self.resolution / self.aspect_ratio)
        else:
            self.lng_sample_points = int(self.resolution / self.aspect_ratio)
            self.lat_sample_points = self.resolution

        self.lng_interval = self.lng_delta / self.lng_sample_points * 1.0
        self.lat_interval = self.lat_delta / self.lat_sample_points * 1.0

        self._calculate_distance_ratio()
        self._calculate_area_size()

        # numpy initizalizes the vertical as the first argument
        # ie zeros((8, 3)) is 8 tall by 3 wide
        self.outfile = zeros((self.lat_sample_points, self.lng_sample_points))

    def _overlay_map(self):
        print "\overlaying relief map\n"

        srtm = SRTMManager(srtm_format=self.srtm_format,
                           patch_mode=self.patch_mode)

        c = 0  # just a counter to track completion
        total_samples = self.lng_sample_points * self.lat_sample_points

        for y in range(1, self.lat_sample_points):
            for x in range(1, self.lng_sample_points):
                sample_lat = self.south_lat + y * self.lat_interval
                sample_lng = self.west_lng + x * self.lng_interval
                alt = srtm.get_altitude(sample_lat, sample_lng)
                if alt:
                    if alt < self.valley["alt"]:
                        self.valley["alt"] = alt
                        self.valley["lat"] = sample_lat
                        self.valley["lng"] = sample_lng
                    if alt > self.peak["alt"]:
                        self.peak["alt"] = alt
                        self.peak["lat"] = sample_lat
                        self.peak["lng"] = sample_lng
                    self.outfile[self.lat_sample_points - y][x] = alt
                c += 1.0
                if (c % 1000) == 0:
                    percent_complete = (c / total_samples) * 100.0
                    update_status(percent_complete)
        self._save_cache()

    def contour(self, contour_delta=50):
        print "\ncontouring\n"
        contoured_data_filepath = os.path.join(
            self.cache_dir, 'contour-%s.npy' % contour_delta)

        if self.no_cache or not os.path.exists(contoured_data_filepath):
            alt_range = self.peak["alt"] - self.valley["alt"]
            steps = math.ceil(alt_range / contour_delta)
            grey_delta = alt_range / steps

            for (x, y), value in np.ndenumerate(self.outfile):
                countour_interval = math.floor(value / contour_delta)
                new_shade = int(math.floor(countour_interval * grey_delta))
                self.outfile[x][y] = new_shade
            np.save(contoured_data_filepath, self.outfile)
        else:
            self.outfile = np.load(contoured_data_filepath)

    def median_filter(self, kernel_size=3):
        from scipy import signal

        self.outfile = signal.medfilt2d(self.outfile, kernel_size=kernel_size)

    def overlay_map(self):
        if os.path.exists(self.cache_dir):
            self.outfile = np.load(self.parsed_data_filepath)

            f = open(self.metadata_filepath, 'r')
            metadata = json.loads(f.read())
            f.close()

            self.north_lat = metadata["north_lat"]
            self.east_lng = metadata["east_lng"]
            self.south_lat = metadata["south_lat"]
            self.west_lng = metadata["west_lng"]
            self.peak = metadata["peak"]
            self.valley = metadata["valley"]
            self.resolution = metadata["resolution"]
            self.aspect_ratio = metadata["aspect_ratio"]
            self.distance_ratio = metadata["distance_ratio"]
            self.lat_delta = metadata["lat_delta"]
            self.lng_delta = metadata["lng_delta"]
            self.lng_sample_points = metadata["lng_sample_points"]
            self.lat_sample_points = metadata["lat_sample_points"]
            self.lng_interval = metadata["lng_interval"]
            self.lat_interval = metadata["lat_interval"]
            self.midpoint = metadata["midpoint"]
            self.lat_km = metadata["lat_km"]
            self.lng_km = metadata["lng_km"]
            self.padding_pct = metadata["padding_pct"]
            self.padding = metadata["padding"]
        else:
            self._overlay_map()

    def overlay_gps(self, gpx, thickness=2, elevation_delta=20):
        print "\noverlaying gps\n"
        srtm = SRTMManager(srtm_format=self.srtm_format,
                           patch_mode=self.patch_mode)

        prev_pixel = None
        prev_alt = 0

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    p_lat, p_lng = point.latitude, point.longitude

                    alt = srtm.get_altitude(p_lat, p_lng)

                    if not alt:
                        alt = prev_alt
                    else:
                        prev_alt = alt

                    # we need to get the percentage of the map where the
                    # point is and convert it to number of pixels
                    lat_pt = abs(p_lat - self.south_lat)
                    lng_pt = abs(self.east_lng - p_lng)

                    if lat_pt < self.lat_delta and lng_pt < self.lng_delta:
                        lat_pct = lat_pt / self.lat_delta
                        lng_pct = lng_pt / self.lng_delta
                        pixel_lat = int(math.floor(lat_pct *
                                        self.lat_sample_points))
                        pixel_lng = int(math.floor(lng_pct *
                                        self.lng_sample_points))

                        # draw a line between the pixels
                        if prev_pixel:
                            coords = bresenham_line(
                                (pixel_lat, pixel_lng),
                                (prev_pixel['lat'], prev_pixel['lng']))
                            for pixel in coords:
                                x, y = pixel

                                pixel_y = self.lat_sample_points - x
                                pixel_x = self.lng_sample_points - y

                                # draw a circle at every point
                                circ = circle(int(thickness))

                                for point in circ:
                                    x, y = point
                                    circ_x = pixel_x + x
                                    circ_y = pixel_y + y
                                    if circ_x >= self.lng_sample_points:
                                        circ_x = self.lng_sample_points - 1
                                    if circ_y >= self.lat_sample_points:
                                        circ_y = self.lat_sample_points - 1
                                    self.outfile[circ_y, circ_x] = alt + \
                                        int(elevation_delta)

                        prev_pixel = {'lat': pixel_lat, 'lng': pixel_lng}
