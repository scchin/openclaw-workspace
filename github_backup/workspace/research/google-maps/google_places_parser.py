
import re

def parse_place_ids(snapshot_text):
    """
    Extracts place_ids from a Google Maps search results snapshot.
    The place_id is usually in the URL after '19s' and before '?' or '&'.
    """
    place_ids = []
    # Look for URLs in the snapshot
    urls = re.findall(r'/url: (https://www.google.com/maps/place/[^ \n]+)', snapshot_text)
    for url in urls:
        # Search for the 19s parameter
        match = re.search(r'19s([a-zA-Z0-9_-]+)', url)
        if match:
            place_ids.append(match.group(1))
    return list(set(place_ids))

def parse_place_details(snapshot_text):
    """
    Extracts name, address, rating, and price from a Google Maps place detail snapshot.
    """
    details = {
        "name": None,
        "address": None,
        "rating": None,
        "price": None
    }
    
    # Extract Name: Usually in a level 1 heading
    name_match = re.search(r'heading "([^"]+)" \[level=1\]', snapshot_text)
    if name_match:
        details["name"] = name_match.group(1)
    
    # Extract Rating: Look for "X.X 顆星" or similar
    rating_match = re.search(r'text: "(\d\.\d)"\s+img "(\d\.\d) 顆星"', snapshot_text)
    if not rating_match:
        rating_match = re.search(r'img "(\d\.\d) 顆星"', snapshot_text)
    
    if rating_match:
        details["rating"] = rating_match.group(1)
    
    # Extract Price: Look for "$X-Y"
    price_match = re.search(r'(\$\d+-\d+)', snapshot_text)
    if price_match:
        details["price"] = price_match.group(1)
    
    # Extract Address: Look for "地址: ..."
    address_match = re.search(r'button "地址: ([^"]+)"', snapshot_text)
    if address_match:
        details["address"] = address_match.group(1).replace("地址: ", "").strip()
    
    return details

# Test with the provided snapshots
if __name__ == "__main__":
    with open("snapshot_results.txt", "r", encoding="utf-8") as f:
        search_snapshot = f.read()
    
    with open("snapshot_place.txt", "r", encoding="utf-8") as f:
        place_snapshot = f.read()
        
    print("--- Place IDs ---")
    print(parse_place_ids(search_snapshot))
    
    print("\n--- Place Details ---")
    print(parse_place_details(place_snapshot))
