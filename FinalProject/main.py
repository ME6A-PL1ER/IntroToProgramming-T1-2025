import sys
import time
import threading
import requests


AI_FLAVORED_ICE_CREAM = True

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

def _run_with_spinner(work_fn, message="The DM is thinking..."):
    """Run a blocking function while showing a console spinner.
    Returns the function's result. Spinner only affects stdout.
    """
    stop = threading.Event()

    def spin():
        frames = "|/-\\"
        i = 0
        try:
            while not stop.is_set():
                sys.stdout.write("\r" + message + " " + frames[i % len(frames)])
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1
        finally:
            # Clear the spinner line
            sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
            sys.stdout.flush()

    t = threading.Thread(target=spin, daemon=True)
    t.start()
    try:
        return work_fn()
    finally:
        stop.set()
        t.join()

def ai_rewrite_scene(prev_scene_text, player_choice_text, scene_text, is_ending=False):
    """
    Rewrite the current scene description in a DM style using AI.
    """
    if not AI_FLAVORED_ICE_CREAM:
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
            "You carry a satchel of fever medicine meant for Haven before nightfall. "
            "At a fork, a crooked sign points LEFT—river ford—and RIGHT—Redline Outpost. The wind smells like rain."
        ),
        "choices": {
            "Go left toward the river crossing.": "river_crossing",
            "Go right toward the abandoned outpost.": "outpost_gate"
        }
    },

    # encounter 2
    "river_crossing": {
        "text": (
            "The river runs low but swift, frothing around black stones. Fresh wagon ruts slide into the mud and vanish at the bank. "
            "Someone forced a crossing not long ago."
        ),
        "choices": {
            "Try to ford the river anyway.": "ford_attempt",
            "Look for whoever left the tracks.": "follow_tracks"
        }
    },

    # encounter 3
    "ford_attempt": {
        "text": (
            "Ice water climbs past your knees. The current tugs your legs sideways; your shoulder smashes a hidden rock. "
            "Breath gone, you cling and choose."
        ),
        "choices": {
            "Push forward, soaking and shivering.": "across_river",
            "Turn back. This isn’t worth dying for.": "river_retreat"
        }
    },

    # encounter 4
    "follow_tracks": {
        "text": (
            "You trace the ruts into thorn and reed. Quiet sobbing rides the wind. "
            "A makeshift camp crouches under a bent bush."
        ),
        "choices": {
            "Call out gently.": "reeds_encounter",
            "Approach silently and observe.": "reeds_watch"
        }
    },

    # encounter 5
    "across_river": {
        "text": (
            "You drag yourself onto the far bank, clothes heavy and fingers numb. "
            "Ahead, a wagon sits gutted and burned, the ash still cold."
        ),
        "choices": {
            "Search the burned wagon.": "burned_wagon",
            "Keep moving down the trail.": "lonely_trail"
        }
    },

    # encounter 6
    "river_retreat": {
        "text": (
            "You step back from the churning water. Thunder rolls upriver; a storm gathers like a bruise. "
            "Every minute you lose is a minute the fevers burn hotter in Haven."
        ),
        "choices": {
            "Make camp and wait out the weather.": "storm_camp",
            "Force yourself to march anyway.": "exhausted_march"
        }
    },

    # encounter 7
    "reeds_encounter": {
        "text": (
            "A bandaged courier startles, eyes wide. 'Not with the Bridge Men?' they rasp. "
            "'They mined the old span. Please—don’t take the ford or they'll hear you.'"
        ),
        "choices": {
            "Offer protection.": "protect_traveler",
            "Back away slowly.": "leave_traveler"
        }
    },

    # encounter 8
    "reeds_watch": {
        "text": (
            "From the shadows you watch. The sobbing fades into careful, measured breaths. "
            "Whoever hides out there knows watchers—and now they’ve seen you."
        ),
        "choices": {
            "Reveal yourself peacefully.": "protect_traveler",
            "Retreat. This is too weird.": "leave_traveler"
        }
    },

    # encounter 9
    "burned_wagon": {
        "text": (
            "Charred ribs of the wagon jut like bones. Scattered vials glitter in the ash—emptied and trampled. "
            "Whoever hit them rolled on."
        ),
        "choices": {
            "Follow the wagon ruts down the canyon.": "canyon_path",
            "Ignore it. You’ve seen enough death.": "lonely_trail"
        }
    },

    # encounter 10
    "lonely_trail": {
        "text": (
            "Back on the open trail, the sky goes wide and gray. You feel watched—measured, not menaced."
        ),
        "choices": {
            "Call out to the unseen watcher.": "voice_in_shade",
            "Keep walking and pretend you saw nothing.": "silent_march"
        }
    },

    # encounter 11
    "storm_camp": {
        "text": (
            "Wind tears at your tarp; grit needles your face. Lightning claws along the far ridge. "
            "The medicine thumps in your satchel like a second heartbeat."
        ),
        "choices": {
            "Stay awake and guard your camp.": "midnight_shapes",
            "Try to sleep through it.": "restless_sleep"
        }
    },

    # encounter 12
    "exhausted_march": {
        "text": (
            "You push onward until thought runs smooth and empty. The world narrows to the next step and the next."
        ),
        "choices": {
            "Force yourself to keep going.": "collapse_road",
            "Sit down, just for a minute. Just to breathe.": "restless_sleep"
        }
    },

    # encounter 13
    "protect_traveler": {
        "text": (
            "They unclench a little. 'Haven sent me to scout,' they whisper. Despite the shakes, their eyes are clear. "
            "'Avoid Black Chasm. Raiders rigged the old bridge. Take the canyon or skirt south.'"
        ),
        "choices": {
            "Ask about the bridge.": "ruined_bridge",
            "Ignore them and move on.": "lonely_trail"
        }
    },

    # encounter 14
    "leave_traveler": {
        "text": (
            "You back away without a word. The crying doesn’t return. The air feels heavier, like you’ve left a kindness undone."
        ),
        "choices": {
            "Head back to the river crossing.": "river_retreat",
            "Head downtrail.": "lonely_trail"
        }
    },

    # encounter 15
    "canyon_path": {
        "text": (
            "The canyon pinches into a stone throat. Charred wood and bootprints stipple the sand. "
            "Light thins to a dim ribbon ahead."
        ),
        "choices": {
            "Keep following the tracks into the dark.": "ambush_site",
            "Turn around. This is a killing ground.": "lonely_trail"
        }
    },

    # encounter 16
    "voice_in_shade": {
        "text": (
            "A voice slides out from behind a collapsed billboard: 'You shouldn’t be out here alone.' "
            "It isn’t quite friendly, but it knows the roads."
        ),
        "choices": {
            "Ask for guidance.": "guide_offer",
            "Threaten whoever it is.": "bad_blood"
        }
    },

    # encounter 17
    "silent_march": {
        "text": (
            "You walk mile after mile until fear fades to background noise and only wind remains."
        ),
        "choices": {
            "Sit and rest on a flat rock.": "rest_stop",
            "Keep pushing forward.": "collapse_road"
        }
    },

    # encounter 18
    "midnight_shapes": {
        "text": (
            "Shapes move just outside the firelight—three, maybe four—circling as if testing fences you can’t see."
        ),
        "choices": {
            "Call out to it.": "voice_in_shade",
            "Stay silent and watch.": "rest_stop"
        }
    },

    # encounter 19
    "restless_sleep": {
        "text": (
            "Your sleep comes in ragged stitches. In every dream, lanterns bob just out of reach."
        ),
        "choices": {
            "Pack up and move on.": "silent_march",
            "Stay. Just a little longer.": "collapse_road"
        }
    },

    # encounter 20
    "ruined_bridge": {
        "text": (
            "You reach Black Chasm. The old bridge hangs in ribbons—boards missing, ropes frayed to hair. "
            "Far below, the river speaks in cold thunder."
        ),
        "choices": {
            "Cross anyway.": "ending_fall",
            "Find another way around.": "canyon_path"
        }
    },

    # encounter 21
    "ambush_site": {
        "text": (
            "Here someone made a stand. Scorch rings freckle the stone; spent shells glitter like dull teeth. "
            "No bodies—only the feeling of a held breath."
        ),
        "choices": {
            "Stay here and wait for whoever did this.": "ending_taken",
            "Walk away quietly.": "rest_stop"
        }
    },

    # encounter 22
    "rest_stop": {
        "text": (
            "For the first time today you sit. The satchel presses its weight into your lap. Your heartbeat becomes distant footfalls."
        ),
        "choices": {
            "Get back up and push on.": "collapse_road",
            "Head toward distant lantern light.": "ending_settlement"
        }
    },

    # encounter 23
    "guide_offer": {
        "text": (
            "'I can get you to Haven,' the voice says. 'Alive, quick, clean. You won’t like the cost.'"
        ),
        "choices": {
            "Accept the guide.": "ending_servitude",
            "Refuse.": "collapse_road"
        }
    },

    # encounter 24
    "bad_blood": {
        "text": (
            "The air goes still. Whoever hides there decides what you are. For a heartbeat, you are prey."
        ),
        "choices": {
            "Keep walking like you’re not scared.": "collapse_road",
            "Run.": "ending_taken"
        }
    },

    # encounter 25
    "collapse_road": {
        "text": (
            "At last your knees fold. Dirt meets your cheek warm as a hand. Ahead, a light flares—lantern or lightning, you can’t tell."
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
            "Redline Outpost crouches behind leaning sheet‑metal walls. The gate hangs half open. "
            "No lights. No voices. A hand‑painted warning reads: DO NOT ENTER AFTER DUSK."
        ),
        "choices": {
            "Slip inside the outpost anyway.": "outpost_inside",
            "Back away from the gate and head for the river instead.": "river_crossing"
        }
    },

    # encounter 27
    "outpost_inside": {
        "text": (
            "You slip through the crooked gate. Wind drags something metal across the concrete with a slow scrape. "
            "Hair rises along your arms. You are not alone."
        ),
        "choices": {
            "Call out: 'I don't want trouble.'": "voice_in_shade",
            "Hide and watch from the shadows.": "reeds_watch"
        }
    },

    # ENDINGS

    "ending_fall": {
        "text": (
            "You stumble where the cliff has eaten the road. The world drops away; the chasm takes you quick and clean."
        ),
        "choices": {},
        "ending": "lost_to_the_chasm"
    },

    "ending_taken": {
        "text": (
            "Figures bloom from the dark—silent, certain. Rough hands find you; cloth covers your face. "
            "The medicine goes one way. You go another."
        ),
        "choices": {},
        "ending": "captured_by_raiders"
    },

    "ending_settlement": {
        "text": (
            "Lanterns gleam on a palisade as voices rise in relief. Haven’s gate swings wide. "
            "The medicine reaches trembling hands. Tonight, hope wins."
        ),
        "choices": {},
        "ending": "haven_reached"
    },

    "ending_servitude": {
        "text": (
            "The guide threads forgotten paths to stout walls and warm light. When the gate shuts, a ledger opens. "
            "Debts here are lifetime things."
        ),
        "choices": {},
        "ending": "bound_by_bargain"
    }
}


