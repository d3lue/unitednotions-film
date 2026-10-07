"""Everything the home page says and shows. Edit here, then run build.py.

Texts come from the current unitednotions.film pages.
Press quotes are read from data/quotes-from-old-site.json and are never typed here.
"""

# ---------------------------------------------------------------- works
# quote: index of the press quote shown in the work's room in the maze
# cards: press quotes shown as separate cards in the maze
# hall:  short press quotes written along the corridors
WORKS = [
    dict(slug="la-lucha", qkey="la-lucha", title="La Lucha", lang="es", year=2023, group="film",
         kind="Feature documentary",
         line="People with disabilities march across the Andes to La Paz to demand a pension.",
         facts=["World premiere at BlackStar Film Festival, Philadelphia, 2023.",
                "NYWIFT Award for Excellence in Directing.",
                "Premiered in the plazas of Cochabamba, La Paz and Potosí in 2024.",
                "Aired on PBS in 2024."],
         href="work/la-lucha.html", cta="Open La Lucha",
         watch=("Watch on sala.video", "https://sala.video/film.php?slug=la-lucha"),
         key="police-line", poster="la-lucha-poster", quote=0, cards=[], hall=[]),
    dict(slug="the-fight", qkey="the-fight", title="The Fight", year=2017, group="film",
         kind="Short documentary",
         line="The short film of that same march.",
         facts=["Released worldwide by The Guardian."],
         href="https://www.theguardian.com/world/ng-interactive/2017/may/05/fighting-for-a-pension-disability-rights-protesters-in-bolivia-face-barricades",
         cta="Watch at The Guardian",
         watch=("Watch at The Guardian", "https://www.theguardian.com/world/ng-interactive/2017/may/05/fighting-for-a-pension-disability-rights-protesters-in-bolivia-face-barricades"),
         key="shout-at-night", poster="the-fight-poster", quote=0, cards=[1], hall=[2]),
    dict(slug="cocaine-prison", qkey="cocaine-prison", title="Cocaine Prison", year=2017, group="film",
         kind="Feature documentary",
         line="Filmed inside San Sebastián prison in Cochabamba, in part by the inmates themselves.",
         facts=["Premiered at the Toronto International Film Festival."],
         href="https://sala.video/film.php?slug=cocaine-prison", cta="Watch on sala.video",
         watch=("Watch on sala.video", "https://sala.video/film.php?slug=cocaine-prison"),
         key="prison-riot-police", poster="cocaine-prison-poster", quote=2, cards=[4], hall=[0, 1, 3]),
    dict(slug="the-bolivian-case", qkey="the-bolivian-case", title="The Bolivian Case", year=2015, group="film",
         kind="Feature documentary",
         line="Three Norwegian teenagers are arrested in Bolivia with 22 kilos of cocaine. The film follows how the media shaped each of their cases.",
         facts=["Premiered at Hot Docs."],
         href="https://www.theboliviancase.com", cta="Visit theboliviancase.com",
         watch=("Watch on theboliviancase.com", "https://www.theboliviancase.com/watch.php"),
         key="document", poster="the-bolivian-case-poster", quote=0, cards=[], hall=[3, 1, 2]),
    dict(slug="stolen", qkey="stolen", title="Stolen", year=2009, group="film",
         kind="Feature documentary",
         line="A documentary on slavery in the Sahrawi refugee camps.",
         facts=["Premiered at the Sydney Film Festival and the Toronto International Film Festival.", "Aired on PBS."],
         href="https://sala.video/film.php?slug=stolen", cta="Watch on sala.video",
         watch=("Watch on sala.video", "https://sala.video/film.php?slug=stolen"),
         key="dune-at-dusk", poster="stolen-poster", quote=0, cards=[], hall=[2, 3]),
    dict(slug="todo-nace-desde-lo-pequeno", qkey=None, title="Todo Nace Desde Lo Pequeño", lang="es", year=2025, group="xr",
         kind="Live performance",
         line="A live performance where Andean cosmology meets AI. Four dancers embody Earth, Water, Wind and Jaguar.",
         facts=["Premiered at El Martadero, Cochabamba."],
         href="https://www.koa.xyz/tao", cta="See the performance",
         watch=None,
         key="todo-nace-stage", poster="todo-nace-dancers", quote=None, cards=[], hall=[]),
    dict(slug="huk-the-jaguaress", qkey="huk", title="Huk the Jaguaress", year=2025, group="xr",
         kind="AI installation",
         line="An AI installation created at the Mila Québec AI Institute residency.",
         facts=["Premiered at CPH:DOX in Copenhagen.", "Shown at NewImages Festival in Paris.", "Part of Huk, an ongoing project."],
         href="https://huk-efwl5jj.gamma.site/huk", cta="Meet the jaguaress",
         watch=None,
         key="golden-jaguar", poster="huk-installation", quote=1, cards=[], hall=[0]),
    dict(slug="las-awichas", qkey="las-awichas", title="Las Awichas", lang="es", year=2024, group="xr",
         kind="Augmented reality installation",
         line="An augmented reality installation. Eight AI-generated Andean grandmothers, each with a robotic animal spirit.",
         facts=["Best Interactive / Immersive Documentary, AIDC Awards 2025.",
                "Shown at King's College London, on the Strand.",
                "Las Awichas VR premiered at Surreality, HKUST (Guangzhou), in 2025.",
                "3D animated characters by Brian Condori Marza."],
         href="https://www.koa.xyz", cta="Visit koa.xyz",
         watch=None,
         key="awichas-gallery", poster="las-awichas-poster", quote=None, cards=[], hall=[],
         award="Best Interactive / Immersive Documentary, AIDC Awards 2025"),
    dict(slug="prison-x", qkey="prison-x", title="Prison X", year=2021, group="xr",
         kind="Virtual reality",
         line="A virtual reality experience set in a Bolivian prison.",
         facts=["Premiered at the Sundance Film Festival.", "Released on Steam in 2024."],
         href="https://prisonx.red", cta="Visit prisonx.red",
         watch=("Get it on Steam", "https://store.steampowered.com/app/1502900/Prison__X__Chapter_1_The_Devil_and_The_Sun/"),
         key="prison-x-booth-haze", poster="prison-x-poster", quote=0, cards=[2, 3], hall=[1]),
]

