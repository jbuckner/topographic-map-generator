#!/usr/bin/env python

# originally from https://trac.openstreetmap.org/browser/subversion/applications/utils/import/srtm2wayinfo/python/srtm.py

# Pylint: Disable name warnings
# pylint: disable-msg=C0103

"""Load and process SRTM data."""

#import xml.dom.minidom
from HTMLParser import HTMLParser
import ftplib
import httplib
import re
import pickle
import os.path
import os
import zipfile
import array
import math


class NoSuchTileError(Exception):
    """Raised when there is no tile for a region."""
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "No SRTM tile for %d, %d available!" % (self.lat, self.lon)


class WrongTileError(Exception):
    """Raised when the value of a pixel outside the tile area is requested."""
    def __init__(self, tile_lat, tile_lon, req_lat, req_lon):
        self.tile_lat = tile_lat
        self.tile_lon = tile_lon
        self.req_lat = req_lat
        self.req_lon = req_lon

    def __str__(self):
        return "SRTM tile for %d, %d does not contain data for %d, %d!" % (
            self.tile_lat, self.tile_lon, self.req_lat, self.req_lon)


class InvalidTileError(Exception):
    """Raised when the SRTM tile file contains invalid data."""
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return "SRTM tile for %d, %d is invalid!" % (self.lat, self.lon)


