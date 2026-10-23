"""
Quran API Integration for Daily Dhikr (Verse of the Day).
Sources authentic Quranic text and verified translations from https://github.com/fawazahmed0/quran-api.
Filters for concise, short, and profoundly meaningful verses suitable for Instagram layouts.
Normalizes Uthmani orthography marks to standard Arabic Unicode with complete Tashkeel.
"""

import json
import logging
import re
import urllib.request
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session

from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    AuditLog,
)
from app.content.verification import compute_arabic_checksum

logger = logging.getLogger(__name__)

# Primary GitHub Raw repository URL and fallback CDN
PRIMARY_API_BASE = "https://raw.githubusercontent.com/fawazahmed0/quran-api/1/editions"
FALLBACK_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions"

DEFAULT_HEADERS = {
    "User-Agent": "DailyDhikr/1.0 (https://github.com/daily-dhikr)"
}

# Complete 114 Surah reference dictionary
SURAHS: Dict[int, Dict[str, str]] = {
    1: {"name_en": "Al-Fatihah", "name_ar": "الفاتحة", "meaning": "The Opening"},
    2: {"name_en": "Al-Baqarah", "name_ar": "البقرة", "meaning": "The Cow"},
    3: {"name_en": "Ali 'Imran", "name_ar": "آل عمران", "meaning": "Family of Imran"},
    4: {"name_en": "An-Nisa", "name_ar": "النساء", "meaning": "The Women"},
    5: {"name_en": "Al-Ma'idah", "name_ar": "المائدة", "meaning": "The Table Spread"},
    6: {"name_en": "Al-An'am", "name_ar": "الأنعام", "meaning": "The Cattle"},
    7: {"name_en": "Al-A'raf", "name_ar": "الأعراف", "meaning": "The Heights"},
    8: {"name_en": "Al-Anfal", "name_ar": "الأنفال", "meaning": "The Spoils of War"},
    9: {"name_en": "At-Tawbah", "name_ar": "التوبة", "meaning": "The Repentance"},
    10: {"name_en": "Yunus", "name_ar": "يونس", "meaning": "Jonah"},
    11: {"name_en": "Hud", "name_ar": "هود", "meaning": "Hud"},
    12: {"name_en": "Yusuf", "name_ar": "يوسف", "meaning": "Joseph"},
    13: {"name_en": "Ar-Ra'd", "name_ar": "الرعد", "meaning": "The Thunder"},
    14: {"name_en": "Ibrahim", "name_ar": "إبراهيم", "meaning": "Abraham"},
    15: {"name_en": "Al-Hijr", "name_ar": "الحجر", "meaning": "The Rocky Tract"},
    16: {"name_en": "An-Nahl", "name_ar": "النحل", "meaning": "The Bee"},
    17: {"name_en": "Al-Isra", "name_ar": "الإسراء", "meaning": "The Night Journey"},
    18: {"name_en": "Al-Kahf", "name_ar": "الكهف", "meaning": "The Cave"},
    19: {"name_en": "Maryam", "name_ar": "مريم", "meaning": "Mary"},
    20: {"name_en": "Taha", "name_ar": "طه", "meaning": "Ta-Ha"},
    21: {"name_en": "Al-Anbiya", "name_ar": "الأنبياء", "meaning": "The Prophets"},
    22: {"name_en": "Al-Hajj", "name_ar": "الحج", "meaning": "The Pilgrimage"},
    23: {"name_en": "Al-Mu'minun", "name_ar": "المؤمنون", "meaning": "The Believers"},
    24: {"name_en": "An-Nur", "name_ar": "النور", "meaning": "The Light"},
    25: {"name_en": "Al-Furqan", "name_ar": "الفرقان", "meaning": "The Criterion"},
    26: {"name_en": "Ash-Shu'ara", "name_ar": "الشعراء", "meaning": "The Poets"},
    27: {"name_en": "An-Naml", "name_ar": "النمل", "meaning": "The Ant"},
    28: {"name_en": "Al-Qasas", "name_ar": "القصص", "meaning": "The Stories"},
    29: {"name_en": "Al-'Ankabut", "name_ar": "العنكبوت", "meaning": "The Spider"},
    30: {"name_en": "Ar-Rum", "name_ar": "الروم", "meaning": "The Romans"},
    31: {"name_en": "Luqman", "name_ar": "لقمان", "meaning": "Luqman"},
    32: {"name_en": "As-Sajdah", "name_ar": "السجدة", "meaning": "The Prostration"},
    33: {"name_en": "Al-Ahzab", "name_ar": "الأحزاب", "meaning": "The Combined Forces"},
    34: {"name_en": "Saba", "name_ar": "سبأ", "meaning": "Sheba"},
    35: {"name_en": "Fatir", "name_ar": "فاطر", "meaning": "Originator"},
    36: {"name_en": "Ya-Sin", "name_ar": "يس", "meaning": "Ya-Sin"},
    37: {"name_en": "As-Saffat", "name_ar": "الصافات", "meaning": "Those who set the Ranks"},
    38: {"name_en": "Sad", "name_ar": "ص", "meaning": "The Letter Sad"},
    39: {"name_en": "Az-Zumar", "name_ar": "الزمر", "meaning": "The Troops"},
    40: {"name_en": "Ghafir", "name_ar": "غافر", "meaning": "The Forgiver"},
    41: {"name_en": "Fussilat", "name_ar": "فصلت", "meaning": "Explained in Detail"},
    42: {"name_en": "Ash-Shura", "name_ar": "الشورى", "meaning": "The Consultation"},
    43: {"name_en": "Az-Zukhruf", "name_ar": "الزخرف", "meaning": "The Ornaments of Gold"},
    44: {"name_en": "Ad-Dukhan", "name_ar": "الدخان", "meaning": "The Smoke"},
    45: {"name_en": "Al-Jathiyah", "name_ar": "الجاثية", "meaning": "The Crouching"},
    46: {"name_en": "Al-Ahqaf", "name_ar": "الأحقاف", "meaning": "The Wind-Curved Sandhills"},
    47: {"name_en": "Muhammad", "name_ar": "محمد", "meaning": "Muhammad"},
    48: {"name_en": "Al-Fath", "name_ar": "الفتح", "meaning": "The Victory"},
    49: {"name_en": "Al-Hujurat", "name_ar": "الحجرات", "meaning": "The Rooms"},
    50: {"name_en": "Qaf", "name_ar": "ق", "meaning": "The Letter Qaf"},
    51: {"name_en": "Adh-Dhariyat", "name_ar": "الذاريات", "meaning": "The Winnowing Winds"},
    52: {"name_en": "At-Tur", "name_ar": "الطور", "meaning": "The Mount"},
    53: {"name_en": "An-Najm", "name_ar": "النجم", "meaning": "The Star"},
    54: {"name_en": "Al-Qamar", "name_ar": "القمر", "meaning": "The Moon"},
    55: {"name_en": "Ar-Rahman", "name_ar": "الرحمن", "meaning": "The Beneficent"},
    56: {"name_en": "Al-Waqi'ah", "name_ar": "الواقعة", "meaning": "The Inevitable"},
    57: {"name_en": "Al-Hadid", "name_ar": "الحديد", "meaning": "The Iron"},
    58: {"name_en": "Al-Mujadila", "name_ar": "المجادلة", "meaning": "The Pleading Woman"},
    59: {"name_en": "Al-Hashr", "name_ar": "الحشر", "meaning": "The Exile"},
    60: {"name_en": "Al-Mumtahanah", "name_ar": "الممتحنة", "meaning": "She that is to be examined"},
    61: {"name_en": "As-Saff", "name_ar": "الصف", "meaning": "The Ranks"},
    62: {"name_en": "Al-Jumu'ah", "name_ar": "الجمعة", "meaning": "Friday"},
    63: {"name_en": "Al-Munafiqun", "name_ar": "المنافقون", "meaning": "The Hypocrites"},
    64: {"name_en": "At-Taghabun", "name_ar": "التغابن", "meaning": "Mutual Disillusion"},
    65: {"name_en": "At-Talaq", "name_ar": "الطلاق", "meaning": "The Divorce"},
    66: {"name_en": "At-Tahrim", "name_ar": "التحريم", "meaning": "The Prohibition"},
    67: {"name_en": "Al-Mulk", "name_ar": "الملك", "meaning": "The Sovereignty"},
    68: {"name_en": "Al-Qalam", "name_ar": "القلم", "meaning": "The Pen"},
    69: {"name_en": "Al-Haqqah", "name_ar": "الحاقة", "meaning": "The Reality"},
    70: {"name_en": "Al-Ma'arij", "name_ar": "المعارج", "meaning": "The Ascending Stairways"},
    71: {"name_en": "Nuh", "name_ar": "نوح", "meaning": "Noah"},
    72: {"name_en": "Al-Jinn", "name_ar": "الجن", "meaning": "The Jinn"},
    73: {"name_en": "Al-Muzzammil", "name_ar": "المزمل", "meaning": "The Enshrouded One"},
    74: {"name_en": "Al-Muddaththir", "name_ar": "المدثر", "meaning": "The Cloaked One"},
    75: {"name_en": "Al-Qiyamah", "name_ar": "القيامة", "meaning": "The Resurrection"},
    76: {"name_en": "Al-Insan", "name_ar": "الإنسان", "meaning": "The Man"},
    77: {"name_en": "Al-Mursalat", "name_ar": "المرسلات", "meaning": "The Emissaries"},
    78: {"name_en": "An-Naba", "name_ar": "النبأ", "meaning": "The Tidings"},
    79: {"name_en": "An-Nazi'at", "name_ar": "النازعات", "meaning": "Those who drag forth"},
    80: {"name_en": "'Abasa", "name_ar": "عبس", "meaning": "He Frowned"},
    81: {"name_en": "At-Takwir", "name_ar": "التكوير", "meaning": "The Overthrowing"},
    82: {"name_en": "Al-Infitar", "name_ar": "الانفطار", "meaning": "The Cleaving"},
    83: {"name_en": "Al-Mutaffifin", "name_ar": "المطففين", "meaning": "Defrauding"},
    84: {"name_en": "Al-Inshiqaq", "name_ar": "الانشقاق", "meaning": "The Splitting Open"},
    85: {"name_en": "Al-Buruj", "name_ar": "البروج", "meaning": "The Mansions of the Stars"},
    86: {"name_en": "At-Tariq", "name_ar": "الطارق", "meaning": "The Morning Star"},
    87: {"name_en": "Al-A'la", "name_ar": "الأعلى", "meaning": "The Most High"},
    88: {"name_en": "Al-Ghashiyah", "name_ar": "الغاشية", "meaning": "The Overwhelming"},
    89: {"name_en": "Al-Fajr", "name_ar": "الفجر", "meaning": "The Dawn"},
    90: {"name_en": "Al-Balad", "name_ar": "البلد", "meaning": "The City"},
    91: {"name_en": "Ash-Shams", "name_ar": "الشمس", "meaning": "The Sun"},
    92: {"name_en": "Al-Layl", "name_ar": "الليل", "meaning": "The Night"},
    93: {"name_en": "Ad-Duha", "name_ar": "الضحى", "meaning": "The Morning Hours"},
    94: {"name_en": "Ash-Sharh", "name_ar": "الشرح", "meaning": "The Relief"},
    95: {"name_en": "At-Tin", "name_ar": "التين", "meaning": "The Fig"},
    96: {"name_en": "Al-'Alaq", "name_ar": "العلق", "meaning": "The Clot"},
    97: {"name_en": "Al-Qadr", "name_ar": "القدر", "meaning": "The Power"},
    98: {"name_en": "Al-Bayyinah", "name_ar": "البينة", "meaning": "The Clear Proof"},
    99: {"name_en": "Az-Zalzalah", "name_ar": "الزلزلة", "meaning": "The Earthquake"},
    100: {"name_en": "Al-'Adiyat", "name_ar": "العاديات", "meaning": "The Courser"},
    101: {"name_en": "Al-Qari'ah", "name_ar": "القارعة", "meaning": "The Calamity"},
    102: {"name_en": "At-Takathur", "name_ar": "التكاثر", "meaning": "The Rivalry in World Increase"},
    103: {"name_en": "Al-'Asr", "name_ar": "العصر", "meaning": "The Declining Day"},
    104: {"name_en": "Al-Humazah", "name_ar": "الهمزة", "meaning": "The Traducer"},
    105: {"name_en": "Al-Fil", "name_ar": "الفيل", "meaning": "The Elephant"},
    106: {"name_en": "Quraysh", "name_ar": "قريش", "meaning": "Quraysh"},
    107: {"name_en": "Al-Ma'un", "name_ar": "الماعون", "meaning": "The Small Kindness"},
    108: {"name_en": "Al-Kawthar", "name_ar": "الكوثر", "meaning": "The Abundance"},
    109: {"name_en": "Al-Kafirun", "name_ar": "الكافرون", "meaning": "The Disbelievers"},
    110: {"name_en": "An-Nasr", "name_ar": "النصر", "meaning": "The Divine Support"},
    111: {"name_en": "Al-Masad", "name_ar": "المسد", "meaning": "The Palm Fiber"},
    112: {"name_en": "Al-Ikhlas", "name_ar": "الإخلاص", "meaning": "The Sincerity"},
    113: {"name_en": "Al-Falaq", "name_ar": "الفلق", "meaning": "The Daybreak"},
    114: {"name_en": "An-Nas", "name_ar": "الناس", "meaning": "Mankind"},
}


