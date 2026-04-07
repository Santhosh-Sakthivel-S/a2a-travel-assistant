import os
from strands import Agent
from strands.multiagent.a2a import A2AServer
from src.config.settings import settings, logger

def create_and_serve_trip_planner(port: int = 8000):
    """Initializes and serves the Trip Planner Agent via A2A."""
    
    # Ensure boto3 uses the region specified in the .env
    os.environ["AWS_DEFAULT_REGION"] = settings.AWS_REGION
    
    trip_planner = Agent(
        name="Trip Planner",
        description="Expert travel agent skilled in creating detailed itineraries.",
        system_prompt=(
            "You are an elite corporate travel agent. "
            "You will receive a destination and its current weather context. "
            "Generate a highly detailed, logical 3-day itinerary adapted to the weather conditions. "
            "Format the output professionally."
        ),
        model=settings.BEDROCK_MODEL_ID
    )

    server = A2AServer(agent=trip_planner)
    
    logger.info(f"Starting Trip Planner A2A Server on port {port}...")
    server.serve(port=port)