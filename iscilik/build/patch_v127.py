from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.7\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.7"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 7, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 7, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.7')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.7')", s)
p.write_text(s, "utf-8")

# ---------- UI performance architecture ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

# 1) Replace switch_page: NEVER refresh the entire application just because the user changes pages.
m = re.search(r"(?m)^    def switch_page\(self, key\):.*?(?=^    def |\Z)", s, re.S)
if not m:
    raise SystemExit("v1.2.7 switch_page not found")

new_switch = r'''    def _refresh_page_only(self, key, force=False):
        """Refresh only one page. Page-to-page navigation must never call refresh_all."""
        loaded = getattr(self, "_page_loaded", set())
        dirty = getattr(self, "_page_dirty", set())
        if not force and key in loaded and key not in dirty:
            return

        if key == "dashboard":
            self.refresh_simple_dashboard()
        elif key == "evidence":
            # Event dropdowns only matter on the evidence page.
            self._fill_event_filters()
            self.refresh_evidence_page()
        elif key == "events":
            self.refresh_events_page()
        elif key == "timeline":
            self.refresh_calendars()
            self.refresh_chrono(self.chrono_table)
        elif key == "calc":
            self.refresh_calc_page()
        elif key == "legal":
            self.refresh_legal_page()
        elif key == "reports":
            self.refresh_reports_page()
        elif key == "notes":
            self.notes_edit.setPlainText(self.svc.profile()["notes"] or "")
        elif key == "settings":
            self.refresh_settings_page()

        loaded.add(key)
        dirty.discard(key)
        self._page_loaded = loaded
        self._page_dirty = dirty

    def switch_page(self, key):
        if key not in self.pages:
            key = "dashboard"
        self.current_page = key

        # Önce sayfayı anında göster. Ağır veri işi yalnız sayfa ilk kez açılıyorsa
        # veya veri gerçekten değiştiyse yapılır.
        self.stack.setCurrentWidget(self.pages[key])
        for k, b in self.side_buttons.items():
            active = (k == key)
            if bool(b.property("active")) != active:
                b.setProperty("active", active)
                b.style().unpolish(b)
                b.style().polish(b)
        for k, b in self.top_buttons.items():
            active = (k == key)
            if bool(b.property("active")) != active:
                b.setProperty("active", active)
                b.style().unpolish(b)
                b.style().polish(b)

        if not hasattr(self, "_page_loaded"):
            self._page_loaded = set()
        if not hasattr(self, "_page_dirty"):
            self._page_dirty = set(self.pages.keys())

        self._refresh_page_only(key)

'''
s = s[:m.start()] + new_switch + s[m.end():]

# 2) Replace refresh_all: mutation path only; preload once and refresh current page only.
m = re.search(r"(?m)^    def refresh_all\(self\):.*?(?=^    def |\Z)", s, re.S)
if not m:
    raise SystemExit("v1.2.7 refresh_all not found")
new_refresh_all = r'''    def refresh_all(self):
        """Data changed: invalidate pages, but redraw only the page the user is on."""
        try:
            self.setWindowTitle(self._window_title())
            self._preload()
            self._page_dirty = set(self.pages.keys())
            if not hasattr(self, "_page_loaded"):
                self._page_loaded = set()

            page = getattr(self, "current_page", "dashboard")
            self._refresh_page_only(page, force=True)

            self.side_status.setText(
                f"Veri: {self.data_dir}\nŞema v{self.svc.db.schema_version} · Sürüm {__version__}"
            )
        except Exception:
            log.exception("refresh_all")
            raise

'''
s = s[:m.start()] + new_refresh_all + s[m.end():]

# 3) Targeted trip refresh: one relation preload; refresh only visible page and invalidate dependants.
m = re.search(r"(?m)^    def _refresh_trip_views\(self\):.*?(?=^    def |\Z)", s, re.S)
if not m:
    raise SystemExit("v1.2.7 _refresh_trip_views not found")
new_trip_refresh = r'''    def _refresh_trip_views(self):
        """Trip/time data changed without globally rebuilding every screen."""
        try:
            self._preload()
        except Exception:
            pass
        dirty = getattr(self, "_page_dirty", set())
        dirty.update(("dashboard", "events", "evidence", "calc", "reports"))
        self._page_dirty = dirty
        page = getattr(self, "current_page", "events")
        if page in ("dashboard", "events", "evidence", "calc", "reports"):
            self._refresh_page_only(page, force=True)

'''
s = s[:m.start()] + new_trip_refresh + s[m.end():]

# 4) Bulk-load timeline segments once on Deplasmanlar page.
# Replace the per-trip helper's DB query with a grouped cache.
old = '''        def rest_minutes_for_trip(code, work_start, work_end):
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
        all_events = list(self.svc.events(include_inactive=True))'''
