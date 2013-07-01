# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  Latitude/longitude spherical geodesy formulae & scripts (c) Chris Veness 2002-2012
#   - www.movable-type.co.uk/scripts/latlong.html
#
#  Sample usage:
#    p1 = new LatLon(51.5136, -0.0983)
#    p2 = new LatLon(51.4778, -0.0015)
#    dist = p1.distanceTo(p2)          # in km
#    brng = p1.bearingTo(p2)           # in degrees clockwise from north
#    ... etc
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  Note that minimal error checking is performed in this example code!
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import math



# Creates a point on the earth's surface at the supplied latitude / longitude
#
# @constructor
# @param {Number} lat: latitude in numeric degrees
# @param {Number} lon: longitude in numeric degrees
# @param {Number} [rad=6371]: radius of earth if different value is required from standard 6,371km
class LatLon:
    def __init__(self, lat, lon, rad=6371):
        # only accept numbers or valid numeric strings
        self._lat = lat
        self._lon = lon
        self._radius = rad

    # Returns the distance from this point to the supplied point, in km
    # (using Haversine formula)
    #
    # from: Haversine formula - R. W. Sinnott, "Virtues of the Haversine",
    #       Sky and Telescope, vol 68, no 2, 1984
    #
    # @param   {LatLon} point: Latitude/longitude of destination point
    # @param   {Number} [precision=4]: no of significant digits to use for returned value
    # @returns {Number} Distance in km between this point and destination points
    def distance_to(point, precision=4):
        # default 4 sig figs reflects typical 0.3% accuracy of spherical model
        R = self._radius
        lat1 = self._lat.toRad(), lon1 = self._lon.toRad()
        lat2 = point._lat.toRad(), lon2 = point._lon.toRad()
        dLat = lat2 - lat1
        dLon = lon2 - lon1

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1) *
            math.cos(lat2) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c
        return d.toPrecisionFixed(precision)

    # Returns the (initial) bearing from this point to the supplied point, in degrees
    #   see http://williams.best.vwh.net/avform.htm#Crs
    #
    # @param   {LatLon} point: Latitude/longitude of destination point
    # @returns {Number} Initial bearing in degrees from North
    def bearingTo = function(point:
        lat1 = self._lat.toRad(), lat2 = point._lat.toRad()
        dLon = (point._lon-self._lon).toRad()

        y = math.sin(dLon) * math.cos(lat2)
        x = math.cos(lat1)*math.sin(lat2) -
                math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
        brng = math.atan2(y, x)

        return (brng.toDeg()+360) % 360



    /**
     * Returns final bearing arriving at supplied destination point from this point the final bearing
     * will differ from the initial bearing by varying degrees according to distance and latitude
     *
     * @param   {LatLon} point: Latitude/longitude of destination point
     * @returns {Number} Final bearing in degrees from North
     */
    def finalBearingTo = function(point:
      # get initial bearing from supplied point back to this point...
      lat1 = point._lat.toRad(), lat2 = self._lat.toRad()
      dLon = (self._lon-point._lon).toRad()

      y = math.sin(dLon) * math.cos(lat2)
      x = math.cos(lat1)*math.sin(lat2) -
              math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
      brng = math.atan2(y, x)

      # ... & reverse it by adding 180°
      return (brng.toDeg()+180) % 360
    }


    /**
     * Returns the midpoint between this point and the supplied point.
     *   see http://mathforum.org/library/drmath/view/51822.html for derivation
     *
     * @param   {LatLon} point: Latitude/longitude of destination point
     * @returns {LatLon} Midpoint between this point and the supplied point
     */
    def midpointTo = function(point:
      lat1 = self._lat.toRad(), lon1 = self._lon.toRad()
      lat2 = point._lat.toRad()
      dLon = (point._lon-self._lon).toRad()

      Bx = math.cos(lat2) * math.cos(dLon)
      By = math.cos(lat2) * math.sin(dLon)

      lat3 = math.atan2(math.sin(lat1)+math.sin(lat2),
                        math.sqrt( (math.cos(lat1)+Bx)*(math.cos(lat1)+Bx) + By*By) )
      lon3 = lon1 + math.atan2(By, math.cos(lat1) + Bx)
      lon3 = (lon3+3*math.PI) % (2*math.PI) - math.PI  # normalise to -180..+180º

      return new LatLon(lat3.toDeg(), lon3.toDeg())
    }


    /**
     * Returns the destination point from this point having travelled the given distance (in km) on the
     * given initial bearing (bearing may vary before destination is reached)
     *
     *   see http://williams.best.vwh.net/avform.htm#LL
     *
     * @param   {Number} brng: Initial bearing in degrees
     * @param   {Number} dist: Distance in km
     * @returns {LatLon} Destination point
     */
    def destinationPoint = function(brng, dist:
      dist = typeof(dist)=='number' ? dist : typeof(dist)=='string' && dist.trim()!='' ? +dist : NaN
      dist = dist/self._radius  # convert dist to angular distance in radians
      brng = brng.toRad()  //
      lat1 = self._lat.toRad(), lon1 = self._lon.toRad()

      lat2 = math.asin( math.sin(lat1)*math.cos(dist) +
                            math.cos(lat1)*math.sin(dist)*math.cos(brng) )
      lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(dist)*math.cos(lat1),
                                   math.cos(dist)-math.sin(lat1)*math.sin(lat2))
      lon2 = (lon2+3*math.PI) % (2*math.PI) - math.PI  # normalise to -180..+180º

      return new LatLon(lat2.toDeg(), lon2.toDeg())
    }


    /**
     * Returns the point of intersection of two paths defined by point and bearing
     *
     *   see http://williams.best.vwh.net/avform.htm#Intersection
     *
     * @param   {LatLon} p1: First point
     * @param   {Number} brng1: Initial bearing from first point
     * @param   {LatLon} p2: Second point
     * @param   {Number} brng2: Initial bearing from second point
     * @returns {LatLon} Destination point (null if no unique intersection defined)
     */
    LatLon.intersection = function(p1, brng1, p2, brng2:
      brng1 = typeof brng1 == 'number' ? brng1 : typeof brng1 == 'string' && trim(brng1)!='' ? +brng1 : NaN
      brng2 = typeof brng2 == 'number' ? brng2 : typeof brng2 == 'string' && trim(brng2)!='' ? +brng2 : NaN
      lat1 = p1._lat.toRad(), lon1 = p1._lon.toRad()
      lat2 = p2._lat.toRad(), lon2 = p2._lon.toRad()
      brng13 = brng1.toRad(), brng23 = brng2.toRad()
      dLat = lat2-lat1, dLon = lon2-lon1

      dist12 = 2*math.asin( math.sqrt( math.sin(dLat/2)*math.sin(dLat/2) +
        math.cos(lat1)*math.cos(lat2)*math.sin(dLon/2)*math.sin(dLon/2) ) )
      if (dist12 == 0) return null

      # initial/final bearings between points
      brngA = math.acos( ( math.sin(lat2) - math.sin(lat1)*math.cos(dist12) ) /
        ( math.sin(dist12)*math.cos(lat1) ) )
      if (isNaN(brngA)) brngA = 0  # protect against rounding
      brngB = math.acos( ( math.sin(lat1) - math.sin(lat2)*math.cos(dist12) ) /
        ( math.sin(dist12)*math.cos(lat2) ) )

      if (math.sin(lon2-lon1) > 0:
        brng12 = brngA
        brng21 = 2*math.PI - brngB
      } else {
        brng12 = 2*math.PI - brngA
        brng21 = brngB
      }

      alpha1 = (brng13 - brng12 + math.PI) % (2*math.PI) - math.PI  # angle 2-1-3
      alpha2 = (brng21 - brng23 + math.PI) % (2*math.PI) - math.PI  # angle 1-2-3

      if (math.sin(alpha1)==0 && math.sin(alpha2)==0) return null  # infinite intersections
      if (math.sin(alpha1)*math.sin(alpha2) < 0) return null       # ambiguous intersection

      //alpha1 = math.abs(alpha1)
      //alpha2 = math.abs(alpha2)
      # ... Ed Williams takes abs of alpha1/alpha2, but seems to break calculation?

      alpha3 = math.acos( -math.cos(alpha1)*math.cos(alpha2) +
                           math.sin(alpha1)*math.sin(alpha2)*math.cos(dist12) )
      dist13 = math.atan2( math.sin(dist12)*math.sin(alpha1)*math.sin(alpha2),
                           math.cos(alpha2)+math.cos(alpha1)*math.cos(alpha3) )
      lat3 = math.asin( math.sin(lat1)*math.cos(dist13) +
                        math.cos(lat1)*math.sin(dist13)*math.cos(brng13) )
      dLon13 = math.atan2( math.sin(brng13)*math.sin(dist13)*math.cos(lat1),
                           math.cos(dist13)-math.sin(lat1)*math.sin(lat3) )
      lon3 = lon1+dLon13
      lon3 = (lon3+3*math.PI) % (2*math.PI) - math.PI  # normalise to -180..+180º

      return new LatLon(lat3.toDeg(), lon3.toDeg())
    }


    /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  */

    /**
     * Returns the distance from this point to the supplied point, in km, travelling along a rhumb line
     *
     *   see http://williams.best.vwh.net/avform.htm#Rhumb
     *
     * @param   {LatLon} point: Latitude/longitude of destination point
     * @returns {Number} Distance in km between this point and destination point
     */
    def rhumbDistanceTo = function(point:
      R = self._radius
      lat1 = self._lat.toRad(), lat2 = point._lat.toRad()
      dLat = (point._lat-self._lat).toRad()
      dLon = math.abs(point._lon-self._lon).toRad()

      dPhi = math.log(math.tan(lat2/2+math.PI/4)/math.tan(lat1/2+math.PI/4))
      q = (isFinite(dLat/dPhi)) ? dLat/dPhi : math.cos(lat1)  # E-W line gives dPhi=0

      # if dLon over 180° take shorter rhumb across anti-meridian:
      if (math.abs(dLon) > math.PI:
        dLon = dLon>0 ? -(2*math.PI-dLon) : (2*math.PI+dLon)
      }

      dist = math.sqrt(dLat*dLat + q*q*dLon*dLon) * R

      return dist.toPrecisionFixed(4)  # 4 sig figs reflects typical 0.3% accuracy of spherical model
    }

    /**
     * Returns the bearing from this point to the supplied point along a rhumb line, in degrees
     *
     * @param   {LatLon} point: Latitude/longitude of destination point
     * @returns {Number} Bearing in degrees from North
     */
    def rhumbBearingTo = function(point:
      lat1 = self._lat.toRad(), lat2 = point._lat.toRad()
      dLon = (point._lon-self._lon).toRad()

      dPhi = math.log(math.tan(lat2/2+math.PI/4)/math.tan(lat1/2+math.PI/4))
      if (math.abs(dLon) > math.PI) dLon = dLon>0 ? -(2*math.PI-dLon) : (2*math.PI+dLon)
      brng = math.atan2(dLon, dPhi)

      return (brng.toDeg()+360) % 360
    }

    /**
     * Returns the destination point from this point having travelled the given distance (in km) on the
     * given bearing along a rhumb line
     *
     * @param   {Number} brng: Bearing in degrees from North
     * @param   {Number} dist: Distance in km
     * @returns {LatLon} Destination point
     */
    def rhumbDestinationPoint = function(brng, dist:
      R = self._radius
      d = parseFloat(dist)/R  # d = angular distance covered on earth’s surface
      lat1 = self._lat.toRad(), lon1 = self._lon.toRad()
      brng = brng.toRad()

      dLat = d*math.cos(brng)
      # nasty kludge to overcome ill-conditioned results around parallels of latitude:
      if (math.abs(dLat) < 1e-10) dLat = 0 # dLat < 1 mm

      lat2 = lat1 + dLat
      dPhi = math.log(math.tan(lat2/2+math.PI/4)/math.tan(lat1/2+math.PI/4))
      q = (isFinite(dLat/dPhi)) ? dLat/dPhi : math.cos(lat1)  # E-W line gives dPhi=0
      dLon = d*math.sin(brng)/q

      # check for some daft bugger going past the pole, normalise latitude if so
      if (math.abs(lat2) > math.PI/2) lat2 = lat2>0 ? math.PI-lat2 : -math.PI-lat2

      lon2 = (lon1+dLon+3*math.PI)%(2*math.PI) - math.PI

      return new LatLon(lat2.toDeg(), lon2.toDeg())
    }

    /**
     * Returns the loxodromic midpoint (along a rhumb line) between this point and the supplied point.
     *   see http://mathforum.org/kb/message.jspa?messageID=148837
     *
     * @param   {LatLon} point: Latitude/longitude of destination point
     * @returns {LatLon} Midpoint between this point and the supplied point
     */
    def rhumbMidpointTo = function(point:
      lat1 = self._lat.toRad(), lon1 = self._lon.toRad()
      lat2 = point._lat.toRad(), lon2 = point._lon.toRad()

      if (math.abs(lon2-lon1) > math.PI) lon1 += 2*math.PI # crossing anti-meridian

      lat3 = (lat1+lat2)/2
      f1 = math.tan(math.PI/4 + lat1/2)
      f2 = math.tan(math.PI/4 + lat2/2)
      f3 = math.tan(math.PI/4 + lat3/2)
      lon3 = ( (lon2-lon1)*math.log(f3) + lon1*math.log(f2) - lon2*math.log(f1) ) / math.log(f2/f1)

      if (!isFinite(lon3)) lon3 = (lon1+lon2)/2 # parallel of latitude

      lon3 = (lon3+3*math.PI) % (2*math.PI) - math.PI  # normalise to -180..+180º

      return new LatLon(lat3.toDeg(), lon3.toDeg())
    }


    /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  */


    /**
     * Returns the latitude of this point signed numeric degrees if no format, otherwise format & dp
     * as per Geo.toLat()
     *
     * @param   {String} [format]: Return value as 'd', 'dm', 'dms'
     * @param   {Number} [dp=0|2|4]: No of decimal places to display
     * @returns {Number|String} Numeric degrees if no format specified, otherwise deg/min/sec
     */
    def lat = function(format, dp:
      if (typeof format == 'undefined') return self._lat

      return Geo.toLat(self._lat, format, dp)
    }

    /**
     * Returns the longitude of this point signed numeric degrees if no format, otherwise format & dp
     * as per Geo.toLon()
     *
     * @param   {String} [format]: Return value as 'd', 'dm', 'dms'
     * @param   {Number} [dp=0|2|4]: No of decimal places to display
     * @returns {Number|String} Numeric degrees if no format specified, otherwise deg/min/sec
     */
    def lon = function(format, dp:
      if (typeof format == 'undefined') return self._lon

      return Geo.toLon(self._lon, format, dp)
    }

    /**
     * Returns a string representation of this point format and dp as per lat()/lon()
     *
     * @param   {String} [format]: Return value as 'd', 'dm', 'dms'
     * @param   {Number} [dp=0|2|4]: No of decimal places to display
     * @returns {String} Comma-separated latitude/longitude
     */
    def toString = function(format, dp:
      if (typeof format == 'undefined') format = 'dms'

      return Geo.toLat(self._lat, format, dp) + ', ' + Geo.toLon(self._lon, format, dp)
    }

    /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  */

    # ---- extend Number object with methods for converting degrees/radians

    /** Converts numeric degrees to radians */
    if (typeof Number.prototype.toRad == 'undefined':
      Number.prototype.toRad = function(:
        return this * math.PI / 180
      }
    }

    /** Converts radians to numeric (signed) degrees */
    if (typeof Number.prototype.toDeg == 'undefined':
      Number.prototype.toDeg = function(:
        return this * 180 / math.PI
      }
    }

    /**
     * Formats the significant digits of a number, using only fixed-point notation (no exponential)
     *
     * @param   {Number} precision: Number of significant digits to appear in the returned string
     * @returns {String} A string representation of number which contains precision significant digits
     */
    if (typeof Number.prototype.toPrecisionFixed == 'undefined':
      Number.prototype.toPrecisionFixed = function(precision:

        # use standard toPrecision method
        n = self.toPrecision(precision)

        # ... but replace +ve exponential format with trailing zeros
        n = n.replace(/(.+)e\+(.+)/, function(n, sig, exp:
          sig = sig.replace(/\./, '')       # remove decimal from significand
          l = sig.length - 1
          while (exp-- > l) sig = sig + '0' # append zeros from exponent
          return sig
        })

        # ... and replace -ve exponential format with leading zeros
        n = n.replace(/(.+)e-(.+)/, function(n, sig, exp:
          sig = sig.replace(/\./, '')       # remove decimal from significand
          while (exp-- > 1) sig = '0' + sig # prepend zeros from exponent
          return '0.' + sig
        })

        return n
      }
    }

    /** Trims whitespace from string (q.v. blog.stevenlevithan.com/archives/faster-trim-javascript) */
    if (typeof String.prototype.trim == 'undefined':
      String.prototype.trim = function(:
        return String(this).replace(/^\s\s*/, '').replace(/\s\s*$/, '')
      }
    }


    /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  */
    if (!window.console) window.console = { log: function(:} }
