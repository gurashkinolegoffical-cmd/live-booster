# screens/calculator_screen.py
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.snackbar import Snackbar
from kivymd.app import MDApp

class CalculatorScreen(MDScreen):
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

        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self._add_transparent_bg(scroll)
        self.scroll = scroll

        self.layout = BoxLayout(orientation="vertical", padding=[dp(12)], spacing=dp(12), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))

        self.input_card = self._create_input_card(theme_cls)
        self.layout.add_widget(self.input_card)

        calc_btn = MDRaisedButton(text="Рассчитать", size_hint=(1,None), height=dp(48),
                                  md_bg_color=theme_cls.primary_color, on_release=self.calculate)
        self.layout.add_widget(calc_btn)

        self.results_card = self._create_results_card(theme_cls)
        self.layout.add_widget(self.results_card)

        clear_btn = MDRaisedButton(text="Очистить", size_hint=(1,None), height=dp(40),
                                   md_bg_color=(0.9,0.3,0.3,1), on_release=self.clear_fields)
        self.layout.add_widget(clear_btn)

        scroll.add_widget(self.layout)
        self.clear_widgets()
        self.add_widget(scroll)

        # Восстановление предыдущего состояния из БД
        state = app.db_helper.get_calculator_state()
        if state.get("income_text"):
            self.income_input.text = state["income_text"]
            self.shifts_input.text = state["shifts_text"]
            self._update_labels(state)

    def _add_transparent_bg(self, widget):
        with widget.canvas.before:
            Color(0, 0, 0, 0)
            rect = Rectangle(size=widget.size, pos=widget.pos)
        widget.bind(size=lambda w, s: setattr(rect, 'size', s),
                    pos=lambda w, p: setattr(rect, 'pos', p))

    def _create_input_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(150), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="vertical", spacing=dp(10))
        box.add_widget(MDLabel(text="Доход за смену (руб.):", theme_text_color="Secondary", size_hint_y=None, height=dp(20)))
        self.income_input = TextInput(hint_text="12000", multiline=False, input_filter="float", size_hint_y=None, height=dp(40))
        box.add_widget(self.income_input)
        box.add_widget(MDLabel(text="Смен в день:", theme_text_color="Secondary", size_hint_y=None, height=dp(20)))
        self.shifts_input = TextInput(text="1", hint_text="1", multiline=False, input_filter="int", size_hint_y=None, height=dp(40))
        box.add_widget(self.shifts_input)
        card.add_widget(box)
        return card

    def _create_results_card(self, theme_cls):
        card = MDCard(size_hint=(1,None), height=dp(180), radius=[20], padding=dp(16))
        box = BoxLayout(orientation="vertical", spacing=dp(4))
        box.add_widget(MDLabel(text="Результаты расчёта", font_style="H6", bold=True, theme_text_color="Primary",
                               size_hint_y=None, height=dp(30)))
        self.day_label = MDLabel(text="За день: 0 руб.", font_style="Body1", theme_text_color="Secondary", size_hint_y=None, height=dp(24))
        self.week_label = MDLabel(text="За неделю: 0 руб.", font_style="Body1", theme_text_color="Secondary", size_hint_y=None, height=dp(24))
        self.month_label = MDLabel(text="За месяц: 0 руб.", font_style="Body1", theme_text_color="Secondary", size_hint_y=None, height=dp(24))
        self.year_label = MDLabel(text="За год: 0 руб.", font_style="Body1", theme_text_color="Secondary", size_hint_y=None, height=dp(24))
        self.five_year_label = MDLabel(text="За 5 лет: 0 руб.", font_style="Body1", theme_text_color="Secondary", size_hint_y=None, height=dp(24))
        box.add_widget(self.day_label)
        box.add_widget(self.week_label)
        box.add_widget(self.month_label)
        box.add_widget(self.year_label)
        box.add_widget(self.five_year_label)
        card.add_widget(box)
        return card

    def _update_labels(self, state):
        self.day_label.text = f"За день: {state['day']:,.0f} руб."
        self.week_label.text = f"За неделю: {state['week']:,.0f} руб."
        self.month_label.text = f"За месяц: {state['month']:,.0f} руб."
        self.year_label.text = f"За год: {state['year']:,.0f} руб."
        self.five_year_label.text = f"За 5 лет: {state['five_years']:,.0f} руб."

    def calculate(self, *args):
        income_text = self.income_input.text.strip()
        shifts_text = self.shifts_input.text.strip()
        if not income_text:
            Snackbar(text="Введите доход за смену").open()
            return
        try:
            income_per_shift = float(income_text)
        except ValueError:
            Snackbar(text="Некорректный доход").open()
            return
        try:
            shifts_per_day = int(shifts_text) if shifts_text else 1
            if shifts_per_day < 1:
                shifts_per_day = 1
        except ValueError:
            shifts_per_day = 1

        day = income_per_shift * shifts_per_day
        week = day * 7
        month = day * 30
        year = day * 365
        five_years = year * 5

        state = {
            "income_text": income_text,
            "shifts_text": shifts_text,
            "day": day,
            "week": week,
            "month": month,
            "year": year,
            "five_years": five_years
        }
        self.app.db_helper.set_calculator_state(state)
        self._update_labels(state)

    def clear_fields(self, *args):
        self.income_input.text = ""
        self.shifts_input.text = "1"
        self.day_label.text = "За день: 0 руб."
        self.week_label.text = "За неделю: 0 руб."
        self.month_label.text = "За месяц: 0 руб."
        self.year_label.text = "За год: 0 руб."
        self.five_year_label.text = "За 5 лет: 0 руб."
        self.app.db_helper.set_calculator_state({
            "income_text": "",
            "shifts_text": "1",
            "day": 0, "week": 0, "month": 0, "year": 0, "five_years": 0
        })