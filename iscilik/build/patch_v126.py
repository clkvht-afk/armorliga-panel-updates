from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.6\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.6"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 6, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 6, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.6')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.6')", s)
p.write_text(s, "utf-8")

# ---------- main UI helpers / performance / summary ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

if "from PySide6.QtGui import QColor" not in s:
    s = "from PySide6.QtGui import QColor\n" + s

helpers = r'''
# ------------------------------------------------------------------ v1.2.6 helpers
def _parse_trip_dt(value):
    """Formdan/veritabanından gelen ISO veya TR tarih-saatini güvenli çözer."""
    from datetime import datetime
    if not value:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    # ISO önce.
    try:
        return datetime.fromisoformat(txt.replace("Z", "+00:00"))
    except Exception:
        pass
    for fmtx in (
        "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y", "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(txt, fmtx)
        except Exception:
            pass
    return None


def _trip_minutes(start_value, end_value):
    a = _parse_trip_dt(start_value)
    b = _parse_trip_dt(end_value)
    if not a or not b:
        return None
    minutes = int((b - a).total_seconds() // 60)
    return minutes if minutes >= 0 else None


def _minutes_label(minutes):
    if minutes is None:
        return "—"
    minutes = max(0, int(minutes))
    h, m = divmod(minutes, 60)
    return f"{h} sa {m:02d} dk"


def _overlap_minutes(a1, a2, b1, b2):
    lo = max(a1, b1)
    hi = min(a2, b2)
    if hi <= lo:
        return 0
    return int((hi - lo).total_seconds() // 60)


def _post_return_is_yes(value):
    if value in (1, True):
        return True
    return str(value or "").strip().lower() in ("1", "evet", "yes", "true")


def _has_words(text, *words):
    x = str(text or "").lower()
    return all(w.lower() in x for w in words)


'''
if "_parse_trip_dt(" not in s:
    marker = "class MainWindow"
    pos = s.index(marker)
    s = s[:pos] + helpers + s[pos:]

# Add summary bar to Deplasmanlar page.
old = '''        root.addLayout(tools)
        self.trip_table = make_table(
            ["Kayıt", "Maç Tarihi", "Takım", "Şehir", "Rakip / Görev", "Ulaşım", "Firma",
             "İş Başlangıcı", "Uçuş / Sefer", "İstanbul'a Dönüş", "İş Bitişi", "Görev Süresi", "Delil", "Durum"],
            [88, 105, 75, 100, 205, 80, 115, 135, 135, 145, 135, 105, 55, 90]
        )'''
new = '''        root.addLayout(tools)

        summary = QHBoxLayout()
        self.trip_total_work_label = QLabel("Toplam Çalışma: —")
        self.trip_overtime_label = QLabel("Fazla Mesai*: —")
        self.trip_complete_label = QLabel("Tam Kayıt: —")
        for lab in (self.trip_total_work_label, self.trip_overtime_label, self.trip_complete_label):
            lab.setStyleSheet(
                "font-weight:700;padding:7px 12px;background:#f5f8fb;"
                "border:1px solid #d8e1e8;border-radius:6px;color:#19364d;"
            )
            summary.addWidget(lab)
        self.trip_overtime_label.setToolTip(
            "Yalnız programa girilmiş çalışma/görev sürelerinin aynı haftada 45 saati aşan kısmıdır. "
            "Normal iş günleri ayrıca kayda alınmadıysa gerçek toplam fazla mesai bundan daha yüksek olabilir."
        )
        summary.addStretch(1)
        root.addLayout(summary)

        self.trip_table = make_table(
            ["Kayıt", "Maç Tarihi", "Takım", "Şehir", "Rakip / Görev", "Ulaşım", "Firma",
             "İş Başlangıcı", "Uçuş / Sefer", "İstanbul'a Dönüş", "İş Bitişi", "Net Çalışma", "Delil", "Durum"],
            [88, 105, 75, 100, 205, 80, 115, 135, 135, 145, 135, 105, 55, 90]
        )'''
