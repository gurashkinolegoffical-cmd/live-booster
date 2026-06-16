# screens/news_screen.py
import feedparser
import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp
import webbrowser

# YouTube плейлист загрузок канала LITVA
RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=UUlC6vz4MPgTXl8ijWh5USiA"

class NewsScreen(MDScreen):
    news_data = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.ui_built = False
        self.news_container = None
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, *args):
        if self.ui_built:
            return
        app = MDApp.get_running_app()
        if not app:
            Clock.schedule_once(self.build_ui, 0.2)
            return
        self.app = app
        theme_cls = app.theme_cls
        self.ui_built = True

        main_box = BoxLayout(orientation="vertical", padding=[dp(12)], spacing=dp(8))
        btn_refresh = MDRaisedButton(
            text="Обновить новости",
            size_hint=(1, None),
            height=dp(40),
            md_bg_color=theme_cls.primary_color,
            on_release=lambda x: threading.Thread(target=self.fetch_news, daemon=True).start()
        )
        main_box.add_widget(btn_refresh)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self._add_transparent_bg(scroll)
        self.scroll = scroll

        self.news_container = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(4)])
        self.news_container.bind(minimum_height=self.news_container.setter("height"))

        scroll.add_widget(self.news_container)
        main_box.add_widget(scroll)

        self.clear_widgets()
        self.add_widget(main_box)

        self.load_sample_news()
        threading.Thread(target=self.fetch_news, daemon=True).start()

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

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

    def fetch_news(self, *args):
        try:
            Clock.schedule_once(lambda dt: Snackbar(text="Загрузка новостей...").open())
            feed = feedparser.parse(RSS_URL)
            if feed.bozo and len(feed.entries) == 0:
                raise Exception("RSS feed is empty or invalid")
            entries = feed.entries
            news_list = []
            for entry in entries:
                if self._is_short(entry):
                    continue
                if len(news_list) >= 5:
                    break
                news_list.append({
                    "title": entry.title,
                    "text": getattr(entry, 'summary', '')[:300],
                    "date": getattr(entry, 'published', '')[:10],
                    "link": entry.link
                })
            Clock.schedule_once(lambda dt, data=news_list: self._apply_news(data))
        except Exception as e:
            print(f"RSS error: {e}")
            Clock.schedule_once(lambda dt, err=e: Snackbar(text=f"Ошибка загрузки RSS: {err}").open())

    def _apply_news(self, news_list):
        self.news_data = news_list
        self.display_news()
        Snackbar(text=f"Загружено {len(news_list)} новостей").open()
        app = MDApp.get_running_app()
        if app:
            app.news_cache = news_list

    def load_sample_news(self):
        sample = [
            {"title":"Обновление карты","text":"Добавлены новые районы.","date":"12.06.2026","link":"#"},
            {"title":"Ивент «Гонки»","text":"Участвуйте и получайте призы.","date":"11.06.2026","link":"#"},
            {"title":"Набор в полицию","text":"Открыты вакансии.","date":"10.06.2026","link":"#"},
            {"title":"Скидки на бизнес","text":"30% скидка.","date":"09.06.2026","link":"#"},
        ]
        self.news_data = sample
        self.display_news()

    def display_news(self):
        if not self.news_container:
            return
        self.news_container.clear_widgets()
        app = MDApp.get_running_app()
        theme_cls = app.theme_cls if app else None
        for item in self.news_data:
            bg = theme_cls.bg_light if theme_cls and theme_cls.theme_style=="Light" else (theme_cls.bg_dark if theme_cls else [0.2,0.2,0.2,1])
            card = MDCard(
                size_hint=(1, None),
                height=dp(200),
                radius=[16],
                padding=dp(8),
                md_bg_color=bg,
                on_release=lambda x, link=item.get("link"): self.open_link(link)
            )
            card_layout = BoxLayout(orientation="vertical", spacing=dp(4))
            header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(8))
            title_label = MDLabel(
                text=item.get("title",""),
                font_style="Subtitle1",
                bold=True,
                theme_text_color="Primary",
                size_hint_x=0.7,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right"
            )
            date_label = MDLabel(
                text=item.get("date",""),
                font_style="Caption",
                theme_text_color="Hint",
                halign="right",
                valign="middle",
                size_hint_x=0.3
            )
            header.add_widget(title_label)
            header.add_widget(date_label)
            card_layout.add_widget(header)

            text_scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
            text_label = MDLabel(
                text=item.get("text",""),
                font_style="Body2",
                theme_text_color="Secondary",
                halign="left",
                valign="top",
                size_hint_y=None,
                height=dp(120),
                text_size=(card.width - dp(32), None)
            )
            card.bind(width=lambda instance, value: setattr(text_label, 'text_size', (value - dp(32), None)))
            text_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
            text_scroll.add_widget(text_label)
            card_layout.add_widget(text_scroll)

            card.add_widget(card_layout)
            self.news_container.add_widget(card)

    def open_link(self, link):
        if link and link != "#":
            try:
                webbrowser.open(link)
            except Exception as e:
                Snackbar(text=f"Не удалось открыть ссылку: {e}").open()
        else:
            Snackbar(text="Ссылка отсутствует").open()