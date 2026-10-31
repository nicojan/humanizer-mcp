"""The modern probe set: what a 2026-10-30 rule round measured beside Tier 2.

NOT a tier. No standing bar reads it and no test gates on it, for the reasons
recorded in docs/superpowers/specs/2026-09-18-bs011-copula-anchor-and-the-modern-prose-hole.md.
It exists so the numbers in
docs/superpowers/specs/2026-10-30-research-round-academic-tells.md can be
re-run instead of quoted.

Two sets, both written before ChatGPT shipped or by an author who does not use it:

- ESSAY_SLUGS: Paul Graham's essays, every page linked from
  paulgraham.com/articles.html on 2026-10-30. Modern first-person argument, the
  register the Victorian Tier 2 cannot see.
- WIKI_TITLES: Wikipedia Featured Articles, each fetched as its last revision
  before 2022-01-01. Modern encyclopedic register.

Both are in copyright, so the text is fetched into eval/fpcorpus/modern_probe/
(gitignored) and never committed, the same arrangement as Tier 2.

    python -m eval.fpcorpus.fetch_modern_probe
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modern_probe"
# Wikimedia answers 429 to a User-Agent with no contact link, so name the project.
_UA = {"User-Agent": "mcp-humanizer-fp-probe/1.0 (https://github.com/nicojan/humanizer-mcp; one request at a time)"}
WIKI_CUTOFF = "2021-12-31T23:59:59Z"

ESSAY_SLUGS = (
    '13sentences',
    '5founders',
    '6631327',
    '95',
    'ace',
    'addiction',
    'airbnb',
    'airbnbs',
    'alien',
    'altair',
    'ambitious',
    'america',
    'angelinvesting',
    'antispam',
    'aord',
    'apple',
    'arc',
    'articles',
    'artistsship',
    'avg',
    'badeconomy',
    'before',
    'bel',
    'best',
    'better',
    'bias',
    'bio',
    'books',
    'boss',
    'brandage',
    'bronze',
    'bubble',
    'charisma',
    'cities',
    'college',
    'colleges',
    'conformism',
    'control',
    'convergence',
    'convince',
    'copy',
    'corpdev',
    'cred',
    'credentials',
    'desres',
    'determination',
    'die',
    'diff',
    'disagree',
    'disc',
    'discover',
    'distraction',
    'divergence',
    'do',
    'donate',
    'ds',
    'early',
    'earn',
    'earnest',
    'ecw',
    'equity',
    'essay',
    'faq',
    'ffb',
    'fh',
    'field',
    'fix',
    'fn',
    'foundermode',
    'founders',
    'foundersatwork',
    'foundervisa',
    'fp',
    'fr',
    'fundraising',
    'future',
    'gap',
    'gba',
    'genius',
    'getideas',
    'gh',
    'good',
    'goodart',
    'goodtaste',
    'goodwriting',
    'google',
    'googles',
    'greatwork',
    'growth',
    'guidetoinvestors',
    'hackernews',
    'head',
    'herd',
    'heresy',
    'heroes',
    'highres',
    'hiresfund',
    'hiring',
    'hp',
    'hs',
    'hubs',
    'hundred',
    'hw',
    'hwh',
    'icad',
    'ideas',
    'identity',
    'iflisp',
    'index',
    'ineq',
    'inequality',
    'investors',
    'invtrend',
    'island',
    'javacover',
    'jessica',
    'judgement',
    'kate',
    'kedrosky',
    'kids',
    'know',
    'ladder',
    'langdes',
    'laundry',
    'lesson',
    'lies',
    'lisp',
    'love',
    'lwba',
    'mac',
    'makersschedule',
    'marginal',
    'maybe',
    'mean',
    'microsoft',
    'mit',
    'mod',
    'name',
    'nerds',
    'newideas',
    'newthings',
    'nft',
    'noob',
    'noop',
    'notnot',
    'nov',
    'nthings',
    'opensource',
    'organic',
    'orth',
    'own',
    'patentpledge',
    'persistence',
    'pgh',
    'philosophy',
    'pinch',
    'polls',
    'popular',
    'pow',
    'power',
    'powerful',
    'prcmc',
    'prepare',
    'procrastination',
    'progbot',
    'prop62',
    'property',
    'publishing',
    'pypar',
    'quo',
    'ramenprofitable',
    'randomness',
    'raq',
    're',
    'read',
    'real',
    'really',
    'reddits',
    'relres',
    'revolution',
    'richnow',
    'road',
    'ronco',
    'rootsoflisp',
    'rss',
    'safe',
    'say',
    'schlep',
    'seesv',
    'segway',
    'selfindulgence',
    'sfp',
    'siliconvalley',
    'simply',
    'smart',
    'softwarepatents',
    'spam',
    'speak',
    'start',
    'startupfunding',
    'startuphubs',
    'startupideas',
    'startuplessons',
    'startupmistakes',
    'stuff',
    'submarine',
    'sun',
    'superangels',
    'superlinear',
    'swan',
    'tablets',
    'talk',
    'taste',
    'think',
    'todo',
    'top',
    'trolls',
    'twitter',
    'unions',
    'usa',
    'useful',
    'users',
    'vb',
    'vcsqueeze',
    'venturecapital',
    'vw',
    'want',
    'wealth',
    'web20',
    'webstartups',
    'weird',
    'when',
    'whyyc',
    'winc',
    'wisdom',
    'woke',
    'word',
    'words',
    'work',
    'worked',
    'writes',
    'writing44',
    'wtax',
    'yahoo',
    'ycombinator',
    'ycstart',
)

WIKI_TITLES = (
    '1850 Atlantic hurricane season',
    '1916 Texas hurricane',
    '1941 Florida hurricane',
    '1983 World Snooker Championship',
    '1995 Pacific hurricane season',
    '1998 FIFA World Cup final',
    '1999–2000 Gillingham F.C. season',
    '2000 Sri Lanka cyclone',
    '2005 Texas Longhorns football team',
    '2007 ACC Championship Game',
    '2007 Coca-Cola 600',
    '2007 USC Trojans football team',
    '2009 International Bowl',
    '2010 Football League Championship play-off final',
    '2019 Tour Championship',
    '22nd Massachusetts Infantry Regiment',
    '55 Wall Street',
    '70 Pine Street',
    '766th Independent Infantry Regiment (North Korea)',
    'A and B Loop',
    'AHS Centaur',
    'AMX-30E',
    'Ada Cambridge',
    'Adrian Cole (RAAF officer)',
    'Adventure Time',
    'Aiphanes',
    'Aitraaz',
    'Al-Hafiz',
    'All Hell Breaks Loose (Charmed)',
    'American logistics in the Northern France campaign',
    'Amphibian',
    'Ancestry of the Godwins',
    'Ancient Egyptian deities',
    'Ann Cook (cookery book writer)',
    'Anna Anderson',
    'Anodyne (album)',
    'Apollo 10',
    'Aquilegia',
    'Archaeoindris',
    'Atlantis: The Lost Empire',
    'Augustine of Canterbury',
    'Australasian Antarctic Expedition',
    'Australian Defence Force',
    'Back to the Future',
    'Balfour Declaration',
    'Batman Returns',
    'Battle of Drepana',
    'Battle of Hayes Pond',
    'Battle of Helena',
    'Battle of Ticinus',
    'Battle of Tory Island',
    'Beaver',
    'Ben Gascoigne',
    "Black Prince's chevauchée of 1355",
    'Bob Dylan',
    'Bramall Hall',
    'Brill Tramway',
    'Buzz Aldrin',
    'Call of Duty: Modern Warfare Remastered',
    'Canada jay',
    'Cape Feare',
    "Carlson's patrol",
    'Carolina Panthers',
    'Carousel (musical)',
    'Chetro Ketl',
    'Chinua Achebe',
    'Cloud Gate',
    'Coeliac disease',
    'Cognition',
    'Colossal Cave Adventure',
    'Columbia, South Carolina, Sesquicentennial half dollar',
    'Common tern',
    'Conan (2007 video game)',
    'Cortinarius caperatus',
    'Cosmic Stories and Stirring Science Stories',
    'Courageous-class aircraft carrier',
    'Coventry City 2–2 Bristol City (1977)',
    'Cryptoprocta spelea',
    "Cycling at the 2008 Summer Olympics – Men's individual road race",
    'D-Day naval deceptions',
    'Daglish railway station',
    'David Suzuki: The Autobiography',
    'Defense of the Ancients',
    'Deinocheirus',
    'Delichon',
    'Dementia with Lewy bodies',
    'Dendrocollybia',
    'Departures (2008 film)',
    'Development of Grand Theft Auto V',
    'Dilwale Dulhania Le Jayenge',
    'Discovery of nuclear fission',
    'Djedkare Isesi',
    'Dover Athletic F.C.',
    "Drapier's Letters",
    'Dromaeosauroides',
    'Drowning Girl',
    'Edward Drinker Cope',
    'El Camino: A Breaking Bad Movie',
    'Entoloma sinuatum',
    'Ernest Joyce',
    'Erschallet, ihr Lieder, erklinget, ihr Saiten! BWV 172',
    'Etihad Stadium',
    'Eurasian crag martin',
    'Everything Tastes Better with Bacon',
    'Faces (Star Trek: Voyager)',
    'Falaise pocket',
    'Fantastic Adventures',
    'Faryl',
    'Ficus macrophylla',
    'Ficus rubiginosa',
    'Fight Club',
    'Fighting in ice hockey',
    'Five pounds (gold coin)',
    'Flag of Hong Kong',
    'Flight Unlimited',
    'Flying Eagle cent',
    'Forest Park (Portland, Oregon)',
    'Fossa (animal)',
    'Fragment of a Crucifixion',
    'Frank Hague',
    'Franklin half dollar',
    'Free State of Galveston',
    'French battleship Courbet',
    'Galerina marginata',
    'Galileo project',
    'Ganoga Lake',
    'General relativity',
    'Georg Forster',
    'George Floyd (American football)',
    'Gerald Durrell',
    'Giant otter',
    'Giants: Citizen Kabuto',
    'God of War (franchise)',
    'Good Girl Gone Bad',
    'Good Girl Gone Bad: Reloaded',
    'Government of Macedonia (ancient kingdom)',
    'HMS Indefatigable (1909)',
    'Halo 3',
    'Ham House',
    'Harta Berdarah',
    'Henry (bishop of Finland)',
    'Herschel Greer Stadium',
    'High and Low (1963 film)',
    'Highway 61 Revisited',
    'History of Arsenal F.C. (1886–1966)',
    "Homer's Phobia",
    'Hoodoo Mountain',
    'Humpback whale',
    'Humphrey Stafford, 1st Duke of Buckingham',
    'Hurricane Cindy (2005)',
    'Hurricane Edith (1971)',
    'Hurricane Joaquin',
    'Hygrophoropsis aurantiaca',
    'Imleria badia',
    'Invisible rail',
    'Isabella Beeton',
    'James Bowie',
    'Jane Cobden',
    'Jarome Iginla',
    'Jersey Act',
    'Joe Hewitt (RAAF officer)',
    'John C. Breckinridge',
    'John Doubleday (restorer)',
    'Joseph Grimaldi',
    'Kalākaua coinage',
    'Kenneth Horne',
    'Kim Clijsters',
    'Learie Constantine',
    'Margaret Bondfield',
    'Martha Layne Collins',
    'Melville Fuller',
    'Michael Jordan',
    'Naval Battle of Guadalcanal',
    'Patrick Francis Healy',
    'Paul Henderson',
    'Piano music of Gabriel Fauré',
    'R. V. C. Bodley',
    'Rachelle Ann Go',
    'Randall Davidson',
    'Raymond Brownell',
    'Robert Downey Jr.',
    'Robert Hues',
    'Rufus Wilmot Griswold',
    'S. O. Davies',
    'SMS Bayern',
    'SMS Elsass',
    'Sonam Kapoor',
    'Stede Bonnet',
    'The Bus Uncle',
    'The Catlins',
    'The Chaser APEC pranks',
    'The Demi-Virgin',
    'The Emancipation of Mimi',
    "The Emperor's New School",
    'The Grand Budapest Hotel',
    'Tropical Storm Hernan (2020)',
    'V. Gordon Childe',
    'War of the Bavarian Succession',
    'Will P. Brady',
    'William Brill (RAAF officer)',
    'William Henry Harrison 1840 presidential campaign',
)


def _get(url: str, attempts: int = 5) -> bytes:
    """One polite request: back off on 429 and 503, honouring Retry-After."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503) or attempt == attempts - 1:
                raise
            time.sleep(int(exc.headers.get("Retry-After") or 2 ** (attempt + 2)))
    raise OSError(f"unreachable: {url}")