# How the names of publications are written on the page (the old site has many in capitals).
SOURCE_NAMES = {
    "Steve Kopian, UNSEEN FILMS": "Steve Kopian, Unseen Films",
    "Juan.J Arroyo, ROLLINGSTONE": "Juan J. Arroyo, Rolling Stone",
    "Anita Hollander, Actress": "Anita Hollander, actress",
    "VICE": "VICE",
    "FILMMAKER MAGAZINE": "Filmmaker Magazine",
    "THE GLOBE AND MAIL": "The Globe and Mail",
    "CINEMA TROPICAL": "Cinema Tropical",
    "MOUSTIQUE": "Moustique",
    "CHRISTIANE AMANPOUR, CNN": "Christiane Amanpour, CNN",
    "NO FILM SCHOOL": "No Film School",
    "AUDIENCE AWARD, SHEFFIELD DOC FEST": "Audience Award, Sheffield Doc/Fest",
    "AMERICAS QUARTERLY": "Americas Quarterly",
    "SHE DOES THE CITY": "She Does The City",
    "4:3": "4:3",
    "EL DEBER": "El Deber",
    "INDIEWIRE": "IndieWire",
    "SEATTLE INTERNATIONAL FILM FESTIVAL": "Seattle International Film Festival",
    "TORONTO INTERNATIONAL FILM FESTIVAL": "Toronto International Film Festival",
    "Richard Kuipers, VARIETY": "Richard Kuipers, Variety",
    "Greg Quill, THE TORONTO STAR": "Greg Quill, Toronto Star",
}

STATEMENTS = ["Imagination is the key.", "The Global South builds its own future.", "Technology is a tool."]

# ---------------------------------------------------------------- photos
# tier: how large a picture is in the maze (S, M, L). The key picture of a work is always the largest.
# focus: the part of the picture that must stay visible when it is cropped (x% y%).
# credit: shown with the caption.
P = lambda slug, alt, work=None, tier="M", focus=None, credit=None: dict(slug=slug, alt=alt, work=work, tier=tier, focus=focus, credit=credit)

