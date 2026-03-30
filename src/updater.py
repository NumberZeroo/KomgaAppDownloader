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
            r = requests.get(url, timeout=10,
                             headers={"Accept": "application/vnd.github+json"})
            r.raise_for_status()
            data = r.json()

            latest_tag = data.get("tag_name", "")
            if _parse_version(latest_tag) > _parse_version(current_version):
                apk_url = next(
                    (a["browser_download_url"] for a in data.get("assets", [])
                     if a["name"].endswith(".apk")),
                    data.get("html_url")
                )
                callback(latest_tag, apk_url)
            else:
                callback(None, None)
        except Exception:
            callback(None, None)

    threading.Thread(target=_fetch, daemon=True).start()