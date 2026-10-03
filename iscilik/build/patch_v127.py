from pathlib import Path
import re

p = Path("work/iscilik_dosyasi/ui_qt.py")
s = p.read_text("utf-8")

def show(name):
    m = re.search(rf"(?m)^    def {re.escape(name)}\(.*?(?=^    def |\Z)", s, re.S)
    print(f"\n===== {name} =====")
    if m:
        print(m.group(0)[:12000])
    else:
        print("NOT FOUND")

for name in [
    "switch_page", "refresh_all", "_rels", "refresh_cards",
    "refresh_evidence_page", "refresh_events_page",
    "refresh_simple_dashboard", "refresh_calc_summary",
    "refresh_reports_page", "_fill_event_filters"
]:
    show(name)

raise SystemExit("PERF_INSPECTION_ONLY")
