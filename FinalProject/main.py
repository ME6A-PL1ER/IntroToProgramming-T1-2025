import os
import sys
import json
import time
import random
import textwrap
import shutil
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

import requests

try:
    import redis
except ImportError:
    redis = None

# Configuration
REDIS_URL   = "redis://localhost:6379/0"
OLLAMA_URL  = "http://localhost:11434/api/chat"
OLLAMA_MODEL= "llama3.1"
PLAYER_ID   = "player1"

# Weights
WEIGHTS = {
    "combat": 2.0,
    "puzzle": 2.0,
    "social": 4.0,
    "exploration": 4.0,
}