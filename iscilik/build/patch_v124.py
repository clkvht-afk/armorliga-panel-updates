from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.4\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.4"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 4, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 4, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.4')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.4')", s)
p.write_text(s, "utf-8")

# ---------- seed metadata migration ----------
p = ROOT / "iscilik_dosyasi/requested_seed_20261001.py"
s = p.read_text("utf-8")
s = s.replace(
    'SEED_KEY = "requested_match_seed_20261002_full_v3"',
    'SEED_KEY = "requested_match_seed_20261002_full_v4"'
)

# 2025/26 kullanıcının çalışma ekibi U19/PAF; UEFA kayıtlarında da aynı görünür.
for day in ("2025-09-18", "2025-11-05", "2025-12-09"):
    s = s.replace(
        f'{{"date":"{day}","season":"2025/26","team":"U19",',
        f'{{"date":"{day}","season":"2025/26","team":"U19/PAF",'
    )

anchor = '''def _title(row):
    return f"{row['opponent']} – Galatasaray"


def apply_requested_match_seed(svc) -> int:
'''
replacement = '''def _title(row):
    return f"{row['opponent']} – Galatasaray"


def _record_notes(notes, row):
    """Sezon/takım/organizasyon bilgisini kullanıcı notunu bozmadan ekler."""
    keep = []
    for line in str(notes or "").splitlines():
        if line.startswith("[KAYIT] Sezon:"):
            continue
        if line.startswith("[KAYIT] Takım:"):
            continue
        if line.startswith("[KAYIT] Organizasyon:"):
            continue
        # v1.2.3 otomatik açıklaması: yeni yapı bunu ayrı meta satırlarına çevirir.
        if line.startswith("Sezon: ") and "| Takım:" in line and "| Organizasyon:" in line:
            continue
        keep.append(line)
    meta = [
        f"[KAYIT] Sezon: {row['season']}",
        f"[KAYIT] Takım: {row['team']}",
        f"[KAYIT] Organizasyon: {row['competition']}",
    ]
    return "\\n".join(meta + keep).strip()


def apply_requested_match_seed(svc) -> int:
'''
if anchor not in s:
    raise SystemExit("v1.2.4 seed helper anchor not found")
s = s.replace(anchor, replacement, 1)

old_query = '''        existing = svc.db.q1(
            "SELECT code,country,purpose FROM trips "
            "WHERE destination=? AND title=? AND status='AKTIF' "
            "AND substr(start_dt,1,10) BETWEEN ? AND ? LIMIT 1",
            (row["city"], title, season_start, season_end),
        )'''
new_query = '''        existing = svc.db.q1(
            "SELECT code,country,purpose,notes,start_dt,end_dt FROM trips "
            "WHERE destination=? AND title=? AND status='AKTIF' "
            "AND substr(start_dt,1,10) BETWEEN ? AND ? LIMIT 1",
            (row["city"], title, season_start, season_end),
        )'''
if old_query not in s:
    raise SystemExit("v1.2.4 existing query not found")
s = s.replace(old_query, new_query, 1)

old_existing = '''        if existing:
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
        )'''
new_existing = '''        if existing:
            # Kullanıcının gerçek seyahat/ulaşım verisini koru.
            # Sezon, takım ve organizasyon metadatasını tamamla.
            changes = {}
            old_country = existing["country"] or ""
            old_purpose = existing["purpose"] or ""
            if not old_country:
                changes["country"] = row["country"]
            if old_purpose in ("", "Deplasman", "Deplasman maçı"):
                changes["purpose"] = row["competition"]
            merged_notes = _record_notes(existing["notes"], row)
            if merged_notes != (existing["notes"] or ""):
                changes["notes"] = merged_notes
            if changes:
                svc.update_trip(existing["code"], changes, "v1.2.4: sezon/takım/organizasyon bilgisi tamamlandı")
            continue

        notes = _record_notes("", row)'''
if old_existing not in s:
    raise SystemExit("v1.2.4 existing block not found")