PHOTOS = [
    # the 39 pictures of the home collage
    P("golden-jaguar", "A golden jaguar sits among amber dunes and bare branches.", "huk-the-jaguaress", "L"),
    P("screening-room", "A dark hall with a lit screen. Small glowing animal figures stand on either side.", None, "M"),
    P("march-altiplano", "A long line of people in wheelchairs and on foot carries Bolivian flags across the altiplano.", "la-lucha", "L"),
    P("shout-at-night", "A man in a knitted cardigan shouts with his arms spread wide, in a street at night.", "the-fight", "L", "45% 40%"),
    P("lone-protester", "A lone protester holds a handwritten sign and a Bolivian flag on the altiplano.", "la-lucha", "L", "60% 60%"),
    P("prison-riot-police", "Riot police stand in front of a prison. Inmates watch from the roof.", "cocaine-prison", "L"),
    P("cnn-studio", "Three people talk on a CNN studio set.", "the-fight", "M"),
    P("fence-at-night", "A man shouts beside a wire fence at night.", "the-fight", "M", "65% 45%"),
    P("megaphone", "A woman in a pink hat speaks into a megaphone.", "la-lucha", "L", "50% 40%"),
    P("inmate-camera", "A man points a small camera at the viewer. Another man watches from behind.", "cocaine-prison", "L", "50% 45%"),
    P("prison-courtyard", "Men stand in a narrow prison courtyard.", "cocaine-prison", "M"),
    P("tiff-trio", "Three people pose in front of a TIFF backdrop.", None, "S", "50% 35%"),
    P("dune-at-dusk", "Three figures cross a sand dune at dusk. The smallest one jumps.", "stolen", "L", "55% 60%"),
    P("fence-banner", "Protesters in wheelchairs raise their arms by a wire fence, under an embroidered banner.", "la-lucha", "L"),
    P("plaza-screen", "A crowd watches an outdoor screen in a plaza at night.", "la-lucha", "M"),
    P("prison-from-above", "A prison courtyard seen from above, crowded with people, stalls and tin roofs.", "cocaine-prison", "L", "50% 60%"),
    P("police-line", "People in wheelchairs and on crutches face a line of riot police with shields.", "la-lucha", "L"),
    P("camera-on-the-altiplano", "A person carries a camera across the altiplano.", "la-lucha", "S"),
    P("sundance-marquee", "A person stands in front of a Sundance Film Festival marquee at dusk.", None, "S", "55% 55%"),
    P("filming-the-march", "A filmmaker kneels with a camera beside men in wheelchairs.", "la-lucha", "M"),
    P("press-wall", "A woman speaks to microphones and cameras in front of a wall of red-tinted photographs.", None, "M", "45% 40%"),
    P("checked-floor", "A figure wrapped in red striped cloth sits on a yellow and black checked floor.", "todo-nace-desde-lo-pequeno", "M", "50% 65%"),
    P("red-neon-portrait", "Portrait of a woman in a rose-print shirt in front of red neon.", None, "M", "55% 35%"),
    P("pink-blanket", "A woman wrapped in a pink blanket sits in a wheelchair at night.", "la-lucha", "M", "40% 50%"),
    P("green-hat", "A man in a green hat and blue sunglasses stands in front of police shields.", "la-lucha", "M", "65% 40%"),
    P("hospital-bed", "A woman lies in a hospital bed in handcuffs.", "the-bolivian-case", "M", "50% 35%"),
    P("document", "A woman holds an official document up to the camera. A baby is beside her.", "the-bolivian-case", "L", "50% 35%"),
    P("blue-jaguar", "A blue jaguar with white whiskers in front of a red curtain, on black.", "prison-x", "L", "62% 50%"),
    P("jaguar-woman", "A drawn woman with jaguar spots on her face, between pale tree trunks.", None, "M", "58% 40%"),
    P("awichas-gallery", "A woman in black stands in a gallery between large black-and-white portraits of Andean grandmothers.", "las-awichas", "L"),
    P("vr-headset", "A man wears a VR headset and headphones in front of a curtain and a bright screen.", None, "M", "50% 40%", "Maxime Raynault, Forum des images"),
    P("stage-talk", "A talk on a stage under a large screen that shows a 3D scene.", None, "S"),
    P("three-filmmakers", "Three filmmakers stand close together with cameras and microphones.", None, "S", "50% 40%"),
    P("awards-selfie", "A selfie of two people at an awards backdrop. A third person stands behind them.", None, "S", "50% 40%"),
    P("surreality-plaza", "Augmented reality sculptures of a silver llama and giant blue mushrooms in a plaza, with the Surreality logo.", "las-awichas", "M"),
    P("red-carpet", "A woman in a sequined dress on a TIFF red carpet.", None, "S", "50% 30%"),
    P("masked-character", "A 3D character with a silver mask over half the face, a blue hoodie and a woven sash.", None, "S", "50% 30%"),
    P("blue-jungle", "A silhouette stands before a screen of blue jungle. Plants sit on lit white plinths.", "huk-the-jaguaress", "L", None, "Maxime Raynault, Forum des images"),
    P("cph-dox", "Two people stand under a CPH:DOX neon sign on a red wall. One raises an arm.", "huk-the-jaguaress", "M"),
    # the posters and work pictures from the home page lists
    P("la-lucha-poster", "Poster of La Lucha.", "la-lucha", "M"),
    P("the-fight-poster", "Poster of The Fight.", "the-fight", "S"),
    P("cocaine-prison-poster", "Poster of Cocaine Prison.", "cocaine-prison", "S"),
    P("the-bolivian-case-poster", "Poster of The Bolivian Case.", "the-bolivian-case", "M"),
    P("stolen-poster", "Poster of Stolen.", "stolen", "S"),
    P("todo-nace-dancers", "Two figures wrapped in red woven cloth crouch on a yellow and black checked floor.", "todo-nace-desde-lo-pequeno", "M", "50% 65%"),
    P("huk-installation", "Three visitors stand before a screen showing a golden jaguar, inside a white tent with lit plinths.", "huk-the-jaguaress", "L"),
    P("las-awichas-poster", "Poster of Las Awichas.", "las-awichas", "M"),
    P("prison-x-poster", "Poster of Prison X.", "prison-x", "M"),
    # more pictures from About, Film Futurism and the lab notes
    P("ridge-silhouettes", "Three silhouettes stand on a ridge under an amber sky.", None, "M", "40% 60%"),
    P("march-on-the-road", "People in wheelchairs travel along a mountain road. One of them waves.", "la-lucha", "L", "55% 50%"),
    P("small-plane", "Two people stand beside a small plane on a dry airfield.", None, "M", "55% 55%"),
    P("head-rig", "A woman in profile wears a helmet with a camera mounted in front of her face.", None, "M", "70% 40%"),
    P("roadside-rest", "Marchers rest beside the road under a deep blue sky.", "la-lucha", "M", "45% 60%"),
    P("awichas-on-the-strand", "A person stands below a large Las Awichas panel on a stone building at night. Eight silver robotic animals surround the face of a grandmother.", "las-awichas", "L", "50% 40%"),
    P("awichas-in-the-hand", "A silver robotic gecko sits on an open hand, in blue light.", "las-awichas", "M", "50% 62%"),
    P("plaza-premiere", "A full plaza watches a film on an outdoor screen at night.", "la-lucha", "L", "55% 55%"),
    P("whale-print", "A translucent 3D-printed whale glows orange on a workbench.", "yakumama", "M", "50% 45%"),
    P("todo-nace-stage", "A dancer crouches on a checked floor under green light. The audience stands around him and two screens show blue creatures.", "todo-nace-desde-lo-pequeno", "L", "50% 60%"),
    P("creature-on-moss", "A white animal sculpture lies on a bed of moss beside a candle and a gold-framed mirror.", None, "L"),
    P("raised-fist", "A woman in a wheelchair raises her fist.", "la-lucha", "S", "50% 35%"),
    P("microphone", "A woman in a wheelchair speaks into a microphone.", "la-lucha", "M", "50% 40%"),
    P("awicha-weaving", "An AI-generated Andean grandmother. Her striped shawl dissolves into streaks of colour.", "las-awichas", "M", "50% 45%"),
    P("awicha-stripes", "An AI-generated Andean grandmother in a striped pink shawl.", "las-awichas", "L", "50% 40%"),
    P("awicha-hands", "An AI-generated Andean grandmother in a knitted hat, in black and white.", "las-awichas", "M", "50% 45%"),
    P("awicha-wind", "An AI-generated Andean grandmother with windswept hair, in black and white.", "las-awichas", "L", "50% 35%"),
    P("awicha-light", "An AI-generated Andean grandmother with braids. A ribbon of light crosses the frame.", "las-awichas", "M", "50% 50%"),
    P("awicha-red", "An AI-generated Andean grandmother in a hat and a red and black shawl.", "las-awichas", "M", "50% 45%"),
    P("prison-x-masks", "A collage of masked dancers, a visitor in a VR headset and cut-out figures in a 3D gallery.", "prison-x", "M"),
    P("neon-headset", "A generated image of a person in a VR headset surrounded by neon textile patterns.", "prison-x", "M"),
    P("prison-x-booth-haze", "A visitor kneels in a VR headset inside the Prison X booth, in purple light.", "prison-x", "L"),
    P("prison-x-booth", "The Prison X booth at an exhibition.", "prison-x", "M", "55% 45%"),
    P("prison-x-player", "A visitor in a VR headset holds two controllers in front of woven textiles.", "prison-x", "M", "60% 40%"),
    P("jaguaress-model", "A silver 3D model of a jaguar in the Blender viewport.", "lab", "M", "38% 50%"),
    P("gecko-on-screen", "A turquoise 3D gecko on a monitor.", "lab", "S", "45% 50%"),
    P("orchid-and-web", "A 3D scene seen through a spider web: an orange orchid, a silver spider and floating screens.", "lab", "M", "60% 45%"),
    P("orchid-hummingbird", "A 3D scene with an orchid, a hummingbird and a walking figure under a white sun.", "lab", "M"),
    P("spider-rig", "The rig of a 3D spider in Blender.", "lab", "S", "50% 45%"),
    P("bird-wings", "A 3D bird with a long beak spreads its wings.", "lab", "M"),
    P("bird-and-cactus", "A 3D bird with a long beak beside a red-spined cactus flower.", "lab", "M"),
    P("whale-and-robot", "A 3D whale and a robot in front of a striped setting sun.", "yakumama", "L"),
    P("whale-on-grid", "A 3D model of a whale floats above a grid under a blue sky.", "yakumama", "L"),
]