CuratedVerseSpec = Union[Tuple[int, int], Tuple[int, Tuple[int, int]]]

# Curated collection of profound, authentic Quranic verses strictly verified for:
# 1. Waqf Hasan & Waqf Taam (الوقف الحسن والتام): Every verse or verse-pair is semantically and
#    theologically complete with zero dangling conditions, missing antecedents, or conflicting clauses.
# 2. Raw Uthmanic Script: Verbatim Madani Mushaf orthography including authentic Tajweed pause marks.
CURATED_SHORT_VERSES: List[CuratedVerseSpec] = [
    (2, 186),         # Al-Baqarah: When My servants ask concerning Me, I am near...
    (39, 53),         # Az-Zumar: O My servants who have transgressed, do not despair of Allah's mercy...
    (35, 2),          # Fatir: Whatever Allah opens to mankind of mercy - none can withhold it; and whatever He withholds - none can release it...
    (2, 152),         # Al-Baqarah: Remember Me; I will remember you. And be grateful to Me and do not deny Me
    (94, (5, 6)),     # Ash-Sharh: For indeed, with hardship ease. Indeed, with hardship ease (paired promise)
    (14, 7),          # Ibrahim: If you are grateful, I will surely increase you
    (9, 129),         # At-Tawbah: If they turn away, say: Sufficient for me is Allah; none has the right to be worshiped but Him
    (40, 60),         # Ghafir: Call upon Me; I will respond to you
    (20, 46),         # Taha: Fear not. Indeed, I am with you both; I hear and I see
    (21, 87),         # Al-Anbiya: Du'a of Yunus (There is no deity except You; exalted are You...)
    (33, (41, 42)),   # Al-Ahzab: O you who have believed, remember Allah with much remembrance and exalt Him morning and afternoon
    (33, 56),         # Al-Ahzab: Indeed, Allah and His angels confer blessing upon the Prophet. O you who have believed, ask blessings...
    (3, 139),         # Ali 'Imran: Do not weaken and do not grieve, and you will be superior if you are [true] believers
    (2, 201),         # Al-Baqarah: Our Lord, give us in this world [that which is] good and in the Hereafter [that which is] good...
    (3, 8),           # Ali 'Imran: Our Lord, let not our hearts deviate after You have guided us and grant us mercy...
    (55, 60),         # Ar-Rahman: Is the reward for good [anything] but good?
    (29, 69),         # Al-Ankabut: And those who strive for Us - We will surely guide them to Our ways
    (50, 16),         # Qaf: And We are closer to him than [his] jugular vein
    (35, 15),         # Fatir: O mankind, you are those in need of Allah, while Allah is the Free of need, the Praiseworthy
    (48, 4),          # Al-Fath: It is He who sent down tranquility into the hearts of the believers...
    (59, 18),         # Al-Hashr: O you who have believed, fear Allah. And let every soul look to what it has put forth for tomorrow...
    (20, 114),        # Taha: Exalted is Allah, the King, the Truth... and say: My Lord, increase me in knowledge
    (15, (98, 99)),   # Al-Hijr: Exalt [Allah] with praise of your Lord and be of those who prostrate, and worship your Lord until certainty...
    (68, 4),          # Al-Qalam: And indeed, you are of a great moral character
    (88, (21, 22)),   # Al-Ghashiyah: So remind, [O Muhammad]; you are only a reminder. You are not over them a controller
    (64, 13),         # At-Taghabun: Allah - there is no deity except Him. And upon Allah let the believers rely
    (41, 34),         # Fussilat: Not equal are the good deed and the bad. Repel [evil] by that [deed] which is better...
    (42, 28),         # Ash-Shura: And it is He who sends down the rain after they had despaired and spreads His mercy...
    (67, (13, 14)),   # Al-Mulk: Conceal your speech or publicize it; indeed, He is Knowing of that within the breasts. Does He not know...
    (112, (1, 4)),    # Al-Ikhlas: Complete Surah (The absolute unity and perfection of Allah)
]