s = s.replace(old_existing, new_existing, 1)
p.write_text(s, "utf-8")

# ---------- trip notes + user form ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")
start = s.index('TRANSPORT_TYPES = ["Uçak", "Otobüs", "Tren", "Özel araç", "Diğer"]')
end = s.index("\n\ndef simple_evidence_fields", start)

new_block = r'''TRANSPORT_TYPES = ["Uçak", "Otobüs", "Tren", "Özel araç", "Diğer"]
_TRANSPORT_PREFIX = "[ULAŞIM]"
_RECORD_PREFIX = "[KAYIT]"
_TIME_PREFIX = "[ZAMAN]"


def _date_only_placeholder(value, match_date):
    """Seed'in maç tarihini gidiş/bitiş saati gibi göstermesini engeller."""
    if not value or not match_date:
        return False
    a = str(value).strip()
    b = str(match_date).strip()
    return len(a) <= 10 and a[:10] == b[:10]


def split_trip_notes(row=None):
    raw = _r(row, "notes", "") or ""
    meta = {
        "transport_type": "", "carrier": "", "service_no": "",
        "season": "", "team": "", "competition": "",
        "return_arrival_dt": "", "facility_return_dt": "",
    }
    normal = []
    for line in str(raw).splitlines():
        if line.startswith(_TRANSPORT_PREFIX + " Tür:"):
            meta["transport_type"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TRANSPORT_PREFIX + " Firma:"):
            meta["carrier"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TRANSPORT_PREFIX + " Sefer:"):
            meta["service_no"] = line.split(":", 1)[1].strip()
        elif line.startswith(_RECORD_PREFIX + " Sezon:"):
            meta["season"] = line.split(":", 1)[1].strip()
        elif line.startswith(_RECORD_PREFIX + " Takım:"):
            meta["team"] = line.split(":", 1)[1].strip()
        elif line.startswith(_RECORD_PREFIX + " Organizasyon:"):
            meta["competition"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TIME_PREFIX + " İstanbul dönüş:"):
            meta["return_arrival_dt"] = line.split(":", 1)[1].strip()
        elif line.startswith(_TIME_PREFIX + " Tesise dönüş:"):
            meta["facility_return_dt"] = line.split(":", 1)[1].strip()
        else:
            normal.append(line)
    meta["notes"] = "\n".join(normal).strip()
    return meta


def build_trip_notes(transport_type="", carrier="", service_no="", notes="",
                     season="", team="", competition="",
                     return_arrival_dt="", facility_return_dt=""):
    lines = []
    if season:
        lines.append(f"{_RECORD_PREFIX} Sezon: {season}")
    if team:
        lines.append(f"{_RECORD_PREFIX} Takım: {team}")
    if competition:
        lines.append(f"{_RECORD_PREFIX} Organizasyon: {competition}")
    if transport_type:
        lines.append(f"{_TRANSPORT_PREFIX} Tür: {transport_type}")
    if carrier:
        lines.append(f"{_TRANSPORT_PREFIX} Firma: {carrier}")
    if service_no:
        lines.append(f"{_TRANSPORT_PREFIX} Sefer: {service_no}")
    if return_arrival_dt:
        lines.append(f"{_TIME_PREFIX} İstanbul dönüş: {return_arrival_dt}")
    if facility_return_dt:
        lines.append(f"{_TIME_PREFIX} Tesise dönüş: {facility_return_dt}")
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

    dep = _r(row, "start_dt")
    work_end = _r(row, "end_dt")
    if _date_only_placeholder(dep, match_date):
        dep = None
    if _date_only_placeholder(work_end, match_date):
        work_end = None

    return [
        {"key": "match_date", "label": "Maç / görev tarihi", "kind": "date", "default": match_date, "required": True},
        {"key": "season", "label": "Sezon", "kind": "combo",
         "options": ["2022/23", "2023/24", "2024/25", "2025/26", "2026/27"],
         "default": tm["season"] or "2026/27", "editable": True},
        {"key": "team", "label": "Takım", "kind": "combo",
         "options": ["U17", "U19", "U19/PAF", "Diğer"],
         "default": tm["team"] or "U19/PAF", "editable": True},
        {"key": "city", "label": "Şehir", "default": _r(event, "city", _r(row, "destination", "")), "required": True,
         "placeholder": "Örn. Trabzon"},
        {"key": "opponent", "label": "Rakip / görev", "default": title, "required": True,
         "placeholder": "Örn. Trabzonspor"},
        {"key": "country", "label": "Ülke",
         "default": _r(event, "country", _r(row, "country", "Türkiye")) or "Türkiye",
         "placeholder": "Örn. Türkiye / Almanya"},
        {"key": "competition", "label": "Organizasyon", "kind": "combo",
         "options": ["Türkiye Ligi", "UEFA Youth League", "Özel Organizasyon", "Hazırlık", "Turnuva", "Diğer"],
         "default": tm["competition"] or _r(row, "purpose", "Türkiye Ligi") or "Türkiye Ligi", "editable": True},
        {"key": "transport_type", "label": "Ulaşım türü", "kind": "combo",
         "options": TRANSPORT_TYPES, "default": ttype, "editable": True,
         "help": "Örn. Uçak veya Otobüs."},
        {"key": "carrier", "label": "Firma / taşıyıcı", "default": tm["carrier"],
         "placeholder": "Örn. Turkish Airlines, Pegasus, Metro"},
        {"key": "service_no", "label": "Uçuş / sefer no (varsa)", "default": tm["service_no"],
         "placeholder": "Örn. TK2830"},
        {"key": "departure_dt", "label": "Gidiş / göreve başlangıç", "kind": "datetime",
         "default": dep,
         "help": "Florya'dan/kafileyle hareket ettiğiniz gerçek zamanı biliyorsanız girin; bilmiyorsanız boş bırakın."},
        {"key": "return_arrival_dt", "label": "İstanbul'a dönüş / varış", "kind": "datetime",
         "default": tm["return_arrival_dt"] or None,
         "help": "Uçak inişi veya otobüsün İstanbul'a varışı. Bilmiyorsanız boş bırakın."},
        {"key": "facility_return_dt", "label": "Tesise dönüş (varsa)", "kind": "datetime",
         "default": tm["facility_return_dt"] or None,
         "help": "Havalimanından/otogardan Florya'ya döndüğünüz saat. Bilmiyorsanız boş bırakın."},
        {"key": "work_end_dt", "label": "Gerçek iş bitişi", "kind": "datetime",
         "default": work_end,
         "help": "Malzeme teslimi, sayım, yıkama/düzenleme vb. bittikten sonra tesisten gerçekten çıktığınız saat."},
        {"key": "origin", "label": "Çıkış", "default": _r(row, "origin", "İstanbul") or "İstanbul"},
        {"key": "post_return_florya", "label": "Dönüşte Florya'da çalışma oldu mu?", "kind": "tri",
         "default": _r(row, "post_return_florya")},
        {"key": "post_return_work", "label": "Dönüş sonrası yapılan iş", "kind": "text",
         "default": _r(row, "post_return_work", "")},
        {"key": "notes", "label": "Not", "kind": "text", "default": tm["notes"]},
    ]
'''
s = s[:start] + new_block + s[end:]
p.write_text(s, "utf-8")

