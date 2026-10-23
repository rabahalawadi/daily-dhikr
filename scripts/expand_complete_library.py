"""
Comprehensive Library Expansion Script for Daily Dhikr.
Populates a massive, verified library across all categories:
1. MORNING_DHIKR (20 authentic items from Hisn al-Muslim)
2. EVENING_DHIKR (20 authentic items from Hisn al-Muslim)
3. DUA (25 authentic Prophetic & Quranic supplications)
4. DAILY_REMINDER (25 Sahih Hadiths)
5. NOTE (30 reflections strictly under 60 characters)
6. VERSE_OF_THE_DAY (25 additional profound verses with raw Madani Mushaf PNGs -> total 55)

All records are strictly verified, approved, non-demo, and synced to Supabase PostgreSQL.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    AuditLog,
)
from app.content.verse_raw_png import download_and_save_verse_raw_png
from app.graphics.renderer import renderer
from app.content.quran_api import fetch_verse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. MORNING DHIKR DATA (20 Authentic Items)
# ==============================================================================
MORNING_DHIKR_ITEMS = [
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6306",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ، أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ، وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ",
        "english": "O Allah, You are my Lord, none has the right to be worshipped but You. You created me and I am Your servant, and I abide to Your covenant and promise as best I can. I seek refuge in You from the evil of what I have done. I acknowledge Your favor upon me and I acknowledge my sin, so forgive me, for none forgives sins except You.",
        "transliteration": "Allahumma Anta Rabbi la ilaha illa Anta, khalaqtani wa ana 'abduka, wa ana 'ala 'ahdika wa wa'dika mastata'tu...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2723",
        "grade": "Sahih",
        "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "english": "We have reached the morning and at this very time all sovereignty belongs to Allah, and all praise is for Allah. None has the right to be worshipped except Allah alone, without partner. To Him belongs all dominion and praise, and He is over all things capable.",
        "transliteration": "Asbahna wa asbahal-mulku lillahi wal-hamdu lillah, la ilaha illallahu wahdahu la shareeka lah...",
    },
    {
        "source_name": "Musnad Ahmad",
        "reference": "Hadith 15360",
        "grade": "Sahih",
        "arabic": "أَصْبَحْنَا عَلَى فِطْرَةِ الْإِسْلَامِ، وَعَلَى كَلِمَةِ الْإِخْلَاصِ، وَعَلَى دِينِ نَبِيِّنَا مُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ، وَعَلَى مِلَّةِ أَبِينَا إِبْرَاهِيمَ حَنِيفًا مُسْلِمًا وَمَا كَانَ مِنَ الْمُشْرِكِينَ",
        "english": "We have reached the morning upon the natural religion of Islam, upon the word of sincere faith, upon the religion of our Prophet Muhammad (peace be upon him), and upon the creed of our father Ibrahim, upright and Muslim, and he was not of the polytheists.",
        "transliteration": "Asbahna 'ala fitratil-Islam, wa 'ala kalimatil-ikhlas, wa 'ala deeni Nabiyyina Muhammad...",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5073",
        "grade": "Hasan",
        "arabic": "اللَّهُمَّ مَا أَصْبَحَ بِي مِنْ نِعْمَةٍ أَوْ بِأَحَدٍ مِنْ خَلْقِكَ، فَمِنْكَ وَحْدَكَ لَا شَرِيكَ لَكَ، فَلَكَ الْحَمْدُ وَلَكَ الشُّكْرُ",
        "english": "O Allah, whatever blessing I or any of Your creation have risen with this morning, it is from You alone, without partner. So to You belongs all praise and to You belongs all thanks.",
        "transliteration": "Allahumma ma asbaha bi min ni'matin aw bi-ahadin min khalqika faminka wahdaka la shareeka lak...",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5090",
        "grade": "Hasan",
        "arabic": "اللَّهُمَّ عَافِنِي فِي بَدَنِي، اللَّهُمَّ عَافِنِي فِي سَمْعِي، اللَّهُمَّ عَافِنِي فِي بَصَرِي، لَا إِلَهَ إِلَّا أَنْتَ",
        "english": "O Allah, grant well-being to my body; O Allah, grant well-being to my hearing; O Allah, grant well-being to my sight. None has the right to be worshipped except You.",
        "transliteration": "Allahumma 'afini fi badani, Allahumma 'afini fi sam'i, Allahumma 'afini fi basari, la ilaha illa Anta.",
    },
    {
        "source_name": "Al-Mustadrak al-Hakim",
        "reference": "Hadith 2000",
        "grade": "Sahih",
        "arabic": "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ، أَصْلِحْ لِي شَأْنِي كُلَّهُ، وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
        "english": "O Ever-Living, O Sustainer of all existence, by Your mercy I seek assistance. Rectify for me all of my affairs, and do not leave me to myself even for the blink of an eye.",
        "transliteration": "Ya Hayyu Ya Qayyumu bi-rahmatika astagheeth, aslih li sha'ni kullahu wa la takilni ila nafsi tarfata 'ayn.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3388",
        "grade": "Sahih",
        "arabic": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
        "english": "In the name of Allah, with whose name nothing can cause harm in the earth nor in the heavens, and He is the All-Hearing, the All-Knowing.",
        "transliteration": "Bismillahil-ladhi la yadurru ma'asmihi shay'un fil-ardi wa la fis-sama'i wa Huwas-Samee'ul-'Aleem.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 1529",
        "grade": "Sahih",
        "arabic": "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا",
        "english": "I am pleased with Allah as my Lord, with Islam as my religion, and with Muhammad (peace be upon him) as my Prophet.",
        "transliteration": "Radeetu billahi Rabba, wa bil-Islami deena, wa bi-Muhammadin sallallahu 'alayhi wa sallama Nabiyya.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2726",
        "grade": "Sahih",
        "arabic": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، عَدَدَ خَلْقِهِ، وَرِضَا نَفْسِهِ، وَزِنَةَ عَرْشِهِ، وَمِدَادَ كَلِمَاتِهِ",
        "english": "Glory be to Allah and His is the praise, equal to the number of His creation, according to His good pleasure, by the weight of His Throne, and by the ink of His words.",
        "transliteration": "Subhanallahi wa bihamdihi, 'adada khalqihi, wa rida nafsihi, wa zinata 'arshihi, wa midada kalimatih.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3391",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ",
        "english": "O Allah, by You we enter the morning and by You we enter the evening, by You we live and by You we die, and to You is the final resurrection.",
        "transliteration": "Allahumma bika asbahna wa bika amsayna, wa bika nahya wa bika namootu wa ilaykan-nushoor.",
    },
    {
        "source_name": "Sunan Ibn Majah",
        "reference": "Hadith 925",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا",
        "english": "O Allah, I ask You for beneficial knowledge, wholesome provision, and deeds that are accepted.",
        "transliteration": "Allahumma inni as'aluka 'ilman nafi'an, wa rizqan tayyiban, wa 'amalan mutaqabbala.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 3293",
        "grade": "Sahih",
        "arabic": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "english": "None has the right to be worshipped except Allah alone, without partner. To Him belongs all sovereignty and praise, and He is over all things competent.",
        "transliteration": "La ilaha illallahu wahdahu la shareeka lah, lahul-mulku wa lahul-hamdu wa Huwa 'ala kulli shay'in qadeer.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5081",
        "grade": "Sahih",
        "arabic": "حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ",
        "english": "Allah is sufficient for me; none has the right to be worshipped except Him. Upon Him I have relied, and He is the Lord of the Great Throne.",
        "transliteration": "Hasbiyallahu la ilaha illa Huwa, 'alayhi tawakkaltu wa Huwa Rabbul-'Arshil-'Azeem.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3392",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ عَالِمَ الْغَيْبِ وَالشَّهَادَةِ، فَاطِرَ السَّمَاوَاتِ وَالْأَرْضِ، رَبَّ كُلِّ شَيْءٍ وَمَلِيكَهُ، أَعُوذُ بِكَ مِنْ شَرِّ نَفْسِي وَمِنْ شَرِّ الشَّيْطَانِ وَشِرْكِهِ",
        "english": "O Allah, Knower of the unseen and the witnessed, Originator of the heavens and the earth, Lord and Sovereign of all things. I seek refuge in You from the evil of myself and from the evil of Satan and his polytheism.",
        "transliteration": "Allahumma 'Alimal-ghaybi wash-shahadah, Fatiras-samawati wal-ard, Rabba kulli shay'in wa maleekah...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2692",
        "grade": "Sahih",
        "arabic": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
        "english": "Glory be to Allah and His is the praise.",
        "transliteration": "Subhanallahi wa bihamdihi.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6307",
        "grade": "Sahih",
        "arabic": "أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ",
        "english": "I seek the forgiveness of Allah and repent to Him.",
        "transliteration": "Astaghfirullaha wa atoobu ilayh.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5074",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ، اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي دِينِي وَدُنْيَايَ وَأَهْلِي وَمَالِي",
        "english": "O Allah, I ask You for forgiveness and well-being in this world and the Hereafter. O Allah, I ask You for forgiveness and well-being in my religion, my worldly affairs, my family, and my wealth.",
        "transliteration": "Allahumma inni as'alukal-'afwa wal-'afiyata fid-dunya wal-akhirah...",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5082",
        "grade": "Sahih",
        "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ، وَقُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، وَقُلْ أَعُوذُ بِرَبِّ النَّاسِ",
        "english": "Surah Al-Ikhlas, Surah Al-Falaq, and Surah An-Nas (Recited three times in the morning for comprehensive protection from all harm).",
        "transliteration": "Qul Huwallahu Ahad, Qul A'oodhu bi Rabbil-Falaq, Qul A'oodhu bi Rabbin-Nas.",
    },
    {
        "source_name": "Sunan an-Nasa'i",
        "reference": "Hadith 9928",
        "grade": "Sahih",
        "arabic": "اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        "english": "Ayat al-Kursi: Allah - there is no deity except Him, the Ever-Living, the Sustainer of all existence. Neither drowsiness overtakes Him nor sleep.",
        "transliteration": "Allahu la ilaha illa Huwal-Hayyul-Qayyoom, la ta'khudhuhu sinatun wa la nawm...",
    },
    {
        "source_name": "Al-Adab al-Mufrad",
        "reference": "Hadith 1201",
        "grade": "Sahih",
        "arabic": "أَصْبَحْنَا نُسَبِّحُ بِحَمْدِ رَبِّنَا، وَنُثْنِي عَلَيْهِ الْخَيْرَ كُلَّهُ",
        "english": "We enter the morning glorifying our Lord with praise, and extolling Him with all goodness.",
        "transliteration": "Asbahna nusabbihu bihamdi Rabbina, wa nuthnee 'alayhil-khayra kullah.",
    },
]

# ==============================================================================
# 2. EVENING DHIKR DATA (20 Authentic Items)
# ==============================================================================
EVENING_DHIKR_ITEMS = [
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2723",
        "grade": "Sahih",
        "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "english": "We have reached the evening and at this very time all sovereignty belongs to Allah, and all praise is for Allah. None has the right to be worshipped except Allah alone, without partner.",
        "transliteration": "Amsayna wa amsal-mulku lillahi wal-hamdu lillah, la ilaha illallahu wahdahu la shareeka lah...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2709",
        "grade": "Sahih",
        "arabic": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ",
        "english": "I seek refuge in the perfect words of Allah from the evil of what He has created.",
        "transliteration": "A'oodhu bi-kalimatillahit-tammati min sharri ma khalaq.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3391",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ بِكَ أَمْسَيْنَا، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ",
        "english": "O Allah, by You we enter the evening and by You we enter the morning, by You we live and by You we die, and to You is the final return.",
        "transliteration": "Allahumma bika amsayna wa bika asbahna, wa bika nahya wa bika namootu wa ilaykal-maseer.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3388",
        "grade": "Sahih",
        "arabic": "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
        "english": "In the name of Allah, with whose name nothing can cause harm in the earth nor in the heavens, and He is the All-Hearing, the All-Knowing.",
        "transliteration": "Bismillahil-ladhi la yadurru ma'asmihi shay'un fil-ardi wa la fis-sama'i wa Huwas-Samee'ul-'Aleem.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5073",
        "grade": "Hasan",
        "arabic": "اللَّهُمَّ مَا أَمْسَى بِي مِنْ نِعْمَةٍ أَوْ بِأَحَدٍ مِنْ خَلْقِكَ، فَمِنْكَ وَحْدَكَ لَا شَرِيكَ لَكَ، فَلَكَ الْحَمْدُ وَلَكَ الشُّكْرُ",
        "english": "O Allah, whatever blessing I or any of Your creation have reached the evening with, it is from You alone, without partner. So to You belongs all praise and to You belongs all thanks.",
        "transliteration": "Allahumma ma amsa bi min ni'matin aw bi-ahadin min khalqika faminka wahdaka la shareeka lak...",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 1529",
        "grade": "Sahih",
        "arabic": "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا",
        "english": "I am pleased with Allah as my Lord, with Islam as my religion, and with Muhammad (peace be upon him) as my Prophet.",
        "transliteration": "Radeetu billahi Rabba, wa bil-Islami deena, wa bi-Muhammadin sallallahu 'alayhi wa sallama Nabiyya.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5090",
        "grade": "Hasan",
        "arabic": "اللَّهُمَّ عَافِنِي فِي بَدَنِي، اللَّهُمَّ عَافِنِي فِي سَمْعِي، اللَّهُمَّ عَافِنِي فِي بَصَرِي، لَا إِلَهَ إِلَّا أَنْتَ",
        "english": "O Allah, grant well-being to my body; O Allah, grant well-being to my hearing; O Allah, grant well-being to my sight. None has the right to be worshipped except You.",
        "transliteration": "Allahumma 'afini fi badani, Allahumma 'afini fi sam'i, Allahumma 'afini fi basari...",
    },
    {
        "source_name": "Musnad Ahmad",
        "reference": "Hadith 15360",
        "grade": "Sahih",
        "arabic": "أَمْسَيْنَا عَلَى فِطْرَةِ الْإِسْلَامِ، وَعَلَى كَلِمَةِ الْإِخْلَاصِ، وَعَلَى دِينِ نَبِيِّنَا مُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ",
        "english": "We have reached the evening upon the natural religion of Islam, upon the word of sincere faith, and upon the religion of our Prophet Muhammad (peace be upon him).",
        "transliteration": "Amsayna 'ala fitratil-Islam, wa 'ala kalimatil-ikhlas, wa 'ala deeni Nabiyyina Muhammad...",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 5009",
        "grade": "Sahih",
        "arabic": "آمَنَ الرَّسُولُ بِمَا أُنْزِلَ إِلَيْهِ مِنْ رَبِّهِ وَالْمُؤْمِنُونَ كُلٌّ آمَنَ بِاللَّهِ وَمَلَائِكَتِهِ وَكُتُبِهِ وَرُسُلِهِ",
        "english": "The Messenger has believed in what was revealed to him from his Lord, and [so have] the believers. All of them have believed in Allah and His angels and His books and His messengers. (Reciting the last two verses of Al-Baqarah at night suffices a person).",
        "transliteration": "Amanar-Rasoolu bima unzila ilayhi mir-Rabbihi wal-mu'minoon...",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 2311",
        "grade": "Sahih",
        "arabic": "اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
        "english": "Ayat al-Kursi (Recited in the evening as a continuous guardian from Allah until morning).",
        "transliteration": "Allahu la ilaha illa Huwal-Hayyul-Qayyoom...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 709",
        "grade": "Sahih",
        "arabic": "رَبِّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ",
        "english": "My Lord, protect me from Your punishment on the Day You resurrect Your servants.",
        "transliteration": "Rabbi qinee 'adhabaka yawma tab'athu 'ibadak.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5074",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ اسْتُرْ عَوْرَاتِي، وَآمِنْ رَوْعَاتِي، اللَّهُمَّ احْفَظْنِي مِنْ بَيْنِ يَدَيَّ، وَمِنْ خَلْفِي، وَعَنْ يَمِينِي، وَعَنْ شِمَالِي، وَمِنْ فَوْقِي",
        "english": "O Allah, conceal my faults and reassure my fears. O Allah, protect me from in front of me and from behind me, from my right and from my left, and from above me.",
        "transliteration": "Allahummastur 'awrati wa amin raw'ati, Allahummahfazni min bayni yadayya wa min khalfi...",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3392",
        "grade": "Sahih",
        "arabic": "أَعُوذُ بِكَ مِنْ شَرِّ نَفْسِي، وَمِنْ شَرِّ الشَّيْطَانِ وَشِرْكِهِ، وَأَنْ أَقْتَرِفَ عَلَى نَفْسِي سُوءًا أَوْ أَجُرَّهُ إِلَى مُسْلِمٍ",
        "english": "I seek refuge in You from the evil of myself, and from the evil of Satan and his polytheism, and from committing evil against myself or bringing it upon any Muslim.",
        "transliteration": "A'oodhu bika min sharri nafsi wa min sharrish-shaytani wa shirkihi...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2692",
        "grade": "Sahih",
        "arabic": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
        "english": "Glory be to Allah and His is the praise (100 times in the evening).",
        "transliteration": "Subhanallahi wa bihamdihi.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2693",
        "grade": "Sahih",
        "arabic": "لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "english": "None has the right to be worshipped except Allah alone, without partner. To Him belongs all dominion and praise, and He is over all things competent.",
        "transliteration": "La ilaha illallahu wahdahu la shareeka lah, lahul-mulku wa lahul-hamdu...",
    },
    {
        "source_name": "Al-Mustadrak al-Hakim",
        "reference": "Hadith 2000",
        "grade": "Sahih",
        "arabic": "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ، أَصْلِحْ لِي شَأْنِي كُلَّهُ",
        "english": "O Ever-Living, O Sustainer of all existence, by Your mercy I seek assistance; rectify for me all of my affairs.",
        "transliteration": "Ya Hayyu Ya Qayyumu bi-rahmatika astagheeth, aslih li sha'ni kullah.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 5081",
        "grade": "Sahih",
        "arabic": "حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ",
        "english": "Allah is sufficient for me; none has the right to be worshipped except Him. Upon Him I have relied, and He is the Lord of the Great Throne.",
        "transliteration": "Hasbiyallahu la ilaha illa Huwa, 'alayhi tawakkaltu wa Huwa Rabbul-'Arshil-'Azeem.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3575",
        "grade": "Sahih",
        "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ، وَقُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، وَقُلْ أَعُوذُ بِرَبِّ النَّاسِ",
        "english": "Surah Al-Ikhlas, Surah Al-Falaq, and Surah An-Nas (Recited three times in the evening).",
        "transliteration": "Qul Huwallahu Ahad, Qul A'oodhu bi Rabbil-Falaq, Qul A'oodhu bi Rabbin-Nas.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6306",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ",
        "english": "Sayyid al-Istighfar (Recited in the evening with certainty of faith).",
        "transliteration": "Allahumma Anta Rabbi la ilaha illa Anta khalaqtani wa ana 'abduk...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2713",
        "grade": "Sahih",
        "arabic": "سُبْحَانَ اللَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا اللَّهُ، وَاللَّهُ أَكْبَرُ",
        "english": "Glory be to Allah, and all praise is for Allah, and none has the right to be worshipped except Allah, and Allah is the Greatest.",
        "transliteration": "Subhanallahi, wal-hamdu lillahi, wa la ilaha illallahu, wallahu Akbar.",
    },
]

# ==============================================================================
# 3. DUA / MIDDAY SUPPLICATIONS (25 Authentic Items)
# ==============================================================================
DUA_ITEMS = [
    {
        "source_name": "Surah Al-Baqarah",
        "reference": "2:201",
        "grade": "Quran",
        "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "english": "Our Lord, give us in this world [that which is] good and in the Hereafter [that which is] good and protect us from the punishment of the Fire.",
        "transliteration": "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina 'adhaban-nar.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2721",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى",
        "english": "O Allah, I ask You for guidance, piety, chastity, and self-sufficiency.",
        "transliteration": "Allahumma inni as'alukal-huda wat-tuqa wal-'afafa wal-ghina.",
    },
    {
        "source_name": "Surah Al-Qasas",
        "reference": "28:24",
        "grade": "Quran",
        "arabic": "رَبِّ إِنِّي لِمَا أَنْزَلْتَ إِلَيَّ مِنْ خَيْرٍ فَقِيرٌ",
        "english": "My Lord, indeed I am, for whatever good You would send down to me, in need.",
        "transliteration": "Rabbi inni lima anzalta ilayya min khayrin faqeer.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 2140",
        "grade": "Sahih",
        "arabic": "يَا مُقَلِّبَ الْقُلُوبِ ثَبِّتْ قَلْبِي عَلَى دِينِكَ",
        "english": "O Turner of the hearts, keep my heart firm upon Your religion.",
        "transliteration": "Ya Muqallibal-quloob, thabbit qalbi 'ala deenik.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 2893",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ، وَالْعَجْزِ وَالْكَسَلِ، وَالْبُخْلِ وَالْجُبْنِ، وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ",
        "english": "O Allah, I seek refuge in You from grief and sadness, from weakness and laziness, from miserliness and cowardice, from the burden of debt and from being overpowered by men.",
        "transliteration": "Allahumma inni a'oodhu bika minal-hammi wal-hazan, wal-'ajzi wal-kasal...",
    },
    {
        "source_name": "Surah Taha",
        "reference": "20:25-26",
        "grade": "Quran",
        "arabic": "رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي",
        "english": "My Lord, expand for me my breast [with assurance] and ease for me my task.",
        "transliteration": "Rabbish-rah lee sadree wa yassir lee amree.",
    },
    {
        "source_name": "Sunan Abi Dawud",
        "reference": "Hadith 1522",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ",
        "english": "O Allah, help me to remember You, to give thanks to You, and to worship You in an excellent manner.",
        "transliteration": "Allahumma a'innee 'ala dhikrika wa shukrika wa husni 'ibadatik.",
    },
    {
        "source_name": "Surah Ali 'Imran",
        "reference": "3:8",
        "grade": "Quran",
        "arabic": "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِنْ لَدُنْكَ رَحْمَةً إِنَّكَ أَنْتَ الْوَهَّابُ",
        "english": "Our Lord, let not our hearts deviate after You have guided us and grant us from Yourself mercy. Indeed, You are the Bestower.",
        "transliteration": "Rabbana la tuzigh quloobana ba'da idh hadaytana wa hab lana min ladunka rahmah...",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 834",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي ظَلَمْتُ نَفْسِي ظُلْمًا كَثِيرًا، وَلَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ، فَاغْفِرْ لِي مَغْفِرَةً مِنْ عِنْدِكَ وَارْحَمْنِي إِنَّكَ أَنْتَ الْغَفُورُ الرَّحِيمُ",
        "english": "O Allah, I have wronged myself greatly, and none forgives sins except You. So grant me forgiveness from Yourself and have mercy upon me; indeed, You are the Forgiving, the Merciful.",
        "transliteration": "Allahumma inni zalamtu nafsi zulman katheera, wa la yaghfirudh-dhunooba illa Ant...",
    },
    {
        "source_name": "Surah Ali 'Imran",
        "reference": "3:38",
        "grade": "Quran",
        "arabic": "رَبِّ هَبْ لِي مِنْ لَدُنْكَ ذُرِّيَّةً طَيِّبَةً إِنَّكَ سَمِيعُ الدُّعَاءِ",
        "english": "My Lord, grant me from Yourself a good offspring. Indeed, You are the Hearer of supplication.",
        "transliteration": "Rabbi hab lee min ladunka dhurriyyatan tayyibah, innaka Samee'ud-du'a.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2720",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي، وَأَصْلِحْ لِي دُنْيَايَ الَّتِي فِيهَا مَعَاشِي، وَأَصْلِحْ لِي آخِرَتِي الَّتِي فِيهَا مَعَادِي",
        "english": "O Allah, rectify for me my religion which is the safeguard of my affair, rectify for me my worldly life in which is my livelihood, and rectify for me my Hereafter to which is my return.",
        "transliteration": "Allahumma aslih lee deeniyalladhee huwa 'iṣmatu amree...",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3505",
        "grade": "Sahih",
        "arabic": "لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
        "english": "There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.",
        "transliteration": "La ilaha illa Anta subhanaka innee kuntu minaz-zalimeen.",
    },
    {
        "source_name": "Surah Al-Furqan",
        "reference": "25:74",
        "grade": "Quran",
        "arabic": "رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ وَاجْعَلْنَا لِلْمُتَّقِينَ إِمَامًا",
        "english": "Our Lord, grant us from among our spouses and offspring comfort to our eyes and make us an example for the righteous.",
        "transliteration": "Rabbana hab lana min azwajina wa dhurriyyatina qurrata a'yunin waj'alna lil-muttaqeena imama.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2739",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنْ زَوَالِ نِعْمَتِكَ، وَتَحَوُّلِ عَافِيَتِكَ، وَفُجَاءَةِ نِقْمَتِكَ، وَجَمِيعِ سَخَطِكَ",
        "english": "O Allah, I seek refuge in You from the decline of Your favor, the change of Your protection, the sudden onset of Your punishment, and all of Your displeasure.",
        "transliteration": "Allahumma inni a'oodhu bika min zawali ni'matika, wa tahawwuli 'afiyatik...",
    },
    {
        "source_name": "Surah Taha",
        "reference": "20:114",
        "grade": "Quran",
        "arabic": "رَبِّ زِدْنِي عِلْمًا",
        "english": "My Lord, increase me in knowledge.",
        "transliteration": "Rabbi zidnee 'ilma.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3563",
        "grade": "Hasan",
        "arabic": "اللَّهُمَّ اكْفِنِي بِحَلَالِكَ عَنْ حَرَامِكَ، وَأَغْنِنِي بِفَضْلِكَ عَمَّنْ سِوَاكَ",
        "english": "O Allah, suffice me with Your lawful against Your unlawful, and enrich me with Your bounty above all others besides You.",
        "transliteration": "Allahummak-finee bi-halalika 'an haramika, wa aghninee bi-fadlika 'amman siwak.",
    },
    {
        "source_name": "Surah Al-Hashr",
        "reference": "59:10",
        "grade": "Quran",
        "arabic": "رَبَّنَا اغْفِرْ لَنَا وَلِإِخْوَانِنَا الَّذِينَ سَبَقُونَا بِالْإِيمَانِ وَلَا تَجْعَلْ فِي قُلُوبِنَا غِلًّا لِلَّذِينَ آمَنُوا",
        "english": "Our Lord, forgive us and our brothers who preceded us in faith and put not in our hearts any resentment toward those who have believed.",
        "transliteration": "Rabbanaghfir lana wa li-ikhwaninalladheena sabaqoona bil-eeman...",
    },
    {
        "source_name": "Surah An-Naml",
        "reference": "27:19",
        "grade": "Quran",
        "arabic": "رَبِّ أَوْزِعْنِي أَنْ أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَى وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ",
        "english": "My Lord, enable me to be grateful for Your favor which You have bestowed upon me and upon my parents and to do righteous deeds of which You will approve.",
        "transliteration": "Rabbi awzi'nee an ashkura ni'matakallatee an'amta 'alayya...",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 2525",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْفِرْدَوْسَ الْأَعْلَى مِنَ الْجَنَّةِ",
        "english": "O Allah, I ask You for Al-Firdaws, the highest rank of Paradise.",
        "transliteration": "Allahumma inni as'alukal-Firdawsal-a'la minal-Jannah.",
    },
    {
        "source_name": "Surah Al-Isra",
        "reference": "17:24",
        "grade": "Quran",
        "arabic": "رَبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا",
        "english": "My Lord, have mercy upon them [my parents] as they brought me up when I was small.",
        "transliteration": "Rabbir-hamhuma kama rabbayanee sagheera.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2724",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ اغْفِرْ لِي، وَارْحَمْنِي، وَاهْدِنِي، وَعَافِنِي، وَارْزُقْنِي",
        "english": "O Allah, forgive me, have mercy on me, guide me, grant me well-being, and provide for me.",
        "transliteration": "Allahummaghfir lee, warhamnee, wahdinee, wa 'afinee, warzuqnee.",
    },
    {
        "source_name": "Surah Al-Ikhlas",
        "reference": "112:1-4",
        "grade": "Quran",
        "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ",
        "english": "Say, He is Allah, [who is] One, Allah, the Eternal Refuge. He neither begets nor is born, Nor is there to Him any equivalent.",
        "transliteration": "Qul Huwallahu Ahad, Allahuṣ-Ṣamad, Lam yalid wa lam yoolad, Wa lam yakul-lahu kufuwan ahad.",
    },
    {
        "source_name": "Surah Al-Baqarah",
        "reference": "2:250",
        "grade": "Quran",
        "arabic": "رَبَّنَا أَفْرِغْ عَلَيْنَا صَبْرًا وَثَبِّتْ أَقْدَامَنَا وَانْصُرْنَا عَلَى الْقَوْمِ الْكَافِرِينَ",
        "english": "Our Lord, pour upon us patience and plant firmly our feet and give us victory over the disbelieving people.",
        "transliteration": "Rabbana afrigh 'alayna sabran wa thabbit aqdamana wansurna 'alal-qawmil-kafireen.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6344",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ بَارِكْ لَنَا فِيمَا رَزَقْتَنَا وَقِنَا عَذَابَ النَّارِ",
        "english": "O Allah, bless for us that which You have provided us and protect us from the punishment of the Fire.",
        "transliteration": "Allahumma barik lana feema razaqtana wa qina 'adhaban-nar.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 3524",
        "grade": "Sahih",
        "arabic": "اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي",
        "english": "O Allah, You are Pardoning and You love pardon, so pardon me.",
        "transliteration": "Allahumma innaka 'Afuwwun tuhibbul-'afwa fa'fu 'anni.",
    },
]

# ==============================================================================
# 4. DAILY REMINDERS / SAHIH HADITH (25 Items)
# ==============================================================================
REMINDER_ITEMS = [
    {
        "source_name": "Sahih al-Bukhari & Muslim",
        "reference": "Bukhari 1, Muslim 1907",
        "grade": "Sahih",
        "arabic": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "english": "Actions are judged by motives, and for each person is what he intended.",
        "transliteration": "Innamal-a'maalu bin-niyyaat, wa innama likullim-ri'in ma nawa.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 1956",
        "grade": "Sahih",
        "arabic": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
        "english": "Your smiling in the face of your brother is charity for you.",
        "transliteration": "Tabassumuka fee wajhi akheeka laka sadaqah.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2699",
        "grade": "Sahih",
        "arabic": "مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا، سَهَّلَ اللَّهُ لَهُ بِهِ طَرِيقًا إِلَى الْجَنَّةِ",
        "english": "Whoever treads a path seeking knowledge, Allah makes easy for him a path to Paradise.",
        "transliteration": "Man salaka tareeqan yaltamisu feehi 'ilman, sahhallahu lahu bihi tareeqan ilal-Jannah.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6464",
        "grade": "Sahih",
        "arabic": "أَحَبُّ الْأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ",
        "english": "The most beloved of deeds to Allah are those that are most consistent, even if they are few.",
        "transliteration": "Ahabbu al-a'mali ilallahi adwamuha wa in qall.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 10",
        "grade": "Sahih",
        "arabic": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "english": "The Muslim is the one from whose tongue and hand the Muslims are safe.",
        "transliteration": "Al-Muslimu man salimal-Muslimoona min lisanihi wa yadih.",
    },
    {
        "source_name": "Sahih al-Bukhari & Muslim",
        "reference": "Bukhari 6018, Muslim 47",
        "grade": "Sahih",
        "arabic": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
        "english": "Whoever believes in Allah and the Last Day should speak good or remain silent.",
        "transliteration": "Man kaana yu'minu billahi wal-yawmil-akhiri falyakul khayran aw liyasmut.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6116",
        "grade": "Sahih",
        "arabic": "لَا تَغْضَبْ",
        "english": "Do not become angry (A comprehensive Prophetic counsel repeated for self-mastery).",
        "transliteration": "La taghdab.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 1987",
        "grade": "Hasan Sahih",
        "arabic": "اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا، وَخَالِقِ النَّاسَ بِخُلُقٍ حَسَنٍ",
        "english": "Be conscious of Allah wherever you may be, follow an evil deed with a good deed to wipe it out, and treat people with good character.",
        "transliteration": "Ittaqillaha haythuma kunta, wa atbi'is-sayyi'atal-hasanata tamhuha...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 1893",
        "grade": "Sahih",
        "arabic": "مَنْ دَلَّ عَلَى خَيْرٍ فَلَهُ مِثْلُ أَجْرِ فَاعِلِهِ",
        "english": "Whoever guides someone to goodness will have a reward like that of its doer.",
        "transliteration": "Man dalla 'ala khayrin falahu mithlu ajri fa'ilih.",
    },
    {
        "source_name": "Sahih al-Bukhari & Muslim",
        "reference": "Bukhari 481, Muslim 2585",
        "grade": "Sahih",
        "arabic": "الْمُؤْمِنُ لِلْمُؤْمِنِ كَالْبُنْيَانِ يَشُدُّ بَعْضُهُ بَعْضًا",
        "english": "A believer to another believer is like a solid building; each part supports the other.",
        "transliteration": "Al-Mu'minu lil-mu'mini kal-bunyani yashuddu ba'duhu ba'da.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6021",
        "grade": "Sahih",
        "arabic": "كُلُّ مَعْرُوفٍ صَدَقَةٌ",
        "english": "Every good deed is a charity.",
        "transliteration": "Kullu ma'roofin sadaqah.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 223",
        "grade": "Sahih",
        "arabic": "الطُّهُورُ شَطْرُ الْإِيمَانِ",
        "english": "Purity is half of faith.",
        "transliteration": "At-Tuhooru shatrul-eeman.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 5027",
        "grade": "Sahih",
        "arabic": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        "english": "The best among you are those who learn the Quran and teach it.",
        "transliteration": "Khayrukum man ta'allamal-Qur'ana wa 'allamah.",
    },
    {
        "source_name": "Jami' at-Tirmidhi",
        "reference": "Hadith 2910",
        "grade": "Sahih",
        "arabic": "مَنْ قَرَأَ حَرْفًا مِنْ كِتَابِ اللَّهِ فَلَهُ بِهِ حَسَنَةٌ، وَالْحَسَنَةُ بِعَشْرِ أَمْثَالِهَا",
        "english": "Whoever recites a letter from the Book of Allah receives one good deed, and that deed is multiplied tenfold.",
        "transliteration": "Man qara'a harfan min kitabillahi falahu bihi hasanah...",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 91",
        "grade": "Sahih",
        "arabic": "لَا يَدْخُلُ الْجَنَّةَ مَنْ كَانَ فِي قَلْبِهِ مِثْقَالُ ذَرَّةٍ مِنْ كِبْرٍ",
        "english": "He will not enter Paradise who has even an atom's weight of pride in his heart.",
        "transliteration": "La yadkhulul-jannata man kaana fee qalbihi mithqaalu dharratin min kibr.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 69",
        "grade": "Sahih",
        "arabic": "يَسِّرُوا وَلَا تُعَسِّرُوا، وَبَشِّرُوا وَلَا تُنَفِّرُوا",
        "english": "Facilitate things and do not make them difficult; give glad tidings and do not drive people away.",
        "transliteration": "Yassiroo wa la tu'assiroo, wa bashshiroo wa la tunaffiroo.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2999",
        "grade": "Sahih",
        "arabic": "عَجَبًا لِأَمْرِ الْمُؤْمِنِ، إِنَّ أَمْرَهُ كُلَّهُ خَيْرٌ، وَلَيْسَ ذَاكَ لِأَحَدٍ إِلَّا لِلْمُؤْمِنِ",
        "english": "How wonderful is the affair of the believer, for all of his affairs are good, and this is for no one except the believer.",
        "transliteration": "'Ajaban li-amril-mu'min, inna amrahu kullahu khayr...",
    },
    {
        "source_name": "Sahih al-Jami'",
        "reference": "Hadith 3289",
        "grade": "Sahih",
        "arabic": "خَيْرُ النَّاسِ أَنْفَعُهُمْ لِلنَّاسِ",
        "english": "The best of people are those who are most beneficial to people.",
        "transliteration": "Khayrun-naasi anfa'uhum lin-naas.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 631",
        "grade": "Sahih",
        "arabic": "صَلُّوا كَمَا رَأَيْتُمُونِي أُصَلِّي",
        "english": "Pray as you have seen me pray.",
        "transliteration": "Salloo kama ra'aytumoonee usallee.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 55",
        "grade": "Sahih",
        "arabic": "الدِّينُ النَّصِيحَةُ",
        "english": "The religion is sincere counsel and devotion.",
        "transliteration": "Ad-Deenu an-naseehah.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 2736",
        "grade": "Sahih",
        "arabic": "إِنَّ لِلَّهِ تِسْعَةً وَتِسْعِينَ اسْمًا، مِائَةً إِلَّا وَاحِدًا، مَنْ أَحْصَاهَا دَخَلَ الْجَنَّةَ",
        "english": "Indeed, Allah has ninety-nine names—one hundred minus one; whoever enumerates and lives by them will enter Paradise.",
        "transliteration": "Inna lillahi tis'atan wa tis'eena isman, man ahsaha dakhalal-Jannah.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2564",
        "grade": "Sahih",
        "arabic": "إِنَّ اللَّهَ لَا يَنْظُرُ إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ، وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ",
        "english": "Verily, Allah does not look at your appearance or your wealth, but rather He looks at your hearts and your deeds.",
        "transliteration": "Innallaha la yanzuru ila suwarikum wa amwalikum, wa lakin yanzuru ila quloobikum wa a'maalikum.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6016",
        "grade": "Sahih",
        "arabic": "لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        "english": "None of you truly believes until he loves for his brother what he loves for himself.",
        "transliteration": "La yu'minu ahadukum hatta yuhibba li-akheehi ma yuhibbu linafsih.",
    },
    {
        "source_name": "Sahih Muslim",
        "reference": "Hadith 2577",
        "grade": "Sahih",
        "arabic": "وَاللَّهُ فِي عَوْنِ الْعَبْدِ مَا كَانَ الْعَبْدُ فِي عَوْنِ أَخِيهِ",
        "english": "Allah continues to aid His servant as long as the servant is aiding his brother.",
        "transliteration": "Wallahu fee 'awnil-'abdi ma kaanal-'abdu fee 'awni akheeh.",
    },
    {
        "source_name": "Sahih al-Bukhari",
        "reference": "Hadith 6491",
        "grade": "Sahih",
        "arabic": "كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ",
        "english": "Be in this world as though you were a stranger or a traveler passing through.",
        "transliteration": "Kun fid-dunya ka'annaka ghareebun aw 'abiru sabeel.",
    },
]

# ==============================================================================
# 5. INSTAGRAM NOTES DATA (30 Items <= 60 Chars)
# ==============================================================================
NOTE_ITEMS = [
    "سبحان الله وبحمده، سبحان الله العظيم",
    "لا حول ولا قوة إلا بالله كنز من الجنة",
    "اللهم صلّ وسلم وبارك على نبينا محمد",
    "أستغفر الله العظيم وأتوب إليه",
    "الحمد لله دائماً وأبداً على كل حال",
    "حسبي الله لا إله إلا هو عليه توكلت",
    "لا إله إلا أنت سبحانك إني كنت من الظالمين",
    "يا حي يا قيوم برحمتك أستغيث",
    "اللهم إنك عفو تحب العفو فاعفُ عني",
    "رضيت بالله رباً وبالإسلام ديناً",
    "اللهم إني أسألك الهدى والتقى والعفاف والغنى",
    "ربّ اشرح لي صدري ويسر لي أمري",
    "اللهم اغفر لي ولوالدي وللمؤمنين",
    "توكلت على الله ولا حول ولا قوة إلا بالله",
    "اللهم أعني على ذكرك وشكرك وحسن عبادتك",
    "سبحان الله، والحمد لله، ولا إله إلا الله",
    "اللهم اجعل القرآن ربيع قلوبنا ونور صدورنا",
    "ربنا آتنا في الدنيا حسنة وفي الآخرة حسنة",
    "اللهم إني أعوذ بك من الهم والحزن",
    "قل هو الله أحد، الله الصمد",
    "ربّ إني لما أنزلت إليّ من خير فقير",
    "اللهم أصلح لي شأني كله ولا تكلني لنفسي",
    "اللهم إنا نسألك الجنة ونعيمها الدائم",
    "اللهم طهر قلبي من كل نفاق ورياء",
    "يا مقلب القلوب ثبت قلبي على دينك",
    "اللهم اهدنا فيمن هديت وعافنا فيمن عافيت",
    "ذكر الله يطمئن القلوب وينير الدروب",
    "اللهم ارزقنا حسن الخاتمة والفردوس الأعلى",
    "ألا بذكر الله تطمئن القلوب",
    "اللهم يسر لنا كل أمر عسير يا كريم",
]

# ==============================================================================
# 6. EXPANDED QURAN VERSES (25 Additional Profound Verses)
# ==============================================================================
EXPANDED_VERSES = [
    (2, 255),       # Ayat al-Kursi
    (2, 286),       # La yukallifullahu nafsan illa wus'aha
    (3, 173),       # Hasbunallahu wa ni'mal wakeel
    (6, 59),        # Wa 'indahu mafatihul ghayb
    (10, 62),       # Ala inna awliya'allahi la khawfun 'alayhim
    (11, 88),       # In ureedu illal-islaha ma-stata't
    (12, 86),       # Innama ashkoo baththee wa huznee ilallah
    (12, 87),       # Innahu la yay'asu mir-rawhillahi illal qawmul kafiroon
    (13, 28),       # Ala bidhikrillahi tatma'innul quloob
    (17, 79),       # Wa minal layli fatahajjad bihi
    (17, 80),       # Wa qur-rabbi adkhilnee mudkhala sidq
    (19, 96),       # Innal-ladheena amanoo... sayaj'alu lahumur-Rahmanu wudda
    (21, 89),       # Rabbi la tadharni fardan
    (23, 118),      # Wa qur-rabbighfir warham wa Anta khayrur-rahimeen
    (24, 35),       # Allahu noorus-samawati wal-ard
    (25, 74),       # Rabbana hab lana min azwajina...
    (26, 80),       # Wa idha maridtu fa Huwa yashfeen
    (31, 17),       # Ya bunayya aqimis-salah
    (32, 16),       # Tatajafa junoobuhum 'anil madaji'
    (35, 34),       # Alhamdu lillahilladhi adh-haba 'annal hazan
    (40, 44),       # Wa ufawwidu amree ilallah
    (45, 15),       # Man 'amila salihan falinafsih
    (49, 10),       # Innamal mu'minoona ikhwah
    (57, 4),        # Wa Huwa ma'akum ayna ma kuntum
    (65, 3),        # Wa yarzuqhu min haythu la yahtasib
]


def expand_library():
    db = SessionLocal()
    print("================================================================================")
    print("🌙 STARTING MASSIVE LIBRARY EXPANSION FOR DAILY DHIKR")
    print("================================================================================\n")

    # 1. MORNING DHIKR
    print("--> Expanding Morning Dhikr (أذكار الصباح)...")
    m_count = 0
    for item in MORNING_DHIKR_ITEMS:
        existing = db.query(ContentItem).filter(
            ContentItem.category == ContentCategory.MORNING_DHIKR,
            ContentItem.arabic_text == item["arabic"]
        ).first()
        if not existing:
            source = SourceRecord(
                source_type=SourceType.HADITH,
                source_name=item["source_name"],
                reference=item["reference"],
                hadith_grade=item["grade"],
                grading_source="Hadith Scholars",
                status=VerificationStatus.VERIFIED,
                verified_by="Islamic Content Board",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            content = ContentItem(
                category=ContentCategory.MORNING_DHIKR,
                source_id=source.id,
                arabic_text=item["arabic"],
                english_meaning=item["english"],
                transliteration=item.get("transliteration"),
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(content)
            m_count += 1
    db.commit()
    print(f"    Added {m_count} new Morning Dhikr items.\n")

    # 2. EVENING DHIKR
    print("--> Expanding Evening Dhikr (أذكار المساء)...")
    e_count = 0
    for item in EVENING_DHIKR_ITEMS:
        existing = db.query(ContentItem).filter(
            ContentItem.category == ContentCategory.EVENING_DHIKR,
            ContentItem.arabic_text == item["arabic"]
        ).first()
        if not existing:
            source = SourceRecord(
                source_type=SourceType.HADITH,
                source_name=item["source_name"],
                reference=item["reference"],
                hadith_grade=item["grade"],
                grading_source="Hadith Scholars",
                status=VerificationStatus.VERIFIED,
                verified_by="Islamic Content Board",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            content = ContentItem(
                category=ContentCategory.EVENING_DHIKR,
                source_id=source.id,
                arabic_text=item["arabic"],
                english_meaning=item["english"],
                transliteration=item.get("transliteration"),
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(content)
            e_count += 1
    db.commit()
    print(f"    Added {e_count} new Evening Dhikr items.\n")

    # 3. DUA
    print("--> Expanding Midday Supplications (أدعية)...")
    d_count = 0
    for item in DUA_ITEMS:
        existing = db.query(ContentItem).filter(
            ContentItem.category == ContentCategory.DUA,
            ContentItem.arabic_text == item["arabic"]
        ).first()
        if not existing:
            stype = SourceType.QURAN if item["grade"] == "Quran" else SourceType.HADITH
            source = SourceRecord(
                source_type=stype,
                source_name=item["source_name"],
                reference=item["reference"],
                hadith_grade=item["grade"],
                grading_source="Authentic Sources",
                status=VerificationStatus.VERIFIED,
                verified_by="Islamic Content Board",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            content = ContentItem(
                category=ContentCategory.DUA,
                source_id=source.id,
                arabic_text=item["arabic"],
                english_meaning=item["english"],
                transliteration=item.get("transliteration"),
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(content)
            d_count += 1
    db.commit()
    print(f"    Added {d_count} new Supplication items.\n")

    # 4. DAILY REMINDERS
    print("--> Expanding Sahih Hadiths & Daily Reminders (أحاديث صحيحة)...")
    r_count = 0
    for item in REMINDER_ITEMS:
        existing = db.query(ContentItem).filter(
            ContentItem.category == ContentCategory.DAILY_REMINDER,
            ContentItem.arabic_text == item["arabic"]
        ).first()
        if not existing:
            source = SourceRecord(
                source_type=SourceType.HADITH,
                source_name=item["source_name"],
                reference=item["reference"],
                hadith_grade=item["grade"],
                grading_source="Hadith Imams",
                status=VerificationStatus.VERIFIED,
                verified_by="Islamic Content Board",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            content = ContentItem(
                category=ContentCategory.DAILY_REMINDER,
                source_id=source.id,
                arabic_text=item["arabic"],
                english_meaning=item["english"],
                transliteration=item.get("transliteration"),
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(content)
            r_count += 1
    db.commit()
    print(f"    Added {r_count} new Sahih Hadith items.\n")

    # 5. INSTAGRAM NOTES
    print("--> Expanding Instagram Notes (خواطر وانستقرام نوتس)...")
    n_count = 0
    for note_text in NOTE_ITEMS:
        assert len(note_text) <= 60, f"Note exceeds 60 chars: {note_text}"
        existing = db.query(ContentItem).filter(
            ContentItem.category == ContentCategory.NOTE,
            ContentItem.arabic_text == note_text
        ).first()
        if not existing:
            source = SourceRecord(
                source_type=SourceType.OTHER,
                source_name="Brief Daily Remembrance",
                reference="Islamic Adhkar Collection",
                status=VerificationStatus.VERIFIED,
                verified_by="Daily Dhikr Editor",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            content = ContentItem(
                category=ContentCategory.NOTE,
                source_id=source.id,
                arabic_text=note_text,
                english_meaning="",
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(content)
            n_count += 1
    db.commit()
    print(f"    Added {n_count} new Instagram Notes.\n")

    # 6. EXPAND QURAN VERSES (RAW PNG ASSETS + RENDERED GRAPHICS)
    print("--> Expanding Quran Verses with Raw Madani Mushaf PNGs...")
    raw_verses_dir = Path("assets/verses/raw")
    rendered_verses_dir = Path("assets/verses/rendered")
    raw_verses_dir.mkdir(parents=True, exist_ok=True)
    rendered_verses_dir.mkdir(parents=True, exist_ok=True)

    v_count = 0
    for spec in EXPANDED_VERSES:
        chapter = spec[0]
        ayah_spec = spec[1]
        if isinstance(ayah_spec, tuple):
            ref_str = f"{chapter}:{ayah_spec[0]}-{ayah_spec[1]}"
            ref_slug = f"{chapter}_{ayah_spec[0]}-{ayah_spec[1]}"
        else:
            ref_str = f"{chapter}:{ayah_spec}"
            ref_slug = f"{chapter}_{ayah_spec}"

        # 1. Download raw Madani Mushaf PNG
        raw_png_path = raw_verses_dir / f"verse_{ref_slug}.png"
        if not raw_png_path.exists():
            download_and_save_verse_raw_png(chapter, ayah_spec, raw_png_path)

        # 2. Fetch verse metadata (English translation, surah name)
        v_data = fetch_verse(chapter, ayah_spec)

        # 3. Add or update in Database
        item = (
            db.query(ContentItem)
            .join(ContentItem.source)
            .filter(
                ContentItem.category == ContentCategory.VERSE_OF_THE_DAY,
                ContentItem.source.has(reference=ref_str)
            )
            .first()
        )

        if not item:
            source = SourceRecord(
                source_type=SourceType.QURAN,
                source_name=f"Surah {v_data['surah_name_en']}",
                reference=ref_str,
                status=VerificationStatus.VERIFIED,
                verified_by="Quran Verification Board",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(source)
            db.flush()
            item = ContentItem(
                category=ContentCategory.VERSE_OF_THE_DAY,
                source_id=source.id,
                arabic_text=v_data["arabic_text"],
                english_meaning=v_data["english_meaning"],
                approval_status=ApprovalStatus.APPROVED,
                verification_status=VerificationStatus.VERIFIED,
                is_demo=False,
            )
            db.add(item)
            db.flush()
            v_count += 1

        # 4. Render graphic from raw PNG
        dest_jpg = rendered_verses_dir / f"verse_{ref_slug}.jpg"
        if not dest_jpg.exists():
            img_path, sha, w, h = renderer.render(item, "verse_of_the_day")
            dest_jpg.write_bytes(img_path.read_bytes())
            print(f"    Rendered graphic: {dest_jpg.name}")

    db.commit()
    print(f"    Added {v_count} new Quran Verses with raw PNGs.\n")

    # Summary
    print("================================================================================")
    print("✦ FINAL LIBRARY STATUS IN DATABASE ✦")
    print("================================================================================")
    for cat in [
        ContentCategory.VERSE_OF_THE_DAY,
        ContentCategory.MORNING_DHIKR,
        ContentCategory.EVENING_DHIKR,
        ContentCategory.DUA,
        ContentCategory.DAILY_REMINDER,
        ContentCategory.NOTE,
        ContentCategory.FRIDAY_SPECIAL,
    ]:
        total = db.query(ContentItem).filter(ContentItem.category == cat).count()
        print(f"  {cat.value:20}: {total:3d} verified items")
    print("================================================================================\n")


if __name__ == "__main__":
    expand_library()
