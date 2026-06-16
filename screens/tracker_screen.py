# screens/tracker_screen.py
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp
import os
import csv
from kivy.utils import platform

class TrackerScreen(MDScreen):
    is_monitoring = BooleanProperty(False)
    session_start_time = ObjectProperty(None, allownone=True)
    current_session_minutes = NumericProperty(0)
    streak_days = NumericProperty(0)
    last_session_time = StringProperty("—")
    status_text = StringProperty("Мониторинг не активен")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self._monitor_timer = None
        self.ui_built = False
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

        # Status card
        self.status_card = self._create_status_card(theme_cls)
        self.layout.add_widget(self.status_card)

        # Session card
        self.session_card = self._create_session_card(theme_cls)
        self.layout.add_widget(self.session_card)

        # Streak card
        self.streak_card = self._create_streak_card(theme_cls)
        self.layout.add_widget(self.streak_card)

        # History card
        self.history_card = self._create_history_card(theme_cls)
        self.layout.add_widget(self.history_card)

        # Кнопка экспорта CSV
        export_btn = MDRaisedButton(
            text="Экспорт истории (CSV)",
            size_hint=(1, None),
            height=dp(40),
            md_bg_color=theme_cls.primary_color,
            on_release=self.export_csv
        )
        self.layout.add_widget(export_btn)

        scroll.add_widget(self.layout)
        self.clear_widgets()
        self.add_widget(scroll)

        self.update_from_app()

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

    def _create_status_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(130), radius=[20], padding=dp(16))
        rel = MDRelativeLayout()
        card.add_widget(rel)
        self.status_icon = MDIcon(icon="monitor-eye" if self.is_monitoring else "monitor-off",
                                  font_size=sp(40), theme_text_color="Primary",
                                  pos_hint={"right":1,"top":1}, size_hint=(None,None), size=(dp(48),dp(48)))
        rel.add_widget(self.status_icon)
        self.bind(is_monitoring=lambda s,v: self._update_icon(v))
        stat = MDLabel(text=self.status_text, font_style="H6", bold=True, theme_text_color="Primary",
                       pos_hint={"left":1,"top":1}, size_hint=(0.7,None), height=dp(30))
        rel.add_widget(stat)
        self.bind(status_text=stat.setter("text"))
        btn_box = BoxLayout(orientation="horizontal", spacing=dp(10),
                            pos_hint={"left":1,"bottom":1}, size_hint=(0.7,None), height=dp(36))
        btn_box.add_widget(MDRaisedButton(text="▶ Старт", on_release=self.start_monitoring,
                                          md_bg_color=theme_cls.primary_color))
        btn_box.add_widget(MDRaisedButton(text="⏹ Стоп", on_release=self.stop_monitoring,
                                          md_bg_color=(0.9,0.2,0.2,1)))
        rel.add_widget(btn_box)
        return card

    def _update_icon(self, value):
        self.status_icon.icon = "monitor-eye" if value else "monitor-off"

    def _create_session_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(140), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="vertical", spacing=dp(6))
        box.add_widget(MDLabel(text="Текущая сессия", font_style="H6", bold=True, theme_text_color="Primary",
                               size_hint_y=None, height=dp(30)))
        self.session_time_label = MDLabel(text=f"Длительность: {self.current_session_minutes} мин.",
                                          font_style="Body1", theme_text_color="Secondary")
        box.add_widget(self.session_time_label)
        self.last_session_label = MDLabel(text=f"Последняя сессия: {self.last_session_time}",
                                          font_style="Body2", theme_text_color="Hint")
        box.add_widget(self.last_session_label)
        self._progress_bar = MDProgressBar(value=0, max=15, size_hint=(1,None), height=dp(8))
        box.add_widget(self._progress_bar)
        self.bind(current_session_minutes=self._update_progress)
        card.add_widget(box)
        return card

    def _update_progress(self, instance, value):
        if value > 15:
            value = 15
        self._progress_bar.value = value

    def _create_streak_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(120), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="horizontal", spacing=dp(12))
        box.add_widget(MDIcon(icon="fire", font_size=sp(48), theme_text_color="Custom", text_color=(1,0.4,0,1)))
        tbox = BoxLayout(orientation="vertical", spacing=dp(4))
        self.streak_label = MDLabel(text=f"Огненный режим: {self.streak_days} дней", font_style="H6", bold=True,
                                    theme_text_color="Primary")
        tbox.add_widget(self.streak_label)
        tbox.add_widget(MDLabel(text="Зайди в игру на 15+ минут, чтобы продлить!", font_style="Body2",
                                theme_text_color="Secondary"))
        box.add_widget(tbox)
        card.add_widget(box)
        return card

    def _create_history_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(200), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="vertical", spacing=dp(4))
        box.add_widget(MDLabel(text="История сессий", font_style="H6", bold=True, theme_text_color="Primary",
                               size_hint_y=None, height=dp(30)))
        self.history_box = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_y=None)
        self.history_box.bind(minimum_height=self.history_box.setter("height"))
        box.add_widget(self.history_box)
        card.add_widget(box)
        return card

    def update_from_app(self):
        app = MDApp.get_running_app()
        if not app:
            return
        self.streak_days = app.streak_days
        if hasattr(self, 'streak_label'):
            self.streak_label.text = f"Огненный режим: {self.streak_days} дней"
        self._update_history_display()

    def _update_history_display(self):
        self.history_box.clear_widgets()
        sessions = self.app.db_helper.get_sessions(5)
        for s in sessions:
            self.history_box.add_widget(MDLabel(text=f"• {s['start']} - {s['end']} ({s['minutes']} мин.)",
                                                font_style="Body2", theme_text_color="Secondary",
                                                size_hint_y=None, height=dp(24)))

    def start_monitoring(self, *args):
        if self.is_monitoring:
            Snackbar(text="Мониторинг уже запущен.").open()
            return
        self.is_monitoring = True
        self.status_text = "Мониторинг активен"
        self.session_start_time = datetime.now()
        self.current_session_minutes = 0
        self._monitor_timer = Clock.schedule_interval(self._emulate_timer, 60)
        Snackbar(text="Мониторинг начат. Идите в игру!").open()

    def stop_monitoring(self, *args):
        if not self.is_monitoring:
            Snackbar(text="Мониторинг не активен.").open()
            return
        if self._monitor_timer:
            Clock.unschedule(self._monitor_timer)
        self.is_monitoring = False
        self.status_text = "Мониторинг не активен"
        if self.session_start_time:
            now = datetime.now()
            delta = now - self.session_start_time
            minutes = int(delta.total_seconds() // 60)
            self.app.db_helper.add_session(
                self.session_start_time.strftime("%d.%m.%Y %H:%M"),
                now.strftime("%d.%m.%Y %H:%M"),
                minutes
            )
            if minutes >= 15:
                self.app.streak_days += 1
                self.app.db_helper.set_streak_days(self.app.streak_days)
                Snackbar(text=f"Огонёк засчитан! Текущий streak: {self.app.streak_days} дн.").open()
            else:
                Snackbar(text="Сессия слишком коротка для огонька.").open()
        self.session_start_time = None
        self.current_session_minutes = 0
        self.update_from_app()

    def _emulate_timer(self, dt):
        self.current_session_minutes += 1
        if self.current_session_minutes == 15:
            Snackbar(text="Вы достигли порога огонька! Продолжайте!").open()

    def export_csv(self, *args):
        """Экспортирует историю сессий и доходы в CSV-файл."""
        try:
            # Выбираем путь для сохранения
            if platform == "android":
                from android.storage import primary_external_storage_path
                export_dir = os.path.join(primary_external_storage_path(), "Download")
            else:
                export_dir = os.getcwd()
            if not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)

            filename = f"live_booster_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(export_dir, filename)

            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Заголовок для сессий
                writer.writerow(["=== История сессий ==="])
                writer.writerow(["Начало", "Конец", "Длительность (мин)"])
                sessions = self.app.db_helper.get_sessions(100)  # все сессии
                for s in sessions:
                    writer.writerow([s["start"], s["end"], s["minutes"]])

                # Пустая строка
                writer.writerow([])

                # Доходы
                state = self.app.db_helper.get_calculator_state()
                writer.writerow(["=== Данные калькулятора ==="])
                writer.writerow(["Доход за смену", "Смен в день", "За день", "За неделю", "За месяц", "За год", "За 5 лет"])
                writer.writerow([
                    state["income_text"],
                    state["shifts_text"],
                    state["day"],
                    state["week"],
                    state["month"],
                    state["year"],
                    state["five_years"]
                ])

            Snackbar(text=f"Файл сохранён: {filepath}").open()
        except Exception as e:
            Snackbar(text=f"Ошибка экспорта: {e}").open()