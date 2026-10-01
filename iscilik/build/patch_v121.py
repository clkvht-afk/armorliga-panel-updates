from pathlib import Path
import re

ROOT = Path("work")

# ---------------- version ----------------
(ROOT / "VERSION").write_text("1.2.1\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.1"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 1, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 1, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.1')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.1')", s)
p.write_text(s, "utf-8")

# ---------------- simple segment form ----------------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")

if "def simple_segment_fields" not in s:
    anchor = "# ------------------------------------------------------------------ talep\n"
    simple = r'''
SIMPLE_SEGMENT_TYPES = [
    "Florya'da kafileye katılım",
    "Takım otobüsü ile havalimanı",
    "Havalimanında zorunlu bekleme",
    "Uçuş",
    "Gece uçuşu",
    "Yurtdışı / şehir içi transfer",
    "Otele giriş",
    "Gerçek serbest dinlenme",
    "Uyku / otel gecesi",
    "Antrenmana yolculuk",
    "Antrenman / görev",
    "Maç hazırlığı",
    "Maç görevi",
    "Zorunlu takım programı",
    "Havalimanına transfer",
    "Havalimanı → Florya",
    "Florya'da malzeme yıkama / sayma / düzenleme / depolama",
    "Gerçek görev bitişi",
    "Diğer",
]


def simple_segment_fields(row=None) -> list[dict]:
    """Kullanıcının günlük olarak dolduracağı sade zaman kaydı."""
    stype = _r(row, "segment_type", "Uçuş")
    if stype not in SIMPLE_SEGMENT_TYPES:
        SIMPLE_SEGMENT_TYPES.append(stype)
    return [
        {"key": "start_dt", "label": "Başlangıç", "kind": "datetime",
         "default": _r(row, "start_dt"), "required": True,
         "help": "Gerçek tarih ve saati girin."},
        {"key": "end_dt", "label": "Bitiş", "kind": "datetime",
         "default": _r(row, "end_dt"), "required": True,
         "help": "Gece yarısını geçiyorsa ertesi günün tarihini seçin."},
        {"key": "segment_type", "label": "Bu sürede ne yapıyordum?", "kind": "combo",
         "options": SIMPLE_SEGMENT_TYPES, "default": stype, "editable": True, "required": True},
        {"key": "location", "label": "Yer (isteğe bağlı)",
         "default": _r(row, "location", ""),
         "placeholder": "Örn. İstanbul Havalimanı / Trabzon / Florya"},
        {"key": "description", "label": "Kısa not (isteğe bağlı)", "kind": "text",
         "default": _r(row, "description", ""),
         "placeholder": "Örn. Maç sonrası havalimanına geçildi."},
    ]


'''
    if anchor not in s:
        raise SystemExit("simple segment insertion anchor not found")
    s = s.replace(anchor, simple + anchor, 1)

# Replace SegmentEditor init/refresh/add/edit with simplified user-facing flow while preserving service/audit data.
start = s.index("class SegmentEditor(QDialog):")
end = s.index("\n\n# ------------------------------------------------------------------", start)
old_class = s[start:end]