class SRTMManager:
    """Automatically download SRTM tiles."""
    def __init__(self, server="dds.cr.usgs.gov",
                 cachedir="cache/srtm",
                 protocol="http",
                 srtm_format=1):
        self.tile_cache = {}

        self.protocol = protocol
        self.server = server

        # directory on remote server to check for SRTM files
        self.directory = "/srtm/version2_1/SRTM%s/" % srtm_format

        # local caching directory
        self.cachedir = cachedir + str(srtm_format)
        if not os.path.exists(cachedir):
            os.mkdir(cachedir)

        self.filelist = {}
        self.filename_regex = re.compile(
            r"([NS])(\d{2})([EW])(\d{3})\.hgt\.zip")
        self.filelist_file = os.path.join(self.cachedir, "filelist_python")

        self.ftpfile = None
        self.ftp_bytes_transfered = 0

    def get_altitude(self, lat, lon):
        tile = self.getTile(lat, lon)
        alt = tile.getAltitudeFromLatLon(lat, lon)
        return alt

    def loadFileList(self):
        """Load a previously created file list or create a new one if none is
            available."""
        try:
            data = open(self.filelist_file, 'rb')
        except IOError:
            print "No cached file list. Creating new one!"
            self.createFileList()
            return
        try:
            self.filelist = pickle.load(data)
        except:
            print "Unknown error loading cached file list. Creating new one!"
            self.createFileList()

    def createFileList(self):
        """SRTM data is split into different directories, get a list of all of
            them and create a dictionary for easy lookup."""
        if self.protocol == "ftp":
            ftp = ftplib.FTP(self.server)
            try:
                ftp.login()
                ftp.cwd(self.directory)
                regions = ftp.nlst()
                for region in regions:
                    print "Downloading file list for", region
                    ftp.cwd(self.directory + "/" + region)
                    files = ftp.nlst()
                    for filename in files:
                        self.filelist[self.parseFilename(filename)] = (
                            region, filename)
            finally:
                ftp.close()
            # Add meta info
            self.filelist["server"] = self.server
            self.filelist["directory"] = self.directory
            with open(self.filelist_file, 'wb') as output:
                pickle.dump(self.filelist, output)
        else:
            self.createFileListHTTP()

    def createFileListHTTP(self):
        """Create a list of the available SRTM files on the server using
        HTTP file transfer protocol (rather than ftp).
        30may2010  GJ ORIGINAL VERSION
        """
        print "createFileListHTTP"
        conn = httplib.HTTPConnection(self.server)
        conn.request("GET", self.directory)
        r1 = conn.getresponse()
        if r1.status == 200:
            print "status200 received ok"
        else:
            print "oh no = status=%d %s" % (r1.status, r1.reason)

        data = r1.read()
        parser = parseHTMLDirectoryListing()
        parser.feed(data)
        regions = parser.getDirListing()
        print regions

        for region in regions:
            print "Downloading file list for", region
            if 'jpg' in region:
                continue
            conn.request("GET", "%s/%s" % (self.directory, region))
            r1 = conn.getresponse()
            if r1.status == 200:
                print "status200 received ok"
            else:
                print "oh no = status=%d %s" % (r1.status, r1.reason)
            data = r1.read()
            parser = parseHTMLDirectoryListing()
            parser.feed(data)
            files = parser.getDirListing()

            for filename in files:
                self.filelist[self.parseFilename(filename)] = (region,
                                                               filename)

            print self.filelist
        # Add meta info
        self.filelist["server"] = self.server
        self.filelist["directory"] = self.directory
        with open(self.filelist_file, 'wb') as output:
            pickle.dump(self.filelist, output)

    def parseFilename(self, filename):
        """Get lat/lon values from filename."""
        match = self.filename_regex.match(filename)
        if match is None:
            # TODO?: Raise exception?
            print "Filename", filename, "unrecognized!"
            return None
        lat = int(match.group(2))
        lon = int(match.group(4))
        if match.group(1) == "S":
            lat = -lat
        if match.group(3) == "W":
            lon = -lon
        return lat, lon

    @staticmethod
    def patched_file_name(lat, lon):
        lat_name = 'N'
        lon_name = 'W'
        if lat < 0:
            lat_name = 'S'
        if lon > 0:
            lon_name = 'E'
        hgt_filename = '%s%s%s%s.patched.hgt' % (lat_name, abs(int(lat)),
                                                 lon_name, abs(int(lon)))
        return hgt_filename

    def getTile(self, lat, lon):
        """Return a tile, first try the cache.
        """
        tile_lat = int(math.floor(lat))
        tile_lon = int(math.floor(lon))

        lat_str = str(tile_lat)
        lon_str = str(tile_lon)

        if lat_str in self.tile_cache:
            if str(lon_str) in self.tile_cache[lat_str]:
                return self.tile_cache[lat_str][lon_str]
        else:
            self.tile_cache[lat_str] = {}

        print "cache miss, fetching %s, %s" % (tile_lat, tile_lon)
        tile = self.fetchTile(tile_lat, tile_lon)
        self.tile_cache[lat_str][lon_str] = tile

        return tile

    def fetchTile(self, lat, lon):
        """Return a Tile by either fetching from disk or downloading.
        If it is a new download, this will also patch the nulls before
        returning the tile.
        """

        # first check for a patched SRTM file (patched nulls)
        patched_filename = self.patched_file_name(lat, lon) + '.zip'
        cached_filepath = os.path.join(self.cachedir, patched_filename)

        srtm_needs_patching = False

        if not os.path.exists(cached_filepath):
            srtm_needs_patching = True
            try:
                region, filename = self.filelist[(int(lat), int(lon))]
            except KeyError:
                raise NoSuchTileError(lat, lon)

            cached_filepath = os.path.join(self.cachedir, filename)

            if not os.path.exists(cached_filepath):
                self.downloadTile(region, filename)

        if srtm_needs_patching:
            srtm_tile = SRTMTile(cached_filepath, int(lat), int(lon))
            srtm_tile.fill_nulls()
            srtm_tile.save_patched_file(cachedir=self.cachedir)
            cached_filepath = os.path.join(self.cachedir, patched_filename)

        return SRTMTile(cached_filepath, int(lat), int(lon))

    def downloadTile(self, region, filename):
        """Download a tile from NASA's server and store it in the cache."""
        if self.protocol == "ftp":
            ftp = ftplib.FTP(self.server)
            try:
                ftp.login()
                ftp.cwd(self.directory + "/" + region)
                # WARNING: This is not thread safe
                self.ftpfile = open(self.cachedir + "/" + filename, 'wb')
                self.ftp_bytes_transfered = 0
                print ""
                try:
                    ftp.retrbinary("RETR " + filename, self.ftpCallback)
                finally:
                    self.ftpfile.close()
                    self.ftpfile = None
            finally:
                ftp.close()
        else:
            #Use HTTP
            conn = httplib.HTTPConnection(self.server)
            conn.set_debuglevel(0)
            filepath = "%s%s%s" % (self.directory, region, filename)
            print "filepath=%s" % filepath
            conn.request("GET", filepath)
            r1 = conn.getresponse()
            if r1.status == 200:
                print "status200 received ok"
                data = r1.read()
                self.ftpfile = open(self.cachedir + "/" + filename, 'wb')
                self.ftpfile.write(data)
                self.ftpfile.close()
                self.ftpfile = None
            else:
                print "oh no = status=%d %s" % (r1.status, r1.reason)

    def ftpCallback(self, data):
        """Called by ftplib when some bytes have been received."""
        self.ftpfile.write(data)
        self.ftp_bytes_transfered += len(data)
        print "\r%d bytes transfered" % self.ftp_bytes_transfered,