def _wiki(params: dict) -> dict:
    query = urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    return json.loads(_get("https://en.wikipedia.org/w/api.php?" + query))


def essay_text(raw_html: str) -> str:
    """Body text of one essay page, hard wrapping undone so a sentence is one line."""
    m = re.search(r'(?is)<font size="2" face="verdana">(.*)', raw_html)
    body = m.group(1) if m else raw_html
    body = re.sub(r"(?i)<br\s*/?>\s*<br\s*/?>", "\n\n", body)
    body = html.unescape(re.sub(r"(?s)<[^>]+>", " ", body))
    body = re.sub(r"[ \t]+", " ", body).split("Thanks to")[0]
    return re.sub(r"(?<!\n)\n(?!\n)", " ", body).strip()


def wiki_text(raw_html: str) -> str:
    """Paragraph text of one parsed revision, without tables, references or footnote marks."""
    raw_html = re.sub(r"(?s)<(table|style|script|sup|figure)\b.*?</\1>", " ", raw_html)
    paras = re.findall(r"(?s)<p>(.*?)</p>", raw_html)
    text = "\n\n".join(html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in paras)
    return re.sub(r"\[\d+\]|\[citation needed\]", "", text)


def _slug(title: str) -> str:
    return re.sub(r"\W+", "_", title)[:80]


