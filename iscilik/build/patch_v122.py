from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.2\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.2"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 2, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 2, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.2')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.2')", s)
p.write_text(s, "utf-8")

# ---------- trip form transport fields ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")

start = s.index("def simple_trip_fields(row=None, event=None) -> list[dict]:")
end = s.index("\n\ndef simple_evidence_fields", start)

new = r'''TRANSPORT_TYPES = ["Uçak", "Otobüs", "Tren", "Özel araç", "Diğer"]
_TRANSPORT_PREFIX = "[ULAŞIM]"


def split_trip_notes(row=None):
    raw = _r(row, "notes", "") or ""
    meta = {"transport_type": "", "carrier": "", "service_no": ""}
    normal = []
    for line in str(raw).splitlines():
        if line.startswith(_TRANSPORT_PREFIX + " Tür:"):
            meta["transport_type"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TRANSPORT_PREFIX + " Firma:"):
            meta["carrier"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TRANSPORT_PREFIX + " Sefer:"):
            meta["service_no"] = line.split(":", 1)[1].strip()
        else:
            normal.append(line)
    meta["notes"] = "\n".join(normal).strip()
    return meta


def build_trip_notes(transport_type="", carrier="", service_no="", notes=""):
    lines = []
    if transport_type:
        lines.append(f"{_TRANSPORT_PREFIX} Tür: {transport_type}")
    if carrier:
        lines.append(f"{_TRANSPORT_PREFIX} Firma: {carrier}")
    if service_no:
        lines.append(f"{_TRANSPORT_PREFIX} Sefer: {service_no}")
    if notes and str(notes).strip():
        lines.append(str(notes).strip())
    return "\n".join(lines).strip() or None


def simple_trip_fields(row=None, event=None) -> list[dict]:
    """Günlük kullanım için sade deplasman formu."""
    title = _r(event, "title", _r(row, "title", ""))
    if title.endswith(" – Galatasaray"):
        title = title[:-len(" – Galatasaray")]
    match_date = _r(event, "start_dt", _r(row, "start_dt"))
    tm = split_trip_notes(row)
    ttype = tm["transport_type"] if tm["transport_type"] in TRANSPORT_TYPES else (tm["transport_type"] or "Uçak")
    return [
        {"key": "match_date", "label": "Maç / görev tarihi", "kind": "date", "default": match_date, "required": True},
        {"key": "city", "label": "Şehir", "default": _r(event, "city", _r(row, "destination", "")), "required": True,
         "placeholder": "Örn. Trabzon"},
        {"key": "opponent", "label": "Rakip / görev", "default": title, "required": True,
         "placeholder": "Örn. Trabzonspor"},
        {"key": "transport_type", "label": "Ulaşım türü", "kind": "combo",
         "options": TRANSPORT_TYPES, "default": ttype, "editable": True,
         "help": "Örn. Uçak veya Otobüs."},
        {"key": "carrier", "label": "Firma / taşıyıcı", "default": tm["carrier"],
         "placeholder": "Örn. Turkish Airlines, Pegasus, Metro"},
        {"key": "service_no", "label": "Uçuş / sefer no (varsa)", "default": tm["service_no"],
         "placeholder": "Örn. TK2830"},
        {"key": "departure_dt", "label": "Gidiş / görev başlangıcı (biliyorsanız)", "kind": "datetime",
         "default": _r(row, "start_dt"),
         "help": "Bilmiyorsanız boş bırakabilirsiniz; daha sonra bilet/programla tamamlanır."},
        {"key": "return_dt", "label": "Dönüş sonrası işin bittiği zaman (biliyorsanız)", "kind": "datetime",
         "default": _r(row, "end_dt"),
         "help": "Havalimanı → Florya → malzeme işi dahil gerçek bitiş zamanı daha sonra eklenebilir."},
        {"key": "origin", "label": "Çıkış", "default": _r(row, "origin", "İstanbul") or "İstanbul"},
        {"key": "post_return_florya", "label": "Dönüşte Florya'da çalışma oldu mu?", "kind": "tri",
         "default": _r(row, "post_return_florya")},
        {"key": "post_return_work", "label": "Dönüş sonrası yapılan iş", "kind": "text",
         "default": _r(row, "post_return_work", "")},
        {"key": "notes", "label": "Not", "kind": "text", "default": tm["notes"]},
    ]
'''

