# main.py
import os, json
from datetime import datetime, timedelta
import threading
from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'minimum_width', '360')
Config.set('graphics', 'minimum_height', '600')

from kivy.app import App
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform, get_color_from_hex
from kivy.properties import (StringProperty, BooleanProperty, NumericProperty,
                            ListProperty, ObjectProperty)

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.button import MDIconButton
from kivymd.uix.snackbar import Snackbar

from screens.home_screen import HomeScreen
from screens.tracker_screen import TrackerScreen
from screens.calculator_screen import CalculatorScreen
from screens.news_screen import NewsScreen
from screens.reminders_screen import RemindersScreen
from screens.settings_screen import SettingsScreen

from utils.config import ConfigManager
from utils.db_helper import DatabaseHelper
from utils.notifications import NotificationManager
from utils.game_tracker import GameTracker

APP_NAME = "LIVE BOOSTER"
APP_VERSION = "1.0"
GAME_PACKAGE = "com.liverussia.game.googleplay"

PRIMARY_COLOR = "Blue"
ACCENT_COLOR = "Teal"
BG_LIGHT = "#F5F5F5"
BG_DARK = "#121212"

# YouTube плейлист загрузок канала LITVA (только обычные видео, без Shorts)
DEFAULT_RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=UUlC6vz4MPgTXl8ijWh5USiA"

