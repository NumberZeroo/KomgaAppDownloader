import requests
import threading

GITHUB_REPO = "NumberZeroo/KomgaAppDownloader"


def _parse_version(tag: str) -> tuple:
    try:
        return tuple(int(x) for x in tag.lstrip('v').split('.'))
    except ValueError:
        return (0, 0, 0)


def check_for_update(current_version: str, callback):
    """
    Esegue il check in background.
    Chiama callback(new_tag, apk_url) se c'è aggiornamento,
    oppure callback(None, None) se è già aggiornato o c'è un errore.
    """

    def _fetch():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "KomgaAppDownloader-Client"
            }

            # Timeout leggermente più lungo per reti mobili instabili
            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code == 403:
                print("GitHub Rate Limit superato o Accesso Negato.")
                return callback(None, None)

            r.raise_for_status()
            data = r.json()

            latest_tag = data.get("tag_name", "")

            # Logica di confronto versioni
            if _parse_version(latest_tag) > _parse_version(current_version):
                # Cerca l'APK tra gli asset
                apk_url = next(
                    (a["browser_download_url"] for a in data.get("assets", [])
                     if a["name"].lower().endswith(".apk")),
                    None
                )

                # Se non trova l'APK, rimanda alla pagina della release
                final_url = apk_url if apk_url else data.get("html_url")
                callback(latest_tag, final_url)
            else:
                callback(None, None)

        except Exception as e:
            print(f"Errore update check: {e}")
            callback(None, None)

    threading.Thread(target=_fetch, daemon=True).start()