from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.3\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.3"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 3, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 3, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.3')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.3')", s)
p.write_text(s, "utf-8")

# ---------- full requested fixture seed: 43 actual away trips ----------
seed = r'''"""Kullanıcının seçtiği gerçek deplasmanlar: 2022/23-2025/26.

2026/27 otomatik eklenmez. Özel organizasyonlar kullanıcı tarafından elle eklenir.
Mevcut kayıtlar bulunduğunda seyahat saatleri/ulaşım/notlar korunur; yalnız eski genel
organizasyon adı güvenli biçimde tamamlanabilir.
"""
from __future__ import annotations

SEED_KEY = "requested_match_seed_20261002_full_v3"

SEASON_BOUNDS = {
    "2022/23": ("2022-07-01", "2023-06-30"),
    "2023/24": ("2023-07-01", "2024-06-30"),
    "2024/25": ("2024-07-01", "2025-06-30"),
    "2025/26": ("2025-07-01", "2026-06-30"),
}

MATCHES = [
    # 2022/23 U17 — Türkiye (Bursaspor ve Hatayspor kullanıcı talebiyle YOK)
    {"date":"2022-10-26","season":"2022/23","team":"U17","city":"Trabzon","country":"Türkiye","opponent":"Trabzonspor","competition":"Türkiye Ligi"},
    {"date":"2022-11-12","season":"2022/23","team":"U17","city":"Alanya","country":"Türkiye","opponent":"Alanyaspor","competition":"Türkiye Ligi"},
    {"date":"2022-12-07","season":"2022/23","team":"U17","city":"Konya","country":"Türkiye","opponent":"Konyaspor","competition":"Türkiye Ligi"},
    {"date":"2022-12-10","season":"2022/23","team":"U17","city":"Adana","country":"Türkiye","opponent":"Adana Demirspor","competition":"Türkiye Ligi"},
    {"date":"2022-12-24","season":"2022/23","team":"U17","city":"Gaziantep","country":"Türkiye","opponent":"Gaziantep FK","competition":"Türkiye Ligi"},
    {"date":"2023-03-04","season":"2022/23","team":"U17","city":"Ankara","country":"Türkiye","opponent":"MKE Ankaragücü","competition":"Türkiye Ligi"},
    {"date":"2023-03-15","season":"2022/23","team":"U17","city":"İzmir","country":"Türkiye","opponent":"Göztepe","competition":"Türkiye Ligi"},

    # 2023/24 U19 — Türkiye
    {"date":"2023-09-23","season":"2023/24","team":"U19","city":"Gaziantep","country":"Türkiye","opponent":"Gaziantep FK","competition":"Türkiye Ligi"},
    {"date":"2023-10-20","season":"2023/24","team":"U19","city":"Malatya","country":"Türkiye","opponent":"Yeni Malatyaspor","competition":"Türkiye Ligi"},
    {"date":"2023-11-03","season":"2023/24","team":"U19","city":"Ankara","country":"Türkiye","opponent":"MKE Ankaragücü","competition":"Türkiye Ligi"},
    {"date":"2023-11-11","season":"2023/24","team":"U19","city":"Adana","country":"Türkiye","opponent":"Adana Demirspor","competition":"Türkiye Ligi"},
    {"date":"2024-01-27","season":"2023/24","team":"U19","city":"Kayseri","country":"Türkiye","opponent":"Kayserispor","competition":"Türkiye Ligi"},
    {"date":"2024-03-01","season":"2023/24","team":"U19","city":"Antalya","country":"Türkiye","opponent":"Antalyaspor","competition":"Türkiye Ligi"},
    {"date":"2024-03-30","season":"2023/24","team":"U19","city":"Ankara","country":"Türkiye","opponent":"Ankaraspor","competition":"Türkiye Ligi"},

    # 2023/24 U19 — UEFA Youth League
    {"date":"2023-10-03","season":"2023/24","team":"U19","city":"Manchester","country":"İngiltere","opponent":"Manchester United U19","competition":"UEFA Youth League"},
    {"date":"2023-11-08","season":"2023/24","team":"U19","city":"Münih","country":"Almanya","opponent":"Bayern München U19","competition":"UEFA Youth League"},
    {"date":"2023-12-12","season":"2023/24","team":"U19","city":"Kopenhag","country":"Danimarka","opponent":"FC København U19","competition":"UEFA Youth League"},

    # 2024/25 U19 — Türkiye (Altınordu ve Yeni Malatyaspor kullanıcı talebiyle YOK)
    {"date":"2024-08-24","season":"2024/25","team":"U19","city":"Antalya","country":"Türkiye","opponent":"Antalyaspor","competition":"Türkiye Ligi"},
    {"date":"2024-09-14","season":"2024/25","team":"U19","city":"Kayseri","country":"Türkiye","opponent":"Kayserispor","competition":"Türkiye Ligi"},
    {"date":"2024-09-25","season":"2024/25","team":"U19","city":"Sivas","country":"Türkiye","opponent":"Sivasspor","competition":"Türkiye Ligi"},
    {"date":"2024-10-26","season":"2024/25","team":"U19","city":"Rize","country":"Türkiye","opponent":"Çaykur Rizespor","competition":"Türkiye Ligi"},
    {"date":"2024-11-02","season":"2024/25","team":"U19","city":"Konya","country":"Türkiye","opponent":"Konyaspor","competition":"Türkiye Ligi"},
    {"date":"2024-11-23","season":"2024/25","team":"U19","city":"Reyhanlı / Hatay","country":"Türkiye","opponent":"Hatayspor","competition":"Türkiye Ligi"},
    {"date":"2024-12-06","season":"2024/25","team":"U19","city":"Ankara","country":"Türkiye","opponent":"MKE Ankaragücü","competition":"Türkiye Ligi"},
    {"date":"2024-12-14","season":"2024/25","team":"U19","city":"Bodrum / Muğla","country":"Türkiye","opponent":"Bodrum FK","competition":"Türkiye Ligi"},
    {"date":"2025-01-11","season":"2024/25","team":"U19","city":"Adana","country":"Türkiye","opponent":"Adana Demirspor","competition":"Türkiye Ligi"},
    {"date":"2025-03-29","season":"2024/25","team":"U19","city":"Bolu","country":"Türkiye","opponent":"Boluspor","competition":"Türkiye Ligi"},
    {"date":"2025-02-08","season":"2024/25","team":"U19","city":"Trabzon","country":"Türkiye","opponent":"Trabzonspor","competition":"Türkiye Ligi"},
    {"date":"2025-05-10","season":"2024/25","team":"U19","city":"Samsun","country":"Türkiye","opponent":"Samsunspor","competition":"Türkiye Ligi"},

    # 2025/26 U19/PAF — Türkiye
    {"date":"2025-08-08","season":"2025/26","team":"U19/PAF","city":"Gaziantep","country":"Türkiye","opponent":"Gaziantep FK","competition":"Türkiye Ligi"},
    {"date":"2025-08-24","season":"2025/26","team":"U19/PAF","city":"Kayseri","country":"Türkiye","opponent":"Kayserispor","competition":"Türkiye Ligi"},
    {"date":"2025-09-26","season":"2025/26","team":"U19/PAF","city":"Alanya","country":"Türkiye","opponent":"Alanyaspor","competition":"Türkiye Ligi"},
    {"date":"2025-11-09","season":"2025/26","team":"U19/PAF","city":"Kocaeli","country":"Türkiye","opponent":"Kocaelispor","competition":"Türkiye Ligi"},
    {"date":"2025-12-13","season":"2025/26","team":"U19/PAF","city":"Antalya","country":"Türkiye","opponent":"Antalyaspor","competition":"Türkiye Ligi"},
    {"date":"2026-03-28","season":"2025/26","team":"U19/PAF","city":"Rize","country":"Türkiye","opponent":"Çaykur Rizespor","competition":"Türkiye Ligi"},
    {"date":"2026-02-21","season":"2025/26","team":"U19/PAF","city":"Konya","country":"Türkiye","opponent":"Konyaspor","competition":"Türkiye Ligi"},
    {"date":"2026-04-08","season":"2025/26","team":"U19/PAF","city":"İzmir","country":"Türkiye","opponent":"Göztepe","competition":"Türkiye Ligi"},
    {"date":"2026-04-04","season":"2025/26","team":"U19/PAF","city":"Trabzon","country":"Türkiye","opponent":"Trabzonspor","competition":"Türkiye Ligi"},
    {"date":"2026-04-18","season":"2025/26","team":"U19/PAF","city":"Ankara","country":"Türkiye","opponent":"Gençlerbirliği","competition":"Türkiye Ligi"},
    {"date":"2026-05-02","season":"2025/26","team":"U19/PAF","city":"Samsun","country":"Türkiye","opponent":"Samsunspor","competition":"Türkiye Ligi"},

    # 2025/26 U19 — UEFA Youth League
    {"date":"2025-09-18","season":"2025/26","team":"U19","city":"Frankfurt","country":"Almanya","opponent":"Eintracht Frankfurt U19","competition":"UEFA Youth League"},
    {"date":"2025-11-05","season":"2025/26","team":"U19","city":"Amsterdam","country":"Hollanda","opponent":"Ajax U19","competition":"UEFA Youth League"},
    {"date":"2025-12-09","season":"2025/26","team":"U19","city":"Monako","country":"Monako","opponent":"Monaco U19","competition":"UEFA Youth League"},
]


def _title(row):
    return f"{row['opponent']} – Galatasaray"


def apply_requested_match_seed(svc) -> int:
    if svc.setting(SEED_KEY, "") == "1":
        return 0

    added = 0
    for row in MATCHES:
        title = _title(row)
        season_start, season_end = SEASON_BOUNDS[row["season"]]
        existing = svc.db.q1(
            "SELECT code,country,purpose FROM trips "
            "WHERE destination=? AND title=? AND status='AKTIF' "
            "AND substr(start_dt,1,10) BETWEEN ? AND ? LIMIT 1",
            (row["city"], title, season_start, season_end),
        )
        if existing:
            # Kullanıcının seyahat saati, ulaşım türü, firma, sefer no ve notlarına dokunma.
            # Yalnız v1.2.0'dan kalan genel organizasyon/ülke değerini güvenle tamamla.
            changes = {}
            old_country = existing["country"] or ""
            old_purpose = existing["purpose"] or ""
            if not old_country:
                changes["country"] = row["country"]
            if old_purpose in ("", "Deplasman", "Deplasman maçı"):
                changes["purpose"] = row["competition"]
            if changes:
                svc.update_trip(existing["code"], changes, "v1.2.3: ülke/organizasyon bilgisi tamamlandı")
            continue

        notes = (
            f"Sezon: {row['season']} | Takım: {row['team']} | Organizasyon: {row['competition']}. "
            "Maç tarihi hazır işlendi; gerçek gidiş-dönüş saatleri ve ulaşım bilgileri bilet/programla sonradan düzenlenebilir."
        )
        trip = svc.add_trip({
            "title": title,
            "start_dt": row["date"],
            "end_dt": row["date"],
            "origin": "İstanbul",
            "destination": row["city"],
            "country": row["country"],
            "purpose": row["competition"],
            "mandatory_group": 1,
            "verification_level": "KULLANICI_BEYANI",
            "include_in_court": 0,
            "notes": notes,
        })
        svc.add_event({
            "title": title,
            "event_type": "Maç",
            "start_dt": row["date"],
            "end_dt": row["date"],
            "country": row["country"],
            "city": row["city"],
            "trip_code": trip,
            "verification_level": "KULLANICI_BEYANI",
            "include_in_court": 0,
        })
        added += 1

    svc.set_setting(SEED_KEY, "1")
    return added
'''
(ROOT / "iscilik_dosyasi/requested_seed_20261001.py").write_text(seed, "utf-8")