def normalize_quranic_text(text: str) -> str:
    """
    Cleans raw Uthmani Quranic text while 100% preserving:
    - Authentic Uthmanic orthography (الرسم العثماني المصحفي).
    - All Tashkeel (harakat, shaddah, sukoon, tanween).
    - Authentic Tajweed and Waqf marks (صلى \u06D6, قلى \u06D7, ج \u06DA, مـ \u06D8, لا \u06D9, معانقة \u06DB).
    - Quranic Sukoon \u06E1 (small dotless head of khah), rounded zero \u06DF,
      small high waw \u06E5 (ۥ), small high yeh \u06E6 (ۦ).
    - Maps Farsi Yeh (\u06CC) to Arabic Yeh (\u064A) to ensure authentic Hafs two-dot rendering.
    - Strips isolated leading Rub el Hizb quarter markers (۞ \u06DE) and non-breaking spaces.
    """
    if not text:
        return ""

    # Strip leading Rub el Hizb quarter marker and non-breaking spaces
    text = text.lstrip(" ۞\xa0\u06de")

    # Map Farsi Yeh to Arabic Yeh for authentic two-dot presentation in Hafs
    text = text.replace("\u06cc", "\u064a")
    text = text.replace("\u06c0", "\u0647\u0654")

    # Clean redundant whitespace while strictly preserving all Uthmani and Waqf marks
    return " ".join(text.strip().split())


