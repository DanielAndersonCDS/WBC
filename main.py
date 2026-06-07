"""
BloodChecker Android – WebView app wrapping the Flask server.
"""
import threading, os, sys, time

APP_DIR = os.path.join(os.path.dirname(__file__), "bloodchecker_app")
sys.path.insert(0, APP_DIR)

PORT = 5050
URL  = f"http://127.0.0.1:{PORT}"


def start_flask():
    os.chdir(APP_DIR)
    import app as bloodchecker
    bloodchecker.app.run(host="127.0.0.1", port=PORT,
                         debug=False, use_reloader=False, threaded=True)


# ── Kivy / Android WebView ──────────────────────────────────────────────────
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock


class BloodCheckerApp(App):
    title = "Blood Cell Counter"

    def build(self):
        self.layout = BoxLayout(orientation="vertical")

        # Start Flask in background
        threading.Thread(target=start_flask, daemon=True).start()

        # Schedule WebView load after Flask warms up
        Clock.schedule_once(self._load_webview, 1.5)

        return self.layout

    def _load_webview(self, dt):
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread

            @run_on_ui_thread
            def _ui():
                activity = autoclass(
                    "org.kivy.android.PythonActivity"
                ).mActivity
                WebView       = autoclass("android.webkit.WebView")
                WebViewClient = autoclass("android.webkit.WebViewClient")
                WebSettings   = autoclass("android.webkit.WebSettings")

                wv = WebView(activity)
                s  = wv.getSettings()
                s.setJavaScriptEnabled(True)
                s.setDomStorageEnabled(True)
                s.setAllowFileAccess(True)
                s.setMixedContentMode(0)          # MIXED_CONTENT_ALWAYS_ALLOW
                s.setCacheMode(WebSettings.LOAD_NO_CACHE)

                wv.setWebViewClient(WebViewClient())
                wv.loadUrl(URL)

                # Attach native view via kivy-android
                from android.widget import AndroidWidget
                self.layout.add_widget(AndroidWidget(wv))

            _ui()

        except Exception as e:
            from kivy.uix.label import Label
            self.layout.add_widget(
                Label(text=f"[b]Open in browser:[/b]\n{URL}\n\n({e})",
                      markup=True, halign="center", font_size="14sp")
            )


if __name__ == "__main__":
    BloodCheckerApp().run()
