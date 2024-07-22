import random
from wave_generation import (
    floatlist,
    generate_frequency_journey,
    find_frequency,
    apply_lengthen,
    apply_trill,
    apply_post_shwoop,
    freq_timeline_from_str,
    generate_phase_continuous_wave,
    # SAMPLE_RATE,
)

# import sounddevice as sd  # type: ignore


class Word:
    MODIFIERS = ["pt", "cp", "sp", "pl", "qu"]

    def __init__(
        self,
        freq_timeline: list[floatlist],
        name: str,
        description: str = "",
        notes_string: str = "nonstandard",
        past_tense: bool = False,
        comparative: bool = False,
        superlative: bool = False,
        plural: bool = False,
        question: bool = False,
        impossible_declensions: list[str] = [],
    ):
        self.freq_timeline = freq_timeline[:]
        self.name = name
        self.description = description
        self.notes_string = notes_string
        self.past_tense = past_tense
        self.comparative = comparative
        self.superlative = superlative
        self.plural = plural
        self.question = question
        self.possible_declensions: dict[str, bool] = {
            m: m not in impossible_declensions for m in self.MODIFIERS
        }

        if past_tense and self.possible_declensions["pt"]:
            self.freq_timeline[-1] = apply_post_shwoop(self.freq_timeline[-1], -7)
        if comparative and self.possible_declensions["cp"]:
            self.freq_timeline[-1] = apply_trill(self.freq_timeline[-1], -2)
        if superlative and self.possible_declensions["sp"]:
            self.freq_timeline[-1] = apply_trill(self.freq_timeline[-1], 2)
        if plural and self.possible_declensions["pl"]:
            self.freq_timeline[-1] = apply_lengthen(self.freq_timeline[-1], 3)
        if question and self.possible_declensions["qu"]:
            self.freq_timeline[-1] = apply_post_shwoop(self.freq_timeline[-1], 7)

    @classmethod
    def from_string(
        cls,
        string: str,
        name: str,
        description: str = "",
        impossible_declensions: list[str] = [],
    ) -> "Word":
        return Word(
            freq_timeline_from_str(string),
            name,
            description,
            string,
            impossible_declensions=impossible_declensions,
        )

    # def play(self, speed: float = 1) -> None:
    #     sd.play(self.wave(), samplerate=SAMPLE_RATE * speed)  # type: ignore
    #     sd.wait()  # type: ignore

    def wave(self) -> floatlist:
        return generate_phase_continuous_wave(self.freq_timeline)

    def __str__(self):
        return f'{self.name}{" (past tense)" if self.past_tense else ""}{" (comparative)" if self.comparative else ""}{" (superlative)" if self.superlative else ""}{" (plural)" if self.plural else ""}{" (question)" if self.question else ""}'

    def __repr__(self):
        return str(self)

    def get_notes_string(self):
        string = self.notes_string
        string = string.replace(":-1:", ":&#8203;-1:")
        if self.past_tense:
            string += "\\"
        if self.comparative:
            string += "~"
        if self.superlative:
            string += "*"
        if self.plural:
            string += "_"
        if self.question:
            string += "/"
        if string[0] == ":":
            string = string[1:]
        return string

    def past_tensify(self):
        return Word(
            self.freq_timeline,
            self.name,
            self.description,
            self.notes_string,
            True,
            self.comparative,
            self.superlative,
            self.plural,
            self.question,
            [k for k in self.possible_declensions if not self.possible_declensions[k]],
        )

    def comparativize(self):
        return Word(
            self.freq_timeline,
            self.name,
            self.description,
            self.notes_string,
            self.past_tense,
            True,
            False,
            self.plural,
            self.question,
            [k for k in self.possible_declensions if not self.possible_declensions[k]],
        )

    def superlativize(self):
        return Word(
            self.freq_timeline,
            self.name,
            self.description,
            self.notes_string,
            self.past_tense,
            False,
            True,
            self.plural,
            self.question,
            [k for k in self.possible_declensions if not self.possible_declensions[k]],
        )

    def pluralize(self):
        return Word(
            self.freq_timeline,
            self.name,
            self.description,
            self.notes_string,
            self.past_tense,
            self.comparative,
            self.superlative,
            True,
            self.question,
            [k for k in self.possible_declensions if not self.possible_declensions[k]],
        )

    def questionify(self):
        return Word(
            self.freq_timeline,
            self.name,
            self.description,
            self.notes_string,
            self.past_tense,
            self.comparative,
            self.superlative,
            self.plural,
            True,
            [k for k in self.possible_declensions if not self.possible_declensions[k]],
        )