# Where and when a picture was taken. Only facts that the current site states or that are written in the picture itself.
# Everything else is for the studio to add: open build/captions.html.
WHERE = {
    "march-altiplano": "The march to La Paz, Bolivia, 2016.",
    "lone-protester": "The march to La Paz, Bolivia, 2016.",
    "march-on-the-road": "The march to La Paz, Bolivia, 2016.",
    "roadside-rest": "The march to La Paz, Bolivia, 2016.",
    "camera-on-the-altiplano": "The march to La Paz, Bolivia, 2016.",
    "filming-the-march": "The march to La Paz, Bolivia, 2016.",
    "plaza-premiere": "The Bolivian premiere of La Lucha, in a central plaza, 2024.",
    "prison-riot-police": "San Sebastián prison, Cochabamba.",
    "prison-courtyard": "San Sebastián prison, Cochabamba.",
    "prison-from-above": "San Sebastián prison, Cochabamba.",
    "inmate-camera": "San Sebastián prison, Cochabamba.",
    "cnn-studio": "A CNN studio.",
    "tiff-trio": "Toronto International Film Festival.",
    "red-carpet": "Toronto International Film Festival.",
    "sundance-marquee": "Sundance Film Festival.",
    "cph-dox": "CPH:DOX, Copenhagen.",
    "surreality-plaza": "Surreality, HKUST (Guangzhou), 2025.",
    "awichas-on-the-strand": "The Strand, King's College London, 2024.",
    "awichas-in-the-hand": "Las Awichas in augmented reality.",
    "blue-jungle": "NewImages Festival, Forum des images, Paris, 2025.",
    "vr-headset": "Forum des images, Paris.",
    "todo-nace-stage": "El Martadero, Cochabamba, 2025.",
    "todo-nace-dancers": "El Martadero, Cochabamba, 2025.",
    "checked-floor": "El Martadero, Cochabamba, 2025.",
    "whale-print": "Yakumama in the making, 2026.",
    "whale-on-grid": "From the lab note The whale that watches back, 2026.",
    "jaguaress-model": "From the lab note The body decides the interface, 2026.",
    "whale-and-robot": "From the lab note The water lily learns to breathe.",
    "bird-wings": "From the lab note The water lily learns to breathe.",
    "bird-and-cactus": "From the lab note The water lily learns to breathe.",
    "orchid-and-web": "From the lab note The spider learns to weave, the gecko learns to feel.",
    "orchid-hummingbird": "From the lab note The spider learns to weave, the gecko learns to feel.",
    "spider-rig": "From the lab note The spider learns to weave, the gecko learns to feel.",
    "gecko-on-screen": "From the lab note The gecko learns to feel, Qwen finds its voice.",
}

