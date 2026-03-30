# 📚 Komga Downloader & Reader

A lightweight, high-performance mobile application built with **Python** and **Kivy** to browse, read, and download manga/comics directly from your **Komga** server.

---

## ✨ Features

* **Multi-Server Support:** Save multiple Komga server profiles and switch between them instantly.
* **Integrated Reader:** A fluid reading experience with support for:
    * **Online Streaming:** Read directly from the server without waiting for downloads.
    * **Offline Mode:** Read your downloaded `.cbz` files anytime, anywhere.
    * **RTL/LTR Support:** Toggle between Right-to-Left (Manga) and Left-to-Right (Comics) modes.
    * **Reading History:** Automatically resumes from the last page you visited.
* **Smart Downloading:** Download any book or entire series as `.cbz` files to your local storage.
* **Lazy Loading UI:** Optimized search results that handle hundreds of entries without lagging or freezing.

---

## 🚀 Getting Started

### Prerequisites
* A running instance of [Komga](https://komga.org/).
* An Android device (for the `.apk`) or a Python environment (for development).

### Installation
1.  Go to the **[Releases](https://github.com/NumberZeroo/KomgaAppDownloader/releases)** section.
2.  Download the latest `komgadownloader-vX.X.X-debug.apk`.
3.  Install it on your Android device (ensure "Install from Unknown Sources" is enabled).

---

## 🛠️ Tech Stack

* **Core:** Python 3.10
* **UI Framework:** [Kivy](https://kivy.org/) & [KivyMD](https://kivymd.de/)
* **Networking:** Requests (for Komga API interaction)
* **Security:** Cryptography (Fernet) for local credential encryption.
* **CI/CD:** GitHub Actions + Buildozer for automated APK generation.

---

## 🔧 Development & Build

If you want to build the APK yourself:

1.  Clone the repository:
    ```bash
    git clone [https://github.com/NumberZeroo/KomgaAppDownloader.git](https://github.com/NumberZeroo/KomgaAppDownloader.git)
    ```
2.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  Use **Buildozer** to compile:
    ```bash
    buildozer android debug
    ```

---

## 🛡️ Security Note
Your credentials (Email/Password/Server URL) are stored locally on your device using **Fernet symmetric encryption**. No data is ever sent to third-party servers; the app only communicates directly with your specified Komga instance.

---

## 📝 License
Distributed under the MIT License. See `LICENSE` for more information.
