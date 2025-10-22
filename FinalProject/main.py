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

# Configuration
REDIS_URL   = "redis://localhost:6379/0"
OLLAMA_URL  = "http://localhost:11434/api/chat"
OLLAMA_MODEL= "gemma3-1b"
PLAYER_ID   = "player1"

# Weights
WEIGHTS = {
    "combat": 2.0,
    "puzzle": 2.0,
    "social": 4.0,
    "exploration": 4.0,
}

# Guidelines
GUIDELINES = """
You are a fair but firm dungeon master guiding a terminal text adventure.
Rules:
- Provide vivid, concise narration that advances the story each turn.
- Offer 2–4 specific choices the player can type.
- Use a balanced mix of encounter types: combat, puzzle, social, exploration.
- Respect stats: Health and Stamina never below 0, never give items/health unless it is the explicit result of an encounter resolution you describe.
- If the player is at 0 Health, they die and the story ends.
- Keep continuity with past choices and inventory.
- Do not scroll needlessly; keep responses short and punchy.
- Output JSON with keys: narration (string), encounter_type (one of: combat, puzzle, social, exploration, none),
  choices (list[str]), effects (list of effects like {"health":-5} or {"add_item":"rope"}), end (bool), end_tag (optional str)
""".strip()

# Redis things i dont know how to code:
try:
    import redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = None

def rget(key, default=None):
    if r:
        val = r.get(key)
        return default if val is None else val
    return _MEM.get(key, default)

def rset(key, val):
    if r:
        r.set(key, val)
    else:
        _MEM[key] = val

_MEM = {}

# Game state dataclass
@dataclass
class GameState:
    player_id: str
    health: int = 100
    stamina: int = 100
    gold: int = 0
    inventory: List[str] = field(default_factory=lambda: ["canteen", "map"])
    encounters_seen: int = 0
    phase: str = "beginning" # beginning, middle, climax, ending
    ended: bool = False
    end_tag: str = ""

# Game state functions

def to_dict(self) -> Dict[str, Any]:
    """Return a plain dict for JSON serialization."""
    return asdict(self)
    
def save(self) -> None:
    """Clamp non-negatives and persist to Redis (or memory)."""
    self.health = max(0, self.health)
    self.stamina = max(0, self.stamina)
    self.gold = max(0, self.gold)
    rset(f"player:{self.player_id}:state", json.dumps(self.to_dict()))

@staticmethod
def load(player_id: str) -> "GameState":
    """Load from Redis; if missing, create default and save."""
    raw = rget(f"player:{player_id}:state")
    if raw:
        return GameState(**json.loads(raw))
    else:
        gs = GameState(player_id=player_id)
        gs.save()
        return gs

def advance_phase(self) -> None:
    """Simple pacing gates to steer beginning → middle → climax → ending."""
    # Hi osowski
    if self.encounters_seen >= 4:
        self.phase = "middle"
    elif self.encounters_seen >= 10:
        self.phase = "climax"
    elif self.encounters_seen >= 16:
        self.phase = "ending"
    else:
        self.phase = "beginning"

# Scchhhhhatttt history helpers

def load_messages(player_id: str) -> List[Dict[str, str]]:
    """Return chat history; seed with system guidelines if empty."""
    # TODO: raw = rget(f"player:{player_id}:messages")
    # TODO: if raw: return json.loads(raw)
    # TODO: else: return [{"role":"system","content": GUIDELINES}]


def save_messages(player_id: str, messages: List[Dict[str, str]]) -> None:
    """Send messages to Redis/in-memory."""
    rset(f"player:{player_id}:messages", json.dumps(messages))

def append_user(player_id: str, content: str) -> List[Dict[str, str]]:
    """Append a user turn and persist; return updated list."""
    # TODO: msgs = load_messages(player_id); msgs.append({"role":"user","content": content}); save_messages(...); return msgs
    msg = load_messages(player_id)
    msg.append({"role":"user","content": content})
    save_messages(player_id, msg)
    return msg

def append_assistant(player_id: str, content: str) -> List[Dict[str, str]]:
    """Append an assistant turn and persist; return updated list."""
    msg = load_messages(player_id)
    msg.append({"role":"assistant","content": content})
    save_messages(player_id, msg)
    return msg

def truncate_messages(messages: List[Dict[str, str]], keep_last: int = 12) -> List[Dict[str, str]]:
    """Keep system + last N turns to control prompt size."""
    system_msg = [m for m in messages if m["role"] == "system"]
    user_assistant_msgs = [m for m in messages if m["role"] != "system"]
    truncated_msgs = system_msg + user_assistant_msgs[-(keep_last*2):]
    return truncated_msgs