new = '''        # Timeline kayıtlarını 43+ ayrı SQL sorgusuyla değil TEK sorguyla yükle.
        segments_by_trip = {}
        for sr in self.svc.segments():
            segments_by_trip.setdefault(sr["trip_code"], []).append(sr)

        def rest_minutes_for_trip(code, work_start, work_end):
            """Yalnız kullanıcı tarafından açıkça dinlenme/uyku girilmiş süreleri düşer."""
            if not work_start or not work_end:
                return 0
            total = 0
            for r in segments_by_trip.get(code, ()):
                if r["status"] != "AKTIF" or not r["is_rest"]:
                    continue
                sa = _parse_trip_dt(r["start_dt"])
                sb = _parse_trip_dt(r["end_dt"])
                if sa and sb and sb > sa:
                    total += _overlap_minutes(work_start, work_end, sa, sb)
            return total

        # Olayları da tek sorguyla yükle.
        all_events = list(self.svc.events(include_inactive=True))'''
if old not in s:
    raise SystemExit("v1.2.7 rest helper anchor not found")
s = s.replace(old, new, 1)

old = '''                    try:
                        for sr in self.svc.segments(t["code"]):
                            if sr["status"] != "AKTIF" or not sr["is_rest"]:
                                continue
                            sa = _parse_trip_dt(sr["start_dt"])
                            sb = _parse_trip_dt(sr["end_dt"])
                            if sa and sb and sb > sa:
                                chunk_rest += _overlap_minutes(cur, chunk_end, sa, sb)
                    except Exception:
                        pass'''
new = '''                    for sr in segments_by_trip.get(t["code"], ()):
                        if sr["status"] != "AKTIF" or not sr["is_rest"]:
                            continue
                        sa = _parse_trip_dt(sr["start_dt"])
                        sb = _parse_trip_dt(sr["end_dt"])
                        if sa and sb and sb > sa:
                            chunk_rest += _overlap_minutes(cur, chunk_end, sa, sb)'''
if old not in s:
    raise SystemExit("v1.2.7 weekly segment anchor not found")
s = s.replace(old, new, 1)

# 5) Hidden legacy event table costs time but user never sees it.
s = s.replace(
'''        if hasattr(self, "event_table"):
            self._fill_events_table(self.event_table, include_all=include_all)
''',
'''        if hasattr(self, "event_table") and self.event_table.isVisible():
            self._fill_events_table(self.event_table, include_all=include_all)
''',
1
)

# 6) Search input: avoid rebuilding whole table for every single key event.
old = '''        self.trip_search.textChanged.connect(self.refresh_events_page)
        tools.addWidget(self.trip_search, 1)'''
new = '''        self._trip_search_timer = QTimer(self)
        self._trip_search_timer.setSingleShot(True)
        self._trip_search_timer.setInterval(120)
        self._trip_search_timer.timeout.connect(self.refresh_events_page)
        self.trip_search.textChanged.connect(lambda _text: self._trip_search_timer.start())
        tools.addWidget(self.trip_search, 1)'''
if old not in s:
    raise SystemExit("v1.2.7 search debounce anchor not found")
s = s.replace(old, new, 1)

p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v127_navigation_perf.py").write_text(r'''import inspect
from iscilik_dosyasi.ui_qt import MainWindow


def test_page_switch_does_not_global_refresh():
    src = inspect.getsource(MainWindow.switch_page)
    assert "refresh_all()" not in src
    assert "_refresh_page_only" in src


def test_events_page_bulk_loads_segments():
    src = inspect.getsource(MainWindow.refresh_events_page)
    assert "self.svc.segments()" in src
    assert 'self.svc.segments(t["code"])' not in src
    assert "segments_by_trip" in src


def test_refresh_all_only_redraws_current_page():
    src = inspect.getsource(MainWindow.refresh_all)
    assert "_refresh_page_only(page, force=True)" in src
    assert "refresh_cards()" not in src
''', "utf-8")

# ---------- changelog ----------
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.7 — Akıcı Sayfa Geçişi
- Sayfa değiştirirken çalışan global refresh_all tamamen kaldırıldı.
- Her sayfa yalnız ilk açılışta veya verisi gerçekten değiştiğinde yenilenir; geri-dönüşlerde önbellekteki ekran anında gösterilir.
- Veri değişikliklerinde bütün uygulama yerine yalnız açık olan sayfa yeniden çizilir.
- Deplasman ekranındaki timeline/dinlenme kayıtları 43+ ayrı sorgu yerine tek sorguda toplu yüklenir.
- Gizli legacy olay tablosu artık gereksiz yere doldurulmaz.
- Deplasman araması 120 ms debounce ile çalışır; her tuş vuruşunda ağır tablo yenilemez.

'''
if "## v1.2.7" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.7 navigation and query performance patch applied")