# ---------- UI payload, table and automatic raw duration ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

# payload: real work end is separate; match date remains only internal placeholder if unknown.
s = s.replace(
    'end_dt = v.get("return_dt") or match_date',
    'end_dt = v.get("work_end_dt") or match_date'
)

old_notes = '''            "notes": build_trip_notes(
                v.get("transport_type"), v.get("carrier"), v.get("service_no"), v.get("notes")
            ),'''
new_notes = '''            "notes": build_trip_notes(
                v.get("transport_type"), v.get("carrier"), v.get("service_no"), v.get("notes"),
                v.get("season"), v.get("team"), v.get("competition"),
                v.get("return_arrival_dt"), v.get("facility_return_dt")
            ),'''
if old_notes not in s:
    raise SystemExit("v1.2.4 build_trip_notes payload block not found")
s = s.replace(old_notes, new_notes, 1)

# clearer form help
s = s.replace(
    'intro="Tarih, şehir ve rakip/görev yeterli. Gidiş-dönüş saatlerini bilmiyorsanız boş bırakın."',
    'intro="Maç tarihi ayrı tutulur. Gidiş, İstanbul dönüşü, tesise dönüş ve gerçek iş bitişi yalnız biliyorsanız girilir."'
)
s = s.replace(
    'intro="Sadece bildiğiniz alanları doldurun; eksik saatleri daha sonra delillerle tamamlayabilirsiniz."',
    'intro="Sadece bildiğiniz gerçek saatleri doldurun. Boş alanlara program maç tarihini saatmiş gibi göstermeyecek."'
)

