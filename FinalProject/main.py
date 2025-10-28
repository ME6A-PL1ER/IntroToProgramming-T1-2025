import sys
import requests

USE_AI_FLAVOR = True

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma3:1b"

DEBUG_AI = True

REWRITE_GUIDELINES = """
You are the Dungeon Master narrator for a wasteland trail adventure.

Task:
- Rewrite the scene description in 2–4 sentences of atmospheric narration, dont overdo it, make sure an 8th grader could read it.
- Keep the key facts from the given scene intact, but you may enhance tone and imagery.
- Do NOT add or list choices, option numbers, inventory, items, stats, or meta instructions.
- If this is not an ending scene, do NOT end the story or imply death.
- If this IS an ending scene, you may conclude the story consistent with the provided ending.

Output:
- Return plain text only, with no extra formatting or lists.
""".strip()

def ai_rewrite_scene(prev_scene_text, player_choice_text, scene_text, is_ending=False):
    """
    Rewrite the current scene description in a DM style using AI.
    Never includes choices; safely falls back to original text on failure.
    """
    if not USE_AI_FLAVOR:
        return scene_text

    try:
        user_prompt = (
            ("Previous scene:\n" + prev_scene_text + "\n\n") if prev_scene_text else ""
        )
        if player_choice_text:
            user_prompt += "Player chose:\n" + player_choice_text + "\n\n"
        user_prompt += "Scene begins:\n" + scene_text + "\n\n"
        user_prompt += (
            "Notes: This IS an ending scene. Conclude appropriately.\n"
            if is_ending else
            "Notes: This is NOT an ending scene. Do not conclude or kill the player.\n"
        )
        user_prompt += "Rewrite the scene description now."

        messages = [
            {"role": "system", "content": REWRITE_GUIDELINES},
            {"role": "user", "content": user_prompt},
        ]

        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        if DEBUG_AI and isinstance(data, dict) and "error" in data:
            print(f"[AI] Ollama error: {data['error']}", file=sys.stderr)

        if isinstance(data, dict) and isinstance(data.get("message"), dict):
            content = data["message"].get("content", "").strip()
            return content or scene_text

        if isinstance(data, dict) and "response" in data:
            content = str(data["response"]).strip()
            return content or scene_text

        if DEBUG_AI:
            print(f"[AI] Unexpected response: {data}", file=sys.stderr)
        return scene_text
    except Exception as e:
        if DEBUG_AI:
            print(f"[AI] Request failed: {e}", file=sys.stderr)
        return scene_text

