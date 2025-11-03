import subprocess
import sys
import os
import ctypes
import winreg

class ProxyDisableError(Exception):
    pass

def _require_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def disable_winhttp_proxy():
    """
    Vypne WinHTTP proxy (systémová vrstva) pomocí `netsh winhttp reset proxy`.
    Vyžaduje spuštění jako administrátor.
    """
    if not _require_admin():
        raise ProxyDisableError("disable_winhttp_proxy vyžaduje administrátorská práva")
    try:
        completed = subprocess.run(
            ["netsh", "winhttp", "reset", "proxy"],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        # Stav "Direct access (no proxy server)" indikuje úspěch
        ok = "Direct access" in completed.stdout or "no proxy" in completed.stdout.lower()
        return ok
    except subprocess.CalledProcessError as e:
        raise ProxyDisableError(f"netsh selhal: {e.stderr or e.stdout}") from e

def disable_internet_settings_proxy(current_user=True):
    """
    Vypne WinINET/IE proxy (což používají i mnohé aplikace a Edge/Chrome přes systém).
    - current_user=True: zapisuje do HKCU (doporučeno).
    - current_user=False: zapisuje do HKLM Policies (potřebuje admin a ovlivní default pro zařízení).
    """
    try:
        if current_user:
            root = winreg.HKEY_CURRENT_USER
            path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as k:
                # ProxyEnable = 0 vypíná proxy
                winreg.SetValueEx(k, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                # AutoDetect = 0 vypne automatickou detekci (volitelné)
                winreg.SetValueEx(k, "AutoDetect", 0, winreg.REG_DWORD, 0)
                # ProxyServer/ProxyOverride lze nechat, ale nevadí je smazat
                try:
                    winreg.DeleteValue(k, "ProxyServer")
                except FileNotFoundError:
                    pass
                try:
                    winreg.DeleteValue(k, "ProxyOverride")
                except FileNotFoundError:
                    pass
            return True
        else:
            # Politiky – spíš pro centrální správu; vyžaduje admin
            if not _require_admin():
                raise ProxyDisableError("Zápis do HKLM Policies vyžaduje administrátorská práva")
            root = winreg.HKEY_LOCAL_MACHINE
            path = r"Software\Policies\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as k:
                # ProxySettingsPerUser = 1 znamená, že se proxy řídí per-user; tu necháme,
                # ale vypneme efektivně volbou v HKCU. Alternativně lze nastavit politiky IE Control Panel.
                winreg.SetValueEx(k, "ProxySettingsPerUser", 0, winreg.REG_DWORD, 1)
            return True
    except PermissionError as e:
        raise ProxyDisableError("Nedostatečná oprávnění pro zápis do registru") from e
    except OSError as e:
        raise ProxyDisableError(f"Chyba registru: {e}") from e

def disable_all_proxies(require_admin_for_all=True):
    """
    Komfortní funkce: vypne WinHTTP proxy i WinINET proxy.
    - require_admin_for_all=True: pokud chybí admin, vyhodí chybu (doporučeno pro konzistentní stav).
      Když False, provede aspoň HKCU a WinHTTP přeskočí.
    """
    results = {"winhttp": None, "internet_settings": None}
    errors = []

    # WinHTTP
    try:
        results["winhttp"] = disable_winhttp_proxy()
    except ProxyDisableError as e:
        if require_admin_for_all:
            raise
        errors.append(str(e))
        results["winhttp"] = False

    # HKCU internet settings
    try:
        results["internet_settings"] = disable_internet_settings_proxy(current_user=True)
    except ProxyDisableError as e:
        errors.append(str(e))
        results["internet_settings"] = False

    # Pokud chcete zapsat i politiky HKLM (většinou není nutné), odkomentujte:
    # try:
    #     _ = disable_internet_settings_proxy(current_user=False)
    # except ProxyDisableError as e:
    #     errors.append(str(e))

    # Volitelné: vyvolat broadcast změny pro aplikace (některé čtou při startu)
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        SMTO_ABORTIFHUNG = 0x0002
        res = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
            SMTO_ABORTIFHUNG,
            2000,
            ctypes.byref(res),
        )
    except Exception:
        pass

    if require_admin_for_all and not all(results.values()):
        raise ProxyDisableError(f"Nepodařilo se vypnout všechny proxy: {results}; errors={errors}")

    return results

if __name__ == "__main__":
    try:
        out = disable_all_proxies(require_admin_for_all=False)
        print(f"Proxy vypnuta: {out}")
        sys.exit(0 if any(out.values()) else 1)
    except Exception as e:
        print(f"Chyba: {e}", file=sys.stderr)
        sys.exit(1)
