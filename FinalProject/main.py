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

# Im to lazy to do env stuff so were doing it manually  
REDIS_URL    = "redis://localhost:6379/0"
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3-1b"
PLAYER_ID    = "player1"

WEIGHTS = {
    "combat": 2.0,
    "puzzle": 2.0,
    "social": 4.0,
    "exploration": 2.0,
}

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

# Soft import redis
try:
    import redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = None

_MEM: Dict[str, str] = {}

def rget(key: str, default=None):
    if r:
        val = r.get(key)
        return default if val is None else val
    return _MEM.get(key, default)

def rset(key: str, val: str):
    if r:
        r.set(key, val)
    else:
        _MEM[key] = val

# Actual game stuff (state, chat history, main loop) below
@dataclass
class GameState:
    player_id: str
    health: int = 100
    stamina: int = 100
    gold: int = 0
    inventory: List[str] = field(default_factory=lambda: ["canteen", "map"])
    encounters_seen: int = 0
    phase: str = "beginning"
    ended: bool = False
    end_tag: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self) -> None:
        self.health  = max(0, self.health)
        self.stamina = max(0, self.stamina)
        self.gold    = max(0, self.gold)
        rset(f"player:{self.player_id}:state", json.dumps(self.to_dict()))

    @staticmethod
    def load(player_id: str) -> "GameState":
        raw = rget(f"player:{player_id}:state")
        if raw:
            return GameState(**json.loads(raw))
        gs = GameState(player_id=player_id)
        gs.save()
        return gs

    def advance_phase(self) -> None:
        if self.encounters_seen >= 16:
            self.phase = "ending"
        elif self.encounters_seen >= 10:
            self.phase = "climax"
        elif self.encounters_seen >= 4:
            self.phase = "middle"
        else:
            self.phase = "beginning"

# Chat history
def load_messages(player_id: str) -> List[Dict[str, str]]:
    raw = rget(f"player:{player_id}:messages")
    if raw:
        return json.loads(raw)
    return [{"role": "system", "content": GUIDELINES}]

def save_messages(player_id: str, messages: List[Dict[str, str]]) -> None:
    rset(f"player:{player_id}:messages", json.dumps(messages))

def append_user(player_id: str, content: str) -> List[Dict[str, str]]:
    msgs = load_messages(player_id)
    msgs.append({"role": "user", "content": content})
    save_messages(player_id, msgs)
    return msgs

def append_assistant(player_id: str, content: str) -> List[Dict[str, str]]:
    msgs = load_messages(player_id)
    msgs.append({"role": "assistant", "content": content})
    save_messages(player_id, msgs)
    return msgs

def truncate_messages(messages: List[Dict[str, str]], keep_last: int = 12) -> List[Dict[str, str]]:
    # Keep system prompt + last N user/assistant turns (N*2 messages)
    system = [m for m in messages if m.get("role") == "system"]
    rest   = [m for m in messages if m.get("role") != "system"]
    return (system[:1] if system else []) + rest[-(keep_last*2):]

# Terminal 
def term_cols() -> int:
    try:
        return shutil.get_terminal_size((100, 30)).columns
    except Exception:
        return 100

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def wrap_lines(text: str, width: int) -> List[str]:
    lines = []
    for para in text.splitlines():
        lines.extend(textwrap.wrap(para, width=width) or [""])
    return lines

def status_line(state: GameState) -> str:
    return f"Health: {state.health} | Stamina: {state.stamina} | Gold: {state.gold} | Phase: {state.phase} | Encounters: {state.encounters_seen}"

def inventory_line(state: GameState) -> str:
    return "Inventory: " + (", ".join(state.inventory) if state.inventory else "(empty)")

def draw(chat: List[str], state: GameState) -> None:
    cols = term_cols()
    clear_screen()
    print("=" * cols)
    print(" AI & Player ".center(cols, "="))
    print("=" * cols)
    for line in chat[-10:]:
        for wrapped in wrap_lines(line, cols):
            print(wrapped)
    print("-" * cols)
    print(status_line(state))
    print(inventory_line(state))
    print("=" * cols)

def prompt_user() -> str:
    try:
        return input("> ").strip()
    except EOFError:
        return "quit"

# Encounters
def pick_encounter_type() -> str:
    items = list(WEIGHTS.items())
    total = sum(w for _, w in items)
    roll  = random.random() * total
    acc = 0.0
    for etype, w in items:
        acc += w
        if roll <= acc:
            return etype
    return "exploration"

# AI Calls
def extract_json_block(text: str) -> Dict[str, Any]:
    """
    Try to pull a JSON object out of the model's response.
    If parsing fails, return a safe default response.
    """
    try:
        s = text.find("{")
        e = text.rfind("}")
        if s != -1 and e != -1 and e > s:
            snippet = text[s:e+1]
            return json.loads(snippet)
    except Exception:
        pass
    # Safe fallback
    return {
        "narration": "You pause at a fork in the road; wind hisses through dry grass.",
        "encounter_type": random.choice(["exploration", "social"]),
        "choices": ["left", "right", "rest"],
        "effects": [{"stamina": -1}],
        "end": False,
        "end_tag": ""
    }