class SRTMTile:
    """Base class for all SRTM tiles.
        Each SRTM tile is size x size pixels big and contains
        data for the area from (lat, lon) to (lat+1, lon+1) inclusive.
        This means there is a 1 pixel overlap between tiles. This makes it
        easier for as to interpolate the value, because for every point we
        only have to look at a single tile.
        """
    def __init__(self, f, lat, lon):
        zipf = zipfile.ZipFile(f, 'r')
        names = zipf.namelist()
        if len(names) != 1:
            raise InvalidTileError(lat, lon)
        data = zipf.read(names[0])
        self.size = int(math.sqrt(len(data) / 2))  # 2 bytes per sample
        # Currently only SRTM1/3 is supported
        if self.size not in (1201, 3601):
            raise InvalidTileError(lat, lon)
        self.data = array.array('h', data)
        self.data.byteswap()
        if len(self.data) != self.size * self.size:
            raise InvalidTileError(lat, lon)
        self.lat = lat
        self.lon = lon

    @staticmethod
    def _avg(value1, value2, weight):
        """
        Returns the weighted average of two values and handles the case where
        one value is None. If both values are None, None is returned.
        """
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        return value2 * weight + value1 * (1 - weight)

    def calcOffset(self, x, y):
        """Calculate offset into data array. Only uses to test correctness
            of the formula."""
        # Datalayout
        # X = longitude
        # Y = latitude
        # Sample for size 1201x1201
        #  (   0/1200)     (   1/1200)  ...    (1199/1200)    (1200/1200)
        #  (   0/1199)     (   1/1199)  ...    (1199/1199)    (1200/1199)
        #       ...            ...                 ...             ...
        #  (   0/   1)     (   1/   1)  ...    (1199/   1)    (1200/   1)
        #  (   0/   0)     (   1/   0)  ...    (1199/   0)    (1200/   0)
        #  Some offsets:
        #  (0/1200)     0
        #  (1200/1200)  1200
        #  (0/1199)     1201
        #  (1200/1199)  2401
        #  (0/0)        1201*1200
        #  (1200/0)     1201*1201-1
        return x + self.size * (self.size - y - 1)

    def getPixelValue(self, x, y):
        """Get the value of a pixel from the data, handling voids in the
            SRTM data."""
        assert x < self.size, "x: %d<%d" % (x, self.size)
        assert y < self.size, "y: %d<%d" % (y, self.size)
        # Same as calcOffset, inlined for performance reasons
        offset = x + self.size * (self.size - y - 1)
        #print offset
        value = self.data[offset]
        if value == -32768:
            return None  # -32768 is a special value for areas with no data
        return value

    def getPixelAverage(self, x, y):
        x_int = int(x)
        y_int = int(y)

        if x_int < 0:
            x_int = 0
        if x_int >= self.size:
            x_int = self.size - 1
        if y_int < 0:
            y_int = 0
        if y_int >= self.size:
            y_int = self.size - 1

        x_frac = x - x_int
        y_frac = y - y_int

        # if x_frac > 0 or y_frac > 0:
        #     print "x, y, frac", x, y, x_int, x_frac, y_int, y_frac

        x_offset = x_int + 1 if x_int + 1 < self.size else x_int
        y_offset = y_int + 1 if y_int + 1 < self.size else y_int

        value00 = self.getPixelValue(x_int, y_int)
        value10 = self.getPixelValue(x_offset, y_int)
        value01 = self.getPixelValue(x_int, y_offset)
        value11 = self.getPixelValue(x_offset, y_offset)

        value1 = self._avg(value00, value10, x_frac)
        value2 = self._avg(value01, value11, x_frac)
        value = self._avg(value1, value2, y_frac)

        # print value

        # print "%4d %4d | %4d\n%4d %4d | %4d\n-------------\n%4d" % (
        #      value00, value10, value1, value01, value11, value2, value)

        return value

    def getAltitudeFromLatLon(self, lat, lon):
        """Get the altitude of a lat lon pair, using the four neighbouring
            pixels for interpolation.
        """
        # print "-----\nFromLatLon", lon, lat
        lat -= self.lat
        lon -= self.lon
        if lat < 0.0 or lat >= 1.0 or lon < 0.0 or lon >= 1.0:
            raise WrongTileError(self.lat, self.lon,
                                 self.lat + lat, self.lon + lon)
        x = lon * (self.size - 1)
        y = lat * (self.size - 1)

        return self.getPixelAverage(x, y)

    def interpolate(self, x, y, dist=1):
        """Retun a pixel value as a weighted average of the surrounding pixels.
        This is brute force right now. Need to algorithm this shit.
        dist is the distance from the target pixel for the average to be
        calculated

        tl2      t2      tr2
            tl1  t1  tr1
        l2  l1   **  r1  r2
            bl1  b1  br1
        bl2      b2      br2

        5 5 5 5 5
        5 6 6 6 5
        4 5 * 5 4
        4 4 3 4 3
        3 4 4 4 4
        """

        # bottom row
        bl1 = self.getPixelAverage(x - 1, y - 1)
        bl2 = self.getPixelAverage(x - dist, y - dist)
        b1 = self.getPixelAverage(x, y - 1)
        b2 = self.getPixelAverage(x, y - dist)
        br1 = self.getPixelAverage(x + 1, y - 1)
        br2 = self.getPixelAverage(x + dist, y - dist)

        # left and right
        l1 = self.getPixelAverage(x - 1, y)
        l2 = self.getPixelAverage(x - dist, y)
        r1 = self.getPixelAverage(x + 1, y)
        r2 = self.getPixelAverage(x + dist, y)

        # top row
        tl1 = self.getPixelAverage(x - 1, y + 1)
        tl2 = self.getPixelAverage(x - dist, y + dist)
        t1 = self.getPixelAverage(x, y + 1)
        t2 = self.getPixelAverage(x, y + dist)
        tr1 = self.getPixelAverage(x + 1, y + 1)
        tr2 = self.getPixelAverage(x + dist, y + dist)

        vectors = []

        # we are appending the next guess for the middle number from each angle
        # so if b1 = 3 and b2 = 4, the next number should be lower, so we have
        # b1 - b2 = -1
        # b1 + (b1 - b2) = 2 (this is the same as b1 * 2 - b2)
        # we append the 2
        # once we have an estimate from every angle, we just average that
        if bl1 is not None and bl2 is not None:
            vectors.append(bl1 * 2 - bl2)
        if b1 is not None and b2 is not None:
            vectors.append(b1 * 2 - b2)
        if br1 is not None and br2 is not None:
            vectors.append(br1 * 2 - br2)
        if l1 is not None and l2 is not None:
            vectors.append(l1 * 2 - l2)
        if r1 is not None and r2 is not None:
            vectors.append(r1 * 2 - r2)
        if tl1 is not None and tl2 is not None:
            vectors.append(tl1 * 2 - tl2)
        if t1 is not None and t2 is not None:
            vectors.append(t1 * 2 - t2)
        if tr1 is not None and tr2 is not None:
            vectors.append(tr1 * 2 - tr2)

        try:
            average = float(sum(vectors)) / float(len(vectors))
        except:
            average = 0

        # TODO:
        # I don't like this at all. I'm not sure why it's working, but it's
        # working. I think I might need to find standard deviation of the
        # tile and filter out the anomolies from that instead of 10000 and -1
        if average > 10000:
            average = None
        if average < -1:
            average = None

        return average

    def fill_nulls(self):
        print "filling nulls"
        for x in range(self.size):
            for y in range(self.size):
                pixel_value = self.getPixelValue(x, y)
                if pixel_value is None:
                    # Same as calcOffset, inlined for performance reasons
                    offset = x + self.size * (self.size - y - 1)

                    interpolated_value = self.interpolate(x, y)

                    if interpolated_value is not None:
                        self.data[offset] = int(interpolated_value)
        print "finished filling nulls"

    @property
    def patched_filename(self):
        lat_name = 'N'
        lon_name = 'W'
        if self.lat < 0:
            lat_name = 'S'
        if self.lon > 0:
            lon_name = 'E'
        hgt_filename = '%s%s%s%s.patched.hgt' % (lat_name, abs(int(self.lat)),
                                                 lon_name, abs(int(self.lon)))
        return hgt_filename

    def save_patched_file(self, cachedir):
        try:
            import zlib
            compression = zipfile.ZIP_DEFLATED
        except:
            compression = zipfile.ZIP_STORED

        patched_filepath = os.path.join(cachedir, self.patched_filename)

        patched_file = open(patched_filepath, 'w')
        self.data.byteswap()
        self.data.tofile(patched_file)
        patched_file.close()
        self.data.byteswap()

        zipped_file = zipfile.ZipFile(patched_filepath + ".zip", 'w')
        zipped_file.write(patched_filepath, compress_type=compression)
        zipped_file.close()

        os.remove(patched_filepath)


