"""What the other pages say: About, People, News and Film Futurism.

All texts come from the current unitednotions.film pages. Edit here, then run build.py.
Pictures named "maze:<name>" are pictures of the home maze. The others are in assets/img/pages.
"""

# ------------------------------------------------------------------------------------------ navigation
NAV = [
    ("Work", "index.html#works"),
    ("Film Futurism", "film-futurism.html"),
    ("Research", "research.html"),
    ("News", "news.html"),
    ("About", "about.html"),
    ("People", "people.html"),
]

# ------------------------------------------------------------------------------------------ about
ABOUT_DESCRIPTION = ("The story of United Notions Film, the film and creative technology studio founded in 2006 by Violeta Ayala and Dan Fallshaw. "
                     "From Stolen (2009) to Huk the Jaguaress (2025): documentaries, virtual reality, installations and a lab, made between Bolivia and Australia.")
ABOUT_LEAD = ("United Notions Film began with two filmmakers and one camera in Mauritania. "
              "Twenty years later it is a studio and a lab working between Bolivia and Australia. This is the story.")

# (year, paragraphs, pictures). A picture is (name, description, focus or None).
ABOUT = [
    ("2005", ["Violeta Ayala and Dan Fallshaw work together for the first time. They travel to Mauritania and make Between the Oil and the Deep Blue Sea, an investigative short documentary about corruption in the oil industry."],
     [("about-01", "DVD cover of Between the Oil and the Deep Blue Sea, a film by Violeta Ayala and Dan Fallshaw.", None)]),
    ("2006", ["They found United Notions Film."], []),
    ("2009", ["Stolen, a feature documentary about slavery in the Sahrawi refugee camps, premieres at the Sydney Film Festival. It screens at 80 festivals, including Toronto, wins 16 awards and airs on PBS. The film causes international controversy."],
     [("maze:ridge-silhouettes", "Three silhouettes stand on a ridge under an amber sky.", None)]),
    ("2015", ["The Bolivian Case premieres at Hot Docs. Three Norwegian teenagers are arrested in Bolivia with 22 kilos of cocaine, and the film follows how the media shaped each of their cases. It is shortlisted for the Premios Platino and the Premios Fénix and is distributed across Latin America.",
              "Producer Redelia Shaw joins UNF."],
     [("about-03", "A woman poses with open arms at a Hot Docs backdrop. The picture is repeated as a pattern.", None),
      ("about-04", "A film team answers questions on stage under a cinema screen with the Hot Docs logo.", "50% 25%")]),
    ("2016", ["People with disabilities march across the Andes to La Paz to demand a pension. UNF films the protest."],
     [("maze:march-on-the-road", "People in wheelchairs travel along a mountain road. One of them waves.", None)]),
    ("2017", ["The Fight, the short film of that march, is released worldwide by The Guardian and wins a Walkley Award. Bolivia then passes a law that grants a monthly payment and labour inclusion to people with disabilities.",
              "Cocaine Prison, filmed over four years inside San Sebastián prison in Cochabamba, premieres at the Toronto International Film Festival. It wins the Audience Award at Cinelatino in Toulouse, airs on the PBS WORLD Channel and is picked up by Amazon Prime."],
     [("maze:small-plane", "Two people stand beside a small plane on a dry airfield.", None)]),
    ("2021", ["Prison X, Chapter 1: The Devil and The Sun, premieres at the Sundance Film Festival. It is a virtual reality experience set in a Bolivian prison and a founding work of Neo-Andean Futurism. It is selected for Cannes XR, Games for Change and SIGGRAPH.",
              "After Prison X, UNF launches koa.xyz, a computational creativity lab."],
     [("maze:head-rig", "A woman in profile wears a helmet with a camera mounted in front of her face.", "70% 40%"),
      ("about-08", "A 3D character stands in a motion capture app, arms out, on a black grid.", None)]),
    ("2022", ["El Martadero, a leading cultural centre in Cochabamba, invites UNF to create its first physical installation. Violeta uses AI to imagine her female ancestors, the Awichas. The eight large acrylic portraits enter the centre's official collection."],
     []),
    ("2023", ["La Lucha, the feature film of the march, premieres at BlackStar Film Festival in Philadelphia and screens at SXSW Sydney. It later wins the NYWIFT Award for Excellence in Directing at its New York premiere, at ReelAbilities and the Museum of the Moving Image."],
     [("maze:roadside-rest", "Marchers rest beside the road under a deep blue sky.", "45% 60%"),
      ("about-10", "Three people take a selfie in front of an SXSW Sydney sign.", "50% 35%")]),
    ("2024", ["Las Awichas becomes an augmented reality installation, co-produced with King's College London for GLOW. It shows on the Strand and in the Arcade gallery, with tullmas woven by Bolivian artisans and 3D-printed animals.",
              "La Lucha premieres in Bolivia in the central plazas of Cochabamba, La Paz and Potosí, with sign language interpretation. Thousands attend.",
              "La Lucha airs on PBS.",
              "Prison X is released on Steam.",
              "Yasmeen Hitti, scientist and creative systems engineer, joins UNF to develop embodied AI systems."],
     [("maze:awichas-on-the-strand", "A person stands below a large Las Awichas panel on a stone building at night.", "50% 40%"),
      ("maze:plaza-premiere", "A full plaza watches a film on an outdoor screen at night.", "55% 55%")]),
    ("2025", ["Las Awichas wins Best Interactive / Immersive Documentary at the AIDC Awards. Las Awichas VR premieres at Surreality, at the Hong Kong University of Science and Technology (Guangzhou) in China.",
              "Huk the Jaguaress, an AI installation created at the Mila Québec AI Institute residency, premieres at CPH:DOX in Copenhagen and shows at NewImages Festival in Paris. It is part of Huk, an ongoing project.",
              "Todo Nace Desde Lo Pequeño, a live performance where Andean cosmology meets AI, premieres at El Martadero in Cochabamba."],
     [("maze:cph-dox", "Two people stand under a CPH:DOX neon sign on a red wall. One raises an arm.", None),
      ("maze:todo-nace-stage", "A dancer crouches on a checked floor under green light. The audience stands around him and two screens show blue creatures.", "50% 60%")]),
    ("2026", ["UNF launches sala.red, investigative tech journalism from Bolivia, and sala.video, independent film distribution.",
              "UNF is creating Yakumama, a robotic whale installation. It is set to premiere at MozFest 2026 in Barcelona."],
     [("maze:whale-print", "A translucent 3D-printed whale glows orange on a workbench.", "50% 45%")]),
]