def _http_get_json(url: str, fallback_url: Optional[str] = None) -> dict:
    """Fetches JSON from URL with error handling and fallback mechanism."""
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        if fallback_url:
            logger.info(f"Primary endpoint failed ({e}). Trying fallback: {fallback_url}")
            fallback_req = urllib.request.Request(fallback_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(fallback_req, timeout=10) as fb_resp:
                return json.loads(fb_resp.read().decode("utf-8"))
        raise


def fetch_verse(chapter: int, verse: Union[int, Tuple[int, int]]) -> dict:
    """
    Fetches Arabic text with authentic Uthmani script, Tashkeel, and Waqf marks,
    along with verified English translation (Sahih International).
    Supports either a single verse (e.g. 186) or a verse range (e.g. (2, 3)).
    """
    if chapter < 1 or chapter > 114:
        raise ValueError(f"Chapter {chapter} is out of bounds (1-114).")

    surah_info = SURAHS.get(chapter, {"name_en": f"Surah {chapter}", "name_ar": "", "meaning": ""})

    if isinstance(verse, (tuple, list)):
        start_v, end_v = int(verse[0]), int(verse[1])
        ref_str = f"{chapter}:{start_v}-{end_v}"
        verses_to_fetch = list(range(start_v, end_v + 1))
    else:
        v_int = int(verse)
        ref_str = f"{chapter}:{v_int}"
        verses_to_fetch = [v_int]

    arabic_parts = []
    english_parts = []

    for v_num in verses_to_fetch:
        url_ar_primary = f"{PRIMARY_API_BASE}/ara-quranacademy/{chapter}/{v_num}.json"
        url_ar_fallback = f"{FALLBACK_API_BASE}/ara-quranacademy/{chapter}/{v_num}.json"
        url_en_primary = f"{PRIMARY_API_BASE}/eng-ummmuhammad/{chapter}/{v_num}.json"
        url_en_fallback = f"{FALLBACK_API_BASE}/eng-ummmuhammad/{chapter}/{v_num}.json"

        data_ar = _http_get_json(url_ar_primary, url_ar_fallback)
        data_en = _http_get_json(url_en_primary, url_en_fallback)

        raw_ar = data_ar.get("text", "")
        clean_ar = normalize_quranic_text(raw_ar)
        raw_en = data_en.get("text", "").strip()

        # Clean unclosed quotes in English
        if raw_en.startswith('"') and not raw_en.endswith('"'):
            raw_en = raw_en + '"'

        arabic_parts.append(clean_ar)
        english_parts.append(raw_en)

    # Join multiple verses with the authentic Ayah sign (۝)
    combined_arabic = " ۝ ".join(arabic_parts) + " ۝"
    combined_english = " ".join(english_parts)

    return {
        "chapter": chapter,
        "verse": verse,
        "surah_name_en": surah_info["name_en"],
        "surah_name_ar": surah_info["name_ar"],
        "surah_meaning": surah_info["meaning"],
        "arabic_text": combined_arabic,
        "english_meaning": combined_english,
        "reference": ref_str,
        "source_citation": f"Surah {surah_info['name_en']} [{ref_str}]",
        "char_count": len(combined_arabic),
        "word_count": len(combined_arabic.split()),
    }


def is_short_and_meaningful(
    verse_data: dict,
    max_words: int = 55,
    max_chars: int = 340,
) -> bool:
    """
    Returns True if the verse meets the criteria,
    ensuring it fits cleanly and comfortably on Instagram graphics.
    """
    words = verse_data.get("word_count", 0)
    chars = verse_data.get("char_count", 0)
    return words <= max_words and chars <= max_chars


def save_verse_to_db(
    db: Session,
    verse_data: dict,
    auto_approve: bool = True,
) -> ContentItem:
    """
    Saves a fetched Quranic verse into the database as a VERSE_OF_THE_DAY item
    with a verified SourceRecord. Idempotent: updates existing verses to raw Uthmanic script.
    """
    ch = verse_data["chapter"]
    ref_str = verse_data.get("reference") or f"{ch}:{verse_data['verse']}"
    surah_name = f"Surah {verse_data['surah_name_en']} ({verse_data.get('surah_name_ar', '')})"

    # Check if source record exists
    source = (
        db.query(SourceRecord)
        .filter(
            SourceRecord.source_type == SourceType.QURAN,
            SourceRecord.reference == ref_str,
        )
        .first()
    )

    if not source:
        source = SourceRecord(
            source_type=SourceType.QURAN,
            source_name=surah_name,
            reference=ref_str,
            verification_notes=(
                f"Sourced from Quran API (fawazahmed0/quran-api). "
                f"Script: Quran Academy (Uthmani/Tanzil verified, King Fahd Complex). "
                f"Translation: Sahih International (Umm Muhammad)."
            ),
            verified_by="Quran API / Tanzil / Sahih International",
            status=VerificationStatus.VERIFIED,
        )
        db.add(source)
        db.flush()

    # Check if content item exists with same source
    existing_item = (
        db.query(ContentItem)
        .filter(
            ContentItem.source_id == source.id,
            ContentItem.category == ContentCategory.VERSE_OF_THE_DAY,
        )
        .first()
    )

    if existing_item:
        # Upgrade existing record to raw Uthmanic script if it had previous stripped text
        if (
            existing_item.arabic_text != verse_data["arabic_text"]
            or existing_item.english_meaning != verse_data["english_meaning"]
        ):
            existing_item.arabic_text = verse_data["arabic_text"]
            existing_item.english_meaning = verse_data["english_meaning"]
            db.commit()
            logger.info(f"Updated verse {ref_str} to authentic raw Uthmanic script.")
        else:
            logger.info(f"Verse {ref_str} already up-to-date in content library (id: {existing_item.id})")
        return existing_item

    item = ContentItem(
        category=ContentCategory.VERSE_OF_THE_DAY,
        arabic_text=verse_data["arabic_text"],
        english_meaning=verse_data["english_meaning"],
        source_id=source.id,
        transliteration=None,
        is_demo=False,
        verification_status=VerificationStatus.VERIFIED,
        approval_status=ApprovalStatus.APPROVED if auto_approve else ApprovalStatus.DRAFT,
    )
    db.add(item)
    db.flush()

    audit = AuditLog(
        action="VERSE_IMPORTED",
        entity_type="content_item",
        entity_id=item.id,
        details=f"Imported Verse of the Day: Surah {verse_data['surah_name_en']} [{ref_str}]"
    )
    db.add(audit)
    db.commit()

    logger.info(f"Imported and saved Verse of the Day: {surah_name} [{ref_str}]")
    return item


def sync_curated_verses(db: Session, auto_approve: bool = True) -> List[ContentItem]:
    """
    Fetches and saves all curated short, meaningful verses from Quran API into the database.
    """
    imported_items = []
    logger.info(f"Syncing {len(CURATED_SHORT_VERSES)} curated short verses from Quran API...")

    for item_spec in CURATED_SHORT_VERSES:
        ch, v_spec = item_spec[0], item_spec[1]
        try:
            verse_data = fetch_verse(ch, v_spec)
            if is_short_and_meaningful(verse_data):
                item = save_verse_to_db(db, verse_data, auto_approve=auto_approve)
                imported_items.append(item)
            else:
                logger.warning(f"Verse {ch}:{v_spec} exceeded short length threshold, skipping.")
        except Exception as e:
            logger.error(f"Failed to fetch or import verse {ch}:{v_spec}: {e}")

    logger.info(f"Successfully synced {len(imported_items)} short verses.")
    return imported_items