s = s[:start] + new + s[end:]
p.write_text(s, "utf-8")

# ---------- main UI ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

s = s.replace(
    "simple_evidence_fields, simple_trip_fields, split_claim_values,",
    "build_trip_notes, simple_evidence_fields, simple_trip_fields, split_claim_values, split_trip_notes,"
)

old = '''            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
            "notes": v.get("notes"),
        }'''
new = '''            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
            "notes": build_trip_notes(
                v.get("transport_type"), v.get("carrier"), v.get("service_no"), v.get("notes")
            ),
        }'''
if old not in s:
    raise SystemExit("trip payload notes block not found")
s = s.replace(old, new, 1)

old = '''        self.trip_table = make_table(
            ["Kayıt", "Maç / Görev Tarihi", "Şehir", "Rakip / Görev", "Gidiş", "Dönüş / Bitiş", "Delil", "Durum"],
            [90, 125, 120, 280, 145, 145, 70, 110]
        )'''
new = '''        self.trip_table = make_table(
            ["Kayıt", "Maç / Görev Tarihi", "Şehir", "Rakip / Görev", "Ulaşım", "Firma", "Gidiş", "Dönüş / Bitiş", "Delil", "Durum"],
            [90, 125, 110, 240, 90, 145, 135, 135, 65, 100]
        )'''
if old not in s:
    raise SystemExit("trip table block not found")
s = s.replace(old, new, 1)

old = '''            evidence_n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            rows.append([
                t["code"], match_date, city, title,
                fmt(t["start_dt"]), fmt(t["end_dt"]), str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])'''
new = '''            evidence_n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            tm = split_trip_notes(t)
            rows.append([
                t["code"], match_date, city, title,
                tm["transport_type"] or "—", tm["carrier"] or "—",
                fmt(t["start_dt"]), fmt(t["end_dt"]), str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])'''
if old not in s:
    raise SystemExit("refresh trip rows block not found")
s = s.replace(old, new, 1)

# Search should find transport/carrier too
s = s.replace(
    'hay = f"{match_date} {city} {title} {t[\'code\']}".lower()',
    'tm_search = split_trip_notes(t)\n            hay = f"{match_date} {city} {title} {tm_search[\'transport_type\']} {tm_search[\'carrier\']} {t[\'code\']}".lower()'
)

p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v122_transport.py").write_text(r'''from iscilik_dosyasi.ui_dialogs import (
    TRANSPORT_TYPES, build_trip_notes, simple_trip_fields, split_trip_notes
)


def test_transport_fields_are_visible_and_simple():
    fields = simple_trip_fields()
    labels = [x["label"] for x in fields]
    assert "Ulaşım türü" in labels
    assert "Firma / taşıyıcı" in labels
    assert "Uçuş / sefer no (varsa)" in labels
    assert "Uçak" in TRANSPORT_TYPES
    assert "Otobüs" in TRANSPORT_TYPES


def test_transport_metadata_roundtrip():
    raw = build_trip_notes("Uçak", "Turkish Airlines", "TK2830", "Kafile ile.")
    row = {"notes": raw}
    meta = split_trip_notes(row)
    assert meta["transport_type"] == "Uçak"
    assert meta["carrier"] == "Turkish Airlines"
    assert meta["service_no"] == "TK2830"
    assert meta["notes"] == "Kafile ile."


def test_plain_old_notes_stay_intact():
    meta = split_trip_notes({"notes": "Eski kullanıcı notu"})
    assert meta["transport_type"] == ""
    assert meta["carrier"] == ""
    assert meta["service_no"] == ""
    assert meta["notes"] == "Eski kullanıcı notu"
''', "utf-8")

print("v1.2.2 transport patch applied")