new_class = r'''class SegmentEditor(QDialog):
    def __init__(self, svc, trip_code: str, host, parent=None):
        super().__init__(parent)
        self.svc, self.trip_code, self.host = svc, trip_code, host
        t = svc.require("SEYAHAT", trip_code)
        self.setWindowTitle(f"Saatleri Gir – {t['title']}")
        self.resize(980, 640)
        v = QVBoxLayout(self)

        head = QLabel(
            f"<b>{t['title']}</b><br>"
            "Buraya yalnız bildiğiniz zamanları girin: uçuş, bekleme, maç görevi, Florya işi veya gerçek dinlenme."
        )
        head.setWordWrap(True)
        v.addWidget(head)

        tb = QHBoxLayout()
        for text, fn in [
            ("+ Zaman Ekle", self.add),
            ("✎ Düzenle", self.edit),
            ("❐ Sonrasına Kopyala", self.duplicate),
            ("▣ Delil Bağla", self.relations),
            ("⊘ Kaydı İptal Et", self.cancel),
        ]:
            b = QPushButton(text)
            b.setObjectName("primaryBtn" if text.startswith("+") else "softBtn")
            b.clicked.connect(lambda _=False, f=fn: f())
            tb.addWidget(b)
        tb.addStretch(1)
        v.addLayout(tb)

        self.show_inactive = QPushButton("İptal edilenleri göster")
        self.show_inactive.setCheckable(True)
        self.show_inactive.toggled.connect(self.refresh)
        v.addWidget(self.show_inactive)

        self.table = make_table(
            ["Kod", "Başlangıç", "Bitiş", "Süre", "Ne yapıyordum?", "Yer", "Delil", "Durum"],
            [92, 135, 135, 80, 310, 170, 90, 80]
        )
        self.table.doubleClicked.connect(self.edit)
        v.addWidget(self.table, 1)

        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(
            "background:#f5f8fb;border:1px solid #d8e1e8;border-radius:6px;padding:10px;color:#334e63;"
        )
        v.addWidget(self.summary)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.button(QDialogButtonBox.StandardButton.Close).setText("Kapat")
        bb.rejected.connect(self.accept)
        v.addWidget(bb)
        self.refresh()

    def _primary_event_code(self):
        events = [e for e in self.svc.events() if e["trip_code"] == self.trip_code]
        for e in events:
            if e["event_type"] == "Maç":
                return e["code"]
        return events[0]["code"] if events else None

    def _payload(self, v, old=None):
        rest = v.get("segment_type") in REST_LIKE_SEGMENT_TYPES
        old_legal = old["legal_class"] if old is not None else None
        if rest:
            legal = "DINLENME"
        elif old_legal in ("AVUKAT_ONAYLI", "HARIC"):
            legal = old_legal
        else:
            legal = "INCELENECEK"

        return {
            "trip_code": self.trip_code,
            "event_code": (old["event_code"] if old is not None else None) or self._primary_event_code(),
            "start_dt": v.get("start_dt"),
            "end_dt": v.get("end_dt"),
            "segment_type": v.get("segment_type"),
            "location": v.get("location"),
            "mandatory": 0 if rest else 1,
            "employer_ordered": 0 if rest else 1,
            "is_rest": 1 if rest else 0,
            "legal_class": legal,
            "verification_level": old["verification_level"] if old is not None else "KULLANICI_BEYANI",
            "description": v.get("description"),
            "internal_notes": old["internal_notes"] if old is not None else None,
        }

    def refresh(self):
        from .analysis import seg_from_row
        rows = []
        active = 0
        total_hours = 0.0
        documented = 0
        for r in self.svc.segments(self.trip_code, include_inactive=self.show_inactive.isChecked()):
            seg = seg_from_row(r)
            ev = self.svc.related_codes("SEGMENT", r["code"], "DELIL")
            hrs = seg.hours if seg else 0
            if r["status"] == "AKTIF":
                active += 1
                total_hours += hrs
                if ev:
                    documented += 1
            rows.append([
                r["code"], fmt(r["start_dt"]), fmt(r["end_dt"]),
                hours_str(hrs) if seg else "?", r["segment_type"],
                r["location"] or "—", ", ".join(ev) or "—", r["status"]
            ])
        fill_table(self.table, rows)
        if active:
            self.summary.setText(
                f"Girilen {active} zaman kaydı var. Toplam ham süre: {hours_str(total_hours)}. "
                f"{documented} kayda delil bağlanmış. Hukuki değerlendirme ve doğrulama bilgileri arka planda korunur."
            )
        else:
            self.summary.setText(
                "Henüz saat girilmemiş. Saatleri bilmiyorsanız boş bırakmanız sorun değil; bilet, WhatsApp veya program buldukça ekleyebilirsiniz."
            )

    def _sel(self):
        return selected_key(self.table, 0)

    def add(self, prefill=None):
        d = FormDialog(
            "Yeni Zaman Kaydı",
            simple_segment_fields(prefill),
            on_save=lambda v: self.svc.add_segment(self._payload(v)),
            parent=self,
            intro="Sadece başlangıç, bitiş ve o sırada ne yaptığınızı yazın. Diğer teknik alanları program arkada yönetir."
        )
        if self.host._exec(d):
            self.refresh()
            self.host.refresh_all()

    def edit(self):
        code = self._sel()
        if not code:
            return self.host.info("Seçim", "Önce bir zaman kaydı seçin.")
        r = self.svc.get("SEGMENT", code)
        d = FormDialog(
            f"Zaman Kaydını Düzenle – {code}",
            simple_segment_fields(r),
            on_save=lambda v, reason: self.svc.update_segment(code, self._payload(v, r), reason),
            parent=self, reason=True,
            intro="Yalnız gördüğünüz alanları düzenleyin. Teknik doğrulama ve hukuki sınıflandırma bilgileri korunur."
        )
        if self.host._exec(d):
            self.refresh()
            self.host.refresh_all()

    def duplicate(self):
        code = self._sel()
        if not code:
            return self.host.info("Seçim", "Önce bir zaman kaydı seçin.")
        r = dict(self.svc.get("SEGMENT", code))
        pre = {
            "start_dt": r["end_dt"],
            "end_dt": None,
            "segment_type": r["segment_type"],
            "location": r["location"],
            "description": r["description"],
        }
        self.add(prefill=pre)

    def relations(self):
        code = self._sel()
        if not code:
            return self.host.info("Seçim", "Önce bir zaman kaydı seçin.")
        self.host._exec(RelationsDialog(self.svc, "SEGMENT", code, self.host, self))
        self.refresh()

    def cancel(self):
        code = self._sel()
        if not code:
            return self.host.info("Seçim", "Önce bir zaman kaydı seçin.")
        reason = self.host.reason("Zaman kaydını iptal et", "İptal nedeni:")
        if reason:
            self.svc.set_status("SEGMENT", code, "İPTAL", reason)
            self.refresh()
            self.host.refresh_all()

    def reactivate(self):
        code = self._sel()
        if not code:
            return self.host.info("Seçim", "Önce bir zaman kaydı seçin.")
        reason = self.host.reason("Zaman kaydını geri al", "Geri alma nedeni:")
        if reason:
            self.svc.set_status("SEGMENT", code, "AKTIF", reason)
            self.refresh()
            self.host.refresh_all()
'''