# ------------------------------------------------------------------------------------------ people
PEOPLE_DESCRIPTION = ("The people of United Notions Film: co-founders Violeta Ayala and Dan Fallshaw, producer Redelia Shaw, "
                      "scientist Yasmeen Hitti and 3D artist Brian Condori Marza.")

# works: the works named for this person on the current site (their bio, the credits of a work or a text of the site).
PEOPLE = [
    dict(slug="violeta-ayala", name="Violeta Ayala", role="Co-founder. Filmmaker, artist and creative technologist.", strip="people-01",
         bio=["Violeta Ayala builds where storytelling, technology and Indigenous futurism meet.",
              "She is a Quechua-Bolivian-Australian filmmaker, artist and creative technologist based in Cochabamba, the first Quechua member of the Academy of Motion Picture Arts and Sciences and a 2026-2027 Mozilla Fellow.",
              "She made Stolen, The Bolivian Case, Cocaine Prison, The Fight and La Lucha, then Prison X, Las Awichas and Huk the Jaguaress. She co-founded United Notions Film and sala.red, and she runs koa.xyz."],
         links=[("violetaayala.com", "https://www.violetaayala.com"), ("Violeta Ayala on Wikipedia", "https://en.wikipedia.org/wiki/Violeta_Ayala"),
                ("sala.red", "https://sala.red"), ("koa.xyz", "https://koa.xyz")],
         works=["la-lucha", "the-fight", "cocaine-prison", "the-bolivian-case", "stolen", "todo-nace-desde-lo-pequeno", "huk-the-jaguaress", "las-awichas", "prison-x"],
         job="Filmmaker, artist and creative technologist", base="Cochabamba, Bolivia"),
    dict(slug="dan-fallshaw", name="Dan Fallshaw", role="Co-founder. Filmmaker, producer and interaction designer.", strip="people-03",
         bio=["Dan Fallshaw is a Walkley Award-winning filmmaker, producer and interaction designer. He co-founded United Notions Film in 2006 with Violeta Ayala.",
              "He co-directed Stolen. His producer credits include The Bolivian Case (Hot Docs), Cocaine Prison (TIFF), La Lucha, the virtual reality experience Prison X (Sundance, Cannes, SXSW) and the augmented reality installation Las Awichas.",
              "He is a Master's candidate in Human-Computer Interaction at the University of Technology Sydney, where he researches how humans create with AI. He holds a Bachelor of Science, a Diploma of Education and a Bachelor of Design."],
         links=[("danfallshaw.com", "https://danfallshaw.com"), ("Dan Fallshaw on Wikipedia", "https://en.wikipedia.org/wiki/Dan_Fallshaw")],
         works=["stolen", "the-bolivian-case", "cocaine-prison", "la-lucha", "prison-x", "las-awichas", "huk-the-jaguaress", "todo-nace-desde-lo-pequeno"],
         job="Filmmaker, producer and interaction designer", base=None),
    dict(slug="redelia-shaw", name="Redelia Shaw", role="Producer.", strip="people-05",
         bio=["Redelia Shaw (she/her) is a producer with over fifteen years of experience across commercial, independent and broadcast projects for Fox, Showtime, ABC and PBS.",
              "She joined United Notions Film in 2015 and produced Cocaine Prison and La Lucha. She teaches Communications and Media Studies at Santa Monica College."],
         links=[("Redelia Shaw on IMDb", "https://www.imdb.com/name/nm1475267/"), ("La Lucha at ITVS", "https://itvs.org/films/la-lucha/")],
         works=["cocaine-prison", "la-lucha"],
         job="Producer", base=None),
    dict(slug="yasmeen-hitti", name="Yasmeen Hitti", role="Scientist. Embodied AI systems.", strip="people-07",
         bio=["Yasmeen Hitti is an interdisciplinary scientist working across biology, AI and interactive media.",
              "She is a postdoctoral researcher in neuroscience at the Université de Montréal, CHU Sainte-Justine and Mila, the Québec AI Institute. She earned her PhD at McGill University in collaboration with Mila, researching how plant behaviour can be sensed, interpreted and shaped through technology.",
              "She joined United Notions Film in 2024 to develop embodied AI systems. Her credits include Huk the Jaguaress."],
         links=[("yasmeenhitti.com", "https://yasmeenhitti.com")],
         works=["huk-the-jaguaress", "todo-nace-desde-lo-pequeno"],
         job="Interdisciplinary scientist", base=None),
    dict(slug="brian-condori-marza", name="Brian Condori Marza", role="3D artist and technical collaborator.", strip="people-09",
         bio=["Brian Condori Marza is a 3D artist and technical collaborator. He works across modelling, rigging, animation and real-time systems.",
              "He made the 3D animated characters of Las Awichas: eight robotic animals that appear in augmented reality in London and in the hands of visitors.",
              "He is the 3D artist of Huk the Jaguaress. In the lab he builds the rigs and the poses of the creatures."],
         links=[("Brian Condori Marza at Mila", "https://mila.quebec/en/directory/brian-condori-marza")],
         works=["las-awichas", "huk-the-jaguaress"],
         # his wall shows the 3D characters, not the portraits of the grandmothers
         wall=["awichas-on-the-strand", "awichas-in-the-hand", "surreality-plaza", "golden-jaguar", "huk-installation", "jaguaress-model"],
         # (file in assets/embeds, title, the lab note it comes from)
         embed=("jaguaress-skeleton-widget", "Huk: the 24 poses by Brian Condori", "the-jaguaress-learns-her-own-skeleton"),
         job="3D artist", base=None),
]

