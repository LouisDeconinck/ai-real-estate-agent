from apify import Actor
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
from pydantic_ai import Agent, Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.settings import ModelSettings
import math
from datetime import datetime, timedelta

from .prompts import TRAVEL_AGENT_SYSTEM_PROMPT
from .models import TravelPlan, Deps
from .tools import search_tripadvisor_attractions, search_airbnb, search_booking_accommodations, search_google_maps_restaurants

load_dotenv()

apify_api_key = os.getenv("APIFY_API_KEY")
client = ApifyClient(apify_api_key)

api_key = os.getenv("GEMINI_API_KEY")
model = GeminiModel('gemini-2.0-flash', provider='google-gla', api_key=api_key)

travel_agent = Agent(
    model,
    system_prompt = TRAVEL_AGENT_SYSTEM_PROMPT,
    result_type=TravelPlan,
    deps_type=Deps,
    model_settings=ModelSettings(temperature=0),
    tools=[Tool(search_tripadvisor_attractions), Tool(search_airbnb), Tool(search_booking_accommodations), Tool(search_google_maps_restaurants)]
)


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() 
        
        await Actor.charge('init', 1)
        
        location = actor_input.get("location")
        
        # Calculate default dates if not provided
        today = datetime.now()
        default_start_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        default_end_date = (today + timedelta(days=37)).strftime('%Y-%m-%d')
        
        start_date = actor_input.get("start_date", default_start_date)
        end_date = actor_input.get("end_date", default_end_date)
        budget = actor_input.get("budget", 1000)
        people = actor_input.get("people", 2)
        notes = actor_input.get("notes", "")
        
        travel_plan_result = await travel_agent.run(
            f"Create a travel plan for {location} from {start_date} to {end_date} with a budget of {budget} for {people} people and the following notes: {notes}", deps=Deps(client=client)
        )
        
        # Charge for token usage
        usage = travel_plan_result.usage()
        await Actor.charge(event_name='1k-llm-tokens', count=math.ceil(usage.total_tokens / 1000))
        
        # Get the travel plan from the result data
        travel_plan = travel_plan_result.data
        
        # Push the result to Apify
        await Actor.push_data(travel_plan.model_dump())