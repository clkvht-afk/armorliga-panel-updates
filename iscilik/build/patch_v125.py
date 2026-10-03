from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.5\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.5"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 5, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 5, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.5')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.5')", s)
p.write_text(s, "utf-8")

# ---------- trip form: work start is separate from flight/bus departure ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")

old = '''        "season": "", "team": "", "competition": "",
        "return_arrival_dt": "", "facility_return_dt": "",
    }'''
new = '''        "season": "", "team": "", "competition": "",
        "work_start_dt": "", "return_arrival_dt": "", "facility_return_dt": "",
    }'''
if old not in s:
    raise SystemExit("v1.2.5 meta dict anchor not found")
s = s.replace(old, new, 1)

old = '''        elif line.startswith(_TIME_PREFIX + " İstanbul dönüş:"):
            meta["return_arrival_dt"] = line.split(":", 1)[1].strip()'''
new = '''        elif line.startswith(_TIME_PREFIX + " İş başlangıcı:"):
            meta["work_start_dt"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TIME_PREFIX + " İstanbul dönüş:"):
            meta["return_arrival_dt"] = line.split(":", 1)[1].strip()'''
if old not in s:
    raise SystemExit("v1.2.5 work start parser anchor not found")
s = s.replace(old, new, 1)

old = '''def build_trip_notes(transport_type="", carrier="", service_no="", notes="",
                     season="", team="", competition="",
                     return_arrival_dt="", facility_return_dt=""):'''
new = '''def build_trip_notes(transport_type="", carrier="", service_no="", notes="",
                     season="", team="", competition="",
                     return_arrival_dt="", facility_return_dt="", work_start_dt=""):'''
if old not in s:
    raise SystemExit("v1.2.5 build signature anchor not found")
s = s.replace(old, new, 1)

old = '''    if return_arrival_dt:
        lines.append(f"{_TIME_PREFIX} İstanbul dönüş: {return_arrival_dt}")'''
new = '''    if work_start_dt:
        lines.append(f"{_TIME_PREFIX} İş başlangıcı: {work_start_dt}")
    if return_arrival_dt:
        lines.append(f"{_TIME_PREFIX} İstanbul dönüş: {return_arrival_dt}")'''
if old not in s:
    raise SystemExit("v1.2.5 work start builder anchor not found")
s = s.replace(old, new, 1)

old = '''        {"key": "departure_dt", "label": "Gidiş / göreve başlangıç", "kind": "datetime",
         "default": dep,
         "help": "Florya'dan/kafileyle hareket ettiğiniz gerçek zamanı biliyorsanız girin; bilmiyorsanız boş bırakın."},'''
new = '''        {"key": "work_start_dt", "label": "İşe başlama", "kind": "datetime",
         "default": tm["work_start_dt"] or None,
         "help": "O gün fiilen işe başladığınız saat. Örn. tesiste 08:00'de işe başlayıp uçuşunuz 16:00 olabilir."},
        {"key": "departure_dt", "label": "Uçuş / sefer hareketi", "kind": "datetime",
         "default": dep,
         "help": "Uçağın, otobüsün, trenin veya kafilenin hareket saati. İşe başlama saatiyle aynı olmak zorunda değildir."},'''
if old not in s:
    raise SystemExit("v1.2.5 departure field anchor not found")
s = s.replace(old, new, 1)
p.write_text(s, "utf-8")

# ---------- payload + table ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

old = '''                v.get("season"), v.get("team"), v.get("competition"),
                v.get("return_arrival_dt"), v.get("facility_return_dt")
            ),'''
new = '''                v.get("season"), v.get("team"), v.get("competition"),
                v.get("return_arrival_dt"), v.get("facility_return_dt"), v.get("work_start_dt")
            ),'''
if old not in s:
    raise SystemExit("v1.2.5 notes payload anchor not found")
s = s.replace(old, new, 1)

s = s.replace(
    'intro="Maç tarihi ayrı tutulur. Gidiş, İstanbul dönüşü, tesise dönüş ve gerçek iş bitişi yalnız biliyorsanız girilir."',
    'intro="İşe başlama ile uçuş/sefer saati ayrıdır. Yalnız bildiğiniz gerçek saatleri girin; bilinmeyen alanları boş bırakın."'
)
s = s.replace(
    'intro="Sadece bildiğiniz gerçek saatleri doldurun. Boş alanlara program maç tarihini saatmiş gibi göstermeyecek."',
    'intro="İşe başlama, uçuş/sefer, İstanbul dönüşü, tesise dönüş ve gerçek iş bitişi ayrı tutulur. Yalnız bildiğiniz saatleri girin."'
)

old = '''        self.trip_table = make_table(
            ["Kayıt", "Maç Tarihi", "Takım", "Şehir", "Rakip / Görev", "Ulaşım", "Firma",
             "Gidiş", "İstanbul'a Dönüş", "İş Bitişi", "Görev Süresi", "Delil", "Durum"],
            [88, 105, 75, 100, 210, 80, 120, 135, 145, 135, 105, 55, 90]
        )'''