if old not in s:
    raise SystemExit("v1.2.6 trip table/summary anchor not found")
s = s.replace(old, new, 1)

# Targeted refresh helper + return-work preset checkboxes.
start = s.index("    def add_trip_simple(self):")
end = s.index("    def add_evidence_simple(self", start)
replacement = r'''    def _refresh_trip_views(self):
        """Ağır refresh_all yerine yalnız ilgili ekranları yenile."""
        try:
            self.refresh_events_page()
        except Exception:
            pass
        try:
            self.refresh_simple_dashboard()
        except Exception:
            pass

    def add_trip_simple(self):
        holder = {}
        def save(v):
            trip_v, event_v = self._simple_trip_payload(v)
            code = self.svc.add_trip(trip_v)
            event_v["trip_code"] = code
            self.svc.add_event(event_v)
            holder["code"] = code
        d = FormDialog(
            "Yeni Deplasman", simple_trip_fields(), on_save=save, parent=self, width=650,
            intro="İşe başlama ile uçuş/sefer saati ayrıdır. Yalnız bildiğiniz gerçek saatleri girin; bilinmeyen alanları boş bırakın."
        )
        if self._exec(d):
            self._refresh_trip_views()
            if holder.get("code") and self.ask(
                "Deplasman kaydedildi",
                "Bu deplasmana şimdi bilet, WhatsApp veya başka bir delil eklemek ister misiniz?"
            ):
                self.add_evidence_for_trip(holder["code"])

    def edit_trip_simple(self, code):
        if not code:
            return self.info("Seçim", "Önce bir deplasman seçin.")
        t = self.svc.get("SEYAHAT", code)
        ev = self._trip_primary_event(code)
        preset_checks = {}
        preset_labels = [
            "Forma yıkama",
            "Ekipman temizliği",
            "Malzeme sayımı / düzenleme",
            "Depolama",
            "Seyahat ekipmanlarını yerleştirme",
        ]
        old_work = str(t["post_return_work"] or "")

        def save(v):
            # Hazır tikleri elle yazılan notu ezmeden ekle.
            work_text = str(v.get("post_return_work") or "").strip()
            chosen = [lab for lab, cb in preset_checks.items() if cb.isChecked()]
            parts = [work_text] if work_text else []
            low = work_text.lower()
            for lab in chosen:
                # Kullanıcının daha önce benzer ifadeyi elle yazdığı durumlarda tekrar ekleme.
                if lab == "Forma yıkama" and ("forma" in low and "yıka" in low):
                    continue
                if lab == "Ekipman temizliği" and ("ekipman" in low and "temiz" in low):
                    continue
                if lab == "Depolama" and "depo" in low:
                    continue
                if lab == "Malzeme sayımı / düzenleme" and ("sayım" in low or "düzen" in low):
                    continue
                if lab == "Seyahat ekipmanlarını yerleştirme" and ("seyahat" in low and "yerleştir" in low):
                    continue
                parts.append(lab)
            if chosen:
                v["post_return_florya"] = 1
            v["post_return_work"] = " | ".join([x for x in parts if x])

            trip_v, event_v = self._simple_trip_payload(v)
            self.svc.update_trip(code, trip_v, "Basit arayüzden düzenlendi")
            if ev:
                self.svc.update_event(ev["code"], {**event_v, "trip_code": code},
                                      "Basit arayüzden düzenlendi")
            else:
                event_v["trip_code"] = code
                self.svc.add_event(event_v)

        d = FormDialog(
            "Deplasmanı Düzenle", simple_trip_fields(t, ev), on_save=save, parent=self, width=650,
            intro="İşe başlama, uçuş/sefer, İstanbul dönüşü, tesise dönüş ve gerçek iş bitişi ayrı tutulur. Yalnız bildiğiniz saatleri girin."
        )

        # Dönüş işi hazır tikleri: formun altına eklenir.
        box = QWidget()
        vb = QVBoxLayout(box)
        vb.setContentsMargins(0, 6, 0, 6)
        title = QLabel("Hazır dönüş işleri — yaptıklarını tikle:")
        title.setStyleSheet("font-weight:700;color:#23445c;")
        vb.addWidget(title)
        for row_labels in (preset_labels[:3], preset_labels[3:]):
            hb = QHBoxLayout()
            for lab in row_labels:
                cb = QCheckBox(lab)
                if lab == "Forma yıkama":
                    cb.setChecked(_has_words(old_work, "forma") and ("yıka" in old_work.lower()))
                elif lab == "Ekipman temizliği":
                    cb.setChecked(_has_words(old_work, "ekipman") and ("temiz" in old_work.lower()))
                elif lab == "Depolama":
                    cb.setChecked("depo" in old_work.lower())
                elif lab == "Malzeme sayımı / düzenleme":
                    cb.setChecked("sayım" in old_work.lower() or "düzen" in old_work.lower())
                elif lab == "Seyahat ekipmanlarını yerleştirme":
                    cb.setChecked("seyahat" in old_work.lower() and "yerleştir" in old_work.lower())
                preset_checks[lab] = cb
                hb.addWidget(cb)
            hb.addStretch(1)
            vb.addLayout(hb)
        try:
            lay = d.layout()
            lay.insertWidget(max(0, lay.count() - 1), box)
        except Exception:
            pass

        if self._exec(d):
            self._refresh_trip_views()

'''
s = s[:start] + replacement + s[end:]

