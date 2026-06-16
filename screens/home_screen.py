# screens/home_screen.py
import random
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.fitimage import FitImage
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp

class HomeScreen(MDScreen):
    greeting_text = StringProperty("Привет, игрок!")
    streak_flame_text = StringProperty("Огонёк не активен")
    streak_days = NumericProperty(0)
    is_flame_active = BooleanProperty(False)
    motivation_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.ui_built = False
        self.motivation_messages = [
            "Ты слил в казино? Это всего лишь игра. Ты сам на это решился. Не удаляй, вернись и отыграйся!",
            "Каждая минута в игре делает тебя сильнее. Продолжай фармить!",
            "Твой персонаж ждёт тебя. Не бросай свой путь!",
            "В LIVE RUSSIA возможно всё – открой бизнес, купи тачку, построй дом.",
            "Помни: даже маленький шаг сегодня – это большой прогресс завтра.",
            "Фракции ждут пополнения. Вливайся в RP-сообщество!",
            "Не дай казино разрушить твою мечту. Играй с умом.",
            "Ты сильнее, чем думаешь. Возвращайся и докажи всем!",
        ]
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

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self._add_transparent_bg(scroll)
        self.scroll = scroll

        self.layout = BoxLayout(orientation="vertical", padding=[dp(12)], spacing=dp(12), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))

        # Приветствие и огонёк
        self.greeting_card = MDCard(size_hint=(1, None), height=dp(150), radius=[20], padding=dp(16))
        rel = MDRelativeLayout()
        self.greeting_card.add_widget(rel)
        greet = MDLabel(text=self.greeting_text, font_style="H5", bold=True, theme_text_color="Primary",
                        pos_hint={"left":1,"top":1}, size_hint=(0.7,None), height=dp(30))
        rel.add_widget(greet)
        self.bind(greeting_text=greet.setter("text"))
        self.flame_icon = MDIcon(icon="fire" if self.is_flame_active else "fire-off",
                                 font_size=sp(36), theme_text_color="Primary",
                                 pos_hint={"right":1,"top":1}, size_hint=(None,None), size=(dp(48),dp(48)))
        rel.add_widget(self.flame_icon)
        self.bind(is_flame_active=lambda s,v: self._update_flame(v))
        stat = MDLabel(text=self.streak_flame_text, font_style="Body1", theme_text_color="Secondary",
                       pos_hint={"center_y":0.6,"left":1}, size_hint=(0.8,None), height=dp(24))
        rel.add_widget(stat)
        self.bind(streak_flame_text=stat.setter("text"))
        days = MDLabel(text=f"Дней в огне: {self.streak_days}", font_style="Body2", theme_text_color="Hint",
                       pos_hint={"center_y":0.3,"left":1}, size_hint=(0.8,None), height=dp(20))
        rel.add_widget(days)
        self.bind(streak_days=days.setter("text"))
        self.layout.add_widget(self.greeting_card)

        # Кнопка запуска игры
        self.launch_card = MDCard(size_hint=(1,None), height=dp(100), radius=[20],
                                  md_bg_color=theme_cls.primary_color, on_release=self.launch_game)
        box = BoxLayout(orientation="horizontal", padding=dp(16), spacing=dp(12))
        box.add_widget(MDIcon(icon="play-circle", font_size=sp(40), theme_text_color="Custom", text_color=(1,1,1,1)))
        box.add_widget(MDLabel(text="ЗАЙТИ В ИГРУ", font_style="H5", bold=True, theme_text_color="Custom", text_color=(1,1,1,1)))
        self.launch_card.add_widget(box)
        self.layout.add_widget(self.launch_card)

        # Новости (горизонтальный скролл) – горизонтальный макет
        news_header = MDLabel(text="Последние новости", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30))
        self.layout.add_widget(news_header)
        self.news_scroll = ScrollView(do_scroll_y=False, bar_width=dp(2), size_hint=(1,None), height=dp(90))
        self._add_transparent_bg(self.news_scroll)
        self.news_box = BoxLayout(orientation="horizontal", spacing=dp(12), padding=[dp(4),0], size_hint_x=None)
        self.news_box.bind(minimum_width=self.news_box.setter("width"))
        self.news_scroll.add_widget(self.news_box)
        self.layout.add_widget(self.news_scroll)

        # Ежедневные задачи
        self.task_card = MDCard(size_hint=(1,None), height=dp(220), radius=[20], padding=dp(16))
        self.task_list_layout = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.task_list_layout.bind(minimum_height=self.task_list_layout.setter("height"))
        self.task_card.add_widget(self.task_list_layout)
        self.layout.add_widget(self.task_card)

        # Мотивация
        self.mot_card = MDCard(size_hint=(1,None), height=dp(130), radius=[20], padding=dp(16))
        quote = MDLabel(text=self.motivation_text, font_style="Body1", theme_text_color="Primary", halign="center", valign="middle")
        self.bind(motivation_text=quote.setter("text"))
        self.mot_card.add_widget(quote)
        self.layout.add_widget(self.mot_card)

        scroll.add_widget(self.layout)
        self.clear_widgets()
        self.add_widget(scroll)

        Clock.schedule_once(lambda dt: self.update_data_from_app(), 0.1)

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

    def _update_flame(self, active):
        self.flame_icon.icon = "fire" if active else "fire-off"

    def update_data_from_app(self):
        app = MDApp.get_running_app()
        if not app:
            return
        self.app = app
        username = app.db_helper.get_username()
        self.greeting_text = f"Привет, {username}!"
        self.is_flame_active = app.is_tracking
        self.streak_days = app.streak_days
        self.streak_flame_text = "Огонёк горит! Дней подряд: {}".format(self.streak_days) if app.is_tracking else "Огонёк не активен. Зайди в игру!"
        self.motivation_text = random.choice(self.motivation_messages)

        cache = app.news_cache if hasattr(app, 'news_cache') else []
        self._update_news_from_cache(cache)
        self._load_daily_tasks()

    def _update_news_from_cache(self, news_cache):
        self.news_box.clear_widgets()
        if not news_cache:
            sample = [
                {"title":"Загрузка новостей...","thumbnail":""},
                {"title":"Включите VPN (если в РФ)","thumbnail":""},
                {"title":"Канал LITVA","thumbnail":""},
            ]
            news_cache = sample

        app = MDApp.get_running_app()
        is_light = app.theme_cls.theme_style == "Light" if app else True
        card_bg = (1, 1, 1, 1) if is_light else (0.12, 0.12, 0.12, 1)
        text_color = (0, 0, 0, 1) if is_light else (1, 1, 1, 1)

        for item in news_cache:
            card = MDCard(
                size_hint=(None, None),
                size=(dp(260), dp(80)),
                radius=[12],
                elevation=0,
                padding=0,
                md_bg_color=card_bg
            )
            h_layout = BoxLayout(orientation="horizontal", spacing=0, padding=0)

            thumb = item.get("thumbnail")
            if thumb:
                # Используем FitImage для мгновенного отображения
                img = FitImage(
                    source=thumb,
                    size_hint=(None, None),
                    size=(dp(80), dp(80)),
                    radius=[12, 0, 0, 12],  # скругление только слева
                    mipmap=True
                )
            else:
                # Заглушка с первой буквой
                first_letter = item.get("title", "?")[0].upper()
                img_container = FloatLayout(size_hint=(None, None), size=(dp(80), dp(80)))
                with img_container.canvas.before:
                    Color(0.3, 0.3, 0.3, 1)
                    Rectangle(size=(dp(80), dp(80)), pos=(0, 0))
                label = MDLabel(
                    text=first_letter,
                    font_style="H4",
                    bold=True,
                    theme_text_color="Custom",
                    text_color=(1,1,1,1),
                    halign="center",
                    valign="middle",
                    size_hint=(1, 1)
                )
                img_container.add_widget(label)
                img = img_container
            h_layout.add_widget(img)

            # Заголовок
            title_label = MDLabel(
                text=item.get("title",""),
                font_style="Body2",
                bold=True,
                theme_text_color="Custom",
                text_color=text_color,
                halign="left",
                valign="middle",
                size_hint=(1, 1),
                padding=[dp(8), dp(4)],
                shorten=True,
                shorten_from="right",
                max_lines=2
            )
            h_layout.add_widget(title_label)

            card.add_widget(h_layout)
            self.news_box.add_widget(card)

    def _load_daily_tasks(self):
        self.task_list_layout.clear_widgets()
        self.task_list_layout.add_widget(MDLabel(text="Ежедневные задачи", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30)))
        reminders = self.app.db_helper.get_reminders()
        active_reminders = [r for r in reminders if r["active"]]
        if not active_reminders:
            self.task_list_layout.add_widget(MDLabel(text="Нет активных напоминаний.", font_style="Body2", theme_text_color="Hint"))
        else:
            for r in active_reminders:
                line = f"• {r['text']} ({r['date']} {r['time']})"
                lbl = MDLabel(text=line, font_style="Body2", theme_text_color="Secondary", size_hint_y=None, height=dp(28))
                self.task_list_layout.add_widget(lbl)

    def launch_game(self, *args):
        app = MDApp.get_running_app()
        if app:
            app.launch_game()
        else:
            Snackbar(text="Функция запуска игры доступна на Android").open()