SCENES = {
    # start scene (encounter 1)
    "start": {
        "text": (
            "Dust hangs in the air. You've been on the trail for days. "
            "Up ahead: a crooked sign points LEFT (river crossing) and RIGHT (abandoned outpost)."
        ),
        "choices": {
            "Go left toward the river crossing.": "river_crossing",
            "Go right toward the abandoned outpost.": "outpost_gate"
        }
    },

    # encounter 2
    "river_crossing": {
        "text": (
            "The river is low, but fast. You see wagon tracks vanishing into the mud. "
            "Something struggled here recently."
        ),
        "choices": {
            "Try to ford the river anyway.": "ford_attempt",
            "Look for whoever left the tracks.": "follow_tracks"
        }
    },

    # encounter 3
    "ford_attempt": {
        "text": (
            "Cold water claws at your legs. Halfway across, you slip and slam into hidden stone. "
            "You drag yourself up coughing."
        ),
        "choices": {
            "Push forward, soaking and shivering.": "across_river",
            "Turn back. This isn’t worth dying for.": "river_retreat"
        }
    },

    # encounter 4
    "follow_tracks": {
        "text": (
            "You follow the muddy imprints into scrub brush. You hear quiet crying. "
            "A small camp is hidden in the reeds."
        ),
        "choices": {
            "Call out gently.": "reeds_encounter",
            "Approach silently and observe.": "reeds_watch"
        }
    },

    # encounter 5
    "across_river": {
        "text": (
            "You reach the far bank. Your boots are heavy, your clothes freezing. "
            "On this side of the river you spot a burned wagon."
        ),
        "choices": {
            "Search the burned wagon.": "burned_wagon",
            "Keep moving down the trail.": "lonely_trail"
        }
    },

    # encounter 6
    "river_retreat": {
        "text": (
            "You back away from the current. Behind you, storm clouds are gathering like bruises."
        ),
        "choices": {
            "Make camp and wait out the weather.": "storm_camp",
            "Force yourself to march anyway.": "exhausted_march"
        }
    },

    # encounter 7
    "reeds_encounter": {
        "text": (
            "A ragged traveler looks up, startled. 'You’re not with them?' they whisper. "
            "'Please. Don’t let them take me back.'"
        ),
        "choices": {
            "Offer protection.": "protect_traveler",
            "Back away slowly.": "leave_traveler"
        }
    },

    # encounter 8
    "reeds_watch": {
        "text": (
            "You crouch behind brush. The crying stops. For a long moment, nothing moves. "
            "Then you feel eyes on you."
        ),
        "choices": {
            "Reveal yourself peacefully.": "protect_traveler",
            "Retreat. This is too weird.": "leave_traveler"
        }
    },

    # encounter 9
    "burned_wagon": {
        "text": (
            "The wagon’s been looted. You see scorch marks and old blood, not fresh. "
            "Whoever did this moved on."
        ),
        "choices": {
            "Follow the wagon ruts down the canyon.": "canyon_path",
            "Ignore it. You’ve seen enough death.": "lonely_trail"
        }
    },

    # encounter 10
    "lonely_trail": {
        "text": (
            "The trail ahead is silent. You feel watched, but not threatened. Just… noticed."
        ),
        "choices": {
            "Call out to the unseen watcher.": "voice_in_shade",
            "Keep walking and pretend you saw nothing.": "silent_march"
        }
    },

    # encounter 11
    "storm_camp": {
        "text": (
            "Wind rips your tarp. Lightning forks in the near hills. "
            "You're alone with your thoughts and the smell of wet dust."
        ),
        "choices": {
            "Stay awake and guard your camp.": "midnight_shapes",
            "Try to sleep through it.": "restless_sleep"
        }
    },

    # encounter 12
    "exhausted_march": {
        "text": (
            "You push onward. Your legs feel like anchors. You stop noticing the cold. "
            "You stop noticing much at all."
        ),
        "choices": {
            "Force yourself to keep going.": "collapse_road",
            "Sit down, just for a minute. Just to breathe.": "restless_sleep"
        }
    },

    # encounter 13
    "protect_traveler": {
        "text": (
            "They relax. 'Then I owe you.' Their eyes are hard despite the shaking hands. "
            "'You need to avoid the bridge.'"
        ),
        "choices": {
            "Ask about the bridge.": "ruined_bridge",
            "Ignore them and move on.": "lonely_trail"
        }
    },

    # encounter 14
    "leave_traveler": {
        "text": (
            "You back out through the reeds. The crying doesn’t start again. "
            "The air feels heavier now."
        ),
        "choices": {
            "Head back to the river crossing.": "river_retreat",
            "Head downtrail.": "lonely_trail"
        }
    },

    # encounter 15
    "canyon_path": {
        "text": (
            "The canyon narrows. Charred wagon wood litters both sides. "
            "The rocks are blackened and sharp."
        ),
        "choices": {
            "Keep following the tracks into the dark.": "ambush_site",
            "Turn around. This is a killing ground.": "lonely_trail"
        }
    },

    # encounter 16
    "voice_in_shade": {
        "text": (
            "A voice from nowhere: 'You shouldn’t be out here alone.' "
            "You can’t tell if it’s friendly or mocking."
        ),
        "choices": {
            "Ask for guidance.": "guide_offer",
            "Threaten whoever it is.": "bad_blood"
        }
    },

    # encounter 17
    "silent_march": {
        "text": (
            "You keep walking. Mile after mile. Eventually the fear becomes normal, "
            "like background noise."
        ),
        "choices": {
            "Sit and rest on a flat rock.": "rest_stop",
            "Keep pushing forward.": "collapse_road"
        }
    },

    # encounter 18
    "midnight_shapes": {
        "text": (
            "Something moved just outside the firelight. More than once."
        ),
        "choices": {
            "Call out to it.": "voice_in_shade",
            "Stay silent and watch.": "rest_stop"
        }
    },

    # encounter 19
    "restless_sleep": {
        "text": (
            "Your dreams are cracked glass. You wake unsure if dawn is real or you invented it."
        ),
        "choices": {
            "Pack up and move on.": "silent_march",
            "Stay. Just a little longer.": "collapse_road"
        }
    },

    # encounter 20
    "ruined_bridge": {
        "text": (
            "You reach the old bridge. Boards missing. Ropes frayed. "
            "The chasm below hums like a throat singing."
        ),
        "choices": {
            "Cross anyway.": "ending_fall",
            "Find another way around.": "canyon_path"
        }
    },

    # encounter 21
    "ambush_site": {
        "text": (
            "You find it. The place where someone made a stand. "
            "Scorch marks in a full circle. No bodies. No bones."
        ),
        "choices": {
            "Stay here and wait for whoever did this.": "ending_taken",
            "Walk away quietly.": "rest_stop"
        }
    },

    # encounter 22
    "rest_stop": {
        "text": (
            "For the first time today, you let yourself sit. Your heartbeat sounds like footsteps "
            "behind you, fading."
        ),
        "choices": {
            "Get back up and push on.": "collapse_road",
            "Head toward distant lantern light.": "ending_settlement"
        }
    },

    # encounter 23
    "guide_offer": {
        "text": (
            "The voice says, 'I can lead you somewhere safe. You won’t like the cost.'"
        ),
        "choices": {
            "Accept the guide.": "ending_servitude",
            "Refuse.": "collapse_road"
        }
    },

    # encounter 24
    "bad_blood": {
        "text": (
            "The air goes still. You feel, for a moment, hunted."
        ),
        "choices": {
            "Keep walking like you’re not scared.": "collapse_road",
            "Run.": "ending_taken"
        }
    },

    # encounter 25
    "collapse_road": {
        "text": (
            "Your legs finally betray you. Knees hit dirt. You see light. "
            "You wonder if it’s dawn."
        ),
        "choices": {
            "Reach toward the light.": "ending_fall",
            "Let darkness take you.": "ending_taken"
        }
    },

    # *** NEW PATH FOR OUTPOST ***
    # encounter 26
    "outpost_gate": {
        "text": (
            "The outpost sits behind leaning sheet-metal walls. The gate is half open. "
            "No lights. No voices. A hand-painted warning says: DO NOT ENTER AFTER DUSK."
        ),
        "choices": {
            "Slip inside the outpost anyway.": "outpost_inside",
            "Back away from the gate and head for the river instead.": "river_crossing"
        }
    },

    # encounter 27
    "outpost_inside": {
        "text": (
            "You step through the crooked gate. Wind moves something metal across the concrete "
            "with a slow scrape. The hairs rise on your arms. You are not alone in here."
        ),
        "choices": {
            "Call out: 'I don't want trouble.'": "voice_in_shade",
            "Hide and watch from the shadows.": "reeds_watch"
        }
    },

    # ENDINGS

    "ending_fall": {
        "text": (
            "Your vision tips and the world tilts with it. Wind howls up from below. "
            "You fall, and the trail ends here."
        ),
        "choices": {},
        "ending": "lost_to_wilds"
    },

    "ending_taken": {
        "text": (
            "Shapes emerge in the dark. They don’t feel cruel. They feel patient. "
            "You are lifted. You do not resist."
        ),
        "choices": {},
        "ending": "mysterious_vanish"
    },

    "ending_settlement": {
        "text": (
            "Lanterns. Fences. Quiet voices. A hidden settlement takes you in. "
            "You’re safe, but you’ll never really be free again."
        ),
        "choices": {},
        "ending": "quiet_return"
    },

    "ending_servitude": {
        "text": (
            "The guide leads you to walls, food, warmth. Your debt is permanent. "
            "Your life is no longer yours, but it is a life."
        ),
        "choices": {},
        "ending": "retired_wealthy"
    }
}


