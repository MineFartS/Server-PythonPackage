
class Coordinate(list[int]):
    
    def __init__(self,
        latitude: int,
        longitude: int
    ) -> None:
        super().__init__((latitude, longitude))        
        self.latitude = latitude
        self.longitude = longitude

    def __sub__(self, other):
        from geopy.distance import geodesic
        return geodesic(
            tuple(self),
            tuple(other)
        )

def fetch(
    max_age: int = 0,
    timeout: int = 15
) -> Coordinate:
    """pos() -> (latitude, longitude)"""
    from winrt.windows.devices.geolocation import Geolocator, PositionAccuracy
    from datetime import timedelta

    gl = Geolocator()
    gl.desired_accuracy_in_meters = 1
    gl.desired_accuracy = PositionAccuracy.HIGH

    pos = gl.get_geoposition_async_with_age_and_timeout(
        timedelta(seconds=max_age),
        timedelta(seconds=timeout)
    ).get()

    return Coordinate(
        pos.coordinate.point.position.latitude,
        pos.coordinate.point.position.longitude
    )