# ------------------------------------------------------------------------------------------ film futurism
FF_DESCRIPTION = ("Film futurism moves beyond fixed narrative into living systems of cinema. United Notions Film brings together AI, robotics, "
                  "game mechanics and immersive environments to create stories that respond, adapt and evolve in real time.")
FF_STATEMENT = "Film futurism moves beyond fixed narrative into living systems of cinema."
FF_DEFINITION = [
    "It brings together AI, robotics, game mechanics and immersive environments such as AR, VR and MR to create stories that respond, adapt and evolve in real time.",
    "These works shift through interaction. Characters, spaces and emotional arcs change as audiences engage with them.",
    "The viewer takes part in building the experience.",
]

# Notes: (title, paragraphs, quote or None, links, picture or None)
FF_NOTES = [
    dict(title="Violeta Ayala is a Mozilla Fellow",
         text=["Our co-founder joins the 2026-2027 cohort of Mozilla Foundation Fellows. Mozilla describes the cohort as builders creating alternatives to dominant technology systems.",
               "Violeta was the first Quechua member of the Academy of Motion Picture Arts and Sciences. Her work keeps expanding what Indigenous storytelling can be: film, VR, robotics, and now AI infrastructure built from her city, Cochabamba."],
         quote=None, links=[], picture=None),
    dict(title="Las Awichas at the Guangdong Museum of Art",
         text=["Las Awichas, a mixed-reality installation by Violeta Ayala, opens at the Guangdong Museum of Art as part of SURREALITY, an art and technology exhibition developed by the Center for Metaverse and Computational Creativity (MC²) at HKUST (Guangzhou), led by Professor Pan Hui.",
               "The installation works at architectural scale. It brings together body, space and ancestral memory, and creates a dialogue between AI-generated Andean grandmothers and visitors.",
               "What started as digital portraits of female ancestors, rooted in Ayala's grandmother Herminia Soto Montaño, grew into robotic animals inspired by the Nazca lines. The work operates through ch'ixi logic (Silvia Rivera Cusicanqui): different ways of knowing held in productive tension.",
               "On view from 15 February to 30 March."],
         quote=("AI-collaborative art is giving me a possibility to imagine my culture in a different light. As a Quechua creator and filmmaker whose civilization was destroyed by colonizers, I really cherished the opportunity to imagine my ancestors.", "Violeta Ayala, 2020"),
         links=[], picture=("ff-02", "A card about Las Awichas at Surreality, HKUST (Guangzhou), with pictures of robotic animal sculptures in a garden.")),
    dict(title="Our own streaming release",
         text=["On New Year's Eve we launched our own streaming release inside The Bolivian Case website. A TV series dropped in Norway and the story we documented was circulating in a new shape, missing key elements. The full story needs to be told with context, from the people who still live it.",
               "We built it ourselves: platform, player, hosting, payments and delivery pipeline. Everything is made in-house, so the film lives on its own terms.",
               "sala.video followed. It is a curated platform releasing 12 films a year, starting with the United Notions Film catalogue. Other filmmakers can host films on their own sites with our tech and keep control of audience, pricing, territories and release strategy."],
         quote=None, links=[("Watch The Bolivian Case", "https://www.theboliviancase.com"), ("sala.video", "https://sala.video/home.php")], picture=None),
    dict(title="Todo Nace Desde Lo Pequeño", lang="es",
         text=["Everything Starts Small. The performance was fleeting and amazing.",
               "It began as a way of VJ-ing for the afterparty, only I was doing it live, in real time, ch'ixi all the way. Dan was on the camera, sending me streams through IoT, and I was transforming everything, fully concentrated.",
               "By the time the performance began, the space was overflowing. From past to future, we shaped a vision of Neo-Andean Futurism. The interfaces were ours, the AI model was local, and our community centre, El mARTadero, became our nest, re-imagined as the future. Music composed by Yasmeen Hitti with Dan's remix. Breakdancers, impossibly talented.",
               "From the south of the world, we are shaping our own cinema, our own experiences, our own narratives. Those who control the systems of distribution control the future, but we have community, and we hold it in our hands."],
         quote=None, links=[],
         list=("Our instrument", ["Visual generation: StreamDiffusion, dynamic prompts, ControlNet",
                                  "Temporal stability: seed noise, V2V cache, feature injection",
                                  "Embodied input: body, breakdance, camera and sensor data",
                                  "Performative output: TouchDesigner, projection, sound sync"]),
         signed="Violeta Ayala",
         picture=("maze:todo-nace-stage", "A dancer crouches on a checked floor under green light. The audience stands around him and two screens show blue creatures.")),
]