new = '''        self.trip_table = make_table(
            ["Kayıt", "Maç Tarihi", "Takım", "Şehir", "Rakip / Görev", "Ulaşım", "Firma",
             "İş Başlangıcı", "Uçuş / Sefer", "İstanbul'a Dönüş", "İş Bitişi", "Görev Süresi", "Delil", "Durum"],
            [88, 105, 75, 100, 205, 80, 115, 135, 135, 145, 135, 105, 55, 90]
        )'''
if old not in s:
    raise SystemExit("v1.2.5 table anchor not found")
s = s.replace(old, new, 1)

old = '''            dep = manual_value(t["start_dt"], event_raw)
            work_end = manual_value(t["end_dt"], event_raw)
            ret = tm["return_arrival_dt"] or None
            team = tm["team"] or "—"
            hay = (
                f"{match_date} {tm['season']} {team} {city} {title} "
                f"{tm['competition']} {tm['transport_type']} {tm['carrier']} {t['code']}"
            ).lower()'''
new = '''            dep = manual_value(t["start_dt"], event_raw)
            work_start = tm["work_start_dt"] or None
            work_end = manual_value(t["end_dt"], event_raw)
            ret = tm["return_arrival_dt"] or None
            team = tm["team"] or "—"
            hay = (
                f"{match_date} {tm['season']} {team} {city} {title} "
                f"{tm['competition']} {tm['transport_type']} {tm['carrier']} "
                f"{work_start or ''} {dep or ''} {t['code']}"
            ).lower()'''
if old not in s:
    raise SystemExit("v1.2.5 refresh values anchor not found")
s = s.replace(old, new, 1)

old = '''                t["code"], match_date, team, city, title,
                tm["transport_type"] or "—", tm["carrier"] or "—",
                fmt(dep) if dep else "—",
                fmt(ret) if ret else "—",
                fmt(work_end) if work_end else "—",
                elapsed_text(dep, work_end),
                str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])'''
new = '''                t["code"], match_date, team, city, title,
                tm["transport_type"] or "—", tm["carrier"] or "—",
                fmt(work_start) if work_start else "—",
                fmt(dep) if dep else "—",
                fmt(ret) if ret else "—",
                fmt(work_end) if work_end else "—",
                elapsed_text(work_start, work_end),
                str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])'''
if old not in s:
    raise SystemExit("v1.2.5 refresh row anchor not found")
s = s.replace(old, new, 1)
p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v125_work_start.py").write_text(r'''from iscilik_dosyasi.ui_dialogs import (
    build_trip_notes, simple_trip_fields, split_trip_notes
)


def test_work_start_and_departure_are_separate():
    notes = build_trip_notes(
        "Uçak", "THY", "", "",
        "2025/26", "U19/PAF", "Türkiye Ligi",
        "2026-05-02 23:00", "", "2026-05-01 08:00"
    )
    row = {
        "start_dt": "2026-05-01 16:00",
        "end_dt": "2026-05-03 05:00",
        "destination": "Samsun",
        "notes": notes,
    }
    ev = {
        "start_dt": "2026-05-02",
        "title": "Samsunspor – Galatasaray",
        "city": "Samsun",
        "country": "Türkiye",
    }
    fields = {x["key"]: x for x in simple_trip_fields(row, ev)}
    assert fields["work_start_dt"]["default"] == "2026-05-01 08:00"
    assert fields["departure_dt"]["default"] == "2026-05-01 16:00"
    assert fields["work_end_dt"]["default"] == "2026-05-03 05:00"
    assert fields["work_start_dt"]["label"] == "İşe başlama"
    assert fields["departure_dt"]["label"] == "Uçuş / sefer hareketi"


def test_work_start_metadata_roundtrip():
    raw = build_trip_notes(
        "Otobüs", "Kiralık Otobüs", "", "Not",
        "2023/24", "U19", "Türkiye Ligi",
        "2023-11-04 02:30", "2023-11-04 03:15", "2023-11-03 08:00"
    )
    m = split_trip_notes({"notes": raw})
    assert m["work_start_dt"] == "2023-11-03 08:00"
    assert m["return_arrival_dt"] == "2023-11-04 02:30"
    assert m["facility_return_dt"] == "2023-11-04 03:15"
    assert m["notes"] == "Not"
''', "utf-8")

# ---------- changelog ----------
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.5 — İş Başlangıcı Uçuş Saatinden Ayrıldı
- İşe başlama saati ile uçuş/otobüs/sefer hareket saati ayrı alanlara ayrıldı.
- Mevcut Gidiş bilgileri korunur ve Uçuş / Sefer olarak gösterilir; kullanıcı verisi taşınmaz veya silinmez.
- Görev Süresi artık İşe Başlama → Gerçek İş Bitişi arasından hesaplanır.
- Örnek: 01.05 08:00 işe başlama + 01.05 16:00 uçuş + 03.05 05:00 iş bitişi = 45 saat ham görev süresi.

'''
if "## v1.2.5" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.5 work start separated from transport departure")
