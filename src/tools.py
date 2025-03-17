from apify import Actor
from typing import List, Tuple
from apify_client import ApifyClient
import os
import json
import urllib.parse
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from .models import ZillowSearchParameters

load_dotenv()

apify_api_key = os.getenv("APIFY_API_KEY")
client = ApifyClient(apify_api_key)

async def get_map_bounds(search_term: str) -> Tuple[float, float, float, float]:
    """
    Get map bounds for a location using OpenCage Geocoding API.
    
    Args:
        search_term: Location search term (e.g., "San Francisco, CA")
        
    Returns:
        Tuple of (west, east, south, north) bounds
    """
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    encoded_search = urllib.parse.quote(search_term)
    url = f"https://api.opencagedata.com/geocode/v1/json?q={encoded_search}&key={opencage_api_key}&no_annotations=1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            bounds = data["results"][0].get("bounds")
            if bounds:
                west = bounds["southwest"]["lng"]
                east = bounds["northeast"]["lng"]
                south = bounds["southwest"]["lat"]
                north = bounds["northeast"]["lat"]
                Actor.log.info(f"Successfully geocoded '{search_term}', bounds: {west}, {east}, {south}, {north}")
                return west, east, south, north
            
    except Exception as e:
        Actor.log.warning(f"Connection error: {str(e)}")
    

async def construct_zillow_url(search_params: ZillowSearchParameters) -> str:
    """Construct a Zillow URL based on the given search parameters."""
    base_url = "https://www.zillow.com/homes/for_sale/?searchQueryState="
    if search_params.for_rent:
        base_url = "https://www.zillow.com/homes/for_rent/?searchQueryState="
    
    # Get dynamic map bounds based on the search term
    try:
        Actor.log.info(f"Getting map bounds for search term: {search_params.search_term}")
        bounds = await get_map_bounds(search_params.search_term)
        west, east, south, north = bounds
    except Exception as e:
        Actor.log.error(f"Error getting map bounds: {str(e)}")
    
    # Initialize with required structure
    search_query_state = {
        "pagination": {},
        "isMapVisible": True,
        "usersSearchTerm": search_params.search_term,
        "mapBounds": {
            "west": west,
            "east": east,
            "south": south,
            "north": north
        },
        "filterState": {
            "sort": {"value": "globalrelevanceex"},
            "fsba": {"value": False},
            "fsbo": {"value": False},
            "nc": {"value": False},
            "cmsn": {"value": False},
            "auc": {"value": False},
            "fore": {"value": False}
        },
        "isListVisible": True
    }
    
    filter_state = search_query_state["filterState"]
    
    # Price range
    if search_params.price_min is not None or search_params.price_max is not None:
        filter_state["price"] = {}
        if search_params.price_min is not None:
            filter_state["price"]["min"] = search_params.price_min

        if search_params.price_max is not None:
            filter_state["price"]["max"] = search_params.price_max
    
    # Basic property features
    if search_params.beds_min is not None:
        filter_state["beds"] = {"min": search_params.beds_min}
    
    if search_params.baths_min is not None:
        filter_state["baths"] = {"min": search_params.baths_min}
    
    if search_params.sqft_min is not None or search_params.sqft_max is not None:
        filter_state["sqft"] = {}
        if search_params.sqft_min is not None:
            filter_state["sqft"]["min"] = search_params.sqft_min
        if search_params.sqft_max is not None:
            filter_state["sqft"]["max"] = search_params.sqft_max
    
    # Key amenities
    if search_params.garage is not None:
        filter_state["gar"] = {"value": search_params.garage}
    
    if search_params.ac is not None:
        filter_state["ac"] = {"value": search_params.ac}
    
    if search_params.pool is not None:
        filter_state["pool"] = {"value": search_params.pool}
    
    if search_params.single_story_only is not None:
        filter_state["sto"] = {"value": search_params.single_story_only}
    
    # Views and location features
    if search_params.waterfront is not None:
        filter_state["wat"] = {"value": search_params.waterfront}
    
    if search_params.city_view is not None:
        filter_state["cityv"] = {"value": search_params.city_view}
    
    if search_params.mountain_view is not None:
        filter_state["mouv"] = {"value": search_params.mountain_view}
    
    # Rental-specific filters
    if search_params.for_rent:
        filter_state["fr"] = {"value": True}
        if search_params.pets_allowed is not None:
            filter_state["np"] = {"value": search_params.pets_allowed}
        if search_params.furnished is not None:
            filter_state["fur"] = {"value": search_params.furnished}
        if search_params.utilities_included is not None:
            filter_state["uti"] = {"value": search_params.utilities_included}
        if search_params.onsite_parking is not None:
            filter_state["par"] = {"value": search_params.onsite_parking}
    
    encoded_query = urllib.parse.quote(json.dumps(search_query_state))
    return base_url + encoded_query

async def search_zillow(search_url: str) -> List[Dict[str, Any]]:
    """Search Zillow for real estate listings.
    
    Args:
        search_url: The Zillow search URL
        
    Returns:
        List of attraction objects with relevant fields for travel recommendations
    """
    Actor.log.info(f"Searching Zillow with URL: {search_url}")
    run_input = {
        "extractionMethod": "MAP_MARKERS",
        "searchUrls": [
            {
            "url": search_url,
            "method": "GET"
            }
        ]
    }
    
    try:
        # Execute the actor and get the run info
        run = client.actor("maxcopell/zillow-scraper").call(run_input=run_input, memory_mbytes=512, max_items=100)
        
        if not run or not run.get("defaultDatasetId"):
            Actor.log.error("Failed to get valid response from Zillow scraper actor")
            return []
        
        list_page = client.dataset(run["defaultDatasetId"]).list_items().items
        
        # Process each item
        results = []
        for item in list_page:
            detail_url = item.get("detailUrl", "")
            if detail_url:
                results.append(detail_url)
                
        Actor.log.info(f"Collected {len(results)} Zillow detail URLs")
        
        await Actor.charge('tool-result', len(results))
        return results
    except Exception as e:
        Actor.log.error(f"Error during Zillow search: {str(e)}")
        return []

