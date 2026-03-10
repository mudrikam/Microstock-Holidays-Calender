import os
import json
import time
from datetime import datetime
import urllib.request
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QSizePolicy, QLineEdit, QPushButton, QSplitter
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage,
    QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
)
import qtawesome as qta
import helper.theme_system as theme
from helper.search_helper import PLATFORMS, build_url, ico_path


_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

_TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
_PROFILE_DIR = os.path.join(_TEMP_DIR, "browser_profile")

_IMAGEYE_EXT_ID = "agionbommeaifngbhincahgmoflcikhm"
_IMAGEYE_CRX_DIR = os.path.join(_TEMP_DIR, "extensions")
_IMAGEYE_CRX_PATH = os.path.join(_IMAGEYE_CRX_DIR, "imageye.crx")
_IMAGEYE_UNPACKED_DIR = os.path.join(_IMAGEYE_CRX_DIR, "imageye_unpacked")
_IMAGEYE_CRX_DOWNLOAD = (
    "https://clients2.google.com/service/update2/crx"
    "?response=redirect&prodversion=120.0.0.0&acceptformat=crx3,crx2"
    f"&x=id%3D{_IMAGEYE_EXT_ID}%26installsource%3Dondemand%26uc"
)


def _extract_crx_to_folder(crx_path: str, out_dir: str) -> bool:
    import struct, zipfile, io, shutil
    try:
        with open(crx_path, "rb") as f:
            data = f.read()
        magic = data[:4]
        if magic != b"Cr24":
            print(f"[EXT] Format CRX tidak dikenal: {magic}")
            return False
        version = struct.unpack_from("<I", data, 4)[0]
        if version == 3:
            proto_len = struct.unpack_from("<I", data, 8)[0]
            zip_offset = 12 + proto_len
        elif version == 2:
            pub_len = struct.unpack_from("<I", data, 8)[0]
            sig_len = struct.unpack_from("<I", data, 12)[0]
            zip_offset = 16 + pub_len + sig_len
        else:
            print(f"[EXT] Versi CRX tidak dikenal: {version}")
            return False
        zip_data = data[zip_offset:]
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extractall(out_dir)
        print(f"[EXT] CRX berhasil di-extract ke {out_dir}")
        return True
    except Exception as e:
        print(f"[EXT] Gagal extract CRX: {e}")
        return False