s = s[:start] + new_class + s[end:]
p.write_text(s, "utf-8")

# ---------------- UI wording ----------------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")
s = s.replace('"Saat Saat Çalışma / Yol"', '"Saatleri Gir"')
p.write_text(s, "utf-8")

# ---------------- tests ----------------
(ROOT / "tests/test_v121_simple_segment.py").write_text(r'''import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from iscilik_dosyasi.service import CaseService
from iscilik_dosyasi.ui_dialogs import simple_segment_fields, SIMPLE_SEGMENT_TYPES
from iscilik_dosyasi.ui_qt import MainWindow


def test_simple_segment_fields_hide_technical_choices():
    labels = [x["label"] for x in simple_segment_fields()]
    joined = " ".join(labels)
    assert "İlgili olay" not in joined
    assert "Zorunlu mu" not in joined
    assert "İşveren emri" not in joined
    assert "Hukuki sınıflandırma" not in joined
    assert "Doğrulama seviyesi" not in joined
    assert "Gerçek dinlenme" not in joined
    assert labels == ["Başlangıç", "Bitiş", "Bu sürede ne yapıyordum?", "Yer (isteğe bağlı)", "Kısa not (isteğe bağlı)"]
    assert "Uçuş" in SIMPLE_SEGMENT_TYPES
    assert "Maç görevi" in SIMPLE_SEGMENT_TYPES
    assert "Florya'da malzeme yıkama / sayma / düzenleme / depolama" in SIMPLE_SEGMENT_TYPES


def test_simple_segment_payload_defaults(tmp_path):
    app = QApplication.instance() or QApplication([])
    svc = CaseService(tmp_path / "case", actor="TEST")
    try:
        trip = svc.add_trip({
            "title": "Trabzonspor – Galatasaray", "start_dt": "2022-10-26",
            "end_dt": "2022-10-26", "destination": "Trabzon",
            "verification_level": "KULLANICI_BEYANI"
        })
        ev = svc.add_event({
            "title": "Trabzonspor – Galatasaray", "event_type": "Maç",
            "start_dt": "2022-10-26", "end_dt": "2022-10-26",
            "trip_code": trip, "city": "Trabzon",
            "verification_level": "KULLANICI_BEYANI"
        })
        w = MainWindow(svc)
        from iscilik_dosyasi.ui_dialogs import SegmentEditor
        d = SegmentEditor(svc, trip, w)
        work = d._payload({
            "start_dt": "2022-10-26 10:00", "end_dt": "2022-10-26 11:00",
            "segment_type": "Uçuş", "location": "İstanbul", "description": ""
        })
        assert work["trip_code"] == trip
        assert work["event_code"] == ev
        assert work["mandatory"] == 1
        assert work["employer_ordered"] == 1
        assert work["is_rest"] == 0
        assert work["legal_class"] == "INCELENECEK"
        assert work["verification_level"] == "KULLANICI_BEYANI"

        rest = d._payload({
            "start_dt": "2022-10-26 23:00", "end_dt": "2022-10-27 07:00",
            "segment_type": "Uyku / otel gecesi", "location": "Otel", "description": ""
        })
        assert rest["mandatory"] == 0
        assert rest["employer_ordered"] == 0
        assert rest["is_rest"] == 1
        assert rest["legal_class"] == "DINLENME"
    finally:
        svc.close()
''', "utf-8")

# changelog
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.1 — Saat Girişi Sadeleştirildi
- “Yeni segment” ekranı kullanıcı için “Yeni Zaman Kaydı” olarak sadeleştirildi.
- Kullanıcı artık yalnız Başlangıç, Bitiş, “Bu sürede ne yapıyordum?”, Yer ve Kısa Not alanlarını görür.
- İlgili olay, zorunluluk, işveren programı, gerçek dinlenme bayrağı, hukuki sınıf ve doğrulama seviyesi arka planda yönetilir.
- Dinlenme türleri otomatik DINLENME olarak, diğer kayıtlar hukuken İNCELENECEK olarak açılır; hiçbir çalışma süresi otomatik hukuki hüküm sayılmaz.
- Zaman çizelgesi tablosu da sadeleştirildi.

'''
if "## v1.2.1" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.1 simple segment patch applied")
