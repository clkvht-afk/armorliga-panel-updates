from pathlib import Path

ROOT = Path("work")


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# Program version
write("VERSION", "1.1.1\n")
p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text(encoding="utf-8")
s = s.replace('__version__ = "1.1.0"', '__version__ = "1.1.1"')
p.write_text(s, encoding="utf-8")

# Windows file metadata
p = ROOT / "packaging/version_info.txt"
s = p.read_text(encoding="utf-8")
s = s.replace("filevers=(1, 1, 0, 0)", "filevers=(1, 1, 1, 0)")
s = s.replace("prodvers=(1, 1, 0, 0)", "prodvers=(1, 1, 1, 0)")
s = s.replace("'1.1.0'", "'1.1.1'")
p.write_text(s, encoding="utf-8")

seed = r'''"""Kullanıcının 2026-10-01 tarihinde verdiği ilk deplasman/maç listesi.

Bu kayıtlar yalnız gerçek Windows EXE normal açılışında bir kez içe alınır.
Bursaspor ve Hatayspor satırları kullanıcı talebi gereği dahil değildir.
Kayıtlar KULLANICI_BEYANI seviyesindedir ve mahkeme paketine otomatik alınmaz.
"""
from __future__ import annotations

SEED_KEY = "requested_match_seed_20261001_v1"

MATCHES = [
    {
        "date": "2022-10-26", "city": "Trabzon",
        "match": "Trabzonspor – Galatasaray", "score": "4-1",
        "source_url": "https://www.tff.org/Default.aspx?hafta=1&pageID=1616",
    },
    {
        "date": "2022-11-12", "city": "Alanya",
        "match": "Alanyaspor – Galatasaray", "score": "1-5",
        "source_url": "https://www.tff.org/Default.aspx?hafta=5&pageID=1616",
    },
    {
        "date": "2022-12-07", "city": "Konya",
        "match": "Konyaspor – Galatasaray", "score": "1-1",
        "source_url": "https://www.tff.org/Default.aspx?hafta=7&pageID=1616&utm_source=chatgpt.com",
    },
    {
        "date": "2022-12-10", "city": "Adana",
        "match": "Adana Demirspor – Galatasaray", "score": "1-3",
        "source_url": "https://www.tff.org/Default.aspx?hafta=9&pageID=1616",
    },
    {
        "date": "2022-12-24", "city": "Gaziantep",
        "match": "Gaziantep FK – Galatasaray", "score": "0-2",
        "source_url": "https://www.tff.org/Default.aspx?hafta=11&pageID=1616",
    },
    {
        "date": "2023-03-04", "city": "Ankara",
        "match": "MKE Ankaragücü – Galatasaray", "score": "2-3",
        "source_url": "https://www.tff.org/Default.aspx?hafta=17&pageID=1616",
    },
    {
        "date": "2023-03-15", "city": "İzmir",
        "match": "Göztepe – Galatasaray", "score": "0-0",
        "source_url": "https://www.tff.org/Default.aspx?hafta=19&pageID=1616",
    },
]


def apply_requested_match_seed(svc) -> int:
    """Eksik kayıtları güvenli/idempotent biçimde ekler; eklenen adet döner."""
    if svc.setting(SEED_KEY, "") == "1":
        return 0

    added = 0
    for row in MATCHES:
        exists = svc.db.q1(
            "SELECT code FROM trips WHERE start_dt=? AND destination=? AND title=? AND status='AKTIF' LIMIT 1",
            (row["date"], row["city"], row["match"]),
        )
        if exists:
            continue
        svc.add_trip({
            "title": row["match"],
            "start_dt": row["date"],
            "end_dt": row["date"],
            "destination": row["city"],
            "purpose": "Deplasman maçı",
            "description": f"Maç: {row['match']} | Sonuç: {row['score']}",
            "notes": (
                "Kullanıcının 01.10.2026 tarihinde verdiği listeden işlendi. "
                "Girilen tarih maç tarihidir; gerçek seyahat başlangıç/bitiş saatleri ve ulaşım delilleri "
                "ayrıca eklenecektir. Kaynak bağlantısı: " + row["source_url"]
            ),
            "verification_level": "KULLANICI_BEYANI",
            "include_in_court": 0,
        })
        added += 1

    svc.set_setting(SEED_KEY, "1")
    return added
'''
write("iscilik_dosyasi/requested_seed_20261001.py", seed)

