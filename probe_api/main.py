import os

from fastapi import FastAPI

from probe_api.components.bedrock_client import BedrockClient
from probe_api.components.grid_manager import GridManager
from probe_api.components.intent_parser import IntentParser
from probe_api.components.probe_engine_manager import ProbeEngineManager
from probe_api.components.probe_store import ProbeStore
from probe_api.routers.probe import router as probe_router, set_engine

app = FastAPI(title="Probe API")

_bedrock_client = BedrockClient(
    model_id=os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0"),
    region=os.environ.get("AWS_REGION", "us-east-1"),
)

_grid_manager = GridManager()
_probe_store = ProbeStore()
_intent_parser = IntentParser(client=_bedrock_client)
_engine = ProbeEngineManager(
    grid_manager=_grid_manager,
    intent_parser=_intent_parser,
    probe_store=_probe_store,
)

# Wire engine into the router
set_engine(_engine)

app.include_router(probe_router)