def files(which: str) -> list[Path]:
    """Fetched files for 'essays' or 'wiki2021'; empty when not fetched."""
    return sorted((OUT / which).glob("*.txt"))


def fetch() -> int:
    missing = 0
    (OUT / "essays").mkdir(parents=True, exist_ok=True)
    (OUT / "wiki2021").mkdir(parents=True, exist_ok=True)
    for slug in ESSAY_SLUGS:
        dest = OUT / "essays" / f"{slug}.txt"
        if dest.exists():
            continue
        try:
            dest.write_text(essay_text(_get(f"https://paulgraham.com/{slug}.html").decode("utf-8", "replace")))
        except OSError as exc:
            missing += 1
            print(f"essay {slug}: {exc}", file=sys.stderr)
    for title in WIKI_TITLES:
        dest = OUT / "wiki2021" / f"{_slug(title)}.txt"
        if dest.exists():
            continue
        try:
            page = _wiki({"action": "query", "prop": "revisions", "titles": title, "rvstart": WIKI_CUTOFF,
                          "rvdir": "older", "rvlimit": 1, "rvprop": "ids"})["query"]["pages"][0]
            revid = page["revisions"][0]["revid"]
            dest.write_text(wiki_text(_wiki({"action": "parse", "oldid": revid, "prop": "text"})["parse"]["text"]))
        except (OSError, KeyError, IndexError) as exc:
            missing += 1
            print(f"wiki {title}: {exc}", file=sys.stderr)
    print(f"essays {len(files('essays'))}/{len(ESSAY_SLUGS)}, wiki2021 {len(files('wiki2021'))}/{len(WIKI_TITLES)}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(fetch())