FREQS = list(map(find_frequency, range(24)))

# Pronouns
# 0
MI = Word.from_string(
    "0:-5",
    "mi",
    "this is the first person singular pronoun",
    ["pt", "cp", "sp"],
)
# 1
MI_ = MI.pluralize()
MI_.description = "elongating the last note indicates plural, so this is the first person plural pronoun"
# 2
SINA = Word.from_string(
    "0:-2",
    "sina",
    "second person singular pronoun",
    ["pt", "cp", "sp"],
)
# 3
ONA = Word.from_string(
    "0:-1",
    "ona",
    "third person singular pronoun",
    ["pt", "cp", "sp"],
)
# 4
NI = Word.from_string(
    "0:2",
    "ni",
    "this",
    ["pt", "cp", "sp"],
)

# Grammar indicators
# 5
O = Word(
    [generate_frequency_journey([FREQS[16], FREQS[0]], duration_scalars=[1.4])],
    "o",
    'indicates vocative. [jan pona mi o] means you\'re addressing a friend, [o tawa] means "go" (imperative), [jan pona mi o tawa] means "go, my friend"',
    impossible_declensions=["pt", "cp", "sp", "pl", "qu"],
)
# 6
FREEFORM = Word(
    [generate_frequency_journey([FREQS[0], FREQS[16]], duration_scalars=[1.4])],
    "freeform",
    "indicates freeform mode start or end. Use to indicate you are gonna just use melody to convey a message. Could be the jingle of a shop you're going to, or the line of a song you both know that carries a particular meaning, or any other soundbite",
    impossible_declensions=["pt", "cp", "sp", "pl", "qu"],
)
# 7
A = Word(
    [
        generate_frequency_journey(
            [FREQS[7], FREQS[7], FREQS[0]], duration_scalars=[1, 1.6]
        )
    ],
    "a",
    'means "ah" or some other exclamation, emphasis to whatever came before it  \netymelogy: sound like "ah"',
    impossible_declensions=["pt", "cp", "sp", "pl"],
)
# 8
E = Word.from_string(
    ":0",
    "e",
    "indicates a direct object follows",
    ["pt", "cp", "sp", "pl", "qu"],
)
# 9
LI = Word.from_string(
    ":0_",
    "li",
    "indicates a verb follows (not necessary after mi and sina)",
    ["pt", "cp", "sp", "pl", "qu"],
)
# 10
LA = Word.from_string(
    ":0~",
    "la",
    "indicates end of a dependent clause (not clear to me whether this word is necessary)",
    ["pt", "cp", "sp", "pl", "qu"],
)
# 11
PI = Word.from_string(
    ":0*",
    "pi",
    "indicates the next words are grouped together [jan moku ike] -> ike is about jan, [jan pi moku ike] -> ike is about moku",
    ["pt", "cp", "sp", "pl", "qu"],
)