# ---------- simple trip form: country + organisation editable ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")
anchor = '''        {"key": "opponent", "label": "Rakip / görev", "default": title, "required": True,
         "placeholder": "Örn. Trabzonspor"},
        {"key": "transport_type", "label": "Ulaşım türü", "kind": "combo",'''
replacement = '''        {"key": "opponent", "label": "Rakip / görev", "default": title, "required": True,
         "placeholder": "Örn. Trabzonspor"},
        {"key": "country", "label": "Ülke",
         "default": _r(event, "country", _r(row, "country", "Türkiye")) or "Türkiye",
         "placeholder": "Örn. Türkiye / Almanya"},
        {"key": "competition", "label": "Organizasyon", "kind": "combo",
         "options": ["Türkiye Ligi", "UEFA Youth League", "Özel Organizasyon", "Hazırlık", "Turnuva", "Diğer"],
         "default": _r(row, "purpose", "Türkiye Ligi") or "Türkiye Ligi", "editable": True},
        {"key": "transport_type", "label": "Ulaşım türü", "kind": "combo",'''
if anchor not in s:
    raise SystemExit("v1.2.3 simple_trip_fields anchor not found")
s = s.replace(anchor, replacement, 1)
p.write_text(s, "utf-8")

# ---------- simple trip payload uses editable country + organisation ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")
old = '''            "origin": v.get("origin") or "İstanbul", "destination": v.get("city"),
            "country": "Türkiye", "purpose": "Deplasman", "mandatory_group": 1,'''
