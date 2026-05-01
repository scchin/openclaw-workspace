import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371000 # Radius of earth in meters. Use 3956 for miles
    return c * r

def calculate_travel_times(distance_m):
    # Walking speed: ~80 meters per minute
    # Driving speed: ~500 meters per minute (considering city traffic)
    walking_min = distance_m / 80
    driving_min = distance_m / 500
    return walking_min, driving_min

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python distance_calculator.py <lat1> <lon1> <lat2> <lon2>")
        sys.exit(1)
    
    try:
        lat1, lon1, lat2, lon2 = map(float, sys.argv[1:])
        dist = haversine(lat1, lon1, lat2, lon2)
        walk, drive = calculate_travel_times(dist)
        print(f"distance_m={dist:.2f}")
        print(f"walking_min={walk:.1f}")
        print(f"driving_min={drive:.1f}")
    except ValueError:
        print("Error: Coordinates must be numbers.")
        sys.exit(1)