# Other words
# 12
ALA = Word.from_string(
    "0:-3", "ala", "negates whatever came before it", ["pt", "cp", "sp", "pl"]
)
# 13
TENPO = Word.from_string(
    "0:9:7",
    "tenpo",
    "time  \netymelogy: vivalda - four seasons",
    ["pt", "cp", "sp"],
)
# 14
TAWA = Word.from_string(
    "0:4:7",
    "tawa",
    "go, leave, towards, departure",
    ["cp", "sp"],
)
# 15
TAWAd = TAWA.past_tensify()
TAWAd.description = "went, gone, something that's gone  \ngoing down in pitch after the last note indicates past tense"
# 16
KAMA = Word.from_string(
    "0:4:2",
    "kama",
    "to come, to arrive, to become, to pursue actions to arrive to (a certain state), (as preverb) to come to (verb), beginning, (as transative verb) to call for / to let [direct object] come  \netymelogy: tawa but other direction, Spinvis - kom terug (line: drink wijn)",
    ["cp", "sp"],
)
# 17
TOKI = Word.from_string("0:7", "toki", "language, speaking, hello", ["cp", "sp"])
# 18
PONA = Word.from_string("0:4", "pona", "good, simple, improve", ["pl"])
# 19
PONA_c = PONA.comparativize()
PONA_c.description = "better. to make a word comparative, add a downwards thingy. [pona~ e sina] -> better than you"
# 20
PONA_s = PONA.superlativize()
PONA_s.description = "best. to make a word superlative, add an upwards thingy."
# 21
IKE = Word.from_string("0:3", "ike", "bad, complicated, to make worse", ["pl"])
# 22
MUSI = Word.from_string("0:5:7", "musi", "beautiful, because sus4 is beautiful")
# 23
JAN = Word.from_string("0:5", "jan", "person, personify")
# 24
KULUPU = Word.from_string("0:-5:2", "kulupu", "club, team  \netymelogy: a-team theme")
# 25
WILE = Word.from_string(
    "0:2:4",
    "wile+",
    "to want  \netymelogy: want want - ik wil een kip en een paard en een koe",
)
# 26
WILE_ = Word.from_string("0:2:3", "wile-", "to have to, the sad version of to want")
# 27
MUTE = Word(
    [generate_frequency_journey([FREQS[1], FREQS[8], FREQS[0]], [1.5, 2.5])],
    "mute",
    "very, much  \netymelogy: woaw",
)
# 28
EN = Word.from_string("0:1", "en", "and", ["pt", "cp", "sp", "pl"])
# 29
ENu = EN.questionify()
ENu.description = "and? going up in pitch after the last note indicates a question"
# 30
ANU = Word.from_string("0:1_", "anu", "or", ["pt", "cp", "sp", "pl"])
# 31
LON = Word.from_string(
    "0:4:5",
    "lon",
    "to exist, to be (not often necessary bc [jan ni li pona] can mean \"this person is good\" but sometimes it's ambiguous and then it's nice to have the verb) etymelogy: let it be (verse)",
)
# 32
TOMO = Word.from_string(
    "0:7:4:2",
    "tomo",
    'house, room  \netymelogy: in my room (beach boys), the line where they say "in my room" (disregarding the chord change to the relative minor that happens just at this line)',
)
# 33
SEME = Word(
    [generate_frequency_journey([FREQS[0], FREQS[8]], duration_scalars=[2.5])],
    "seme",
    "what?",
)
# 34
TASO = Word.from_string(
    "0:-4", "taso", "but, only, sole  \netymelogy: sounds like a vibe shift"
)
# 35
LAPE = Word.from_string("0:4:4:7", "lape", "sleep  \netymelogy: the classic lullabye")
# 36
PILIN = Word.from_string(
    "0:7:3",
    "pilin",
    "to feel, feeling, touch  \netymelogy: robbie william - feel (guitar part bridge)",
)
# 37
AWEN = Word.from_string(
    "0:2:3:7",
    "awen",
    "to wait, to keep, permanent  \netymelogy: tommy emmanuel - those who wait (cool riff leading from post-verse back into verse 0:2:3:7:8:11:14:15)",
)
# 38
MOKU = Word.from_string(
    "0:-5:-1:2",
    "moku",
    "food, to eat  \netymelogy: unchained melody (line: i've hungered for)",
)
# 39
KEN = Word.from_string(
    "0:5:7:5",
    "ken",
    "to be able to, possibility, enable  \netymelogy: arctic monkeys - cornerstone (can i call you...)",
)
# 40
UNPA = Word(
    [
        generate_frequency_journey([FREQS[0], FREQS[10]], [1]),
        generate_frequency_journey([FREQS[0], FREQS[10], FREQS[0]], [1.2, 1]),
    ],
    "unpa",
    "sex, sexual  \netymelogy: obvious",
)
# 41
SONA = Word.from_string(
    "0:2:-3",
    "sona",
    "to know, knowledge, understand, know how to  \netymelogy: abba - knowing me, knowing you (intro)",
)
# 42
JO = Word.from_string("0:5:9", "jo", "to have  \netymelogy: green day - having a blast")
# 43
PALI = Word.from_string(
    "0:5:3",
    "pali",
    "to do, to make, activity, active, to create  \netymelogy: linkin park - what i've done (where he says the title)",
)
# 44
NASA = Word.from_string("0:6", "nasa", "strange, psychoactive")
# 45
MA = Word.from_string(
    "0:2:4:7", "ma", "land, outdoor area  \netymelogy: theme of the shire"
)
# 46
TELO = Word.from_string(
    "0:3:5", "telo", "water, liquid  \netymelogy: smoke on the water"
)
# 47
PO = Word.from_string(
    "0:9:5:9", "po", "police, to police, to (en)force  \netymelogy: siren"
)
# 48
ALI = Word.from_string(
    "0:8:3", "ali", "all, every, life, the universe, everything  \netymelogy: all of me"
)
# 49
MAMA = Word.from_string(
    "0:4:9:7", "mama", "parent, parental  \netymelogy: bohemian rhapsody (piano)"
)
# 50
TAN = Word.from_string(
    "0:7:5",
    "tan",
    "from, because of, since, origin, cause  \netymelogy: will young - from now on (pre-chorus) & kelly clarkson - because of you (from the root of the chord it lands on)",
)
# 51
LILI = Word.from_string("0:-1:-2", "lili", "small, a bit, short, reduce, to minimize")
# 52
SULI = Word.from_string(
    "0:1:2", "suli", "importance, big, important, significant, to matter"
)
# 53
MANI = Word.from_string(
    "0:7:5:3", "mani", "money, payment, to pay  \netymelogy: meja - all 'bout the money"
)
# 54
TRAIN = Word.from_string(
    "0:-4:3", "train", "train  (the vehicle)  \netymelogy: NS jingle"
)
# 55
RED = Word.from_string(
    "0:-5:-1",
    "red",
    "red  \netymelogy: red red wine (we try not to let words end in 0, so that 0 is always indicative of new word)",
)
# 56
ORANGE = Word.from_string(
    "0:2:4:5",
    "orange",
    "orange  \netymelogy: spinvis - grote zon (line: het is oran(je))",
)
# 57
YELLOW = Word.from_string("0:7:9:2", "yellow", "yellow  \netymelogy: yellow submarine")
# 58
GREEN = Word.from_string("0:3:5:7", "green", "green  \netymelogy: greensleeves")
# 59
BLUE = Word.from_string("0:2:7:4", "blue", "blue  \netymelogy: elo - mr blue sky")
# 60
PURPLE = Word.from_string(
    "0:3:2:3",
    "purple",
    "purple  \netymelogy: jimi hendrix - purple haze (line: purple haze)",
)
# 61
PINK = Word.from_string(
    "0:3:7:6",
    "pink",
    "pink  \netymelogy: pink panther theme",
)
# 62
BLACK = Word.from_string(
    "0:2:3:5",
    "black",
    "black  \netymelogy: rolling stones - paint it black",
)
# 63
WHITE = Word.from_string(
    "0:5:7:9", "white", "white  \netymelogy: witte rozen (line: een boeketje)"
)
# 64
SUNO = Word.from_string(
    "0:2:5:7",
    "suno",
    "sun, solar, light, to shine, bright  \tetymelogy: jacob - sun is in your eyes / beatles - here comes the sun (part after it's all right)",
)
# 65
# MUN = Word.from_string(
#     "0:8:5",
#     "mun",
#     "moon, lunar, to shine mysteriously, kinda bright  \tetymelogy: negative of SUNO",
# )
FOREST = Word.from_string("0:4:6", "forest", "forest  \netymelogy: zelda - lost woods")
KAMAPONA = Word.from_string(
    "0:4:2:4",
    "kama pona",
    "welcome  \netymelogy: composite word from kama and pona (0:4:2:**~~0~~**:4)",
)
KAMASONA = Word.from_string(
    "0:4:2:-3",
    "kama sona",
    "to learn  \netymelogy: composite word from kama and sona (0:4:2:**~~0:2~~**:-3)",
)
KULE = Word.from_string(
    "0:4:7:9", "kule", "colour  \netymelogy: cyndi lauper - true colors"
)
TAWAPONA = Word.from_string(
    "0:4:7:4",
    "tawa pona",
    "bon voyage  \netymelogy: composite word from tawa and pona (0:4:7:**~~0~~**:4)",
)
PANA = Word.from_string(
    "0:3:7", "pana", "to give, to put, emission  \netymelogy: abba - gimme gimme gimme"
)
SEWI = Word.from_string(
    "0:2:5:9", "sewi", "up, high, divine, sacred, sky  \netymelogy: hoobastank - divine"
)
LAPEPONA = Word.from_string(
    "0:4:4:7:4",
    "lape pona",
    "good night  \netymelogy: composite word from lape and pona (0:4:4:7:**~~0~~**:4)",
)
SITELEN = Word.from_string(
    "0:4:7:7",
    "sitelen",
    "to write, picture, image, to paint  \netymelogy: paper kites - paint",
)
PINI = Word.from_string(
    "0:7:3:2",
    "pini",
    "end, tip, to finish, to close  \netymelogy: linkin park - in the end",
)
SAMA = Word.from_string(
    "0:4:7:6",
    "sama",
    "same, equal, like, as  \netymelogy: courtney barnett - sunday roast (you know it's all the same to me)",
)
TENPONI = Word.from_string(
    "0:9:7:2",
    "tenpo ni",
    "then  \netymelogy: composite word from tenpo and ni (0:9:7:**~~0~~**:2)",
)
KAMAJO = Word.from_string("0:4:2:7:9", "kama jo" "to receive, to acquire")