# The record: one card for each moment, as made by the studio. (when, sort key, title, place, card)
FF_RECORD = [
    ("September 2018", "2018-09", "Prison X at CPH:LAB", "Copenhagen. Immersive story development.", "ff-33"),
    ("May 2019", "2019-05", "La Diablita at the MIT Open Documentary Lab", "Cambridge. Animatronic prototype reveal.", "ff-32"),
    ("January 2021", "2021-01", "Prison X premieres at Sundance", "Park City. Chapter 1: The Devil and The Sun.", "ff-31"),
    ("2022", "2022-01", "EXPYLab", "Asunción. Meta Community Grant.", "ff-29"),
    ("June 2022", "2022-06", "Prison X at NewImages Festival", "Paris. Live meta-creation showcase.", "ff-27"),
    ("September to December 2022", "2022-09", "Las Awichas, world premiere", "El Martadero, Cochabamba. A 300 m² hall.", "ff-28"),
    ("February 2023", "2023-02", "Electric Dreams: Decolonising Virtual Spaces", "Adelaide. Keynote and panel.", "ff-26"),
    ("March 2023", "2023-03", "Cyberpunk Tinkus Live at AIDC", "Melbourne. Mocap, Metahuman and multi-screen cinema.", "ff-25"),
    ("2023", "2023-06", "Games for Change XR Brain Jam", "New York. XR Innovation Award.", "ff-23"),
    ("October 2023", "2023-10", "Prison X at SXSW Sydney", "International Convention and Entertainment Centre. Double-booth installation.", "ff-24"),
    ("7 March to 20 April 2024", "2024-03", "Las Awichas at GLOW", "The Arcade, King's College London, the Strand.", "ff-22"),
    ("May 2024", "2024-05", "Violeta Ayala is selected as a Salzburg Global Fellow", "", "ff-21"),
    ("August 2024", "2024-08", "Violeta Ayala speaks at the Asia Blockchain Summit", "Taipei.", "ff-20"),
    ("September 2024", "2024-09", "Huk the Jaguaress in development at Mila", "Mila, the Québec AI Institute, Montréal.", "ff-18"),
    ("November 2024", "2024-11", "Prison X is released on Steam", "From Sundance to Cannes to Steam.", "ff-17"),
    ("2024", "2024-11b", "Yasmeen Hitti joins United Notions Film", "", "ff-16"),
    ("December 2024", "2024-12", "Las Awichas secures Screen NSW development funding", "", "ff-14"),
    ("12 December and 10 January", "2024-12b", "Two online workshops with the University of Nottingham", "For women, non-binary, trans and LGBTQIA+ artists, on large language models and creative practice.", "ff-15"),
    ("February 2025", "2025-02", "Feminist tech at the University of Nottingham", "Violeta Ayala and Yasmeen Hitti at the Fair Futures initiative.", "ff-13"),
    ("February 2025", "2025-02b", "Las Awichas XR is nominated at AIDC", "Best Interactive / Immersive Documentary, Melbourne.", "ff-12"),
    ("2025", "2025-03", "Las Awichas wins at the AIDC Awards", "Best Interactive / Immersive Documentary, at the Australian International Documentary Conference.", "ff-08"),
    ("19 to 30 March 2025", "2025-03b", "Huk the Jaguaress premieres at CPH:DOX", "Kunsthal Charlottenborg, Copenhagen. Inter:Active exhibition.", "ff-10"),
    ("March 2025", "2025-03c", "Huk at CPH:DOX", "Kunsthal Charlottenborg, Copenhagen. A 4 m by 4.6 m gallery.", "ff-07"),
    ("25 March 2025", "2025-03d", "Adaptive Storytelling: Crafting the Future Production Team", "CPH:DOX, Dialogues on Interactivity.", "ff-11"),
    ("", "2025-03e", "Dr Yasmeen Hitti: bridging plant behaviour and technology", "She defends her PhD at McGill University and Mila.", "ff-09"),
    ("April 2025", "2025-04", "Huk at NewImages Festival", "Forum des images, Paris. An 80 m² tent.", "ff-03"),
    ("26 June to 26 August 2025", "2025-06", "Las Awichas at SURREALITY", "HKUST (Guangzhou). An AI and XR art exhibition.", "ff-02"),
]