# Normal Windows EXE açılışında bir kez seed uygula.
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text(encoding="utf-8")
needle = """    try:\n        svc = CaseService(data_dir)\n    except Exception as e:\n"""
replacement = """    try:\n        svc = CaseService(data_dir)\n        # v1.1.1: Kullanıcının talep ettiği ilk deplasman listesi gerçek Windows EXE'de bir kez işlenir.\n        # Test/özel veri klasörlerinde otomatik kişisel veri tohumu çalıştırılmaz.\n        if os.name == \"nt\" and getattr(sys, \"frozen\", False) and not os.environ.get(\"ISCILIK_DATA_DIR\"):\n            from .requested_seed_20261001 import apply_requested_match_seed\n            added = apply_requested_match_seed(svc)\n            if added:\n                logging.getLogger(\"iscilik\").info(\"İlk deplasman listesi işlendi: %s kayıt\", added)\n    except Exception as e:\n"""
if needle not in s:
    raise SystemExit("ui_qt.py seed insertion point not found")
s = s.replace(needle, replacement, 1)
p.write_text(s, encoding="utf-8")

# Test: tam 7 kayıt, Bursaspor/Hatayspor yok, tekrar çalıştırınca çoğaltmıyor.
test = r'''from iscilik_dosyasi.requested_seed_20261001 import MATCHES, SEED_KEY, apply_requested_match_seed
from iscilik_dosyasi.service import CaseService


def test_requested_match_seed_is_exact_and_idempotent(tmp_path):
    svc = CaseService(tmp_path / "case", actor="TEST")
    try:
        assert len(MATCHES) == 7
        assert all("Bursaspor" not in x["match"] for x in MATCHES)
        assert all("Hatayspor" not in x["match"] for x in MATCHES)
        assert apply_requested_match_seed(svc) == 7
        rows = svc.trips()
        assert len(rows) == 7
        assert [r["destination"] for r in rows] == ["Trabzon", "Alanya", "Konya", "Adana", "Gaziantep", "Ankara", "İzmir"]
        assert [r["start_dt"] for r in rows] == [x["date"] for x in MATCHES]
        assert "Sonuç: 4-1" in rows[0]["description"]
        assert all(r["verification_level"] == "KULLANICI_BEYANI" for r in rows)
        assert all(r["include_in_court"] == 0 for r in rows)
        assert svc.setting(SEED_KEY) == "1"
        assert apply_requested_match_seed(svc) == 0
        assert len(svc.trips()) == 7
        assert svc.vault.verify_audit_chain()[0]
    finally:
        svc.close()
'''
write("tests/test_v111_seed.py", test)

# Changelog
p = ROOT / "CHANGELOG.md"
s = p.read_text(encoding="utf-8")
entry = """## v1.1.1 — İlk deplasman listesi + güncelleme testi
- Kullanıcının verdiği listeden 7 deplasman kaydı ilk normal Windows açılışında bir kez eklenir.
- Bursaspor ve Hatayspor kayıtları özellikle dahil edilmez.
- Kayıtlar KULLANICI_BEYANI seviyesinde ve mahkeme paketine varsayılan olarak dahil değil.
- Tarihler maç tarihi olarak kaydedilir; gerçek seyahat saatleri daha sonra delillerle tamamlanır.

"""
if "## v1.1.1" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
    p.write_text(s, encoding="utf-8")
