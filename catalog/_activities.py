"""Komodo Wellbeing Flash Cards — activity data.

Source: MERCHRESOURCES Wellbeing Flash Cards (125 x 90 mm).pdf
Each Activity has:
  - id, name, age, props_needed/props_description
  - emoji: hero icon shown large on the card
  - purposes: tags for filter and themed sets
  - duration_minutes: suggested run-time
  - objective: psychologist-written rationale
  - instructions: prose version used on the browse card
  - steps: structured list of step dicts (for stepped/list widgets)
  - interactive_type: which interactive widget to render
  - widget_config: type-specific parameters
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Activity:
    id: str
    name: str
    age: str               # "Jr" | "Sr" | "All"
    emoji: str
    props_needed: bool
    props_description: str
    purposes: tuple[str, ...]
    duration_minutes: int
    objective: str
    instructions: str
    steps: tuple[dict[str, Any], ...]
    interactive_type: str  # "breathe" | "bilateral" | "stepped" | "list_prompts" | "timer_simple" | "weather_pick" | "colour_breath" | "creative_pad"
    widget_config: dict[str, Any] = field(default_factory=dict)


ACTIVITIES: list[Activity] = [
    Activity(
        id="five_senses_checkin",
        name="Five senses check-in",
        age="All",
        emoji="👀",
        props_needed=False,
        props_description="",
        purposes=("Grounding", "Mindfulness", "Calming"),
        duration_minutes=3,
        objective=(
            "Promotes mindfulness and emotional regulation by engaging students' senses "
            "and focusing on the present experience. Helps manage stress, reduce anxiety, "
            "and enhance emotional awareness."
        ),
        instructions=(
            "Name 5 things you can see, 4 things you can touch, 3 things you can hear, "
            "2 things you can smell & 1 thing you can taste."
        ),
        steps=(
            {"icon": "👀", "label": "5 things you can SEE", "count": 5, "placeholder": "e.g. the window, a pencil…"},
            {"icon": "✋", "label": "4 things you can TOUCH", "count": 4, "placeholder": "e.g. my desk, my jumper…"},
            {"icon": "👂", "label": "3 things you can HEAR", "count": 3, "placeholder": "e.g. footsteps, my breath…"},
            {"icon": "👃", "label": "2 things you can SMELL", "count": 2, "placeholder": "e.g. paper, fresh air…"},
            {"icon": "👅", "label": "1 thing you can TASTE", "count": 1, "placeholder": "e.g. toothpaste, water…"},
        ),
        interactive_type="list_prompts",
    ),
    Activity(
        id="feeling_scan",
        name="Feeling scan",
        age="All",
        emoji="💗",
        props_needed=False,
        props_description="",
        purposes=("Emotional awareness", "Breathing", "Mindfulness"),
        duration_minutes=3,
        objective=(
            "Enhances students' emotional awareness and mindfulness skills by helping them "
            "connect with their emotions physically. Through deep breathing and 'spotlighting' "
            "body sensations, they learn emotional literacy, regulation, and build resilience."
        ),
        instructions=(
            "Close your eyes and name the emotion you're feeling. Notice where it sits in your "
            "body. Breathe deeply into that part of your body and slowly exhale."
        ),
        steps=(
            {"icon": "🧘", "label": "Close your eyes", "body": "Take a quiet moment. Settle into your seat."},
            {"icon": "🏷️", "label": "Name the emotion", "body": "What emotion are you experiencing right now? Just one word is enough."},
            {"icon": "📍", "label": "Locate it in your body", "body": "Where do you feel this? In your chest? Stomach? Throat? Shoulders?"},
            {"icon": "🌬️", "label": "Breathe into it", "body": "Take a slow breath in, imagining the breath reaching that part of your body. Slowly exhale."},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 20},
    ),
    Activity(
        id="sensory_stomp_shake",
        name="Sensory stomp & shake",
        age="Jr",
        emoji="👟",
        props_needed=False,
        props_description="",
        purposes=("Energy release", "Calming"),
        duration_minutes=1,
        objective=(
            "Helps students release excess energy or emotion by engaging in physical movement. "
            "Stomping and shaking the body for 30 seconds can promote regulation and focus. "
            "The deep breath at the end encourages a sense of calm and mindfulness."
        ),
        instructions=(
            "Regulate excess energy by stomping your feet and shaking your arms and legs for "
            "30 seconds. Finish with one big, deep breath."
        ),
        steps=(),
        interactive_type="timer_simple",
        widget_config={
            "seconds": 30,
            "prompt": "Stomp your feet 👣 — Shake your arms 🙌 — Shake your legs 🦵",
            "finish_prompt": "Now take ONE BIG, DEEP BREATH 🌬️",
            "animation": "stomp_shake",
        },
    ),
    Activity(
        id="what_keeps_me_well",
        name="What keeps me well?",
        age="Sr",
        emoji="🌿",
        props_needed=True,
        props_description="A device or creative supplies (paper, pens, magazines)",
        purposes=("Self-reflection", "Creative expression", "Self-worth"),
        duration_minutes=20,
        objective=(
            "Encourages students to reflect on what promotes their wellbeing by creating "
            "personalised resources like posters, collages, or playlists. Fosters emotional "
            "connection and self-expression."
        ),
        instructions=(
            "Reflect on what brings you peace, joy, or comfort. Then create something — a "
            "poster, collage, playlist, screensaver, or voice message — that captures it. Keep "
            "it somewhere you can see it."
        ),
        steps=(
            {"icon": "💭", "label": "People who bring me joy", "placeholder": "Names of people who make you feel good…", "count": 1, "multiline": True},
            {"icon": "🎨", "label": "Activities I love", "placeholder": "Things you do that bring peace, fun, or focus…", "count": 1, "multiline": True},
            {"icon": "🎶", "label": "Sounds, songs or colours that calm me", "placeholder": "Anything sensory that helps you settle…", "count": 1, "multiline": True},
            {"icon": "📍", "label": "Places I feel safe", "placeholder": "Where do you feel most yourself?", "count": 1, "multiline": True},
            {"icon": "✨", "label": "One thing I'll make / save this week", "placeholder": "A poster, a playlist, a screensaver…", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
    ),
    Activity(
        id="personal_cheerleader",
        name="Personal cheerleader",
        age="All",
        emoji="📣",
        props_needed=True,
        props_description="A device or pen & paper",
        purposes=("Self-worth", "Self-reflection", "Positivity"),
        duration_minutes=10,
        objective=(
            "Helps students reflect on their strengths and boost self-esteem through positive "
            "affirmations. Writing and repeating affirmations builds confidence and reinforces "
            "emotional resilience."
        ),
        instructions=(
            "Write 3 positive affirmations about who you are — qualities you value, strengths "
            "you've grown, or moments you're proud of."
        ),
        steps=(
            {"icon": "1️⃣", "label": "Affirmation #1", "placeholder": "e.g. One thing that makes me special is…", "count": 1, "multiline": True},
            {"icon": "2️⃣", "label": "Affirmation #2", "placeholder": "e.g. I am getting better at…", "count": 1, "multiline": True},
            {"icon": "3️⃣", "label": "Affirmation #3", "placeholder": "e.g. I feel strong when I…", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
        widget_config={
            "examples": [
                "One thing that makes me special is…",
                "I am getting better at…",
                "Something I like about me is…",
                "I am kind because I…",
                "I am a good friend because I…",
                "I feel strong when I…",
                "I am happy when I…",
            ],
        },
    ),
    Activity(
        id="positive_outlook",
        name="Positive outlook",
        age="All",
        emoji="🌅",
        props_needed=False,
        props_description="",
        purposes=("Positivity", "Social connection"),
        duration_minutes=3,
        objective=(
            "Helps students shift their focus to positive experiences by sharing something they "
            "are looking forward to. Talking about upcoming events encourages optimism and "
            "enhances social connections."
        ),
        instructions=(
            "Turn to the person beside you and tell them ONE thing you're looking forward to "
            "today or this week."
        ),
        steps=(
            {"icon": "👋", "label": "Turn to the person beside you", "body": "Make eye contact. Say hello."},
            {"icon": "💬", "label": "Share ONE thing you're looking forward to", "body": "Today, this week, this term — anything at all."},
            {"icon": "👂", "label": "Now switch — listen to theirs", "body": "Notice how it feels to hear someone else's good news."},
        ),
        interactive_type="stepped",
    ),
    Activity(
        id="highlight_reel",
        name="Highlight reel",
        age="All",
        emoji="🌟",
        props_needed=False,
        props_description="",
        purposes=("Gratitude", "Positivity", "Self-reflection"),
        duration_minutes=5,
        objective=(
            "Encourages students to reflect on the positive aspects of their day. Sharing 3 "
            "positive experiences fosters gratitude, boosts mood, and promotes a positive mindset."
        ),
        instructions=(
            "Share 3 things — big or small — that have gone well for you today."
        ),
        steps=(
            {"icon": "🌟", "label": "Highlight #1", "placeholder": "Something that went well today…", "count": 1, "multiline": True},
            {"icon": "🌟", "label": "Highlight #2", "placeholder": "Even something small counts…", "count": 1, "multiline": True},
            {"icon": "🌟", "label": "Highlight #3", "placeholder": "A win, a kindness, a moment…", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
    ),
    Activity(
        id="guided_imagery",
        name="Guided imagery",
        age="Sr",
        emoji="🏞️",
        props_needed=False,
        props_description="",
        purposes=("Calming", "Mindfulness", "Visualisation"),
        duration_minutes=8,
        objective=(
            "Encourages students to visualise a peaceful space to reduce stress and promote "
            "relaxation. Provides a mental escape during times of difficult emotions."
        ),
        instructions=(
            "Sit comfortably, close your eyes, and travel in your mind to a calm and happy "
            "place. Notice the sights, sounds, and feelings of that place — then return gently."
        ),
        steps=(
            {"icon": "🪑", "label": "Get comfortable", "body": "Sit with both feet on the floor. Close your eyes. Take one deep breath."},
            {"icon": "🌅", "label": "Travel to a calm, happy place", "body": "Picture it as clearly as you can. It might be a beach, a forest, your bedroom, somewhere from a holiday."},
            {"icon": "👀", "label": "Look around", "body": "What do you see? What colours? What's near you, what's far?"},
            {"icon": "👂", "label": "Listen", "body": "What can you hear in this place? Wind, water, voices, silence?"},
            {"icon": "💛", "label": "Notice how it feels", "body": "Safe? Warm? Relaxed? Sit with that feeling for a moment."},
            {"icon": "🌬️", "label": "Come back gently", "body": "Take a deep breath. Wiggle your fingers and toes. Slowly open your eyes."},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 45},
    ),
    Activity(
        id="five_finger_breathing",
        name="Five finger breathing",
        age="All",
        emoji="✋",
        props_needed=False,
        props_description="",
        purposes=("Breathing", "Calming", "Grounding", "Mindfulness"),
        duration_minutes=3,
        objective=(
            "Promotes mindfulness and relaxation by combining breath with a calming tactile "
            "activity. Tracing around the fingers grounds students in the present moment."
        ),
        instructions=(
            "Hold out one hand. Use the index finger of your other hand to slowly trace up and "
            "down each finger — breathe IN going up, breathe OUT coming down. Trace your whole "
            "hand twice."
        ),
        steps=(),
        interactive_type="breathe",
        widget_config={
            "mode": "five_finger",
            "in_seconds": 4,
            "out_seconds": 4,
            "cycles": 10,
        },
    ),
    Activity(
        id="gratitude_chain",
        name="Gratitude chain",
        age="All",
        emoji="💛",
        props_needed=False,
        props_description="",
        purposes=("Gratitude", "Social connection", "Positivity"),
        duration_minutes=3,
        objective=(
            "Promotes gratitude by encouraging students to reflect and share positive "
            "experiences. Expressing gratitude boosts mood and strengthens social connections."
        ),
        instructions=(
            "Turn to the person beside you and tell them ONE thing you're grateful for today "
            "or this week."
        ),
        steps=(
            {"icon": "💛", "label": "Something I'm grateful for today is…", "placeholder": "A person, a moment, something small…", "count": 1, "multiline": True},
            {"icon": "💛", "label": "Something I'm grateful for this week is…", "placeholder": "Something that helped, made you smile, or lifted you…", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
    ),
    Activity(
        id="butterfly_hugs",
        name="Butterfly hugs",
        age="All",
        emoji="🦋",
        props_needed=False,
        props_description="",
        purposes=("Calming", "Grounding", "Anxiety response"),
        duration_minutes=2,
        objective=(
            "Helps students regulate emotions and calm their nervous system using bilateral "
            "stimulation. Reduces anxiety, brings attention to the present moment, and "
            "fosters a sense of safety and emotional balance."
        ),
        instructions=(
            "Cross your arms over your chest with a hand on each upper arm. Alternate tapping "
            "left, right, left, right — slowly, for about 2 minutes."
        ),
        steps=(),
        interactive_type="bilateral",
        widget_config={
            "tap_interval_ms": 900,
            "total_seconds": 120,
        },
    ),
    Activity(
        id="draw_it_out",
        name="Draw it out",
        age="Jr",
        emoji="🎨",
        props_needed=True,
        props_description="A device with drawing software, or paper & colouring supplies",
        purposes=("Creative expression", "Emotional awareness", "Self-reflection"),
        duration_minutes=10,
        objective=(
            "Helps students diffuse difficult emotions by using art to express their feelings. "
            "Drawing externalises worries and reduces emotional intensity."
        ),
        instructions=(
            "Draw how you're feeling. Imagine the feeling as a creature, a kind of weather, a "
            "shape, a colour, or an object. Use the pad below — choose a colour and brush size."
        ),
        steps=(),
        interactive_type="canvas",
        widget_config={
            "width": 640,
            "height": 380,
        },
    ),
    Activity(
        id="inner_weather_report",
        name="The inner weather report",
        age="Jr",
        emoji="🌤️",
        props_needed=True,
        props_description="Paper & pens, or a device",
        purposes=("Emotional awareness", "Creative expression", "Self-reflection"),
        duration_minutes=8,
        objective=(
            "Develops emotional recognition and awareness using weather metaphors to "
            "externalise complex feelings, making them easier to identify, communicate, and "
            "proactively manage."
        ),
        instructions=(
            "If your mood was weather, what would it be? Write a forecast for the rest of the "
            "day, and one thing you'll do to prepare."
        ),
        steps=(),
        interactive_type="weather_pick",
        widget_config={
            "options": [
                {"emoji": "☀️", "label": "Sunny", "feel": "Bright, happy, energised"},
                {"emoji": "⛅", "label": "Partly cloudy", "feel": "Okay, a bit mixed"},
                {"emoji": "☁️", "label": "Overcast", "feel": "Flat, dull, low energy"},
                {"emoji": "🌫️", "label": "Foggy", "feel": "Hard to think, unfocused"},
                {"emoji": "🌦️", "label": "Light drizzle", "feel": "A bit sad or unsettled"},
                {"emoji": "⛈️", "label": "Thunderstorm", "feel": "Frustrated, overwhelmed"},
                {"emoji": "🌪️", "label": "Tornado", "feel": "Spinning, lots happening inside"},
                {"emoji": "❄️", "label": "Snowy", "feel": "Quiet, frozen, withdrawn"},
            ],
        },
    ),
    Activity(
        id="tense_release",
        name="Tense & release",
        age="All",
        emoji="💪",
        props_needed=False,
        props_description="",
        purposes=("Calming", "Energy release", "Grounding"),
        duration_minutes=4,
        objective=(
            "Helps students release tension and promote relaxation by moving through different "
            "muscle groups. Builds awareness of where the body holds tension."
        ),
        instructions=(
            "Move through the body, tensing each muscle group for a few seconds then releasing. "
            "Start at the eyebrows and work down to the feet. Shake it all off at the end."
        ),
        steps=(
            {"icon": "🤨", "label": "Eyebrows & eyes", "body": "Scrunch up your face — eyebrows up, eyes squeezed shut. Hold… and release."},
            {"icon": "😬", "label": "Jaw", "body": "Clench your teeth gently. Hold… and release. Let your jaw drop loose."},
            {"icon": "💪", "label": "Shoulders", "body": "Lift your shoulders up to your ears. Hold… and let them drop heavy."},
            {"icon": "🫃", "label": "Stomach", "body": "Tighten your belly muscles. Hold… and release."},
            {"icon": "🤜", "label": "Hands", "body": "Squeeze your hands into fists. Hold… and stretch your fingers wide."},
            {"icon": "🦵", "label": "Legs", "body": "Tighten your thigh muscles. Hold… and release."},
            {"icon": "🦶", "label": "Feet", "body": "Curl your toes tight. Hold… and release."},
            {"icon": "🌀", "label": "Shake it all off", "body": "10 seconds. Shake out your hands, arms, legs, and body."},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 12},
    ),
    Activity(
        id="sensory_scrunch",
        name="Sensory scrunch",
        age="All",
        emoji="🧻",
        props_needed=True,
        props_description="Towels, paper, tissues or other sensory items",
        purposes=("Energy release", "Grounding", "Calming"),
        duration_minutes=3,
        objective=(
            "Helps students release tension and excess energy through controlled physical "
            "manipulation of paper or fabric. Tactile sensations ground the body and distract "
            "from difficult emotions."
        ),
        instructions=(
            "Pick up a piece of paper, tissue, or towel. Scrunch, rip, twist, or squeeze it for "
            "a minute or two. Then finish with one deep breath."
        ),
        steps=(),
        interactive_type="timer_simple",
        widget_config={
            "seconds": 90,
            "prompt": "Scrunch 🤏 — Rip ✂️ — Twist 🔄 — Squeeze 🤜",
            "finish_prompt": "Now take ONE BIG, DEEP BREATH 🌬️",
            "animation": "squeeze",
        },
    ),
    Activity(
        id="shape_shifting",
        name="Shape-shifting",
        age="Jr",
        emoji="🦒",
        props_needed=False,
        props_description="",
        purposes=("Energy release", "Mindfulness", "Creative expression"),
        duration_minutes=5,
        objective=(
            "Regulates energy through playful movement. Shifting from stiff to wobbly, or tall "
            "to small, promotes mindfulness, body awareness, and grounding."
        ),
        instructions=(
            "Stand tall and breathe deeply. Pick a transformation — try going from a tall "
            "TREE into a wobbly JELLY, or a tall GIRAFFE into a tiny BUG. Hold each shape for "
            "a moment, then morph."
        ),
        steps=(
            {"icon": "🌳", "label": "TREE → 🍮 JELLY", "body": "Stand tall and still like a tree. Slowly soften and wobble into jelly."},
            {"icon": "🦒", "label": "GIRAFFE → 🐞 BUG", "body": "Reach up tall like a giraffe. Slowly shrink down small like a bug."},
            {"icon": "⛄", "label": "SNOWMAN → 💧 PUDDLE", "body": "Stand stiff and round like a snowman. Slowly melt down into a puddle."},
            {"icon": "🌬️", "label": "Big breath", "body": "Now stand still and take one big, deep breath. Notice how your body feels."},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 20},
    ),
    Activity(
        id="appreciation_postits",
        name="Appreciation post-its",
        age="Sr",
        emoji="📝",
        props_needed=True,
        props_description="Post-it notes & pens",
        purposes=("Gratitude", "Social connection", "Positivity"),
        duration_minutes=10,
        objective=(
            "Fosters positive relationships and a culture of kindness by encouraging students "
            "to acknowledge and celebrate the character strengths and positive actions of "
            "their peers."
        ),
        instructions=(
            "Write a specific compliment or note of gratitude for a classmate, focused on "
            "something they DID — not how they look. Place it on their desk or an "
            "Appreciation Wall."
        ),
        steps=(
            {"icon": "📝", "label": "Grab a sticky note", "body": "Each person picks up one sticky note and a pen."},
            {"icon": "🎲", "label": "Pick a classmate", "body": "Pull a name from a hat — or assign randomly to make sure everyone gets one."},
            {"icon": "💛", "label": "Write a SPECIFIC compliment", "body": "Focus on something they DID or a character trait. Avoid comments about appearance.\n\nExamples:\n• \"Thanks for helping me with…\"\n• \"You were really brave when…\"\n• \"You make our group better because…\""},
            {"icon": "🧱", "label": "Place it on the Appreciation Wall", "body": "Stick it on their desk or a shared wall where everyone can see them grow."},
        ),
        interactive_type="stepped",
    ),
    Activity(
        id="circle_of_safety",
        name="Circle of safety & support",
        age="Sr",
        emoji="🤝",
        props_needed=True,
        props_description="A device, whiteboard, or large piece of paper",
        purposes=("Self-reflection", "Social connection", "Self-worth"),
        duration_minutes=15,
        objective=(
            "Helps students identify individuals who provide emotional safety and support. "
            "Strengthens emotional resilience and encourages students to lean on their circle "
            "when facing challenges."
        ),
        instructions=(
            "Fill out concentric circles with the names of real people who support you. "
            "Family, Friends, School/Work, and the wider Community."
        ),
        steps=(
            {"icon": "👪", "label": "Family", "placeholder": "Names of family who support you…", "count": 1, "multiline": True},
            {"icon": "🧑‍🤝‍🧑", "label": "Friends", "placeholder": "Names of friends who are there for you…", "count": 1, "multiline": True},
            {"icon": "🏫", "label": "School / Work", "placeholder": "Teachers, coaches, counsellors, colleagues, managers…", "count": 1, "multiline": True},
            {"icon": "🌍", "label": "Wider Community", "placeholder": "GP, youth worker, club leader, religious leader…", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
    ),
    Activity(
        id="tension_tamers",
        name="Tension tamers",
        age="Jr",
        emoji="🌀",
        props_needed=False,
        props_description="",
        purposes=("Energy release", "Grounding", "Calming"),
        duration_minutes=3,
        objective=(
            "Helps students manage emotions and energy through a range of movements. Promotes "
            "grounding, control, and a mind-body connection."
        ),
        instructions=(
            "Choose a movement and do it for about 30 seconds. Try rocking, crawling, stomping, "
            "twisting, spinning, tapping, or pushing your hands against a wall."
        ),
        steps=(),
        interactive_type="motion_picker",
        widget_config={
            "seconds": 30,
            "finish_prompt": "Big breath in… and out. Notice how your body feels now.",
        },
    ),
    Activity(
        id="colour_breathing",
        name="Colour breathing",
        age="All",
        emoji="🎨",
        props_needed=False,
        props_description="",
        purposes=("Breathing", "Calming", "Visualisation", "Mindfulness"),
        duration_minutes=4,
        objective=(
            "Promotes relaxation through visualisation and breath work. Selecting a soothing "
            "colour and imagining it flowing with each breath creates a calming experience."
        ),
        instructions=(
            "Pick a colour that feels calming to you. Breathe IN through your nose, imagining "
            "the colour filling your body. Breathe OUT through your mouth, imagining it flowing "
            "softly away."
        ),
        steps=(),
        interactive_type="colour_breath",
        widget_config={
            "in_seconds": 4,
            "out_seconds": 6,
            "cycles": 8,
            "default_colour": "#55b5f2",
            "palette": [
                {"name": "Sky blue", "hex": "#55b5f2"},
                {"name": "Soft green", "hex": "#77eed6"},
                {"name": "Lavender", "hex": "#b39ddb"},
                {"name": "Sunset orange", "hex": "#ffb37a"},
                {"name": "Rose pink", "hex": "#f5a6c0"},
                {"name": "Mint", "hex": "#a7e8c2"},
                {"name": "Pale yellow", "hex": "#ffe082"},
                {"name": "Deep navy", "hex": "#3d92e6"},
            ],
        },
    ),
    Activity(
        id="body_scan",
        name="Body scan meditation",
        age="All",
        emoji="🧘",
        props_needed=False,
        props_description="",
        purposes=("Mindfulness", "Grounding", "Calming"),
        duration_minutes=6,
        objective=(
            "Increases awareness of physical sensations and tension in the body. Serves as a "
            "powerful grounding technique and builds interoception skills."
        ),
        instructions=(
            "Move your attention slowly through your body — feet, legs, hands, shoulders, face. "
            "Notice what you feel in each spot. Drop any tension you find."
        ),
        steps=(
            {"icon": "🪑", "label": "Settle in", "body": "Sit comfortably and close your eyes. Take one slow breath."},
            {"icon": "🦶", "label": "Feet", "body": "Notice your feet resting on the floor. Wiggle your toes."},
            {"icon": "🦵", "label": "Legs", "body": "Move your attention to your legs sitting on the chair. Notice the weight of them."},
            {"icon": "✋", "label": "Hands", "body": "Notice your hands resting in your lap. Stretch out your fingers, then let them rest."},
            {"icon": "💪", "label": "Shoulders", "body": "Are your shoulders relaxed? Can you gently drop them down away from your ears?"},
            {"icon": "😌", "label": "Face", "body": "Soften your jaw. Soften your forehead. Let your face be calm."},
            {"icon": "🌬️", "label": "Notice the difference", "body": "How do you feel now compared to before you started?"},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 35},
    ),
    Activity(
        id="mindful_motion",
        name="Mindful motion",
        age="All",
        emoji="🫧",
        props_needed=True,
        props_description="A lava lamp, bubbles, food colouring in water, fish in an aquarium — or a YouTube video of any of these",
        purposes=("Mindfulness", "Calming", "Visualisation"),
        duration_minutes=5,
        objective=(
            "Promotes mindfulness by observing calming, slow movements. Focusing on visual "
            "stimuli helps students centre attention, reduce stress, and practice "
            "present-moment awareness."
        ),
        instructions=(
            "Watch something slow-moving — a lava lamp, bubbles, food colouring in water, fish "
            "in an aquarium, or a YouTube video of any of these. Breathe deeply and let the "
            "movement guide your attention."
        ),
        steps=(
            {"icon": "🫧", "label": "Choose your focus", "body": "A lava lamp, bubbles, food colouring dropped in water, or fish in a tank. No physical option? Use a calming YouTube video."},
            {"icon": "🌬️", "label": "Breathe deeply", "body": "Settle into the moment. Notice how your body feels. Release any tension."},
            {"icon": "👁️", "label": "Watch the movement", "body": "Follow the slow flow. Don't try to control it — just observe."},
            {"icon": "🧠", "label": "Stay present", "body": "If your mind drifts, gently bring your focus back to the movement. Let it guide your breath."},
            {"icon": "✅", "label": "Conclude", "body": "Take one final deep breath. Notice how your body feels now."},
        ),
        interactive_type="stepped",
        widget_config={"auto_advance_seconds": 30},
    ),
    Activity(
        id="mindful_listening_walk",
        name="Mindful listening walk",
        age="All",
        emoji="👂",
        props_needed=False,
        props_description="",
        purposes=("Mindfulness", "Grounding", "Social connection"),
        duration_minutes=10,
        objective=(
            "Practices focused attention and active listening by tuning into the sounds of "
            "the immediate environment, fostering present-moment awareness."
        ),
        instructions=(
            "Walk silently for 5 minutes, focusing only on what you can hear. Listen for close, "
            "mid-distance, and distant sounds. Reflect on what you heard at the end."
        ),
        steps=(
            {"icon": "🔇", "label": "Walk in silence", "body": "Walk slowly and quietly for 5 minutes. Focus only on listening."},
            {"icon": "👂", "label": "Close sounds", "placeholder": "e.g. footsteps, your own breathing…", "count": 1, "multiline": True},
            {"icon": "🎶", "label": "Mid-distance sounds", "placeholder": "e.g. voices, doors, chairs scraping…", "count": 1, "multiline": True},
            {"icon": "🌍", "label": "Distant sounds", "placeholder": "e.g. traffic, birds, wind…", "count": 1, "multiline": True},
            {"icon": "💭", "label": "Reflect", "placeholder": "What sound did you rarely notice before? What was hardest about listening?", "count": 1, "multiline": True},
        ),
        interactive_type="list_prompts",
    ),
]


ALL_PURPOSES = sorted({p for a in ACTIVITIES for p in a.purposes})
ALL_AGES = ["Jr", "Sr", "All"]


def get_activity(activity_id: str) -> Activity | None:
    """Look up an activity by id."""
    for a in ACTIVITIES:
        if a.id == activity_id:
            return a
    return None


def filter_activities(
    *,
    ages: list[str] | None = None,
    purposes: list[str] | None = None,
    words: list[str] | None = None,
    props_filter: str = "Any",  # "Any" | "Body-only" | "Needs supplies"
    search: str = "",
) -> list[Activity]:
    """Apply filters to the activity list."""
    out = list(ACTIVITIES)
    if ages:
        # An activity labelled "All" matches any age filter.
        out = [a for a in out if a.age in ages or a.age == "All"]
    if purposes:
        out = [a for a in out if any(p in a.purposes for p in purposes)]
    if words:
        # Words filter: activity matches if it's tagged with any selected word.
        from words import get_activity_word_set  # local import to avoid cycle
        out = [a for a in out if get_activity_word_set(a.id) & set(words)]
    if props_filter == "Body-only":
        out = [a for a in out if not a.props_needed]
    elif props_filter == "Needs supplies":
        out = [a for a in out if a.props_needed]
    if search:
        s = search.lower().strip()
        from words import get_activity_word_set
        out = [
            a
            for a in out
            if s in a.name.lower()
            or s in a.objective.lower()
            or s in a.instructions.lower()
            or any(s in p.lower() for p in a.purposes)
            or any(s in w.lower() for w in get_activity_word_set(a.id))
        ]
    return out