def call_ollama(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Send chat messages to Ollama and parse compact JSON per our contract.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        # Ollama's /api/chat returns {"message":{"role":"assistant","content":"..."}, ...}
        content = ""
        if "message" in data and isinstance(data["message"], dict):
            content = data["message"].get("content", "") or ""
        elif "content" in data:
            content = data.get("content", "") or ""
        else:
            # Some servers return a list of messages
            content = str(data)
        return extract_json_block(content)
    except Exception:
        return {
            "narration": "The signal from the oracle is faint. You rely on instinct.",
            "encounter_type": random.choice(["exploration", "social", "puzzle"]),
            "choices": ["press on", "backtrack", "camp"],
            "effects": [{"stamina": -1}],
            "end": False,
            "end_tag": ""
        }

# Effects & Rules
def apply_effects(state: GameState, effects: List[Dict[str, Any]], via_encounter: bool) -> None:
    """
    Enforce school rules:
    - No negative final values.
    - Only allow add_item if via_encounter is True.
    """
    for eff in effects or []:
        if "health" in eff:
            try: state.health += int(eff["health"])
            except Exception: pass
        if "stamina" in eff:
            try: state.stamina += int(eff["stamina"])
            except Exception: pass
        if "gold" in eff:
            try: state.gold += int(eff["gold"])
            except Exception: pass
        if "add_item" in eff and via_encounter:
            item = str(eff["add_item"]).strip()
            if item and item not in state.inventory:
                state.inventory.append(item)
        if "remove_item" in eff:
            item = str(eff["remove_item"]).strip()
            if item in state.inventory:
                state.inventory.remove(item)
    # Clamp
    state.health  = max(0, state.health)
    state.stamina = max(0, state.stamina)
    state.gold    = max(0, state.gold)
    if state.health <= 0:
        state.ended = True
        state.end_tag = "death"

# Main Loop
def main():
    state = GameState.load(PLAYER_ID)
    chat: List[str] = []
    messages = load_messages(PLAYER_ID)

    # Intro shown once
    if state.encounters_seen == 0 and state.phase == "beginning":
        chat.append("AI: Your wagon creaks toward the frontier. A crossroads looms.")
        chat.append('AI: Choices → "press on" | "barter" | "make camp"')
        draw(chat, state)

    while not state.ended:
        # hard-stop ending if long enough to hit ≥20 encounters
        if state.phase == "ending" and state.encounters_seen >= 18:
            state.ended = True
            state.end_tag = random.choice([
                "retired_wealthy", "legend_told", "quiet_return", "lost_to_wilds", "mysterious_vanish"
            ])
            break

        user_text = prompt_user()
        if user_text.lower() in {"quit", "exit"}:
            print("Saving and exiting…")
            state.save()
            save_messages(PLAYER_ID, messages)
            sys.exit(0)
        if user_text.lower() in {"restart", "reset"}:
            # quick reset for demo
            state = GameState(player_id=PLAYER_ID)
            state.save()
            messages = [{"role": "system", "content": GUIDELINES}]
            save_messages(PLAYER_ID, messages)
            chat = []
            draw(chat, state)
            continue

        # Pick encounter type to nudge balance; send along as a JSON hint in the user turn
        hint = pick_encounter_type()
        user_payload = json.dumps({
            "request": user_text,
            "encounter_type_hint": hint,
            "player": {
                "health": state.health,
                "stamina": state.stamina,
                "gold": state.gold,
                "inventory": state.inventory,
                "phase": state.phase,
                "encounters_seen": state.encounters_seen
            }
        })

        messages = append_user(PLAYER_ID, user_payload)
        messages = truncate_messages(messages, keep_last=12)

        # Call model, expecting compact JSON
        out = call_ollama(messages)

        # Append raw assistant JSON back into history (so model remembers what it said)
        messages = append_assistant(PLAYER_ID, json.dumps(out, ensure_ascii=False))
        messages = truncate_messages(messages, keep_last=12)
        save_messages(PLAYER_ID, messages)

        # Apply effects with enforcement
        via_encounter = out.get("encounter_type", "none") in {"combat", "puzzle", "social", "exploration"}
        apply_effects(state, out.get("effects", []), via_encounter)

        # Update encounter pacing
        if via_encounter:
            state.encounters_seen += 1
            state.advance_phase()

        # Display
        nar = str(out.get("narration", "")).strip()
        choices = out.get("choices", [])
        if nar:
            chat.append("AI: " + nar)
        if choices:
            chat.append("AI: Choices → " + " | ".join(map(str, choices)))
        draw(chat, state)

        # End if model signals
        if bool(out.get("end", False)):
            state.ended = True
            tag = str(out.get("end_tag", "")).strip()
            if tag:
                state.end_tag = tag

        state.save()

    # End screen
    clear_screen()
    print("#" * 60)
    print("#                THE JOURNEY CONCLUDES                 #")
    print("#" * 60)
    print(f"Ending: {state.end_tag or 'faded trails'}")
    print(f"Encounters survived: {state.encounters_seen}")
    print(f"Final stats — Health {state.health} | Stamina {state.stamina} | Gold {state.gold}")
    print("Inventory:", ", ".join(state.inventory) if state.inventory else "(empty)")
    print("#" * 60)
    print("Tip: type 'restart' next time to begin fresh.")

if __name__ == "__main__":
    main()
