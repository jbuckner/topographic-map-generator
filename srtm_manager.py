import os
import math
import json

from pylab import *

from srtm import SRTMDownloader

from util import haversine


class SRTMManager:
    def __init__(self, srtm_format=1):
        self.tile = None
        self.downloader = SRTMDownloader(
            directory="/srtm/version2_1/SRTM%s/" % srtm_format,
            cachedir="cache/srtm%s" % srtm_format)
        self.downloader.loadFileList()

    def get_altitude(self, lat, lon):
        tile_lat = int(math.floor(lat))
        tile_lng = int(math.floor(lon))
        if (not self.tile or
                self.tile.lat != tile_lat or
                self.tile.lon != tile_lng):
            self.tile = self.downloader.getTile(tile_lat, tile_lng)
        alt = self.tile.getAltitudeFromLatLon(lat, lon)
        return alt


class Region:
    def __init__(self, north_lat, east_lng, south_lat, west_lng,
                 resolution=500, base_cache_dir='cache/parsed_data',
                 no_cache=False):
        self.north_lat = north_lat
        self.east_lng = east_lng
        self.south_lat = south_lat
        self.west_lng = west_lng
        self.aspect_ratio = 1.0
        self.peak = {"lat": None, "lng": None, "alt": 0}
        self.valley = {"lat": None, "lng": None, "alt": 32767}
        self.resolution = resolution
        self.cache_dir = None
        self.parsed_data_filepath = None
        self.metadata_filepath = None
        self.outfile = None
        self.distance_ratio = None  # the lng/lat distance ratio of the region

        self._set_cache_filenames(base_cache_dir)
        if no_cache:
            self.parse_region()
        else:
            self._load_cache()

    def _set_cache_filenames(self, base_cache_dir):
        parsed_data_filename = "parsed_data.npy"
        metadata_filename = "metadata.json"

        self.cache_dir = os.path.join(base_cache_dir, "%s,%s_%s,%s_%s" % (
            str(self.south_lat)[0:7], str(self.west_lng)[0:7],
            str(self.north_lat)[0:7], str(self.east_lng)[0:7],
            self.resolution))
        self.parsed_data_filepath = os.path.join(
            self.cache_dir, parsed_data_filename)
        self.metadata_filepath = os.path.join(
            self.cache_dir, metadata_filename)

    def _load_cache(self):
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
        else:
            self.parse_region()

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
            "lat_interval": self.lat_interval
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
        # bad people.
        north_parallel = math.ceil(self.north_lat + 0.0001)
        south_parallel = math.floor(self.north_lat + 0.0001)
        west_meridian = math.ceil(self.east_lng + 0.0001)
        east_meridian = math.floor(self.east_lng + 0.0001)

        lat_distance = haversine(east_meridian, north_parallel,
                                 east_meridian, south_parallel)
        lng_distance = haversine(east_meridian, north_parallel,
                                 west_meridian, north_parallel)

        self.distance_ratio = lng_distance / lat_distance

    def parse_region(self):
        self.lat_delta = abs(self.north_lat - self.south_lat)
        self.lng_delta = abs(self.east_lng - self.west_lng)
        self.aspect_ratio = self.lat_delta / self.lng_delta

        if self.aspect_ratio > 1:
            self.lng_sample_points = self.resolution
            self.lat_sample_points = int(self.resolution / self.aspect_ratio)
        else:
            self.lng_sample_points = int(self.resolution / self.aspect_ratio)
            self.lat_sample_points = self.resolution

        self.lng_interval = self.lng_delta / self.lng_sample_points * 1.0
        self.lat_interval = self.lat_delta / self.lat_sample_points * 1.0

        self._calculate_distance_ratio()

        # numpy initizalizes the vertical as the first argument
        # ie zeros((8, 3)) is 8 tall by 3 wide
        self.outfile = zeros((self.lat_sample_points, self.lng_sample_points))
        srtm = SRTMManager()

        for y in range(1, self.lat_sample_points):
            for x in range(1, self.lng_sample_points):
                sample_lat = self.south_lat + y * self.lat_interval
                sample_lng = self.west_lng + x * self.lng_interval
                alt = srtm.get_altitude(sample_lat, sample_lng)
                #print x, sample_lng, y, sample_lat, alt
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

        self._save_cache()

    def contour(self, contour_delta=50):
        # return a contoured version of the map
        contoured = self.outfile.copy()

        alt_range = self.peak["alt"] - self.valley["alt"]
        steps = math.ceil(alt_range / contour_delta)
        grey_delta = alt_range / steps

        for (x, y), value in np.ndenumerate(contoured):
            countour_interval = math.floor(value / contour_delta)
            new_shade = int(math.floor(countour_interval * grey_delta))
            contoured[x][y] = new_shade

        return contoured