class DraggableFAB(MDIconButton):
    """Кнопка, свободно перемещаемая пальцем/курсором по всему экрану.
       При коротком нажатии (без перетаскивания) срабатывает событие on_release."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(56), dp(56))
        self.icon = "cog"
        self._touch_offset_x = 0
        self._touch_offset_y = 0
        self._initial_placed = False
        self._is_dragging = False
        self._drag_threshold = dp(5)

    def on_parent(self, widget, parent):
        if parent and not self._initial_placed:
            self.x = parent.width - self.width - dp(16)
            self.y = dp(16) + dp(56)
            self._initial_placed = True

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_offset_x = self.x - touch.x
            self._touch_offset_y = self.y - touch.y
            self._is_dragging = False
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x + self._touch_offset_x - self.x
            dy = touch.y + self._touch_offset_y - self.y
            if abs(dx) > self._drag_threshold or abs(dy) > self._drag_threshold:
                self._is_dragging = True
            if self._is_dragging:
                new_x = touch.x + self._touch_offset_x
                new_y = touch.y + self._touch_offset_y
                self.x = max(0, min(new_x, Window.width - self.width))
                self.y = max(0, min(new_y, Window.height - self.height))
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if not self._is_dragging:
                self.dispatch('on_release')
            return True
        return super().on_touch_up(touch)


class ThemeController:
    def __init__(self, app):
        self.app = app

    def apply_theme(self, theme_mode=None):
        if theme_mode is None:
            theme_mode = self.app.config_manager.get("theme", "system")
        if theme_mode == "system":
            is_dark = False
            if is_dark:
                self.set_dark_theme()
            else:
                self.set_light_theme()
        elif theme_mode == "dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()
        self.app.rebuild_all_screens()

    def set_light_theme(self):
        self.app.theme_cls.theme_style = "Light"
        self.app.theme_cls.primary_palette = PRIMARY_COLOR
        self.app.theme_cls.accent_palette = ACCENT_COLOR
        Window.clearcolor = get_color_from_hex(BG_LIGHT)

    def set_dark_theme(self):
        self.app.theme_cls.theme_style = "Dark"
        self.app.theme_cls.primary_palette = PRIMARY_COLOR
        self.app.theme_cls.accent_palette = ACCENT_COLOR
        Window.clearcolor = get_color_from_hex(BG_DARK)

class LiveBoosterApp(MDApp):
    title = APP_NAME
    icon = "assets/icon.png"

    config_manager = ObjectProperty(None)
    db_helper = ObjectProperty(None)
    notification_manager = ObjectProperty(None)
    game_tracker = ObjectProperty(None)

    is_tracking = BooleanProperty(False)
    streak_days = NumericProperty(0)
    current_session_minutes = NumericProperty(0)

    news_cache = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.db_helper = DatabaseHelper()
        self.notification_manager = NotificationManager(self)
        self.game_tracker = GameTracker(self)
        self.screen_dict = {}
        self.theme_controller = ThemeController(self)
        self.main_screen = None

    def build(self):
        self.theme_controller.apply_theme()
        self.sm = MDScreenManager(transition=SlideTransition())
        self._init_screens()
        self.sm.add_widget(self.settings_screen)
        self.main_layout = self._build_main_layout()
        self.sm.add_widget(self.main_layout)
        self.sm.current = "main"
        Clock.schedule_once(self.post_build_init, 0.5)
        return self.sm

    def _init_screens(self):
        self.home_screen = HomeScreen(name="home")
        self.tracker_screen = TrackerScreen(name="tracker")
        self.calculator_screen = CalculatorScreen(name="calculator")
        self.news_screen = NewsScreen(name="news")
        self.reminders_screen = RemindersScreen(name="reminders")
        self.settings_screen = SettingsScreen(name="settings")

        self.screen_dict.update({
            "home": self.home_screen,
            "tracker": self.tracker_screen,
            "calculator": self.calculator_screen,
            "news": self.news_screen,
            "reminders": self.reminders_screen,
            "settings": self.settings_screen
        })

    def rebuild_all_screens(self):
        for screen in self.screen_dict.values():
            if hasattr(screen, 'ui_built'):
                screen.ui_built = False
                screen.clear_widgets()
                screen.build_ui()
        if self.main_screen:
            is_light = self.theme_cls.theme_style == "Light"
            self.main_screen.md_bg_color = (0.96, 0.96, 0.96, 1) if is_light else (0.12, 0.12, 0.12, 1)

    def _build_main_layout(self):
        main_screen = MDScreen(name="main")
        self.main_screen = main_screen
        bottom_nav = MDBottomNavigation()

        tab_home = MDBottomNavigationItem(name="home", text="Главная", icon="home")
        tab_home.add_widget(self.home_screen)
        tab_tracker = MDBottomNavigationItem(name="tracker", text="Трекер", icon="fire")
        tab_tracker.add_widget(self.tracker_screen)
        tab_calculator = MDBottomNavigationItem(name="calculator", text="Доходы", icon="calculator-variant")
        tab_calculator.add_widget(self.calculator_screen)
        tab_news = MDBottomNavigationItem(name="news", text="Новости", icon="newspaper-variant-outline")
        tab_news.add_widget(self.news_screen)
        tab_reminders = MDBottomNavigationItem(name="reminders", text="Напоминания", icon="bell-outline")
        tab_reminders.add_widget(self.reminders_screen)

        bottom_nav.add_widget(tab_home)
        bottom_nav.add_widget(tab_tracker)
        bottom_nav.add_widget(tab_calculator)
        bottom_nav.add_widget(tab_news)
        bottom_nav.add_widget(tab_reminders)

        float_layout = FloatLayout()
        float_layout.add_widget(bottom_nav)

        self.settings_fab = DraggableFAB()
        self.settings_fab.md_bg_color = self.theme_cls.primary_color
        self.settings_fab.bind(on_release=lambda x: self.open_settings())
        float_layout.add_widget(self.settings_fab)

        main_screen.add_widget(float_layout)
        return main_screen

    def open_settings(self):
        self.sm.current = "settings"

    def post_build_init(self, dt):
        self.game_tracker.start_monitoring()
        self.notification_manager.schedule_all()
        self.streak_days = self.db_helper.get_streak_days()

        # Принудительно устанавливаем YouTube-плейлист, если ещё не задан
        if not self.config_manager.get("youtube_rss_url"):
            self.config_manager.set("youtube_rss_url", DEFAULT_RSS_URL)
            self.config_manager.save()

        self.load_news_cache()
        self.fetch_and_cache_news()
        Clock.schedule_interval(lambda dt: self.fetch_and_cache_news(), 30)

    def load_news_cache(self):
        try:
            with open("news_cache.json", "r", encoding="utf-8") as f:
                self.news_cache = json.load(f)
        except:
            pass

    def save_news_cache(self):
        try:
            with open("news_cache.json", "w", encoding="utf-8") as f:
                json.dump(self.news_cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _is_short(self, entry):
        """Возвращает True, если видео является Shorts."""
        title = entry.title.lower()
        summary = getattr(entry, 'summary', '').lower()
        if '#shorts' in title or '#shorts' in summary:
            return True
        duration = entry.get('yt_duration')
        if duration is not None:
            try:
                if int(duration) < 60:
                    return True
            except:
                pass
        return False

    def fetch_and_cache_news(self, *args):
        def _load():
            try:
                import feedparser
                rss_url = self.config_manager.get("youtube_rss_url", DEFAULT_RSS_URL)
                feed = feedparser.parse(rss_url)
                if feed.bozo and len(feed.entries) == 0:
                    return
                entries = feed.entries
                news_list = []
                for entry in entries:
                    if self._is_short(entry):
                        continue
                    if len(news_list) >= 5:
                        break
                    thumbnail = ""
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        thumb_url = entry.media_thumbnail[0]['url']
                        thumb_url = thumb_url.replace('maxresdefault.jpg', 'hqdefault.jpg')
                        thumbnail = thumb_url
                    news_list.append({
                        "title": entry.title,
                        "text": getattr(entry, 'summary', '')[:200],
                        "date": getattr(entry, 'published', '')[:10],
                        "link": entry.link,
                        "thumbnail": thumbnail
                    })
                Clock.schedule_once(lambda dt: self._update_cache(news_list))
            except Exception as e:
                print(f"Cache news error: {e}")
        threading.Thread(target=_load, daemon=True).start()

    def _update_cache(self, news_list):
        self.news_cache = news_list
        self.save_news_cache()

    def on_start(self):
        if platform == "android":
            self.request_android_permissions()
        self.notification_manager.show_snackbar("Добро пожаловать в LIVE BOOSTER!")

    def request_android_permissions(self):
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.POST_NOTIFICATIONS,
            Permission.FOREGROUND_SERVICE,
            Permission.PACKAGE_USAGE_STATS,
            Permission.VIBRATE,
        ])

    def on_pause(self):
        self.config_manager.save()
        self.save_news_cache()
        return True

    def on_resume(self):
        self.theme_controller.apply_theme()

    def on_stop(self):
        self.game_tracker.stop_monitoring()
        self.config_manager.save()
        self.save_news_cache()
        self.db_helper.close()
        print("Приложение LIVE BOOSTER завершено.")

    def launch_game(self):
        if platform == "android":
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            context = PythonActivity.mActivity
            try:
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"liverussia://"))
                intent.setPackage(GAME_PACKAGE)
                context.startActivity(intent)
            except Exception as e:
                print(f"Ошибка запуска игры: {e}")
                try:
                    intent = Intent(Intent.ACTION_VIEW, Uri.parse(f"market://details?id={GAME_PACKAGE}"))
                    context.startActivity(intent)
                except:
                    pass
        else:
            Snackbar(text="Функция запуска игры доступна на Android").open()

if __name__ == "__main__":
    app = LiveBoosterApp()
    app.run()