def run():
    scene_id = "start"
    encounter_count = 0
    prev_scene_text = ""
    prev_choice_text = ""

    while True:
        # if the scene isnt real then we just end the game
        scene = SCENES.get(scene_id)
        if scene is None:
            print("\nThe world ends here. There's nothing beyond this point.")
            print(f"(Missing scene: {scene_id})")
            break

        encounter_count += 1

        # Show scene (AI-rewritten if enabled)
        is_ending = "ending" in scene
        display_text = ai_rewrite_scene(prev_scene_text, prev_choice_text, scene["text"], is_ending)
        print("\n" + "=" * 60)
        print(display_text)
        print("=" * 60)

        if is_ending:
            print(f"\nTHE END: {scene['ending']}")
            print(f"Encounters experienced: {encounter_count}")
            break

        options = list(scene["choices"].keys())
        for i, choice_text in enumerate(options, start=1):
            print(f"{i}. {choice_text}")

        pick = input("> ").strip()

        # Validate input 
        try:
            idx = int(pick) - 1
            assert 0 <= idx < len(options)
        except:
            print("\nYou hesitate too long. The wasteland swallows the moment, and your story ends unfinished.")
            break

        chosen_text = options[idx]
        next_scene_id = scene["choices"][chosen_text]

        # Remember context for next scene rewrite
        prev_scene_text = scene["text"]
        prev_choice_text = chosen_text

        scene_id = next_scene_id


if __name__ == "__main__":
    run()
