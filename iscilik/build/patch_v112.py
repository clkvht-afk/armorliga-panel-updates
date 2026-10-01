from pathlib import Path

ROOT = Path("work")

# Version bump
(ROOT / "VERSION").write_text("1.1.2\n", encoding="utf-8")

p = ROOT / "iscilik_dosyasi/__init__.py"
s = p.read_text(encoding="utf-8")
s = s.replace('__version__ = "1.1.1"', '__version__ = "1.1.2"')
p.write_text(s, encoding="utf-8")

p = ROOT / "packaging/version_info.txt"
s = p.read_text(encoding="utf-8")
s = s.replace("filevers=(1, 1, 1, 0)", "filevers=(1, 1, 2, 0)")
s = s.replace("prodvers=(1, 1, 1, 0)", "prodvers=(1, 1, 2, 0)")
s = s.replace("'1.1.1'", "'1.1.2'")
p.write_text(s, encoding="utf-8")

# Critical updater fix: the child PowerShell must NOT inherit the program folder
# as its current working directory, otherwise Windows keeps a handle to that folder
# and Rename-Item fails with "because it is in use".
p = ROOT / "iscilik_dosyasi/update_manager.py"
s = p.read_text(encoding="utf-8")
s = s.replace('UPDATER_VERSION = "1.1.0"', 'UPDATER_VERSION = "1.1.2"')
old = '''    subprocess.Popen(
        [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden", "-File", str(ps1), "-Mode", "InstallAfterExit",
        ],
        creationflags=flags,
        close_fds=True,
    )
'''
new = '''    # ÖNEMLİ: cwd program klasörü olamaz. Windows bir prosesin current-directory
    # handle'ı açıkken o klasörün yeniden adlandırılmasına izin vermez.
    # Updater, veri klasöründen çalışır ve program kapandıktan sonra install_dir'i değiştirir.
    subprocess.Popen(
        [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden", "-File", str(ps1), "-Mode", "InstallAfterExit",
        ],
        creationflags=flags,
        close_fds=True,
        cwd=str(updater_dir()),
    )
'''
if old not in s:
    raise SystemExit("update_manager launch block not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# PowerShell side double-safety: immediately move its working directory out of install_dir,
# and give Windows a small grace period after the EXE disappears.
p = ROOT / "iscilik_dosyasi/updater_support/updater.ps1"
s = p.read_text(encoding="utf-8-sig")
needle = "$histPath = Join-Path $updaterDir 'update_history.jsonl'\n"
replacement = needle + "\n# Kendi current-directory handle'ımız program klasörünü kilitlemesin.\nSet-Location -LiteralPath $updaterDir\n"
if needle not in s:
    raise SystemExit("updater insertion point not found")
s = s.replace(needle, replacement, 1)
s = s.replace(
'''    if (Get-Process -Name 'IscilikDosyasi' -ErrorAction SilentlyContinue) {
        throw 'Program belirtilen sürede kapanmadı. Güncelleme uygulanmadı.'
    }
}''',
'''    if (Get-Process -Name 'IscilikDosyasi' -ErrorAction SilentlyContinue) {
        throw 'Program belirtilen sürede kapanmadı. Güncelleme uygulanmadı.'
    }
    # EXE kapandıktan hemen sonra Windows/AV kısa süreli dosya handle'ı tutabilir.
    Start-Sleep -Milliseconds 1200
}''',
1)
p.write_text(s, encoding="utf-8-sig")

# Regression guard: source must explicitly launch updater outside install folder.
test = r'''from pathlib import Path

def test_updater_does_not_inherit_program_working_directory():
    root = Path(__file__).resolve().parents[1]
    py = (root / "iscilik_dosyasi" / "update_manager.py").read_text("utf-8")
    ps = (root / "iscilik_dosyasi" / "updater_support" / "updater.ps1").read_text("utf-8-sig")
    assert "cwd=str(updater_dir())" in py
    assert "Set-Location -LiteralPath $updaterDir" in ps
    assert "Start-Sleep -Milliseconds 1200" in ps
'''
(ROOT / "tests/test_v112_updater.py").write_text(test, encoding="utf-8")

p = ROOT / "CHANGELOG.md"
s = p.read_text(encoding="utf-8")
entry = """## v1.1.2 — Yerinde güncelleme kilit hatası düzeltildi
- Program içinden “İndir ve Güncelle” seçildiğinde Windows klasör kilidi yüzünden oluşan Rename-Item hatası giderildi.
- Güncelleyici artık program klasörü dışında bir çalışma dizininden başlar.
- Program kapandıktan sonra Windows dosya kilitlerinin serbest kalması için kısa güvenli bekleme eklendi.
- Dava verileri, delil kasası ve audit verileri yine program klasöründen ayrı tutulur.

"""
if "## v1.1.2" not in s:
    lines = s.splitlines(True)
    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    s = "".join(lines[:idx]) + entry + "".join(lines[idx:])
p.write_text(s, encoding="utf-8")