# ------------------------------------------------------------------------------------------ for press and media
PRESS_DESCRIPTION = ("The press page of United Notions Film: interviews, press materials, images and background on the films, "
                     "the virtual reality, the installations and the lab.")
PRESS_LEAD = ("We make films, immersive experiences and computational storytelling systems across screen, space and code. "
              "We give interviews and we provide images, clips and background on every work.")
PRESS_PROVIDE = [
    "Contact with directors, artists, producers and collaborators",
    "Press materials and digital assets",
    "Images and photography",
    "Trailers and video excerpts",
    "B-roll, raw footage or edited clips on request",
    "Graphics and stills",
    "Slides and presentation materials",
    "Interviews by email, remote or in person",
    "Studio visits where possible",
    "Broadcast-quality audio and video participation where feasible",
    "Attendance at select screenings, exhibitions, talks and events",
]
PRESS_TOPICS = [
    "Film futurism",
    "Documentary innovation",
    "XR, VR and spatial storytelling",
    "Feminist AI",
    "Computational creativity",
    "Nonhuman characters and AI animation",
    "Embodied interfaces",
    "Real-time image systems",
    "Indigenous and non-Western systems",
    "Access, infrastructure and public life",
    "Technologies of distribution",
    "Art, politics and emerging media",
    "Public-interest storytelling",
    "Experimental animation and immersive narrative design",
]
PRESS_CONTACT = ("dan", "unf.red")
PRESS_CONTACT_NOTE = "To speak with United Notions Film about any of these topics, or about a specific work, write to this address."
# descriptions of the pictures of the press page
PRESS_PICTURES = {
    "press-page-01": "A speaker holds a microphone and a phone on a stage, in front of a projected slide.",
    "press-page-02": "A speaker in a green top talks into a microphone.",
    "press-page-03": "A speaker at a lectern raises a hand beside a large screen. On the screen, a silver gecko sits on that hand.",
}