new = '''            "origin": v.get("origin") or "İstanbul", "destination": v.get("city"),
            "country": v.get("country") or "Türkiye",
            "purpose": v.get("competition") or "Türkiye Ligi", "mandatory_group": 1,'''
if old not in s:
    raise SystemExit("v1.2.3 trip payload country/purpose block not found")
s = s.replace(old, new, 1)
old = '''            "title": title, "event_type": "Maç", "start_dt": match_date, "end_dt": match_date,
            "country": "Türkiye", "city": v.get("city"),'''
new = '''            "title": title, "event_type": "Maç", "start_dt": match_date, "end_dt": match_date,
            "country": v.get("country") or "Türkiye", "city": v.get("city"),'''
if old not in s:
    raise SystemExit("v1.2.3 event payload country block not found")
s = s.replace(old, new, 1)
p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v111_seed.py").write_text(r'''from collections import Counter
from iscilik_dosyasi.requested_seed_20261001 import MATCHES, SEED_KEY, apply_requested_match_seed
from iscilik_dosyasi.service import CaseService


def test_requested_match_seed_is_exact_and_idempotent(tmp_path):
    assert len(MATCHES) == 43
    assert all(x["season"] != "2026/27" for x in MATCHES)
    assert sum(x["competition"] == "UEFA Youth League" for x in MATCHES) == 6
    counts = Counter((x["season"], x["competition"]) for x in MATCHES)
    assert counts[("2022/23", "Türkiye Ligi")] == 7
    assert counts[("2023/24", "Türkiye Ligi")] == 7
    assert counts[("2023/24", "UEFA Youth League")] == 3
    assert counts[("2024/25", "Türkiye Ligi")] == 12
    assert counts[("2025/26", "Türkiye Ligi")] == 11
    assert counts[("2025/26", "UEFA Youth League")] == 3
    assert not any(x["season"] == "2022/23" and x["opponent"] == "Bursaspor" for x in MATCHES)
    assert not any(x["season"] == "2022/23" and x["opponent"] == "Hatayspor" for x in MATCHES)

    svc = CaseService(tmp_path / "case", actor="TEST")
    try:
        assert apply_requested_match_seed(svc) == 43
        assert len(svc.trips()) == 43
        assert svc.setting(SEED_KEY) == "1"
        assert apply_requested_match_seed(svc) == 0
        assert len(svc.trips()) == 43
        assert svc.vault.verify_audit_chain()[0]
    finally:
        svc.close()
