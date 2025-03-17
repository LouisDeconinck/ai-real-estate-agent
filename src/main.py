from apify import Actor
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
import math
import json

from .prompts import ZILLOW_SEARCH_EXPERT_SYSTEM_PROMPT, REAL_ESTATE_AGENT_SYSTEM_PROMPT
from .models import ZillowSearchParameters, Deps, RealEstateAgentResult
from .tools import construct_zillow_url, search_zillow, get_zillow_details

load_dotenv()

apify_api_key = os.getenv("APIFY_API_KEY")
client = ApifyClient(apify_api_key) 

gemini_flash_2_model = GeminiModel('gemini-2.0-flash', provider='google-gla')
gpt4o_model = OpenAIModel('gpt-4o')

zillow_search_expert = Agent(
    gpt4o_model,
    system_prompt = ZILLOW_SEARCH_EXPERT_SYSTEM_PROMPT,
    result_type=ZillowSearchParameters,
    deps_type=Deps,
    model_settings=ModelSettings(temperature=0),
)

real_estate_agent = Agent(
    gemini_flash_2_model,
    system_prompt = REAL_ESTATE_AGENT_SYSTEM_PROMPT,
    result_type=RealEstateAgentResult,
    deps_type=Deps,
    model_settings=ModelSettings(temperature=0),
)

async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() 
        
        await Actor.charge('init', 1)
        
        search = actor_input.get("search")
        
        zillow_parameters = await zillow_search_expert.run(
            f"get the zillow parameters for this request: {search}"
        )
        
        # Charge for token usage
        usage = zillow_parameters.usage()
        await Actor.charge(event_name='1k-llm-tokens', count=math.ceil(usage.total_tokens / 1000))
        zillow_url = await construct_zillow_url(zillow_parameters.data)
        
        # Perform the search
        zillow_results = await search_zillow(search_url=zillow_url)
        
        # Get the details of the properties
        zillow_details = await get_zillow_details(property_urls=zillow_results, for_rent=zillow_parameters.data.for_rent)
        
        # Add the Zillow URL to the output data
        output_data = zillow_parameters.data.model_dump()
        output_data['zillow_url'] = zillow_url
        
        # Save Zillow details to KV store
        default_kv_store = await Actor.open_key_value_store()
        await default_kv_store.set_value('zillow_details', zillow_details)
        
        try:
            # Use all Zillow details for analysis
            agent_result = await real_estate_agent.run(
                f"Analyze these properties. Select the top 5 meeting the client's needs, provide your reasoning and an overall summary: {search}\n\nHere are all the properties:\n{json.dumps(zillow_details, indent=2)}",
            )
            
            # Charge for token usage from real estate agent
            agent_usage = agent_result.usage()
            await Actor.charge(event_name='1k-llm-tokens', count=math.ceil(agent_usage.total_tokens / 1000))
            
            # Add real estate agent recommendations to output
            output_data['property_recommendations'] = [prop.model_dump() for prop in agent_result.data.properties]
            output_data['summary'] = agent_result.data.summary
            
        except Exception as e:
            Actor.log.error(f"Error during property analysis: {str(e)}")
            output_data['property_recommendations'] = []
            output_data['summary'] = "Unable to analyze properties due to an error"
        
        # Push the result to Apify
        await Actor.push_data(output_data)