old_table = '''        self.trip_table = make_table(
            ["Kayıt", "Maç / Görev Tarihi", "Şehir", "Rakip / Görev", "Ulaşım", "Firma", "Gidiş", "Dönüş / Bitiş", "Delil", "Durum"],
            [90, 125, 110, 240, 90, 145, 135, 135, 65, 100]
        )'''
new_table = '''        self.trip_table = make_table(
            ["Kayıt", "Maç Tarihi", "Takım", "Şehir", "Rakip / Görev", "Ulaşım", "Firma",
             "Gidiş", "İstanbul'a Dönüş", "İş Bitişi", "Görev Süresi", "Delil", "Durum"],
            [88, 105, 75, 100, 210, 80, 120, 135, 145, 135, 105, 55, 90]
        )'''
if old_table not in s:
    raise SystemExit("v1.2.4 trip table block not found")
s = s.replace(old_table, new_table, 1)

# Replace current simple refresh with explicit placeholder handling and elapsed duration.
a = s.index("    def refresh_events_page(self):")
b = s.index("    # ================================================================ talepler / hesap", a)
new_refresh = r'''    def refresh_events_page(self):
        from datetime import datetime

        def manual_value(raw, event_raw):
            if not raw:
                return None
            txt = str(raw).strip()
            evtxt = str(event_raw or "").strip()
            # Seed kayıtlarında trip start/end maç tarihidir; kullanıcı saati değildir.
            if len(txt) <= 10 and evtxt and txt[:10] == evtxt[:10]:
                return None
            return raw

        def elapsed_text(start_raw, end_raw):
            if not start_raw or not end_raw:
                return "—"
            try:
                a = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
                b = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
                minutes = int((b - a).total_seconds() // 60)
                if minutes < 0:
                    return "—"
                h, m = divmod(minutes, 60)
                return f"{h} sa {m:02d} dk"
            except Exception:
                return "—"

        rows = []
        q = self.trip_search.text().strip().lower() if hasattr(self, "trip_search") else ""
        include_all = self.trip_show_all.isChecked() if hasattr(self, "trip_show_all") else False
        for t in self.svc.trips(include_inactive=include_all):
            ev = self._trip_primary_event(t["code"])
            event_raw = ev["start_dt"] if ev else t["start_dt"]
            match_date = fmt(event_raw)
            city = (ev["city"] if ev else None) or t["destination"] or "—"
            title = (ev["title"] if ev else None) or t["title"] or "—"
            tm = split_trip_notes(t)
            dep = manual_value(t["start_dt"], event_raw)
            work_end = manual_value(t["end_dt"], event_raw)
            ret = tm["return_arrival_dt"] or None
            team = tm["team"] or "—"
            hay = (
                f"{match_date} {tm['season']} {team} {city} {title} "
                f"{tm['competition']} {tm['transport_type']} {tm['carrier']} {t['code']}"
            ).lower()
            if q and q not in hay:
                continue
            evidence_n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            rows.append([
                t["code"], match_date, team, city, title,
                tm["transport_type"] or "—", tm["carrier"] or "—",
                fmt(dep) if dep else "—",
                fmt(ret) if ret else "—",
                fmt(work_end) if work_end else "—",
                elapsed_text(dep, work_end),
                str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])
        fill_table(self.trip_table, rows)
        if hasattr(self, "event_table"):
            self._fill_events_table(self.event_table, include_all=include_all)

'''
s = s[:a] + new_refresh + s[b:]
p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v124_trip_times.py").write_text(r'''from iscilik_dosyasi.ui_dialogs import (
    build_trip_notes, simple_trip_fields, split_trip_notes
)