# Evidence flow: don't refresh entire application for every click.
s = s.replace("            self.refresh_all()\n            if holder.get(\"code\"):", "            self._refresh_trip_views()\n            if holder.get(\"code\"):", 1)
s = s.replace("                self.refresh_all()\n                return self.info(\"Belge zaten vardı\",", "                self._refresh_trip_views()\n                return self.info(\"Belge zaten vardı\",", 1)

# Fast event-page refresh with correct TR datetime parsing, rest deduction, weekly 45h view, green complete rows.
a = s.index("    def refresh_events_page(self):")
b = s.index("    # ================================================================ talepler / hesap", a)
new_refresh = r'''    def refresh_events_page(self):
        from datetime import timedelta

        def manual_value(raw, event_raw):
            if not raw:
                return None
            txt = str(raw).strip()
            evtxt = str(event_raw or "").strip()
            # Seed kayıtlarında yalnız maç tarihi varsa bunu gerçek saat sayma.
            if len(txt) <= 10 and evtxt and txt[:10] == evtxt[:10]:
                return None
            return raw

        def rest_minutes_for_trip(code, work_start, work_end):
            """Yalnız kullanıcı tarafından açıkça dinlenme/uyku girilmiş süreleri düşer."""
            if not work_start or not work_end:
                return 0
            total = 0
            try:
                segs = self.svc.segments(code)
            except Exception:
                return 0
            for r in segs:
                if r["status"] != "AKTIF" or not r["is_rest"]:
                    continue
                sa = _parse_trip_dt(r["start_dt"])
                sb = _parse_trip_dt(r["end_dt"])
                if sa and sb and sb > sa:
                    total += _overlap_minutes(work_start, work_end, sa, sb)
            return total

        # OPTİMİZASYON: her satırda bütün olayları tekrar tekrar çekmek yerine bir kez çek.
        all_events = list(self.svc.events(include_inactive=True))
        event_by_trip = {}
        for e in all_events:
            tc = e["trip_code"]
            if not tc:
                continue
            old = event_by_trip.get(tc)
            preferred = e["event_type"] in ("Maç", "Turnuva", "Görev / Program")
            old_preferred = old is not None and old["event_type"] in ("Maç", "Turnuva", "Görev / Program")
            if old is None or (preferred and not old_preferred):
                event_by_trip[tc] = e

        q = self.trip_search.text().strip().lower() if hasattr(self, "trip_search") else ""
        include_all = self.trip_show_all.isChecked() if hasattr(self, "trip_show_all") else False
        trips = list(self.svc.trips(include_inactive=include_all))

        rows = []
        complete_flags = []
        total_work_minutes = 0
        complete_count = 0
        weekly_minutes = {}

        for t in trips:
            ev = event_by_trip.get(t["code"])
            event_raw = ev["start_dt"] if ev else t["start_dt"]
            match_date = fmt(event_raw)
            city = (ev["city"] if ev else None) or t["destination"] or "—"
            title = (ev["title"] if ev else None) or t["title"] or "—"
            tm = split_trip_notes(t)

            dep = manual_value(t["start_dt"], event_raw)
            work_start_raw = tm["work_start_dt"] or None
            work_end_raw = manual_value(t["end_dt"], event_raw)
            ret = tm["return_arrival_dt"] or None
            facility = tm["facility_return_dt"] or None
            team = tm["team"] or "—"

            work_start = _parse_trip_dt(work_start_raw)
            work_end = _parse_trip_dt(work_end_raw)
            gross = _trip_minutes(work_start_raw, work_end_raw)
            rest = rest_minutes_for_trip(t["code"], work_start, work_end) if gross is not None else 0
            net = max(0, gross - rest) if gross is not None else None

            if t["status"] == "AKTIF" and net is not None:
                total_work_minutes += net

                # Haftalık 45 saat görünümü: yalnız programa girilmiş süreler üzerinden.
                # Çalışma aralığını hafta sınırlarında böl, açıkça girilmiş dinlenmeyi ayrıca düş.
                cur = work_start
                while cur and work_end and cur < work_end:
                    monday = (cur - timedelta(days=cur.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                    next_week = monday + timedelta(days=7)
                    chunk_end = min(work_end, next_week)
                    chunk_minutes = int((chunk_end - cur).total_seconds() // 60)
                    chunk_rest = 0
                    try:
                        for sr in self.svc.segments(t["code"]):
                            if sr["status"] != "AKTIF" or not sr["is_rest"]:
                                continue
                            sa = _parse_trip_dt(sr["start_dt"])
                            sb = _parse_trip_dt(sr["end_dt"])
                            if sa and sb and sb > sa:
                                chunk_rest += _overlap_minutes(cur, chunk_end, sa, sb)
                    except Exception:
                        pass
                    weekly_minutes[monday.date().isoformat()] = weekly_minutes.get(monday.date().isoformat(), 0) + max(0, chunk_minutes - chunk_rest)
                    cur = chunk_end

            transport = tm["transport_type"] or ""
            carrier_needed = transport in ("Uçak", "Otobüs", "Tren")
            post_yes = _post_return_is_yes(t["post_return_florya"])
            complete = bool(
                team != "—" and city != "—" and title != "—"
                and transport
                and (not carrier_needed or tm["carrier"])
                and work_start_raw and dep and ret and work_end_raw
                and (not post_yes or (facility and str(t["post_return_work"] or "").strip()))
            )
            if complete and t["status"] == "AKTIF":
                complete_count += 1

            hay = (
                f"{match_date} {tm['season']} {team} {city} {title} "
                f"{tm['competition']} {transport} {tm['carrier']} "
                f"{work_start_raw or ''} {dep or ''} {t['code']}"
            ).lower()
            if q and q not in hay:
                continue

            # Delil sayısı bağımsız kalır; olay taraması artık satır başına tekrarlanmıyor.
            evidence_n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            rows.append([
                t["code"], match_date, team, city, title,
                transport or "—", tm["carrier"] or "—",
                fmt(work_start_raw) if work_start_raw else "—",
                fmt(dep) if dep else "—",
                fmt(ret) if ret else "—",
                fmt(work_end_raw) if work_end_raw else "—",
                _minutes_label(net),
                str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])
            complete_flags.append(complete)

        fill_table(self.trip_table, rows)

        # Tam doldurulmuş satır komple yeşil.
        for rr, ok in enumerate(complete_flags):
            if not ok:
                continue
            for cc in range(self.trip_table.columnCount()):
                item = self.trip_table.item(rr, cc)
                if item is not None:
                    item.setBackground(QColor("#dcfce7"))
                    item.setForeground(QColor("#14532d"))

        overtime_minutes = sum(max(0, mins - 45 * 60) for mins in weekly_minutes.values())
        if hasattr(self, "trip_total_work_label"):
            self.trip_total_work_label.setText(f"Toplam Çalışma: {_minutes_label(total_work_minutes)}")
            self.trip_overtime_label.setText(f"Fazla Mesai*: {_minutes_label(overtime_minutes)}")
            active_n = sum(1 for t in trips if t["status"] == "AKTIF")
            self.trip_complete_label.setText(f"Tam Kayıt: {complete_count} / {active_n}")

        if hasattr(self, "event_table"):
            self._fill_events_table(self.event_table, include_all=include_all)

'''
s = s[:a] + new_refresh + s[b:]

