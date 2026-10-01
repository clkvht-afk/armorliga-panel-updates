from pathlib import Path
import re

ROOT = Path("work")

# ---------- version ----------
(ROOT / "VERSION").write_text("1.2.0\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text("utf-8")
s = re.sub(r'__version__\s*=\s*"[^"]+"', '__version__ = "1.2.0"', s)
p.write_text(s, "utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text("utf-8")
s = re.sub(r'filevers=\([^\)]*\)', 'filevers=(1, 2, 0, 0)', s)
s = re.sub(r'prodvers=\([^\)]*\)', 'prodvers=(1, 2, 0, 0)', s)
s = re.sub(r"StringStruct\('FileVersion', '[^']+'\)", "StringStruct('FileVersion', '1.2.0')", s)
s = re.sub(r"StringStruct\('ProductVersion', '[^']+'\)", "StringStruct('ProductVersion', '1.2.0')", s)
p.write_text(s, "utf-8")

# ---------- simple form helpers ----------
p = ROOT / "iscilik_dosyasi/ui_dialogs.py"
s = p.read_text("utf-8")
if "def simple_trip_fields" not in s:
    s += r'''

# ------------------------------------------------------------------ Basit kullanıcı akışı
def simple_trip_fields(row=None, event=None) -> list[dict]:
    """Günlük kullanım için sade deplasman formu."""
    title = _r(event, "title", _r(row, "title", ""))
    if title.endswith(" – Galatasaray"):
        title = title[:-len(" – Galatasaray")]
    match_date = _r(event, "start_dt", _r(row, "start_dt"))
    return [
        {"key": "match_date", "label": "Maç / görev tarihi", "kind": "date", "default": match_date, "required": True},
        {"key": "city", "label": "Şehir", "default": _r(event, "city", _r(row, "destination", "")), "required": True,
         "placeholder": "Örn. Trabzon"},
        {"key": "opponent", "label": "Rakip / görev", "default": title, "required": True,
         "placeholder": "Örn. Trabzonspor"},
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
        {"key": "notes", "label": "Not", "kind": "text", "default": _r(row, "notes", "")},
    ]


def simple_evidence_fields(filename: str | None = None) -> list[dict]:
    """Yeni delil eklerken yalnız gerekli alanları gösterir."""
    return [
        {"key": "title", "label": "Belge adı", "default": Path(filename).stem if filename else "", "required": True},
        {"key": "evidence_type", "label": "Belge türü", "kind": "combo", "options": EVIDENCE_TYPES,
         "default": EVIDENCE_TYPES[0], "required": True},
        {"key": "source_category", "label": "Nereden geldi?", "kind": "combo", "options": SOURCE_CATEGORIES,
         "required": True, "help": "Örn. WhatsApp, Havayolu, İşveren kaydı, E-posta."},
        {"key": "evidence_date", "label": "Belge tarihi", "kind": "datetime"},
        {"key": "description", "label": "Kısa açıklama", "kind": "text", "default": ""},
    ]
'''
p.write_text(s, "utf-8")

# ---------- requested initial trips, no scores ----------
seed = '''"""Kullanıcının istediği ilk yurt içi deplasman kayıtları (skorsuz)."""
from __future__ import annotations

SEED_KEY = "requested_match_seed_20261001_simple_v2"
MATCHES = [
    ("2022-10-26", "Trabzon", "Trabzonspor – Galatasaray"),
    ("2022-11-12", "Alanya", "Alanyaspor – Galatasaray"),
    ("2022-12-07", "Konya", "Konyaspor – Galatasaray"),
    ("2022-12-10", "Adana", "Adana Demirspor – Galatasaray"),
    ("2022-12-24", "Gaziantep", "Gaziantep FK – Galatasaray"),
    ("2023-03-04", "Ankara", "MKE Ankaragücü – Galatasaray"),
    ("2023-03-15", "İzmir", "Göztepe – Galatasaray"),
]

def apply_requested_match_seed(svc) -> int:
    if svc.setting(SEED_KEY, "") == "1":
        return 0
    added = 0
    for day, city, title in MATCHES:
        row = svc.db.q1(
            "SELECT code,description FROM trips WHERE destination=? AND title=? AND status='AKTIF' LIMIT 1",
            (city, title),
        )
        if row:
            desc = row["description"] or ""
            if "Sonuç:" in desc:
                svc.update_trip(row["code"], {"description": None},
                                "Kullanıcı talebi: skor bilgisi kaldırıldı")
            continue
        trip = svc.add_trip({
            "title": title, "start_dt": day, "end_dt": day,
            "origin": "İstanbul", "destination": city, "country": "Türkiye",
            "purpose": "Deplasman", "mandatory_group": 1,
            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
            "notes": "Kullanıcının verdiği ilk deplasman listesinden işlendi; seyahat saatleri delillerle tamamlanacak.",
        })
        svc.add_event({
            "title": title, "event_type": "Maç", "start_dt": day, "end_dt": day,
            "country": "Türkiye", "city": city, "trip_code": trip,
            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
        })
        added += 1
    svc.set_setting(SEED_KEY, "1")
    return added
'''
(ROOT / "iscilik_dosyasi/requested_seed_20261001.py").write_text(seed, "utf-8")

# ---------- main UI ----------
p = ROOT / "iscilik_dosyasi/ui_qt.py"
s = p.read_text("utf-8")

s = s.replace(
'''from .ui_dialogs import (RelationsDialog, SegmentEditor, calc_detail_html, ceiling_fields, claim_fields, event_fields,
                         evidence_fields, legal_fields, split_claim_values, strip_private, trip_fields, wage_fields)''',
'''from .ui_dialogs import (RelationsDialog, SegmentEditor, calc_detail_html, ceiling_fields, claim_fields, event_fields,
                         evidence_fields, legal_fields, simple_evidence_fields, simple_trip_fields, split_claim_values,
                         strip_private, trip_fields, wage_fields)'''
)

s = re.sub(
    r'NAV_ITEMS = \[.*?\]\nTOP_ITEMS = \[.*?\]\nCLAIM_NAV =',
    '''NAV_ITEMS = [
    ("⌂", "Ana Sayfa", "dashboard"),
    ("✈", "Deplasmanlar", "events"),
    ("▣", "Deliller", "evidence"),
    ("∑", "Alacaklar", "calc"),
    ("▤", "Dosyayı Hazırla", "reports"),
    ("⚙", "Ayarlar", "settings"),
]
TOP_ITEMS = []
CLAIM_NAV =''',
    s, flags=re.S
)

# topbar
a = s.index("    def _build_topbar(self):")
b = s.index("    def _build_sidebar(self):", a)
s = s[:a] + '''    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(58)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 12, 0)
        lay.setSpacing(8)
        brand = QLabel("⚖  İşçilik Dosyası")
        self.brand_label = brand
        brand.setStyleSheet("font-size:16px;font-weight:800;color:#123b59;background:transparent;")
        lay.addWidget(brand)
        subtitle = QLabel("Delilleri ve deplasmanları tek yerde topla")
        subtitle.setStyleSheet("color:#6a7b8c;background:transparent;")
        lay.addWidget(subtitle)
        lay.addStretch(1)
        lay.addWidget(self._btn("+ Deplasman", self.add_trip_simple, "primaryBtn"))
        lay.addWidget(self._btn("+ Delil", self.add_evidence_simple, "blueBtn"))
        lay.addWidget(self._btn("Dosyayı Hazırla", lambda: self.switch_page("reports"), "darkBtn"))
        lay.addWidget(self._btn("⚙", lambda: self.switch_page("settings"), "softBtn", "Ayarlar"))
        self.top_buttons = {}
        self.pkg_buttons = {}
        self.pkg_texts = {}
        return bar

''' + s[b:]

# sidebar
a = s.index("    def _build_sidebar(self):")
b = s.index("    def _page(self, title:", a)
s = s[:a] + '''    def _build_sidebar(self):
        scroll = QScrollArea()
        scroll.setObjectName("sideScroll")
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(190)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        frame = QWidget()
        frame.setObjectName("sideInner")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 12, 8, 10)
        lay.setSpacing(5)
        name = QLabel("İşçilik Dosyası")
        name.setStyleSheet("color:white;font-size:15px;font-weight:800;padding:4px 3px 10px 3px;background:transparent;")
        lay.addWidget(name)
        self.side_buttons = {}
        for icon, title, key in NAV_ITEMS:
            b = QPushButton(f"{icon}   {title}")
            b.setObjectName("navBtn")
            b.setProperty("active", False)
            b.setMinimumHeight(36)
            b.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            lay.addWidget(b)
            self.side_buttons[key] = b
        lay.addStretch(1)
        help_box = QLabel("Kullanım sırası:\n1. Deplasman ekle\n2. Delil ekle\n3. Alacağı hesapla\n4. Dosyayı hazırla")
        help_box.setWordWrap(True)
        help_box.setStyleSheet("color:#c9dbe8;font-size:11px;background:#123b59;padding:9px;border-radius:5px;")
        lay.addWidget(help_box)
        self.side_status = QLabel("")
        self.side_status.setWordWrap(True)
        self.side_status.setStyleSheet("color:#98b4c9;font-size:10px;background:transparent;")
        lay.addWidget(self.side_status)
        self.claim_nav_buttons = []
        self.tool_buttons = {}
        scroll.setWidget(frame)
        return scroll

''' + s[b:]

# simple dashboard
a = s.index("    def _build_dashboard(self):")
b = s.index("    def _build_dashboard_left(self):", a)
s = s[:a] + '''    def _build_dashboard(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(14, 14, 14, 12)
        root.setSpacing(12)

        title = QLabel("Dava dosyan")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        hint = QLabel("Önce deplasmanları ve belgeleri gir. Teknik hukuk ve audit işleri arkada çalışır.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        cards = QHBoxLayout()
        self.card_events = Card("Deplasman", "0", "Kayıtlı seyahat", "#15944b", "✈")
        self.card_evidence = Card("Delil", "0", "Bilet, WhatsApp, kafile, PDF…", "#1683e6", "▣")
        self.card_amount = Card("Tahmini Alacak", "₺ 0", "Hesaplanan toplam", "#df3d3d", "∑")
        self.card_events.clicked.connect(lambda: self.switch_page("events"))
        self.card_evidence.clicked.connect(lambda: self.switch_page("evidence"))
        self.card_amount.clicked.connect(lambda: self.switch_page("calc"))
        cards.addWidget(self.card_events, 1)
        cards.addWidget(self.card_evidence, 1)
        cards.addWidget(self.card_amount, 1)
        root.addLayout(cards)

        actions = QFrame()
        actions.setObjectName("panel")
        av = QVBoxLayout(actions)
        av.setContentsMargins(14, 12, 14, 12)
        ah = QLabel("Ne yapmak istiyorsun?")
        ah.setObjectName("panelTitle")
        av.addWidget(ah)
        row = QHBoxLayout()
        for text, fn, obj in [
            ("+ Deplasman Ekle", self.add_trip_simple, "primaryBtn"),
            ("+ Delil Ekle", self.add_evidence_simple, "blueBtn"),
            ("Alacakları Gör", lambda: self.switch_page("calc"), "softBtn"),
            ("Avukat / Mahkeme Dosyası", lambda: self.switch_page("reports"), "darkBtn"),
        ]:
            btn = self._btn(text, fn, obj)
            btn.setMinimumHeight(42)
            row.addWidget(btn, 1)
        av.addLayout(row)
        root.addWidget(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(12, 10, 12, 10)
        ph = QHBoxLayout()
        lab = QLabel("Son Deplasmanlar")
        lab.setObjectName("panelTitle")
        ph.addWidget(lab)
        ph.addStretch(1)
        ph.addWidget(self._btn("Tümünü Aç", lambda: self.switch_page("events")))
        pv.addLayout(ph)
        self.home_trip_table = make_table(["Tarih", "Şehir", "Rakip / Görev", "Delil", "Durum"],
                                          [105, 120, 330, 80, 130])
        self.home_trip_table.doubleClicked.connect(lambda: self.edit_trip_simple(self._home_selected_trip()))
        pv.addWidget(self.home_trip_table, 1)
        root.addWidget(panel, 1)

        self.card_holiday = Card("", "0", "", "#ffffff", "")
        self.card_chain = Card("", "0", "", "#ffffff", "")
        return page

    def _home_selected_trip(self):
        item = self.home_trip_table.currentItem()
        if not item:
            return None
        code_item = self.home_trip_table.item(item.row(), 0)
        return code_item.data(Qt.ItemDataRole.UserRole) if code_item else None

''' + s[b:]

# simple events/deployment page
a = s.index("    def _build_events_page(self):")
b = s.index("    # ================================================================ kronoloji sayfası", a)
s = s[:a] + '''    def _build_events_page(self):
        page, root, head = self._page(
            "Deplasmanlar",
            "Tarih, şehir ve rakip/görev yeterli. Uçuş saatleri ve belgeleri buldukça aynı kayda eklersin."
        )
        head.addWidget(self._btn("+ Deplasman Ekle", self.add_trip_simple, "primaryBtn"))
        tools = QHBoxLayout()
        tools.addWidget(self._btn("✎ Düzenle", lambda: self.edit_trip_simple(selected_key(self.trip_table))))
        tools.addWidget(self._btn("▣ Bu Deplasmana Delil Ekle",
                                  lambda: self.add_evidence_for_trip(selected_key(self.trip_table)), "blueBtn"))
        tools.addWidget(self._btn("Saat Saat Çalışma / Yol",
                                  lambda: self.open_timeline(selected_key(self.trip_table))))
        tools.addWidget(self._btn("Arşivle / İptal",
                                  lambda: self.entity_status("SEYAHAT", selected_key(self.trip_table))))
        tools.addStretch(1)
        self.trip_search = QLineEdit()
        self.trip_search.setPlaceholderText("Ara: şehir, rakip, tarih…")
        self.trip_search.textChanged.connect(self.refresh_events_page)
        tools.addWidget(self.trip_search, 1)
        root.addLayout(tools)
        self.trip_table = make_table(
            ["Kayıt", "Maç / Görev Tarihi", "Şehir", "Rakip / Görev", "Gidiş", "Dönüş / Bitiş", "Delil", "Durum"],
            [90, 125, 120, 280, 145, 145, 70, 110]
        )
        self.trip_table.doubleClicked.connect(lambda: self.edit_trip_simple(selected_key(self.trip_table)))
        root.addWidget(self.trip_table, 1)
        self.trip_show_all = QCheckBox("Arşiv / iptal kayıtlarını da göster")
        self.trip_show_all.toggled.connect(self.refresh_events_page)
        root.addWidget(self.trip_show_all)
        self.event_table = make_table(
            ["No", "Başlangıç", "Bitiş", "Tür", "Başlık", "Ülke/Şehir", "Seyahat",
             "Deliller", "Talepler", "Doğrulama", "Mahkeme", "Durum"]
        )
        self.event_table.hide()
        return page

''' + s[b:]

# simpler event filter safety because old dashboard filters no longer exist
old = '''    def _fill_event_filters(self):
        items = [("", "Tüm Olaylar"), ("__NONE__", "İlişkisiz deliller")]
        items += [(t["code"], f"{t['code']} {t['title']}") for t in self.svc.trips()]
        items += [(e["code"], f"{e['code']} {e['title']}") for e in self.svc.events()]
        for box in (self.dash_event, self.ev_event):
            cur = box.currentData()
            box.blockSignals(True)
            box.clear()
            for k, lab in items:
                box.addItem(lab, k)
            idx = box.findData(cur)
            box.setCurrentIndex(idx if idx >= 0 else 0)
            box.blockSignals(False)
'''
new = '''    def _fill_event_filters(self):
        items = [("", "Tüm Olaylar"), ("__NONE__", "İlişkisiz deliller")]
        items += [(t["code"], f"{t['code']} {t['title']}") for t in self.svc.trips()]
        items += [(e["code"], f"{e['code']} {e['title']}") for e in self.svc.events()]
        boxes = []
        for name in ("dash_event", "ev_event"):
            box = getattr(self, name, None)
            if box is not None:
                boxes.append(box)
        for box in boxes:
            cur = box.currentData()
            box.blockSignals(True)
            box.clear()
            for k, lab in items:
                box.addItem(lab, k)
            idx = box.findData(cur)
            box.setCurrentIndex(idx if idx >= 0 else 0)
            box.blockSignals(False)
'''
if old in s:
    s = s.replace(old, new, 1)

s = s.replace(
'''        self.refresh_dash_evidence() if box is self.dash_date else self.refresh_evidence_page()''',
'''        if getattr(self, "dash_date", None) is box:
            self.refresh_dash_evidence()
        else:
            self.refresh_evidence_page()''',
1
)

# simple trip/evidence actions inserted before old advanced add_trip
pos = s.index("    def add_trip(self):")
simple_methods = r'''    def _trip_primary_event(self, trip_code):
        for e in self.svc.events(include_inactive=True):
            if e["trip_code"] == trip_code and e["event_type"] in ("Maç", "Turnuva", "Görev / Program"):
                return e
        for e in self.svc.events(include_inactive=True):
            if e["trip_code"] == trip_code:
                return e
        return None

    def _simple_trip_payload(self, v):
        title = (v.get("opponent") or "").strip()
        if title and "galatasaray" not in title.lower():
            title = title + " – Galatasaray"
        match_date = v.get("match_date")
        start_dt = v.get("departure_dt") or match_date
        end_dt = v.get("return_dt") or match_date
        trip = {
            "title": title, "start_dt": start_dt, "end_dt": end_dt,
            "origin": v.get("origin") or "İstanbul", "destination": v.get("city"),
            "country": "Türkiye", "purpose": "Deplasman", "mandatory_group": 1,
            "post_return_florya": v.get("post_return_florya"),
            "post_return_work": v.get("post_return_work"),
            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
            "notes": v.get("notes"),
        }
        event = {
            "title": title, "event_type": "Maç", "start_dt": match_date, "end_dt": match_date,
            "country": "Türkiye", "city": v.get("city"),
            "verification_level": "KULLANICI_BEYANI", "include_in_court": 0,
        }
        return trip, event

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
            intro="Tarih, şehir ve rakip/görev yeterli. Gidiş-dönüş saatlerini bilmiyorsanız boş bırakın."
        )
        if self._exec(d):
            self.refresh_all()
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
        def save(v):
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
            intro="Sadece bildiğiniz alanları doldurun; eksik saatleri daha sonra delillerle tamamlayabilirsiniz."
        )
        if self._exec(d):
            self.refresh_all()

    def add_evidence_simple(self, path: str | None = None, trip_code: str | None = None):
        path = path or self.pick_file("Delil dosyasını seç")
        if not path:
            return
        try:
            digest = sha256_file(Path(path))
        except OSError as e:
            return self.error("Dosya okunamadı", str(e))
        existing = self.svc.find_by_hash(digest)
        if existing:
            ex = existing[0]
            if trip_code:
                try:
                    self.svc.add_relation("DELIL", ex["code"], "SEYAHAT", trip_code, role="DESTEK")
                except Exception:
                    pass
                self.refresh_all()
                return self.info("Belge zaten vardı",
                                 f"{ex['code']} mevcut kayıttı; seçili deplasmana bağlandı.")
            return self._handle_duplicate(DuplicateEvidence(existing, digest, path))
        holder = {}
        def save(v):
            meta = dict(v)
            meta.update({
                "verification_level": "HUKUKEN_INCELENECEK",
                "include_in_court": 0,
                "include_in_mediation": 0,
                "confidentiality": "NORMAL",
            })
            links = [("SEYAHAT", trip_code, "DESTEK")] if trip_code else None
            holder["code"] = self.svc.add_evidence(Path(path), meta, links=links)
        intro = "Belge orijinal haliyle kasaya kopyalanacak ve SHA-256 ile korunacak."
        if trip_code:
            intro += f"\nBu belge otomatik olarak {trip_code} deplasmanına bağlanacak."
        d = FormDialog("Delil Ekle", simple_evidence_fields(Path(path).name), on_save=save,
                       parent=self, intro=intro, width=620)
        if self._exec(d):
            self.refresh_all()
            if holder.get("code"):
                self.info("Delil eklendi",
                          f"{holder['code']} kaydedildi" +
                          (" ve deplasmana bağlandı." if trip_code else "."))

    def add_evidence_for_trip(self, code):
        if not code:
            return self.info("Seçim", "Önce bir deplasman seçin.")
        self.add_evidence_simple(trip_code=code)

'''
s = s[:pos] + simple_methods + s[pos:]

# replace old complex events refresh
a = s.index("    def refresh_events_page(self):")
b = s.index("    # ================================================================ talepler / hesap", a)
s = s[:a] + r'''    def refresh_events_page(self):
        rows = []
        q = self.trip_search.text().strip().lower() if hasattr(self, "trip_search") else ""
        include_all = self.trip_show_all.isChecked() if hasattr(self, "trip_show_all") else False
        for t in self.svc.trips(include_inactive=include_all):
            ev = self._trip_primary_event(t["code"])
            match_date = fmt(ev["start_dt"] if ev else t["start_dt"])
            city = (ev["city"] if ev else None) or t["destination"] or "—"
            title = (ev["title"] if ev else None) or t["title"] or "—"
            hay = f"{match_date} {city} {title} {t['code']}".lower()
            if q and q not in hay:
                continue
            evidence_n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            rows.append([
                t["code"], match_date, city, title,
                fmt(t["start_dt"]), fmt(t["end_dt"]), str(evidence_n),
                RECORD_STATUS_LABELS.get(t["status"], t["status"])
            ])
        fill_table(self.trip_table, rows)
        if hasattr(self, "event_table"):
            self._fill_events_table(self.event_table, include_all=include_all)

''' + s[b:]

# dashboard refresh branch
old = '''            if page == "dashboard":
                self.refresh_dash_evidence()
                self.refresh_dash_trips()
                self.refresh_dashboard_inner()
                self.refresh_calc_summary()
                self.refresh_legal_small()
                self.refresh_calendars()'''
if old in s:
    s = s.replace(old, '''            if page == "dashboard":
                self.refresh_simple_dashboard()''', 1)

# simple dashboard refresher
pos = s.index("    def refresh_cards(self):")
s = s[:pos] + r'''    def refresh_simple_dashboard(self):
        st = analysis.dashboard_stats(self.svc)
        self.card_evidence.set_values(str(st["evidence"]), "Bilet, WhatsApp, kafile, PDF…")
        self.card_events.set_values(str(st["trips"]), "Kayıtlı deplasman")
        total = 0.0
        missing = 0
        for c in self.svc.claims():
            a = calc.claim_amount(self.svc, c)
            if a["amount"] is None:
                missing += 1
            else:
                total += a["amount"]
        self.card_amount.set_values(
            tr_money(total, 0),
            "Hesaplanan toplam" + (f" · {missing} kalem eksik" if missing else "")
        )
        rows = []
        trips = list(self.svc.trips())[-10:][::-1]
        for t in trips:
            ev = self._trip_primary_event(t["code"])
            d = fmt(ev["start_dt"] if ev else t["start_dt"])
            city = (ev["city"] if ev else None) or t["destination"] or "—"
            title = (ev["title"] if ev else None) or t["title"] or "—"
            n = len(self._rels("SEYAHAT", t["code"], "DELIL"))
            first = QTableWidgetItem(d)
            first.setData(Qt.ItemDataRole.UserRole, t["code"])
            rows.append([first, city, title, str(n),
                         RECORD_STATUS_LABELS.get(t["status"], t["status"])])
        fill_table(self.home_trip_table, rows)

''' + s[pos:]

# resize safety
s = s.replace(
'''            for k, b in self.pkg_buttons.items():
                b.setText(self.pkg_texts[k][0] if w >= 1300 else self.pkg_texts[k][1])''',
'''            for k, b in self.pkg_buttons.items():
                if k in self.pkg_texts:
                    b.setText(self.pkg_texts[k][0] if w >= 1300 else self.pkg_texts[k][1])'''
)
s = s.replace(
'''            for c in [self.card_evidence, self.card_events, self.card_holiday, self.card_chain, self.card_amount]:
                c.set_compact(compact)
            self.trips_panel_title.setText("Deplasmanlar" if compact else "Olaylar (Deplasmanlar)")''',
'''            for c in [self.card_evidence, self.card_events, self.card_amount]:
                c.set_compact(compact)
            if hasattr(self, "trips_panel_title"):
                self.trips_panel_title.setText("Deplasmanlar")'''
)

# startup seed
needle = '''    try:
        svc = CaseService(data_dir)
    except Exception as e:
'''
if needle in s and "apply_requested_match_seed(svc)" not in s:
    s = s.replace(
        needle,
'''    try:
        svc = CaseService(data_dir)
        if os.name == "nt" and getattr(sys, "frozen", False) and not os.environ.get("ISCILIK_DATA_DIR"):
            try:
                from .requested_seed_20261001 import apply_requested_match_seed
                apply_requested_match_seed(svc)
            except Exception:
                logging.getLogger("iscilik").exception("ilk deplasman listesi")
    except Exception as e:
''',
        1
    )

p.write_text(s, "utf-8")

# ---------- tests ----------
(ROOT / "tests/test_v120_simple.py").write_text(r'''from pathlib import Path

def test_simple_mode_source_shape():
    root = Path(__file__).resolve().parents[1]
    ui = (root / "iscilik_dosyasi" / "ui_qt.py").read_text("utf-8")
    dialogs = (root / "iscilik_dosyasi" / "ui_dialogs.py").read_text("utf-8")
    assert '"Deplasmanlar", "events"' in ui
    assert '"Dosyayı Hazırla", "reports"' in ui
    assert "def add_trip_simple" in ui
    assert "def add_evidence_for_trip" in ui
    assert "def simple_trip_fields" in dialogs
    assert "Rakip / görev" in dialogs
    from iscilik_dosyasi.requested_seed_20261001 import MATCHES
    assert len(MATCHES) == 7
    assert all(len(row) == 3 for row in MATCHES)

def test_updater_lock_fix_is_carried_forward():
    root = Path(__file__).resolve().parents[1]
    py = (root / "iscilik_dosyasi" / "update_manager.py").read_text("utf-8")
    ps = (root / "iscilik_dosyasi" / "updater_support" / "updater.ps1").read_text("utf-8-sig")
    assert "cwd=str(updater_dir())" in py
    assert "Set-Location -LiteralPath $updaterDir" in ps
''', "utf-8")

# changelog
p = ROOT / "CHANGELOG.md"
s = p.read_text("utf-8")
entry = '''## v1.2.0 — Basit Mod
- Günlük kullanım arayüzü sadeleştirildi: Ana Sayfa, Deplasmanlar, Deliller, Alacaklar, Dosyayı Hazırla, Ayarlar.
- Teknik menüler ana menüden kaldırıldı; çekirdek veri/audit/hesap altyapısı korunuyor.
- Yeni “Deplasman Ekle” formunda yalnız tarih, şehir, rakip/görev ve isteğe bağlı gidiş-dönüş bilgileri var.
- Seçili deplasmana tek düğmeyle delil eklenip otomatik bağlanabiliyor.
- İlk 7 deplasman kaydı skorsuz işlendi; Bursaspor ve Hatayspor dahil değil.
- Windows yerinde güncelleme klasör kilidi düzeltmesi korunuyor.

'''
if "## v1.2.0" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, "utf-8")

print("v1.2.0 simple mode patch applied")