def _try_download_imageye_crx() -> bool:
    os.makedirs(_IMAGEYE_CRX_DIR, exist_ok=True)
    req = urllib.request.Request(
        _IMAGEYE_CRX_DOWNLOAD,
        headers={"User-Agent": _CHROME_UA, "Accept": "*/*"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(_IMAGEYE_CRX_PATH, "wb") as f:
            f.write(data)
        print(f"[EXT] Imageye CRX berhasil diunduh: {len(data):,} bytes → {_IMAGEYE_CRX_PATH}")
        return True
    except Exception as e:
        print(f"[EXT] Gagal download Imageye CRX: {e}")
        print(f"[EXT] Download manual dari: {_IMAGEYE_CRX_DOWNLOAD}")
        print(f"[EXT] Simpan file sebagai: {_IMAGEYE_CRX_PATH}")
        return False


class _HeadersInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.resourceType() == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:
            info.setHttpHeader(b"Sec-Fetch-Site", b"none")
            info.setHttpHeader(b"Sec-Fetch-Mode", b"navigate")
            info.setHttpHeader(b"Sec-Fetch-User", b"?1")
            info.setHttpHeader(b"Sec-Fetch-Dest", b"document")
            info.setHttpHeader(b"Upgrade-Insecure-Requests", b"1")
            info.setHttpHeader(b"Accept", b"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9")
        info.setHttpHeader(b"sec-ch-ua", b'"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"')
        info.setHttpHeader(b"sec-ch-ua-mobile", b"?0")
        info.setHttpHeader(b"sec-ch-ua-platform", b'"Windows"')


class _BrowserPage(QWebEnginePage):
    _profile: QWebEngineProfile = None
    _interceptor: _HeadersInterceptor = None
    imageye_ext_id: str = ""
    _current_platform_id: str = "downloads"
    _download_session_dir: str = ""
    _download_session_time: float = 0.0
    _DOWNLOAD_SESSION_TIMEOUT: float = 30.0

    @classmethod
    def _get_or_create_download_dir(cls) -> str:
        now = time.time()
        if not cls._download_session_dir or (now - cls._download_session_time) > cls._DOWNLOAD_SESSION_TIMEOUT:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            cls._download_session_dir = os.path.join(_TEMP_DIR, "downloads", cls._current_platform_id, ts)
            os.makedirs(cls._download_session_dir, exist_ok=True)
            print(f"[DL] New download session: {cls._download_session_dir}")
        cls._download_session_time = now
        return cls._download_session_dir

    @classmethod
    def get_profile(cls) -> QWebEngineProfile:
        if cls._profile is None:
            os.makedirs(_PROFILE_DIR, exist_ok=True)
            cls._profile = QWebEngineProfile("MicrostockBrowser")
            cls._profile.setPersistentStoragePath(_PROFILE_DIR)
            cls._profile.setCachePath(os.path.join(_PROFILE_DIR, "cache"))
            cls._profile.setHttpUserAgent(_CHROME_UA)
            cls._profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
            )
            cls._interceptor = _HeadersInterceptor()
            cls._profile.setUrlRequestInterceptor(cls._interceptor)

            def _on_download_requested(download):
                dl_dir = _BrowserPage._get_or_create_download_dir()
                download.setDownloadDirectory(dl_dir)
                suggested = download.suggestedFileName()
                if suggested:
                    download.setDownloadFileName(suggested)
                download.accept()
                print(f"[DL] Saving: {suggested!r} -> {dl_dir}")

            cls._profile.downloadRequested.connect(_on_download_requested)

            em = cls._profile.extensionManager()

            def _on_ext_loaded(info):
                try:
                    ext_id = info.id()
                    ext_name = info.name()
                    _BrowserPage.imageye_ext_id = ext_id
                    print(f"[EXT] Loaded: {ext_name} (id={ext_id})")
                except Exception as e:
                    print(f"[EXT] loadFinished info error: {e}")

            em.loadFinished.connect(_on_ext_loaded)

            if os.path.isdir(_IMAGEYE_UNPACKED_DIR) and os.path.exists(
                os.path.join(_IMAGEYE_UNPACKED_DIR, "manifest.json")
            ):
                print(f"[EXT] Memuat Imageye dari {_IMAGEYE_UNPACKED_DIR}")
                em.loadExtension(_IMAGEYE_UNPACKED_DIR)
            else:
                if not os.path.exists(_IMAGEYE_CRX_PATH):
                    print("[EXT] Imageye belum ada, mencoba mengunduh...")
                    _try_download_imageye_crx()
                if os.path.exists(_IMAGEYE_CRX_PATH):
                    print(f"[EXT] Mengekstrak Imageye CRX ...")
                    if _extract_crx_to_folder(_IMAGEYE_CRX_PATH, _IMAGEYE_UNPACKED_DIR):
                        print(f"[EXT] Memuat Imageye dari {_IMAGEYE_UNPACKED_DIR}")
                        em.loadExtension(_IMAGEYE_UNPACKED_DIR)

        return cls._profile

    def __init__(self, parent=None):
        super().__init__(_BrowserPage.get_profile(), parent)


class _PlatformBrowserWidget(QWidget):

    def __init__(self, platform: dict, parent=None):
        super().__init__(parent)
        self._platform = platform
        self._current_keyword = ""
        self._loaded_keyword = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- navigation bar ---
        nav_bar = QWidget()
        nav_bar.setFixedHeight(36)
        nav_bar.setStyleSheet(
            f"background-color: {theme.color('surface')};"
            f"border-bottom: 1px solid {theme.color('border')};"
        )
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(6, 4, 6, 4)
        nav_layout.setSpacing(4)

        btn_style = (
            f"QPushButton {{ background: transparent; border: none; border-radius: 4px;"
            f" padding: 2px 6px; color: {theme.color('text_secondary')}; }}"
            f"QPushButton:hover {{ background: {theme.color('surface_raised')}; }}"
            f"QPushButton:disabled {{ color: {theme.color('text_muted')}; }}"
        )
        btn_active_style = (
            f"QPushButton {{ background: {theme.color('accent_dim')}; border: 1px solid {theme.color('accent')};"
            f" border-radius: 4px; padding: 2px 6px; color: {theme.color('accent')}; }}"
            f"QPushButton:hover {{ background: {theme.color('accent_dim')}; }}"
        )

        self._btn_back = QPushButton()
        self._btn_back.setIcon(qta.icon("fa5s.arrow-left", color=theme.color("text_secondary")))
        self._btn_back.setFixedSize(28, 28)
        self._btn_back.setStyleSheet(btn_style)
        self._btn_back.setToolTip("Back")
        self._btn_back.clicked.connect(lambda: self._web_view.back())

        self._btn_forward = QPushButton()
        self._btn_forward.setIcon(qta.icon("fa5s.arrow-right", color=theme.color("text_secondary")))
        self._btn_forward.setFixedSize(28, 28)
        self._btn_forward.setStyleSheet(btn_style)
        self._btn_forward.setToolTip("Forward")
        self._btn_forward.clicked.connect(lambda: self._web_view.forward())

        self._btn_reload = QPushButton()
        self._btn_reload.setIcon(qta.icon("fa5s.redo", color=theme.color("text_secondary")))
        self._btn_reload.setFixedSize(28, 28)
        self._btn_reload.setStyleSheet(btn_style)
        self._btn_reload.setToolTip("Reload")
        self._btn_reload.clicked.connect(lambda: self._web_view.reload())

        self._url_bar = QLineEdit()
        self._url_bar.setReadOnly(True)
        self._url_bar.setPlaceholderText("URL...")
        self._url_bar.setStyleSheet(
            f"QLineEdit {{ background: {theme.color('background')};"
            f" border: 1px solid {theme.color('border')}; border-radius: 4px;"
            f" padding: 2px 6px; color: {theme.color('text_primary')};"
            f" font-size: {theme.font_size('size_small')}px; }}"
        )
        self._url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._btn_copy = QPushButton()
        self._btn_copy.setIcon(qta.icon("fa5s.copy", color=theme.color("text_secondary")))
        self._btn_copy.setFixedSize(28, 28)
        self._btn_copy.setStyleSheet(btn_style)
        self._btn_copy.setToolTip("Copy URL")
        self._btn_copy.clicked.connect(self._copy_url)

        self._btn_imageye = QPushButton()
        self._btn_imageye.setFixedSize(28, 28)
        self._btn_imageye.setStyleSheet(btn_style)
        self._btn_imageye.setToolTip("Toggle Imageye Image Downloader")
        ico_imageye = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "temp", "extensions", "imageye_unpacked", "imageye128.png"
        )
        if os.path.exists(ico_imageye):
            self._btn_imageye.setIcon(QIcon(ico_imageye))
        else:
            try:
                self._btn_imageye.setIcon(qta.icon("fa5s.images", color=theme.color("text_secondary")))
            except Exception:
                self._btn_imageye.setText("img")
        self._btn_imageye.clicked.connect(self._toggle_imageye_panel)
        self._imageye_panel_visible = False
        self._btn_imageye_normal_style = btn_style
        self._btn_imageye_active_style = btn_active_style

        nav_layout.addWidget(self._btn_back)
        nav_layout.addWidget(self._btn_forward)
        nav_layout.addWidget(self._btn_reload)
        nav_layout.addWidget(self._url_bar, 1)
        nav_layout.addWidget(self._btn_copy)
        nav_layout.addWidget(self._btn_imageye)

        # --- splitter: main browser | imageye side panel ---
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet("QSplitter::handle { background: " + theme.color('border') + "; width: 1px; }")

        self._web_view = QWebEngineView()
        self._web_view.setPage(_BrowserPage(self._web_view))
        self._web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._web_view.loadFinished.connect(self._on_load_finished)
        self._web_view.urlChanged.connect(self._on_url_changed)

        self._imageye_view = QWebEngineView()
        self._imageye_view.setPage(_BrowserPage(self._imageye_view))
        self._imageye_view.setFixedWidth(380)
        self._imageye_view.setVisible(False)

        self._splitter.addWidget(self._web_view)
        self._splitter.addWidget(self._imageye_view)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)

        self._error_label = QLabel()
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet(
            f"color: {theme.color('text_muted')}; "
            f"font-size: {theme.font_size('size_large')}px; background: transparent;"
        )
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)

        layout.addWidget(nav_bar)
        layout.addWidget(self._splitter, 1)
        layout.addWidget(self._error_label)

    def _toggle_imageye_panel(self):
        self._imageye_panel_visible = not self._imageye_panel_visible
        self._imageye_view.setVisible(self._imageye_panel_visible)
        if self._imageye_panel_visible:
            self._btn_imageye.setStyleSheet(self._btn_imageye_active_style)
            ext_id = _BrowserPage.imageye_ext_id
            if ext_id:
                popup_url = f"chrome-extension://{ext_id}/popup.html"
                print(f"[EXT] Opening Imageye panel: {popup_url}")
                self._imageye_view.loadFinished.connect(self._on_imageye_popup_loaded)
                self._imageye_view.load(QUrl(popup_url))
            else:
                print("[EXT] Extension ID belum tersedia, coba lagi sebentar")
        else:
            self._btn_imageye.setStyleSheet(self._btn_imageye_normal_style)

    def _on_imageye_popup_loaded(self, ok: bool):
        self._imageye_view.loadFinished.disconnect(self._on_imageye_popup_loaded)
        if not ok:
            return
        scraper_path = os.path.join(_IMAGEYE_UNPACKED_DIR, "imageScraper.js")
        if not os.path.exists(scraper_path):
            print("[EXT] imageScraper.js not found")
            return
        with open(scraper_path, "r", encoding="utf-8") as f:
            scraper_js = f.read()

        imageye_view_ref = self._imageye_view

        def _on_scraper_result(result):
            if result is None:
                print("[EXT] imageScraper returned None (page may not have loaded yet)")
                return
            images = result.get("images", []) if isinstance(result, dict) else []
            print(f"[EXT] imageScraper found {len(images)} images")
            result_json = json.dumps(result)
            fix_js = f"""
(function() {{
    var resultData = {result_json};
    function applyFix(attempt) {{
        if (typeof Ie === 'undefined' || !Ie.getImagesCallback) {{
            if (attempt < 20) {{
                setTimeout(function() {{ applyFix(attempt + 1); }}, 200);
            }} else {{
                console.log('[EXT-FIX] Ie never became available');
            }}
            return;
        }}
        console.log('[EXT-FIX] Injecting ' + (resultData.images ? resultData.images.length : 0) + ' images into Imageye');
        Ie.initiated = false;
        Ie.getImagesCallback([{{documentId:null, frameId:null, result:resultData}}]);
    }}
    applyFix(0);
}})();
"""
            imageye_view_ref.page().runJavaScript(fix_js)

        self._web_view.page().runJavaScript(scraper_js, _on_scraper_result)

    def _on_url_changed(self, url: QUrl):
        self._url_bar.setText(url.toString())

    def _copy_url(self):
        url = self._url_bar.text()
        if url:
            QGuiApplication.clipboard().setText(url)
            print(f"[SEARCH] URL copied: {url}")

    def _on_load_finished(self, ok: bool):
        if not ok:
            self._show_error()
        else:
            self._error_label.setVisible(False)

    def _show_error(self):
        try:
            self._error_label.setPixmap(qta.icon("fa5s.globe", color=theme.color("text_muted")).pixmap(48, 48))
        except Exception:
            self._error_label.setText("🌐  Failed to load page")
        self._error_label.setVisible(True)

    def load_for_keyword(self, keyword: str):
        self._current_keyword = keyword
        if not keyword:
            return
        if self._loaded_keyword == keyword:
            return
        self._loaded_keyword = keyword
        _BrowserPage._current_platform_id = self._platform["id"]
        _BrowserPage._download_session_dir = ""  # reset session on new keyword
        url = build_url(self._platform["id"], keyword)
        print(f"[SEARCH] Loading {self._platform['name']}: {url}")
        self._web_view.load(QUrl(url))

    def keyword(self) -> str:
        return self._current_keyword


class SearchTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_holiday = None
        self._current_keyword = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._no_selection_label = QLabel("Select a holiday to begin searching")
        self._no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_selection_label.setStyleSheet(
            f"color: {theme.color('text_muted')}; "
            f"font-size: {theme.font_size('size_large')}px;"
        )

        self._platform_tabs = QTabWidget()
        self._platform_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {theme.color('background')};
                border: none;
            }}
            QTabBar::tab {{
                background-color: {theme.color('tab_bg')};
                color: {theme.color('text_secondary')};
                padding: 6px 14px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {theme.font_size('size_small')}px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme.color('surface')};
                color: {theme.color('accent')};
                border-bottom: 2px solid {theme.color('accent')};
            }}
            QTabBar::tab:hover {{
                background-color: {theme.color('surface_raised')};
                color: {theme.color('text_primary')};
            }}
        """)

        self._browsers: dict[str, _PlatformBrowserWidget] = {}
        for p in PLATFORMS:
            browser = _PlatformBrowserWidget(p)
            self._browsers[p["id"]] = browser
            icon_file = ico_path(p["id"])
            icon = QIcon(icon_file) if os.path.exists(icon_file) else QIcon()
            self._platform_tabs.addTab(browser, icon, p["name"])

        self._platform_tabs.currentChanged.connect(self._on_platform_tab_changed)

        layout.addWidget(self._no_selection_label, 1)
        layout.addWidget(self._platform_tabs, 1)
        self._platform_tabs.setVisible(False)

    def set_holiday(self, holiday: dict):
        self._current_holiday = holiday
        self._current_keyword = holiday.get("name", "") if holiday else ""
        print(f"[SEARCH] Holiday set: {self._current_keyword!r}")
        if self._current_keyword:
            self._no_selection_label.setVisible(False)
            self._platform_tabs.setVisible(True)
            self._load_current_tab()
        else:
            self._no_selection_label.setVisible(True)
            self._platform_tabs.setVisible(False)

    def switch_to_platform(self, platform_id: str):
        for i, p in enumerate(PLATFORMS):
            if p["id"] == platform_id:
                self._platform_tabs.setCurrentIndex(i)
                return

    def _on_platform_tab_changed(self, index: int):
        if index < 0 or index >= len(PLATFORMS):
            return
        platform_id = PLATFORMS[index]["id"]
        browser = self._browsers.get(platform_id)
        if browser and self._current_keyword:
            browser.load_for_keyword(self._current_keyword)

    def _load_current_tab(self):
        index = self._platform_tabs.currentIndex()
        if index < 0 or index >= len(PLATFORMS):
            return
        platform_id = PLATFORMS[index]["id"]
        browser = self._browsers.get(platform_id)
        if browser:
            browser.load_for_keyword(self._current_keyword)

