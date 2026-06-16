# screens/reminders_screen.py
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp

class RemindersScreen(MDScreen):
    reminders = ListProperty([])
    next_payday = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
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

        self.reminders = app.db_helper.get_reminders()

        main_box = BoxLayout(orientation="vertical", padding=[dp(12)], spacing=dp(8))

        self.payday_card = self._create_payday_card(theme_cls)
        main_box.add_widget(self.payday_card)

        header_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        header_box.add_widget(MDLabel(text="Мои напоминания", font_style="H6", bold=True, theme_text_color="Primary"))
        add_btn = MDRaisedButton(
            text="+ Добавить",
            size_hint=(None, None),
            size=(dp(120), dp(36)),
            md_bg_color=theme_cls.primary_color,
            on_release=self.show_add_dialog,
        )
        header_box.add_widget(add_btn)
        main_box.add_widget(header_box)

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self._add_transparent_bg(scroll)
        self.scroll = scroll

        self.reminder_container = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=[0, dp(4)])
        self.reminder_container.bind(minimum_height=self.reminder_container.setter("height"))

        scroll.add_widget(self.reminder_container)
        main_box.add_widget(scroll)

        self.clear_widgets()
        self.add_widget(main_box)

        self._display_reminders()
        self.update_payday()

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

    def _create_payday_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(90), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="vertical", spacing=dp(4))
        box.add_widget(MDLabel(text="Ближайший PayDay", font_style="H6", bold=True,
                               theme_text_color="Custom", text_color=(1,1,1,1)))
        self.payday_label = MDLabel(text=self.next_payday if self.next_payday else "Загрузка...",
                                    font_style="Body1", theme_text_color="Custom", text_color=(1,1,1,0.9))
        box.add_widget(self.payday_label)
        card.add_widget(box)
        return card

    def update_payday(self):
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        delta = next_hour - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        self.next_payday = f"Через {hours} ч {minutes} мин (в {next_hour.strftime('%H:%M')})"
        if hasattr(self, 'payday_label'):
            self.payday_label.text = self.next_payday

    def _display_reminders(self):
        if not self.reminder_container:
            return
        self.reminder_container.clear_widgets()
        for reminder in self.reminders:
            card = self._create_reminder_card(reminder)
            self.reminder_container.add_widget(card)

    def _create_reminder_card(self, reminder):
        active = reminder["active"]
        card = MDCard(size_hint=(1,None), height=dp(70), radius=[12], padding=dp(12))
        box = BoxLayout(orientation="vertical", spacing=dp(2))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        header.add_widget(MDLabel(text=reminder["text"], font_style="Body1", bold=True,
                                  theme_text_color="Primary" if active else "Hint", size_hint_x=0.6))
        header.add_widget(MDLabel(text=f"{reminder['date']} {reminder['time']}",
                                  font_style="Caption", theme_text_color="Secondary", halign="right", size_hint_x=0.4))
        box.add_widget(header)
        btn_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(28))
        toggle_btn = MDFlatButton(
            text="✓ Выполнено" if active else "↩ Вернуть",
            font_style="Caption",
            theme_text_color="Primary",
            on_release=lambda x, rid=reminder["id"]: self.toggle_reminder(rid),
        )
        delete_btn = MDFlatButton(
            text="✕ Удалить",
            font_style="Caption",
            theme_text_color="Error",
            on_release=lambda x, rid=reminder["id"]: self.delete_reminder(rid),
        )
        btn_box.add_widget(toggle_btn)
        btn_box.add_widget(delete_btn)
        box.add_widget(btn_box)
        card.add_widget(box)
        return card

    def toggle_reminder(self, rid):
        for r in self.reminders:
            if r["id"] == rid:
                r["active"] = not r["active"]
                self.app.db_helper.update_reminder(rid, r["active"])
                break
        self._display_reminders()
        Snackbar(text="Статус изменён").open()

    def delete_reminder(self, rid):
        self.app.db_helper.delete_reminder(rid)
        self.reminders = [r for r in self.reminders if r["id"] != rid]
        self._display_reminders()
        Snackbar(text="Напоминание удалено").open()

    def show_add_dialog(self, *args):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        text_input = TextInput(hint_text="Текст напоминания", multiline=False, size_hint_y=None, height=dp(40))
        date_input = TextInput(hint_text="ДД.ММ.ГГГГ", multiline=False, size_hint_y=None, height=dp(40))
        time_input = TextInput(hint_text="ЧЧ:ММ", multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(text_input)
        content.add_widget(date_input)
        content.add_widget(time_input)

        btn_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(40))
        add_btn = MDRaisedButton(text="Добавить", size_hint=(0.5,1))
        cancel_btn = MDFlatButton(text="Отмена", size_hint=(0.5,1))
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(add_btn)
        content.add_widget(btn_box)

        popup = Popup(title="Новое напоминание", content=content, size_hint=(0.85,0.4), auto_dismiss=False)

        def on_add(instance):
            text = text_input.text.strip()
            if not text:
                Snackbar(text="Введите текст напоминания").open()
                return
            new_id = self.app.db_helper.add_reminder(
                text,
                date_input.text.strip() or datetime.now().strftime("%d.%m.%Y"),
                time_input.text.strip() or "12:00"
            )
            self.reminders.append({
                "id": new_id,
                "text": text,
                "date": date_input.text.strip() or datetime.now().strftime("%d.%m.%Y"),
                "time": time_input.text.strip() or "12:00",
                "active": True
            })
            self._display_reminders()
            popup.dismiss()
            Snackbar(text="Напоминание добавлено").open()

        def on_cancel(instance):
            popup.dismiss()

        add_btn.bind(on_release=on_add)
        cancel_btn.bind(on_release=on_cancel)
        popup.open()