async def get_zillow_details(property_urls: List[str], for_rent: bool) -> List[Dict[str, Any]]:
    """Get detailed information about specific Zillow property listings.
    
    Args:
        property_urls: List of Zillow property detail URLs
        for_rent: Whether the properties are for rent (True) or for sale (False)

    Returns:
        List of property objects with detailed information
    """
    if not property_urls:
        Actor.log.warning("No property URLs provided to get_zillow_details")
        return []
        
    Actor.log.info(f"Fetching details for {len(property_urls)} Zillow properties")
    
    # Prepare the start URLs in the format required by the actor
    start_urls = [{"url": url, "method": "GET"} for url in property_urls]
    
    property_status = "FOR_RENT" if for_rent else "FOR_SALE"
    
    run_input = {
        "extractBuildingUnits": "disabled",
        "propertyStatus": property_status,
        "startUrls": start_urls,
        "addresses": [],
        "searchResultsDatasetId": ""
    }
    
    try:
        # Execute the actor and get the run info
        run = client.actor("maxcopell/zillow-detail-scraper").call(run_input=run_input, memory_mbytes=1024)
        
        if not run or not run.get("defaultDatasetId"):
            Actor.log.error("Failed to get valid response from Zillow detail scraper actor")
            return []
            
        # Get all items from the dataset
        all_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not all_items:
            Actor.log.warning("No items found in the Zillow detail scraper dataset")
            return []
            
        # Safe getter function for nested properties
        def safe_get(obj, *keys, default=None):
            """Safely access nested dictionary properties."""
            current = obj
            for key in keys:
                if not isinstance(current, dict):
                    return default
                current = current.get(key)
                if current is None:
                    return default
            return current
        
        # Filter to include only the specified fields
        filtered_results = []
        for item in all_items:
            # Basic properties with simple fallbacks
            filtered_item = {
                "city": item.get("city") or safe_get(item, "address", "city"),
                "state": item.get("state") or safe_get(item, "address", "state"),
                "streetAddress": item.get("streetAddress") or safe_get(item, "address", "streetAddress"),
                "zipcode": item.get("zipcode") or safe_get(item, "address", "zipcode"),
                "country": item.get("country"),
                "yearBuilt": item.get("yearBuilt"),
                "description": item.get("description"),
                "url": item.get("addressOrUrlFromInput") or item.get("url")
            }
            
            # Process floor plans for apartments to get average beds, baths, and price
            floor_plans = safe_get(item, "floorPlans")
            if floor_plans and len(floor_plans) > 0:
                total_beds = 0
                total_baths = 0
                total_price = 0
                count = 0
                
                for plan in floor_plans:
                    if plan.get("beds") is not None and plan.get("baths") is not None:
                        count += 1
                        total_beds += plan.get("beds", 0)
                        total_baths += plan.get("baths", 0)
                        # Use minPrice or maxPrice, whichever is available
                        price = plan.get("minPrice") or plan.get("maxPrice", 0)
                        total_price += price
                
                if count > 0:
                    filtered_item["bedrooms"] = int(total_beds / count)
                    filtered_item["bathrooms"] = int(total_baths / count)
                    filtered_item["price"] = int(total_price / count)
                else:
                    filtered_item["bedrooms"] = item.get("bedrooms")
                    filtered_item["bathrooms"] = item.get("bathrooms")
                    filtered_item["price"] = item.get("price")
            else:
                filtered_item["bedrooms"] = item.get("bedrooms")
                filtered_item["bathrooms"] = item.get("bathrooms")
                filtered_item["price"] = item.get("price")
            
            # Complex nested properties
            homeinsights = safe_get(item, "homeinsights")
            if homeinsights:
                insights = safe_get(homeinsights, "insights")
                if insights and len(insights) > 0:
                    filtered_item["features"] = safe_get(insights[0], "phrases")
            
            # Safe access to other nested properties
            filtered_item["facts"] = safe_get(item, "resoFacts", "atAGlanceFacts")
            filtered_item["amenities"] = safe_get(item, "amenityDetails", "customAmenities", "rawAmenities")
            filtered_item["communityAmenities"] = safe_get(item, "commonUnitAmenities")
            
            # Complex conditional property - add null checks before concatenating
            building_appliances = safe_get(item, "buildingAttributes", "appliances") or []
            reso_appliances = safe_get(item, "resoFacts", "appliances") or []
            filtered_item["appliances"] = list(set(building_appliances + reso_appliances))
            
            # Scores
            filtered_item["bikescore"] = safe_get(item, "bikescore", "bikescore")
            filtered_item["transitScore"] = safe_get(item, "transitScore", "transit_score")
            filtered_item["walkScore"] = safe_get(item, "walkScore", "walk_score")
            
            filtered_results.append(filtered_item)
        
        Actor.log.info(f"Processed {len(filtered_results)} detailed property listings")
        
        await Actor.charge('tool-result', len(filtered_results))
        return filtered_results
    except Exception as e:
        Actor.log.error(f"Error during Zillow detail retrieval: {str(e)}")
        return [] 