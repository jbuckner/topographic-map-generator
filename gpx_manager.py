class GPXManager:
    def __init__(self, gpx):
        if not gpx:
            raise ValueError("You must provide a path to a gpx file.")
        self.gpx = gpx
        self.ne = {"lat": None, "lng": None}
        self.sw = {"lat": None, "lng": None}
        self.parse()

    def parse(self):
        # returns ne, sw dictionary: {"ne": (x,y), "sw": (x,y)}
        north_lat = -300
        west_lng = 300
        south_lat = 300
        east_lng = -300

        for track in self.gpx.tracks:
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
        self.ne["lat"] = north_lat
        self.ne["lng"] = east_lng
        self.sw["lat"] = south_lat
        self.sw["lng"] = west_lng

    def get_boundaries(self):
        return {"ne": self.ne, "sw": self.sw}