def test_trip_form_has_separate_real_times_and_team():
    row = {"start_dt": "2022-10-26", "end_dt": "2022-10-26", "notes": "[KAYIT] Sezon: 2022/23\n[KAYIT] Takım: U17"}
    ev = {"start_dt": "2022-10-26", "title": "Trabzonspor – Galatasaray", "city": "Trabzon"}
    fields = simple_trip_fields(row, ev)
    by_key = {x["key"]: x for x in fields}
    assert by_key["team"]["default"] == "U17"
    assert by_key["season"]["default"] == "2022/23"
    assert by_key["departure_dt"]["default"] is None
    assert by_key["work_end_dt"]["default"] is None
    labels = [x["label"] for x in fields]
    assert "İstanbul'a dönüş / varış" in labels
    assert "Tesise dönüş (varsa)" in labels
    assert "Gerçek iş bitişi" in labels


def test_trip_note_metadata_roundtrip():
    raw = build_trip_notes(
        "Otobüs", "KİRALIK OTOBÜS", "", "Kullanıcı notu",
        "2023/24", "U19", "Türkiye Ligi",
        "2023-11-04 02:30", "2023-11-04 03:15"
    )
    m = split_trip_notes({"notes": raw})
    assert m["transport_type"] == "Otobüs"
    assert m["carrier"] == "KİRALIK OTOBÜS"
    assert m["season"] == "2023/24"
    assert m["team"] == "U19"
    assert m["competition"] == "Türkiye Ligi"
    assert m["return_arrival_dt"] == "2023-11-04 02:30"
    assert m["facility_return_dt"] == "2023-11-04 03:15"
    assert m["notes"] == "Kullanıcı notu"
''', "utf-8")

# Seed test: metadata is written into all 43 records.
p = ROOT / "tests/test_v111_seed.py"
ts = p.read_text("utf-8")
needle = '''        assert apply_requested_match_seed(svc) == 43
        assert len(svc.trips()) == 43'''
rep = '''        assert apply_requested_match_seed(svc) == 43
        assert len(svc.trips()) == 43
        assert all("[KAYIT] Sezon:" in (r["notes"] or "") for r in svc.trips())
        assert all("[KAYIT] Takım:" in (r["notes"] or "") for r in svc.trips())'''
if needle not in ts:
    raise SystemExit("v1.2.4 seed test anchor not found")
ts = ts.replace(needle, rep, 1)
p.write_text(ts, "utf-8")

# ---------- changelog ----------
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.4 — Gerçek Gidiş/Dönüş/İş Bitişi + Takım
- Maç tarihi artık Gidiş veya İş Bitişi gibi gösterilmez; bilinmeyen saatler “—” görünür.
- Deplasman formunda Gidiş/Göreve Başlangıç, İstanbul'a Dönüş/Varış, Tesise Dönüş ve Gerçek İş Bitişi ayrı alanlardır.
- U17 / U19 / U19-PAF bilgisi hem kaydın notlarına yazılır hem Deplasmanlar tablosunda ayrı Takım sütununda görünür.
- Gidiş ve Gerçek İş Bitişi girildiğinde ham Görev Süresi otomatik hesaplanır.
- Hukuki fazla mesai hesabı için saat-saat çalışma/dinlenme kayıtları ayrıca kullanılmaya devam eder.
- Kullanıcının mevcut ulaşım, firma, sefer ve serbest notları korunur.

'''
if "## v1.2.4" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.4 real trip times/team patch applied")
