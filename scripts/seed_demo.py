"""
Seeds the database with authentic Islamic reminders and clearly marked DEMO records.
Demo records are explicitly flagged (is_demo=True) to test safety exclusion.
"""

from datetime import datetime, timezone
import sys
from pathlib import Path

# Ensure UTF-8 stdout for Windows consoles and Linux runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, get_db_context
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
)


def seed():
    init_db()
    with get_db_context() as db:
        print("Seeding verified Islamic content library...")

        # ----------------------------------------------------------------------
        # Authentic Source 1: Quran - Surah Al-Baqarah 2:152
        # ----------------------------------------------------------------------
        src_quran_1 = SourceRecord(
            source_type=SourceType.QURAN,
            source_name="Surah Al-Baqarah",
            reference="2:152",
            verification_notes="Noble Quran verse on the virtue of remembering Allah.",
            verified_by="Imam & Islamic Studies Committee",
            verified_at=datetime.now(timezone.utc),
            status=VerificationStatus.VERIFIED,
        )
        db.add(src_quran_1)
        db.flush()

        item_quran_1 = ContentItem(
            category=ContentCategory.DAILY_REMINDER,
            arabic_text="فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ",
            english_meaning="So remember Me; I will remember you. And be grateful to Me and do not deny Me.",
            transliteration="Fadhkuroonee adhkurkum washkuroo lee wa la takfuroon",
            source_id=src_quran_1.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=False,
        )
        db.add(item_quran_1)

        # ----------------------------------------------------------------------
        # Authentic Source 2: Sahih al-Bukhari - Morning Dhikr
        # ----------------------------------------------------------------------
        src_hadith_1 = SourceRecord(
            source_type=SourceType.HADITH,
            source_name="Sahih al-Bukhari",
            reference="Hadith 6306",
            hadith_grade="Sahih",
            grading_source="Imam al-Bukhari",
            verification_notes="Sayyid al-Istighfar (The Master of Forgiveness Supplication).",
            verified_by="Hadith Verification Board",
            verified_at=datetime.now(timezone.utc),
            status=VerificationStatus.VERIFIED,
        )
        db.add(src_hadith_1)
        db.flush()

        item_hadith_1 = ContentItem(
            category=ContentCategory.MORNING_DHIKR,
            arabic_text="اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ، أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ، وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ",
            english_meaning="O Allah, You are my Lord, none has the right to be worshipped but You. You created me and I am Your slave, and I am faithful to my covenant and promise to You as much as I can.",
            transliteration="Allahumma Anta Rabbi, la ilaha illa Anta, khalaqtani wa ana 'abduka, wa ana 'ala 'ahdika wa wa'dika mastata'tu...",
            source_id=src_hadith_1.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=False,
        )
        db.add(item_hadith_1)

        # ----------------------------------------------------------------------
        # Authentic Source 3: Sahih Muslim - Evening Dhikr
        # ----------------------------------------------------------------------
        src_hadith_2 = SourceRecord(
            source_type=SourceType.HADITH,
            source_name="Sahih Muslim",
            reference="Hadith 2723",
            hadith_grade="Sahih",
            grading_source="Imam Muslim",
            verification_notes="Evening refuge prayer.",
            verified_by="Hadith Verification Board",
            verified_at=datetime.now(timezone.utc),
            status=VerificationStatus.VERIFIED,
        )
        db.add(src_hadith_2)
        db.flush()

        item_hadith_2 = ContentItem(
            category=ContentCategory.EVENING_DHIKR,
            arabic_text="أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ",
            english_meaning="We have reached the evening and at this very time all sovereignty belongs to Allah, and all praise is for Allah. None has the right to be worshipped except Allah alone, without partner.",
            transliteration="Amsayna wa amsal-mulku lillah, wal-hamdu lillah, la ilaha illallahu wahdahu la shareeka lah",
            source_id=src_hadith_2.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=False,
        )
        db.add(item_hadith_2)

        # ----------------------------------------------------------------------
        # Authentic Source 4: Sahih al-Bukhari & Muslim - Beloved Words
        # ----------------------------------------------------------------------
        src_hadith_3 = SourceRecord(
            source_type=SourceType.HADITH,
            source_name="Sahih al-Bukhari & Muslim",
            reference="Bukhari 6407, Muslim 2694",
            hadith_grade="Sahih",
            grading_source="Muttafaq 'Alayh",
            verification_notes="Two words beloved to the Most Merciful.",
            verified_by="Hadith Verification Board",
            verified_at=datetime.now(timezone.utc),
            status=VerificationStatus.VERIFIED,
        )
        db.add(src_hadith_3)
        db.flush()

        item_hadith_3 = ContentItem(
            category=ContentCategory.DUA,
            arabic_text="سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
            english_meaning="Glory be to Allah and His is the praise; Glory be to Allah the Magnificent.",
            transliteration="Subhan Allahi wa bihamdihi, Subhan Allahil-Azim",
            source_id=src_hadith_3.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=False,
        )
        db.add(item_hadith_3)

        # ----------------------------------------------------------------------
        # Authentic Source 5: Daily Note Content (Short, concise <= 60 chars)
        # ----------------------------------------------------------------------
        item_note = ContentItem(
            category=ContentCategory.NOTE,
            arabic_text="سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
            english_meaning="Subhan Allah wa bihamdihi",
            transliteration="Subhan Allahi wa bihamdih",
            source_id=src_hadith_3.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=False,
        )
        db.add(item_note)

        # ----------------------------------------------------------------------
        # STRICT DEMO RECORD (is_demo=True, MUST NEVER BE PUBLISHED)
        # ----------------------------------------------------------------------
        src_demo = SourceRecord(
            source_type=SourceType.OTHER,
            source_name="Demo Test Source [NOT FOR BROADCAST]",
            reference="Test-Ref-999",
            hadith_grade="Demo Only",
            verification_notes="Test record solely to verify safety filters exclude demo data.",
            verified_by="Automated Test Suite",
            verified_at=datetime.now(timezone.utc),
            status=VerificationStatus.VERIFIED,
        )
        db.add(src_demo)
        db.flush()

        item_demo = ContentItem(
            category=ContentCategory.DAILY_REMINDER,
            arabic_text="هَذَا سِجِلِّ تَجْرِيبِيّ لَا يَجُوزُ نَشْرُهُ",
            english_meaning="This is a test demo record and must never be published to production Instagram.",
            source_id=src_demo.id,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
            is_demo=True,  # Critical demo flag
        )
        db.add(item_demo)

        db.commit()
        print("Database successfully seeded with authentic reminders and safety test demo record.")


if __name__ == "__main__":
    seed()
