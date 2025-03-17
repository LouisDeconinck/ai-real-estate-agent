from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Deps:
    pass

class ZillowSearchParameters(BaseModel):
    # Essential search parameters
    search_term: str = Field(..., description="Location to search (e.g. city, zip code)")
    for_rent: bool = Field(False, description="Search for rentals instead of sales")
    
    # Price and payment
    price_min: Optional[int] = Field(None, description="Minimum price")
    price_max: Optional[int] = Field(None, description="Maximum price")
    
    # Basic property features
    beds_min: Optional[int] = Field(None, description="Minimum number of bedrooms")
    baths_min: Optional[int] = Field(None, description="Minimum number of bathrooms")
    sqft_min: Optional[int] = Field(None, description="Minimum square footage")
    sqft_max: Optional[int] = Field(None, description="Maximum square footage")
    
    # Key amenities
    garage: Optional[bool] = Field(None, description="Has garage")
    ac: Optional[bool] = Field(None, description="Has air conditioning")
    pool: Optional[bool] = Field(None, description="Has pool")
    single_story_only: Optional[bool] = Field(None, description="Single story only")
    
    # Views and location features
    waterfront: Optional[bool] = Field(None, description="Is waterfront property")
    city_view: Optional[bool] = Field(None, description="Has city view")
    mountain_view: Optional[bool] = Field(None, description="Has mountain view")
    
    # Rental-specific features (only used if for_rent is True)
    pets_allowed: Optional[bool] = Field(None, description="Pets allowed")
    furnished: Optional[bool] = Field(None, description="Furnished property")
    utilities_included: Optional[bool] = Field(None, description="Utilities included")
    onsite_parking: Optional[bool] = Field(None, description="Onsite parking available")
    
class Property(BaseModel):
    match_reason: str
    url: str = Field(..., description="The property's Zillow URL")

class RealEstateAgentResult(BaseModel):
    properties: List[Property]
    summary: str