# Dashboard event lookups: build one map, not a full event scan for every trip.
old = '''        rows = []
        trips = list(self.svc.trips())[-10:][::-1]
        for t in trips:
            ev = self._trip_primary_event(t["code"])
            d = fmt(ev["start_dt"] if ev else t["start_dt"])'''
new = '''        rows = []
        all_events = list(self.svc.events(include_inactive=True))
        event_by_trip = {}
        for e in all_events:
            if e["trip_code"] and e["trip_code"] not in event_by_trip:
                event_by_trip[e["trip_code"]] = e
            if e["trip_code"] and e["event_type"] in ("Maç", "Turnuva", "Görev / Program"):
                event_by_trip[e["trip_code"]] = e
        trips = list(self.svc.trips())[-10:][::-1]
        for t in trips:
            ev = event_by_trip.get(t["code"])
            d = fmt(ev["start_dt"] if ev else t["start_dt"])'''
if old not in s:
    raise SystemExit("v1.2.6 dashboard optimization anchor not found")
s = s.replace(old, new, 1)

p.write_text(s, "utf-8")

# ---------- SegmentEditor: targeted refresh instead of refresh_all ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")
s = s.replace(
    "            self.host.refresh_all()",
    "            getattr(self.host, '_refresh_trip_views', self.host.refresh_all)()"
)
p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v126_perf_totals.py").write_text(r'''from iscilik_dosyasi.ui_qt import _parse_trip_dt, _trip_minutes, _minutes_label


