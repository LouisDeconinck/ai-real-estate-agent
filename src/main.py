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
from .tools import construct_zillow_url, search_zillow, get_zillow_details, generate_markdown_report

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
        
        # Create search_parameters object
        search_parameters = zillow_parameters.data.model_dump()
        search_parameters['zillow_url'] = zillow_url
        
        # Initialize output_data dictionary
        output_data = {
            'search_parameters': search_parameters
        }
        
        # Save Zillow details to KV store
        default_kv_store = await Actor.open_key_value_store()
        await default_kv_store.set_value('zillow_details', zillow_details)
        
        try:
            # Update prompt to include requirement for URL
            modified_prompt = f"Analyze these properties. Select the top 5 meeting the client's needs, provide your reasoning and an overall summary. For each property, be sure to include its exact URL: {search}\n\nHere are all the properties:\n{json.dumps(zillow_details, indent=2)}"
            
            agent_result = await real_estate_agent.run(modified_prompt)
            
            # Charge for token usage from real estate agent
            agent_usage = agent_result.usage()
            await Actor.charge(event_name='1k-llm-tokens', count=math.ceil(agent_usage.total_tokens / 1000))
            
            # Create a dictionary mapping URLs to their full zillow_details
            url_to_details = {prop.get('url', ''): prop for prop in zillow_details}
            
            # Merge AI recommendations with full property details
            enhanced_recommendations = []
            for ai_prop in agent_result.data.properties:
                # Get the URL from the AI's evaluation
                ai_prop_data = ai_prop.model_dump()
                url = ai_prop_data.get('url', '')
                
                # Find matching property in zillow_details by URL
                full_property_details = url_to_details.get(url)
                
                if full_property_details:
                    # Keep all the original Zillow details
                    enhanced_property = dict(full_property_details)
                    # Add the AI's reason
                    enhanced_property['match_reason'] = ai_prop_data.get('match_reason', '')
                    enhanced_recommendations.append(enhanced_property)
                else:
                    # If no match found, use the AI's data as fallback
                    enhanced_recommendations.append(ai_prop_data)
            
            # Add enhanced recommendations to output
            output_data['property_recommendations'] = enhanced_recommendations
            output_data['summary'] = agent_result.data.summary
            
            # Generate markdown report
            markdown_report = generate_markdown_report(
                search=search,
                search_parameters=output_data['search_parameters'],
                recommendations=output_data['property_recommendations'],
                summary=output_data['summary']
            )
            
            # Add markdown report to output data
            output_data['markdown_report'] = markdown_report
            
            # Save markdown report to KV store as well
            await default_kv_store.set_value('property_report.md', markdown_report)
            
            # Log success
            Actor.log.info("Markdown report generated and saved successfully")
            
        except Exception as e:
            Actor.log.error(f"Error during property analysis: {str(e)}")
            output_data['property_recommendations'] = []
            output_data['summary'] = "Unable to analyze properties due to an error"
            output_data['markdown_report'] = "# Error\n\nUnable to generate property report due to an error."
        
        # Push the result to Apify
        await Actor.push_data(output_data)
