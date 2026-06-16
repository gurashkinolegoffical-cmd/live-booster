# screens/settings_screen.py
import re
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp

# Список запрещённых слов
BAD_WORDS = {
    'fuck', 'shit', 'ass', 'bitch', 'dick', 'piss', 'cunt', 'whore',
    'bastard', 'damn', 'hell', 'fag', 'slut', 'cock', 'douche', 'eblan',
    'pidor', 'pidr', 'hui', 'pizda', 'pizdec', 'gandon', 'mudak',
    'suka', 'blyad', 'nahui', 'gavno', 'chmo', 'ublyudok', 'svoloch'
}

class SettingsScreen(MDScreen):
    theme_mode = StringProperty("system")
    notifications_enabled = BooleanProperty(True)
    sound_enabled = BooleanProperty(True)
    vibration_enabled = BooleanProperty(True)
    username = StringProperty("игрок")
    tracker_interval = StringProperty("30")
    app_version = StringProperty("1.0")

    blocked = BooleanProperty(False)
    block_remaining = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.ui_built = False
        self._block_event = None
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
        self.load_settings()
        self.ui_built = True

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self._add_transparent_bg(scroll)
        self.scroll = scroll

        self.layout = BoxLayout(orientation="vertical", padding=[dp(12)], spacing=dp(12), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))

        self.profile_card = self._create_profile_card(theme_cls)
        self.layout.add_widget(self.profile_card)

        self.theme_card = self._create_theme_card(theme_cls)
        self.layout.add_widget(self.theme_card)

        self.notif_card = self._create_notifications_card(theme_cls)
        self.layout.add_widget(self.notif_card)

        self.tracker_card = self._create_tracker_card(theme_cls)
        self.layout.add_widget(self.tracker_card)

        btn_back = MDRaisedButton(
            text="← На главный экран",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=theme_cls.primary_color,
            on_release=self.go_to_main,
        )
        self.layout.add_widget(btn_back)

        self.info_card = self._create_info_card(theme_cls)
        self.layout.add_widget(self.info_card)

        scroll.add_widget(self.layout)
        self.clear_widgets()
        self.add_widget(scroll)

        self.bind(blocked=self._update_save_button_state)

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

    def load_settings(self):
        cfg = self.app.config_manager
        self.theme_mode = cfg.get("theme", "system")
        self.notifications_enabled = cfg.get("notifications", True)
        self.sound_enabled = cfg.get("sound_enabled", True)
        self.vibration_enabled = cfg.get("vibration", True)
        self.username = cfg.get("username", "игрок")
        self.tracker_interval = str(cfg.get("tracker_interval", 30))

    def save_settings(self):
        cfg = self.app.config_manager
        cfg.set("theme", self.theme_mode)
        cfg.set("notifications", self.notifications_enabled)
        cfg.set("sound_enabled", self.sound_enabled)
        cfg.set("vibration", self.vibration_enabled)
        cfg.set("username", self.username)
        cfg.set("tracker_interval", int(self.tracker_interval) if self.tracker_interval.isdigit() else 30)
        cfg.save()
        self.app.theme_controller.apply_theme(self.theme_mode)
        Snackbar(text="Настройки сохранены").open()

    def _create_profile_card(self, theme_cls):
        bg = theme_cls.bg_light if theme_cls.theme_style=="Light" else theme_cls.bg_dark
        card = MDCard(size_hint=(1,None), height=dp(180), radius=[20], padding=dp(16), md_bg_color=bg)
        box = BoxLayout(orientation="vertical", spacing=dp(8))
        box.add_widget(MDLabel(text="Профиль", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30)))

        # Поле ввода с форматом Name_Surname
        name_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        name_box.add_widget(MDLabel(text="Имя:", theme_text_color="Secondary", size_hint_x=0.3, halign="right"))
        self.username_input = TextInput(
            text=self.username if re.fullmatch(r'[A-Za-z_]+', self.username) else "",
            hint_text="Name_Surname",
            multiline=False,
            size_hint_x=0.7,
            height=dp(40),
            font_size=dp(14),
            input_filter=self._filter_username
        )
        name_box.add_widget(self.username_input)
        box.add_widget(name_box)

        # Кнопка сохранения и таймер блокировки
        action_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
        self.save_profile_btn = MDRaisedButton(
            text="Сохранить имя",
            size_hint=(0.6, 1),
            md_bg_color=theme_cls.primary_color,
            on_release=lambda x: self._update_username()
        )
        self.block_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Error",
            size_hint=(0.4, 1),
            halign="center",
            valign="middle"
        )
        action_box.add_widget(self.save_profile_btn)
        action_box.add_widget(self.block_label)
        box.add_widget(action_box)

        card.add_widget(box)
        return card

    def _filter_username(self, substring, from_undo):
        """Разрешает только A-Z, a-z и _"""
        return ''.join(c for c in substring if c.isalpha() and c.isascii() or c == '_')

    def _update_save_button_state(self, *args):
        if self.blocked:
            self.save_profile_btn.disabled = True
            self.block_label.text = f"Ждите {self.block_remaining}с"
        else:
            self.save_profile_btn.disabled = False
            self.block_label.text = ""

    def _update_username(self):
        if self.blocked:
            return
        new_name = self.username_input.text.strip()
        if not new_name:
            Snackbar(text="Введите имя").open()
            return

        if not re.fullmatch(r'[A-Za-z_]+', new_name):
            Snackbar(text="Разрешены только латинские буквы и '_'").open()
            return

        lower_name = new_name.lower()
        for part in lower_name.split('_'):
            if part in BAD_WORDS:
                self._start_block()
                Snackbar(text="Недопустимое слово! Блокировка на 1 минуту.").open()
                return

        self.username = new_name
        self.app.db_helper.set_username(new_name)
        Snackbar(text=f"Имя изменено на {new_name}").open()
        self.save_settings()

    def _start_block(self):
        self.blocked = True
        self.block_remaining = 60
        if self._block_event:
            Clock.unschedule(self._block_event)
        self._block_event = Clock.schedule_interval(self._tick_block, 1)

    def _tick_block(self, dt):
        self.block_remaining -= 1
        if self.block_remaining <= 0:
            self.blocked = False
            self.block_remaining = 0
            Clock.unschedule(self._block_event)
            self._block_event = None
            Snackbar(text="Блокировка снята").open()
        self._update_save_button_state()

    def _create_theme_card(self, theme_cls):
        bg = theme_cls.bg_light if theme_cls.theme_style=="Light" else theme_cls.bg_dark
        card = MDCard(size_hint=(1,None), height=dp(80), radius=[20], padding=dp(16), md_bg_color=bg)
        box = BoxLayout(orientation="vertical", spacing=dp(6))
        box.add_widget(MDLabel(text="Оформление", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30)))
        switch_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
        switch_box.add_widget(MDLabel(text="Тёмная тема:", theme_text_color="Secondary", size_hint_x=0.5))
        self.theme_checkbox = MDCheckbox(active=self.theme_mode == "dark", size_hint_x=0.5)
        self.theme_checkbox.bind(active=self._toggle_theme)
        switch_box.add_widget(self.theme_checkbox)
        box.add_widget(switch_box)
        card.add_widget(box)
        return card

    def _toggle_theme(self, checkbox, value):
        self.theme_mode = "dark" if value else "light"
        self.save_settings()

    def _create_notifications_card(self, theme_cls):
        bg = theme_cls.bg_light if theme_cls.theme_style=="Light" else theme_cls.bg_dark
        card = MDCard(size_hint=(1,None), height=dp(170), radius=[20], padding=dp(16), md_bg_color=bg)
        box = BoxLayout(orientation="vertical", spacing=dp(6))
        box.add_widget(MDLabel(text="Уведомления", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30)))
        notif_row = self._checkbox_row("Уведомления:", self.notifications_enabled)
        self.notif_checkbox = notif_row.children[0]
        self.notif_checkbox.bind(active=self._toggle_notifications)
        box.add_widget(notif_row)
        sound_row = self._checkbox_row("Звук:", self.sound_enabled)
        self.sound_checkbox = sound_row.children[0]
        self.sound_checkbox.bind(active=self._toggle_sound)
        box.add_widget(sound_row)
        vibro_row = self._checkbox_row("Вибрация:", self.vibration_enabled)
        self.vibro_checkbox = vibro_row.children[0]
        self.vibro_checkbox.bind(active=self._toggle_vibration)
        box.add_widget(vibro_row)
        card.add_widget(box)
        return card

    def _checkbox_row(self, label_text, active):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
        row.add_widget(MDLabel(text=label_text, theme_text_color="Secondary", size_hint_x=0.5))
        cb = MDCheckbox(active=active, size_hint_x=0.5)
        row.add_widget(cb)
        return row

    def _toggle_notifications(self, checkbox, value):
        self.notifications_enabled = value
        self.save_settings()

    def _toggle_sound(self, checkbox, value):
        self.sound_enabled = value
        self.save_settings()

    def _toggle_vibration(self, checkbox, value):
        self.vibration_enabled = value
        self.save_settings()

    def _create_tracker_card(self, theme_cls):
        bg = theme_cls.bg_light if theme_cls.theme_style=="Light" else theme_cls.bg_dark
        card = MDCard(size_hint=(1,None), height=dp(120), radius=[20], padding=dp(16), md_bg_color=bg)
        box = BoxLayout(orientation="vertical", spacing=dp(6))
        box.add_widget(MDLabel(text="Трекер игры", font_style="H6", bold=True, theme_text_color="Primary", size_hint_y=None, height=dp(30)))
        interval_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
        interval_box.add_widget(MDLabel(text="Интервал (сек):", theme_text_color="Secondary", size_hint_x=0.5))
        self.interval_input = TextInput(text=self.tracker_interval, input_filter="int", multiline=False, size_hint_x=0.5, height=dp(36))
        interval_box.add_widget(self.interval_input)
        box.add_widget(interval_box)
        save_btn = MDFlatButton(text="Сохранить интервал", on_release=lambda x: self._save_tracker_interval())
        box.add_widget(save_btn)
        card.add_widget(box)
        return card

    def _save_tracker_interval(self):
        new_val = self.interval_input.text.strip()
        if new_val.isdigit() and int(new_val) >= 5:
            self.tracker_interval = new_val
            Snackbar(text=f"Интервал обновлён ({new_val} с)").open()
            self.save_settings()
        else:
            Snackbar(text="Введите число не менее 5").open()

    def _create_info_card(self, theme_cls):
        bg = theme_cls.bg_light if theme_cls.theme_style=="Light" else theme_cls.bg_dark
        card = MDCard(size_hint=(1,None), height=dp(100), radius=[20], padding=dp(16), md_bg_color=bg)
        box = BoxLayout(orientation="vertical", spacing=dp(4))
        box.add_widget(MDLabel(text=f"LIVE BOOSTER v{self.app_version}", font_style="Body1", bold=True, theme_text_color="Primary"))
        box.add_widget(MDLabel(text="Компаньон для LIVE RUSSIA", font_style="Body2", theme_text_color="Secondary"))
        box.add_widget(MDLabel(text="© 2026, All rights reserved.", font_style="Caption", theme_text_color="Hint"))
        card.add_widget(box)
        return card

    def go_to_main(self, *args):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'sm'):
            app.sm.current = "main"
        else:
            Snackbar(text="Ошибка навигации").open()