def run():
    if input("Enable AI-flavored ice cream narration? (y/n): ").strip().lower().startswith('n'):
        global AI_FLAVORED_ICE_CREAM
        AI_FLAVORED_ICE_CREAM = False
    scene_id = "start"
    encounter_count = 0
    prev_scene_text = ""
    prev_choice_text = ""
    next_display_text_cache = None

    while True:
        scene = SCENES.get(scene_id)
        if scene is None:
            print("\nThe world ends here. There's nothing beyond this point.")
            print(f"(Missing scene: {scene_id})")
            break

        encounter_count += 1

        is_ending = "ending" in scene
        if next_display_text_cache is not None:
            display_text = next_display_text_cache
            next_display_text_cache = None
        else:
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

        try:
            idx = int(pick) - 1
            assert 0 <= idx < len(options)
        except:
            print("\nYou hesitate too long. The wasteland swallows the moment, and your story ends unfinished.")
            break

        chosen_text = options[idx]
        next_scene_id = scene["choices"][chosen_text]

        prev_scene_text = scene["text"]
        prev_choice_text = chosen_text

        next_scene = SCENES.get(next_scene_id)
        if next_scene is None:
            print("\nYou move forward into uncharted territory... and the story simply stops being written.")
            print(f"(Scene '{next_scene_id}' not implemented.)")
            print(f"Encounters experienced: {encounter_count}")
            break

        if AI_FLAVORED_ICE_CREAM:
            def _work():
                return ai_rewrite_scene(prev_scene_text, prev_choice_text, next_scene["text"], "ending" in next_scene)

            next_display_text_cache = _run_with_spinner(_work, "The DM is thinking...")
        else:
            next_display_text_cache = next_scene["text"]

        scene_id = next_scene_id


if __name__ == "__main__":
    run()