words = {
    MI,
    MI_,
    SINA,
    ONA,
    NI,
    O,
    A,
    E,
    LI,
    LA,
    PI,
    ALA,
    TENPO,
    TAWA,
    TAWAd,
    KAMA,
    TOKI,
    PONA,
    PONA_c,
    PONA_s,
    IKE,
    MUSI,
    JAN,
    KULUPU,
    WILE,
    WILE_,
    MUTE,
    EN,
    ENu,
    ANU,
    LON,
    TOMO,
    SEME,
    TASO,
    LAPE,
    PILIN,
    AWEN,
    MOKU,
    KEN,
    UNPA,
    SONA,
    JO,
    PALI,
    NASA,
    MA,
    TELO,
    PO,
    ALI,
    MAMA,
    TAN,
    LILI,
    SULI,
    MANI,
    TRAIN,
    RED,
    ORANGE,
    YELLOW,
    GREEN,
    BLUE,
    PURPLE,
    PINK,
    BLACK,
    WHITE,
    SUNO,
    FOREST,
    KAMAPONA,
    KAMASONA,
    KULE,
    TAWAPONA,
    PANA,
    SEWI,
    LAPEPONA,
    SITELEN,
    SAMA,
    TENPONI,
}

grammar_indicators = [E, LI, PI, LA, A, O, FREEFORM]
pronouns = [MI, MI_, SINA, ONA, NI]
hard_to_classify = [ALA, SEME, MUTE]
colours = [KULE, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, BLACK, WHITE]
other_two_note_words = [PONA, PONA_c, PONA_s, IKE, TOKI, JAN, TASO, NASA, EN, ENu, ANU]
other_three_note_words = [
    LON,
    TAWA,
    TAWAd,
    KAMA,
    SONA,
    TENPO,
    WILE,
    WILE_,
    PILIN,
    KEN,
    PANA,
    LILI,
    SULI,
    TAN,
    PALI,
    MUSI,
    ALI,
    JO,
    TELO,
    KULUPU,
    TRAIN,
    FOREST,
]
other_four_note_words = [
    MA,
    TOMO,
    LAPE,
    MOKU,
    AWEN,
    MAMA,
    MANI,
    SEWI,
    PO,
    SUNO,
    SITELEN,
    SAMA,
]
other_nonstandard_words = [UNPA]
composite_words = [KAMAPONA, KAMASONA, TAWAPONA, LAPEPONA, TENPONI]


def get_random_word() -> "Word":
    moderator = random.choice(["", "pl", "pt", "qu", "cp", "sp"])
    w = random.choice(list(words))
    if moderator == "pl":
        w = w.pluralize()
    elif moderator == "pt":
        w = w.past_tensify()
    elif moderator == "qu":
        w = w.questionify()
    elif moderator == "cp":
        w = w.comparativize()
    elif moderator == "sp":
        w = w.superlativize()
    return w


todo = [
    "nimi (name, word)",
    "kepeken (to use)",
    "ijo (thing)",
    "ilo (tool)",
    "kin (also)",
    "ante (other)",
    "kalama (sound, to make noise, to play (instrument))",
    "sin (to add, new thing, addition, new, another)",
    "lipu (book, page, flat bendable thing, document, file)",
    "pakala (accident, mistake, damage, to hurt, to break, FUCK)",
    "kanker (kanker)",
    "soweli (animal, esp land animal)",
    "nasin (way, manner, road, path, system)",
]