def test_turkish_datetime_and_samsun_45_hours():
    assert _parse_trip_dt("01.05.2026 08:00") is not None
    assert _parse_trip_dt("03.05.2026 05:00") is not None
    mins = _trip_minutes("01.05.2026 08:00", "03.05.2026 05:00")
    assert mins == 45 * 60
    assert _minutes_label(mins) == "45 sa 00 dk"


def test_iso_datetime_still_supported():
    assert _trip_minutes("2026-05-01 08:00", "2026-05-01 16:00") == 8 * 60
''', "utf-8")

# ---------- changelog ----------
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.6 — Hız + Çalışma Toplamı + Tam Kayıt
- Deplasman ekranında satır başına tüm olay listesini tekrar tarayan ağır akış kaldırıldı; olaylar tek seferde eşlenir.
- Deplasman/zaman düzenlemelerinde tüm programı refresh_all ile baştan yenilemek yerine ilgili ekranlar yenilenir.
- DD.MM.YYYY SS:DD biçimi doğru hesaplanır; 01.05.2026 08:00 → 03.05.2026 05:00 artık 45 saat gösterir.
- İş başlangıcı → gerçek iş bitişi arasından, kullanıcının açıkça girdiği uyku/dinlenme süreleri düşülerek Net Çalışma gösterilir.
- Deplasman ekranında Toplam Çalışma, girilmiş kayıtlara göre haftalık 45 saat üzeri Fazla Mesai ve Tam Kayıt sayısı canlı görünür.
- Forma yıkama, ekipman temizliği, malzeme sayımı/düzenleme, depolama ve seyahat ekipmanlarını yerleştirme için hazır tikler eklendi.
- Ulaşım ve temel saat alanları tamamlanmış satırın tamamı yeşil görünür.

'''
if "## v1.2.6" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.6 optimization, totals, presets and completion color applied")