# Who made what a picture shows, when the current site says so.
MADE = {
    "awichas-on-the-strand": "3D animated characters by Brian Condori Marza.",
    "awichas-in-the-hand": "3D animated character by Brian Condori Marza.",
    "surreality-plaza": "The llama is one of the 3D animated characters by Brian Condori Marza.",
}

# Pictures that come from a lab note lead to that note.
NOTE_OF = {
    "jaguaress-model": "the-body-decides-the-interface",
    "gecko-on-screen": "the-gecko-learns-to-feel-qwen-finds-its-voice",
    "orchid-and-web": "the-spider-learns-to-weave-the-gecko-learns-to-feel",
    "orchid-hummingbird": "the-spider-learns-to-weave-the-gecko-learns-to-feel",
    "spider-rig": "the-spider-learns-to-weave-the-gecko-learns-to-feel",
    "bird-wings": "the-water-lily-learns-to-breathe",
    "bird-and-cactus": "the-water-lily-learns-to-breathe",
}

# Pictures that are not one of the nine works but still lead somewhere.
OTHER_LINKS = {
    "yakumama": ("Yakumama, coming in 2026", "#now"),
    "lab": ("From the lab", "#lab"),
}

# Pictures placed by hand instead of by colour. The value is (part, position):
# part 0 is day and part 1 is night, position runs from 0 to 1 inside the part.
# (-1, 0) puts a picture at the very start.
NUDGE = {
    "police-line": (-1, 0.0),      # the maze opens on La Lucha
}

