from pathlib import Path
import re

def show(path, name):
    s=Path(path).read_text("utf-8")
    m=re.search(rf"(?m)^    def {re.escape(name)}\(.*?(?=^    def |\Z)", s, re.S)
    print(f"\n===== {path} :: {name} =====")
    if m:
        print(m.group(0)[:16000].encode("ascii","backslashreplace").decode("ascii"))
    else:
        print("NOT FOUND")

for name in ["_preload","refresh_all","switch_page","refresh_calc_page","refresh_settings_page"]:
    show("work/iscilik_dosyasi/ui_qt.py",name)
for name in ["segments","trips","events","list_evidence","relations","related_codes"]:
    show("work/iscilik_dosyasi/service.py",name)
raise SystemExit("PERF_INSPECTION_ONLY")