class parseHTMLDirectoryListing(HTMLParser):

    def __init__(self):
        #print "parseHTMLDirectoryListing.__init__"
        HTMLParser.__init__(self)
        self.title = "Undefined"
        self.isDirListing = False
        self.dirList = []
        self.inTitle = False
        self.inHyperLink = False
        self.currAttrs = ""
        self.currHref = ""

    def handle_starttag(self, tag, attrs):
        #print "Encountered the beginning of a %s tag" % tag
        if tag == "title":
            self.inTitle = True
        if tag == "a":
            self.inHyperLink = True
            self.currAttrs = attrs
            for attr in attrs:
                if attr[0] == 'href':
                    self.currHref = attr[1]

    def handle_endtag(self, tag):
        #print "Encountered the end of a %s tag" % tag
        if tag == "title":
            self.inTitle = False
        if tag == "a":
            # This is to avoid us adding the parent directory to the list.
            if self.currHref != "":
                self.dirList.append(self.currHref)
            self.currAttrs = ""
            self.currHref = ""
            self.inHyperLink = False

    def handle_data(self, data):
        if self.inTitle:
            self.title = data
            print "title=%s" % data
            if "Index of" in self.title:
                #print "it is an index!!!!"
                self.isDirListing = True
        if self.inHyperLink:
            # We do not include parent directory in listing.
            if "Parent Directory" in data:
                self.currHref = ""

    def getDirListing(self):
        return self.dirList

#DEBUG ONLY
if __name__ == '__main__':
    srtm_format = 3
    downloader = SRTMManager(
        directory="/srtm/version2_1/SRTM%s/" % srtm_format,
        cachedir="cache/srtm%s" % srtm_format)
    downloader.loadFileList()
    tile = downloader.getTile(37, -123)
    tile.fill_nulls()
    tile.save_to_file()
    # print tile.getAltitudeFromLatLon(49.1234, 12.56789)