# ---------------------------------------------------------------- the rest of the page
INTRO = ("United Notions Film is an award-winning film and creative technology studio based in Bolivia and Australia, "
         "founded in 2006 by Violeta Ayala and Dan Fallshaw.")
INTRO_MORE = ("We make documentaries, virtual reality experiences and cinematic installations. "
              "We run a lab that develops cinema systems, AI and robotics.")

HOW_TO_WALK = "This page is a maze. Scroll and a line leads the way. To walk it your own way, tap a corridor or a room, or use the arrows."

NOW_SHOWING = [
    ("La Lucha", "es", "On sala.video", "Watch La Lucha", "https://sala.video/film.php?slug=la-lucha"),
    ("Cocaine Prison", None, "On sala.video", "Watch Cocaine Prison", "https://sala.video/film.php?slug=cocaine-prison"),
    ("The Bolivian Case", None, "On theboliviancase.com", "Watch The Bolivian Case", "https://www.theboliviancase.com/watch.php"),
    ("Stolen", None, "On sala.video", "Watch Stolen", "https://sala.video/film.php?slug=stolen"),
    ("The Fight", None, "At The Guardian", "Watch The Fight", "https://www.theguardian.com/world/ng-interactive/2017/may/05/fighting-for-a-pension-disability-rights-protesters-in-bolivia-face-barricades"),
    ("Prison X", None, "Virtual reality on Steam", "Get Prison X on Steam", "https://store.steampowered.com/app/1502900/Prison__X__Chapter_1_The_Devil_and_The_Sun/"),
]

# ---------------------------------------------------------------- captions written by the studio
# build/captions.html is a sheet with every picture. What is typed there is saved as build/captions.json
# and wins over the descriptions above: what the picture shows, who is in it, where and when.
STUDIO_WROTE = set()      # pictures whose caption was typed by the studio: these are shown as typed, in both languages


def _studio_captions():
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captions.json")
    if not os.path.exists(path):
        return
    for slug, c in json.load(open(path, encoding="utf-8")).items():
        if any(str(v).strip() for v in c.values()):
            STUDIO_WROTE.add(slug)
        for p in PHOTOS:
            if p["slug"] == slug:
                if c.get("shows", "").strip():
                    p["alt"] = c["shows"].strip()
                if "where" in c:
                    WHERE[slug] = c["where"].strip()
                if c.get("who", "").strip():
                    p["who"] = c["who"].strip()


for _p in PHOTOS:
    _p.setdefault("who", "")
_studio_captions()


def caption(p):
    """The full sentence for one picture: who, what, where and when."""
    parts = [p["who"].rstrip(".") + "." if p.get("who") else "", p["alt"], WHERE.get(p["slug"], ""), MADE.get(p["slug"], "")]
    return " ".join(x for x in parts if x)