''', "utf-8")

p = ROOT / "tests/test_v120_simple.py"
s = p.read_text("utf-8")
s = s.replace("assert len(MATCHES) == 7", "assert len(MATCHES) == 43")
s = s.replace("assert all(len(row) == 3 for row in MATCHES)", "assert all(isinstance(row, dict) for row in MATCHES)")
p.write_text(s, "utf-8")

(ROOT / "tests/test_v123_full_fixture.py").write_text(r'''from iscilik_dosyasi.requested_seed_20261001 import MATCHES
from iscilik_dosyasi.ui_dialogs import simple_trip_fields


def test_full_fixture_scope_and_edit_fields():
    assert len(MATCHES) == 43
    labels = [x["label"] for x in simple_trip_fields()]
    assert "Ülke" in labels
    assert "Organizasyon" in labels
    assert "Ulaşım türü" in labels
    assert "Firma / taşıyıcı" in labels
    assert "Uçuş / sefer no (varsa)" in labels
    assert not any(x["season"] == "2026/27" for x in MATCHES)


def test_user_exclusions_and_uefa_count():
    assert not any(x["season"] == "2022/23" and x["opponent"] == "Bursaspor" for x in MATCHES)
    assert not any(x["season"] == "2022/23" and x["opponent"] == "Hatayspor" for x in MATCHES)
    assert sum(x["competition"] == "UEFA Youth League" for x in MATCHES) == 6
''', "utf-8")

# ---------- changelog ----------
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.3 — 43 Deplasman + Türkiye/UEFA Ayrımı
- 2022/23–2025/26 arasında kullanıcının gerçekten gittiğini seçtiği 43 deplasman hazır eklendi.
- 2022/23 Bursaspor ve Hatayspor dahil edilmedi; 2026/27 sezonu özellikle boş bırakıldı.
- 2023/24 ve 2025/26 UEFA Youth League yurt dışı deplasmanları ayrı organizasyon olarak eklendi.
- Deplasman Düzenle ekranına Ülke ve Organizasyon alanları eklendi.
- Uçak/Otobüs, firma/taşıyıcı ve uçuş/sefer no alanları düzenlenebilir olmaya devam eder.
- Mevcut kayıtların kullanıcı tarafından girilmiş seyahat saatleri, ulaşım bilgileri ve notları seed güncellemesinde korunur.

'''
if "## v1.2.3" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.3 full fixture/edit patch applied")