# ------------------------------------------------------------------------------------------ news
NEWS_DESCRIPTION = ("What the press wrote about the films, the virtual reality and the installations of United Notions Film. "
                    "Every clipping links to the article.")
# newest work first: (key in the picture manifest, work slug)
NEWS_ORDER = [("press-huk", "huk-the-jaguaress"), ("press-las-awichas", "las-awichas"), ("press-la-lucha", "la-lucha"),
              ("press-prison-x", "prison-x"), ("press-cocaine-prison", "cocaine-prison"), ("press-the-fight", "the-fight"),
              ("press-the-bolivian-case", "the-bolivian-case"), ("press-stolen", "stolen")]

OUTLETS = {
    "chickeneggfilms.org": "Chicken & Egg Films", "chickeneggpics.org": "Chicken & Egg Pictures", "lostiempos.com": "Los Tiempos", "opinion.com.bo": "Opinión",
    "vision360.bo": "Visión 360", "yotambien.mx": "Yo También", "movingimage.org": "Museum of the Moving Image", "youtu.be": "YouTube", "youtube.com": "YouTube",
    "forbes.com": "Forbes", "theindianpanorama.news": "The Indian Panorama", "instagram.com": "Instagram", "deadline.com": "Deadline", "vozdeamerica.com": "Voz de América",
    "vistprojects.com": "VIST Projects", "moveablefest.com": "The Moveable Fest", "unseenfilms.net": "Unseen Films", "thetruthinthisart.com": "The Truth In This Art",
    "laestatuilla.com": "La Estatuilla", "southphillyreview.com": "South Philly Review", "phillytrib.com": "The Philadelphia Tribune", "la-razon.com": "La Razón",
    "realscreen.com": "Realscreen", "sohu.com": "Sohu", "britishcinematographer.co.uk": "British Cinematographer", "8thwall.com": "8th Wall",
    "nottingham.ac.uk": "University of Nottingham", "xrmust.com": "XR Must", "kcl.ac.uk": "King's College London", "wolfbrown.com": "WolfBrown",
    "povmagazine.com": "POV Magazine", "cinema-scope.com": "Cinema Scope", "cinematropical.com": "Cinema Tropical", "filmmakermagazine.com": "Filmmaker Magazine",
    "remezcla.com": "Remezcla", "nilegirl.medium.com": "Medium", "medium.com": "Medium", "womenandhollywood.com": "Women and Hollywood", "shedoesthecity.com": "She Does The City",
    "nonfics.com": "Nonfics", "inreviewonline.com": "In Review Online", "baz-art.org": "Baz'art", "eldeber.com.bo": "El Deber", "nowtoronto.com": "NOW Toronto",
    "wifv.org": "Women in Film & Video", "thefilmstage.com": "The Film Stage", "girltalkhq.com": "GirlTalkHQ", "straight.com": "The Georgia Straight",
    "culturopoing.com": "Culturopoing", "lavozdebolivia.com": "La Voz de Bolivia", "france24.com": "France 24", "noticiasfides.com": "Agencia de Noticias Fides",
    "theplaylist.net": "The Playlist", "nofilmschool.com": "No Film School", "theverge.com": "The Verge", "rivista.ai": "Rivista.AI", "dl.acm.org": "ACM Digital Library",
    "nationaltribune.com.au": "The National Tribune", "panoramaducinemacolombien.com": "Panorama du cinéma colombien", "screenhub.com.au": "ScreenHub", "13.cl": "Canal 13",
    "noproscenium.com": "No Proscenium", "smh.com.au": "The Sydney Morning Herald", "roughcutfilm.com": "Rough Cut", "paginasiete.bo": "Página Siete", "fivars.net": "FIVARS",
    "prensa-latina.cu": "Prensa Latina", "uploadvr.com": "UploadVR", "artnews.com": "ARTnews", "cocreationstudio.mit.edu": "MIT Co-Creation Studio", "w.soundcloud.com": "SoundCloud",
    "vrscout.com": "VRScout", "voicesofvr.com": "Voices of VR", "variety.com": "Variety", "ausfilm.com.au": "Ausfilm", "sundance.org": "Sundance Institute",
    "filmink.com.au": "FilmInk", "immerse.news": "Immerse", "vanityfair.com": "Vanity Fair", "opendoclab.mit.edu": "MIT Open Documentary Lab", "cnet.com": "CNET",
    "popmatters.com": "PopMatters", "stfdocs.com": "Stranger Than Fiction", "newmatilda.com": "New Matilda", "facebook.com": "Facebook", "vt.tiktok.com": "TikTok",
    "timeout.com": "Time Out", "ibermediadigital.com": "Ibermedia Digital", "theguardian.com": "The Guardian", "cnn.com": "CNN", "tvtechnology.com": "TV Technology",
    "abc.net.au": "ABC", "indiewire.com": "IndieWire", "elpais.com": "El País", "bbc.com": "BBC", "elmundo.es": "El Mundo",
}
# links whose outlet is better told from the address than from the site
OUTLET_BY_PATH = [("/art-in-america/", "Art in America"), ("face2face-with-david-peck", "Face2Face with David Peck"), ("bbc.com/mundo", "BBC Mundo"),
                  ("docs.google.com/document/d/1qJl3UPDaWRslQQHZgYoXv_Y3OAPv0NKD00LkUd4cHL8", "Review by Juan J. Arroyo")]
