A powerful automated solution for property searchers to find their ideal homes through AI-powered analysis and personalized recommendations.

## Overview

This AI Real Estate Agent project helps property searchers find their perfect match. The system collects and analyzes real estate listings from Zillow, applying artificial intelligence to understand user preferences, compare properties, and provide personalized recommendations. Whether you're looking for your first home, an investment property, or a rental, this tool streamlines your search process with data-driven insights.

## Architecture & Data Flow

1. **Input**: Users provide a natural language search query through the input schema (e.g., "Searching for a 2-bedroom apartment in San Francisco, CA, with a monthly rent between $2000 and $4000, and preferably featuring amenities such as parking and a gym").

2. **Processing Pipeline**:
   - The `zillow_search_expert` agent parses the natural language query into structured search parameters
   - The system constructs a Zillow search URL based on these parameters
   - Crawlee/Apify tools fetch property listings from Zillow
   - Detailed information for each property is retrieved
   - The `real_estate_agent` analyzes properties and selects the best matches

3. **Output**: The system generates:
   - A structured JSON dataset containing search parameters, property recommendations with detailed attributes (amenities, prices, etc.), and a summary
   - A formatted markdown report with property details, images, and personalized match reasoning

## Features

- **Natural Language Processing**: Convert plain English requests into structured search parameters
- **Intelligent Property Matching**: Analyze properties against user criteria to find the best matches
- **Comprehensive Data Collection**: Gather detailed property information including amenities, transit scores, and more
- **Personalized Recommendations**: Provide specific reasoning for why each property matches the user's needs
- **Automated Reporting**: Generate detailed markdown reports with formatted property listings and summaries

Examle Report

```markdown
# 2+ Bedroom Rentals in San Francisco, CA ($2,000-$4,000)

## Summary

After analyzing the provided listings, I've selected five properties that best fit the client's criteria of a 2-bedroom apartment in San Francisco, CA, with a monthly rent between $2000 and $4000, and preferably featuring amenities such as parking and a gym. These properties offer a combination of desirable features, convenient locations, and reasonable prices, making them excellent options for the client to consider. Note that some properties outside of San Francisco were excluded due to the location preference. Also, some properties within San Francisco were excluded because they did not have at least 2 bedrooms.


## Top Recommended Properties

### 1. 950 Franklin St, San Francisco, CA 94109

**$4,045** | 2 bed, 1 bath

Welcome to 950 Franklin Apartments, a pet-friendly, smoke-free community designed for effortless city living in San Francisco's Western Addition. This secure-access building offers gated entry, security cameras, intercom access, and an elevator ... [See more](https://www.zillow.com/apartments/san-francisco-ca/950-franklin-street/5Xj398/)


**Features:**
- Motorcycle Parking
- Energy Efficient
- Unit Specific Storage
- Resident Support Service
- Online Payment Portal
- Common Area Plants
- Storage
- Pet Friendly
- Elevator
- Security Cameras
- *(and more)*

**Why This Property Matches Your Needs:**
Located in San Francisco, this 2-bedroom apartment is within the specified price range. It also offers amenities like parking and is pet-friendly.

---

### 2. 845 California St, San Francisco, CA 94108

**$3,595** | 2 bed, 1 bath

Welcome to 845 California Apartments, a refined Nob Hill residence offering the perfect balance of elegance and modern comfort. This pet-friendly, smoke-free building provides secure entry with surveillance cameras, an elevator for effortless ac... [See more](https://www.zillow.com/apartments/san-francisco-ca/845-california-street/5XjSFD/)


**Features:**
- Storage
- Resident Support Service
- Online Payment Portal
- Pet Friendly
- Elevator
- Security Cameras
- Trash / Recycling / Compost
- Nearby Park
- Resident Manager

**Why This Property Matches Your Needs:**
Located in San Francisco and within the price range, this 2-bedroom apartment offers amenities such as an elevator and storage.

---

### 3. 140 20th Ave, San Francisco, CA 94121

**$3,795** | 2 bed, 1 bath

Who could ask for more? Laurel Heights- 2 beds available. Steps away from Presidio.... [See more](https://www.zillow.com/apartments/san-francisco-ca/140-20th/5YCpkN/)


**Features:**
- Hardwood
- Washer
- Dryer
- Dishwasher

**Why This Property Matches Your Needs:**
This 2-bedroom apartment in San Francisco fits the price range and is located near the Presidio.

---

### 4. 1100 Gough St, San Francisco, CA 94109

**$3,995** | 2 bed, 1 bath

Welcome to Carillon Tower! Carillon Tower offers SPECTACULAR VIEWS from atop Cathedral Hill in the center of San Francisco. Each apartment has its own private demimonde balcony that affords sweeping views of the city. Large windows and sliding doors give each apartment an open feel! You will feel ri... [See more](https://www.zillow.com/apartments/san-francisco-ca/carillon-tower/5XjPcB/)


**Features:**
- Trash Compactor
- Laminate
- Dishwasher
- Tile
- MicrowaveOven
- Range
- Sauna
- GarbageDisposal
- Jaquzzi
- Garage
- *(and more)*

**Why This Property Matches Your Needs:**
Located in San Francisco, this 2-bedroom apartment is within the specified price range and offers a garage.

---

### 5. 3711 19th Ave, San Francisco, CA 94132

**$3,840** | 2 bed, 1 bath

Nestled among 152 acres of outdoor space and parkland, adjacent to beaches, coastal trails, lakes and golf courses, Parkmerced is a unique and vibrant San Francisco community. Our apartment homes offer more living space, indoors and out, with a mix of styles, sizes, floor plans, views and unique loc... [See more](https://www.zillow.com/apartments/san-francisco-ca/parkmerced/5XjKHx/)


**Features:**
- Free Weights
- Community Outdoor Kitchen (2)
- Hardwood
- High-Efficiency Energy-Star Appliances
- Ceiling Fan(s)
- Amazon Lockers (14)
- Pet-Friendly (all but 4 breeds)
- Bocce Ball Courts (2)
- Resident Service Department
- Resident Parties & Events
- *(and more)*

**Why This Property Matches Your Needs:**
Located in San Francisco, this 2-bedroom apartment is within the specified price range and offers a garage and fitness center.
```

## License

This project is licensed under the MIT License.
