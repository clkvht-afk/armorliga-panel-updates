from pathlib import Path

ROOT = Path("work")
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

# Deliller sayfasına gerçek önizleme ekle. Eski dashboard kaldırılınca self.preview da kaybolmuştu.
old = '''        self.ev_count = QLabel("")
        self.ev_count.setObjectName("hint")
        root.addWidget(self.ev_count)
        return page
'''
new = '''        self.ev_count = QLabel("")
        self.ev_count.setObjectName("hint")
        root.addWidget(self.ev_count)
        self.preview = EvidencePreview()
        self.preview.setMinimumHeight(130)
        root.addWidget(self.preview, 1)
        return page
'''
if old not in s:
    raise SystemExit("evidence page insertion point not found")
s = s.replace(old, new, 1)

# Basit modda eski dashboard takvimi yok; yalnız var olan takvim(ler)i yenile.
old = '''        self.calendar.set_marks(marks)
        self.big_calendar.set_marks(marks)
        if marks and not getattr(self, "_calendar_positioned", False):
            last = max(d for d, k in marks.items() if k - {"TATIL"}) if any(k - {"TATIL"} for k in marks.values()) else None
            if last:
                for cal in (self.calendar, self.big_calendar):
                    cal.setCurrentPage(last.year, last.month)
                self._calendar_positioned = True
'''
new = '''        calendars = [c for c in (getattr(self, "calendar", None), getattr(self, "big_calendar", None)) if c is not None]
        for cal in calendars:
            cal.set_marks(marks)
        if marks and calendars and not getattr(self, "_calendar_positioned", False):
            last = max(d for d, k in marks.items() if k - {"TATIL"}) if any(k - {"TATIL"} for k in marks.values()) else None
            if last:
                for cal in calendars:
                    cal.setCurrentPage(last.year, last.month)
                self._calendar_positioned = True
'''
if old not in s:
    raise SystemExit("calendar block not found")
s = s.replace(old, new, 1)

p.write_text(s, "utf-8")

# Basit mod UI smoke testi: yalnız kullanıcıya açık sayfalar.
(ROOT / "tests/test_v120_public_ui.py").write_text(r'''import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from iscilik_dosyasi.service import CaseService
from iscilik_dosyasi.ui_qt import MainWindow, NAV_ITEMS


def test_public_pages_open_in_simple_mode(tmp_path):
    app = QApplication.instance() or QApplication([])
    svc = CaseService(tmp_path / "case", actor="TEST")
    try:
        w = MainWindow(svc)
        public = [key for _, _, key in NAV_ITEMS]
        assert public == ["dashboard", "events", "evidence", "calc", "reports", "settings"]
        for key in public:
            w.switch_page(key)
            app.processEvents()
        assert hasattr(w, "home_trip_table")
        assert hasattr(w, "trip_table")
        assert hasattr(w, "ev_table")
        assert hasattr(w, "preview")
    finally:
        svc.close()
''', "utf-8")

print("v1.2.0 runtime UI fix applied")
