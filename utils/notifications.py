# utils/notifications.py
import plyer
from kivy.clock import Clock
from kivy.utils import platform
from datetime import datetime, timedelta

class NotificationManager:
    def __init__(self, app):
        self.app = app
        self._payday_event = None
        self._absence_event = None

    def send_notification(self, title, message):
        """Отправляет локальное уведомление, если разрешено в настройках."""
        if not self.app.config_manager.get("notifications", True):
            return
        try:
            # Параметры уведомления
            kwargs = {
                'title': title,
                'message': message,
                'app_name': self.app.title,
                'timeout': 5  # секунд, для Windows
            }
            # Иконка приложения (только для Android)
            if platform == "android":
                kwargs['app_icon'] = 'assets/icon.png'

            # Звук и вибрация согласно настройкам
            if not self.app.config_manager.get("sound_enabled", True):
                kwargs['ticker'] = ''  # отключаем звук
            if not self.app.config_manager.get("vibration", True):
                kwargs['vibrate'] = False

            plyer.notification.notify(**kwargs)
        except Exception as e:
            print(f"Notification error: {e}")

    def show_snackbar(self, text):
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=text).open()

    def schedule_all(self):
        """Запускает все периодические уведомления."""
        # PayDay уведомления
        interval = self.app.config_manager.get("payday_interval", 60)  # минут
        self._payday_event = Clock.schedule_interval(
            lambda dt: self._send_payday_notification(),
            interval * 60  # переводим в секунды
        )
        # Проверка долгого отсутствия раз в час
        self._absence_event = Clock.schedule_interval(
            lambda dt: self._check_absence(),
            3600
        )

    def _send_payday_notification(self):
        """Уведомление о PayDay."""
        self.send_notification(
            "PayDay!",
            "Заходите в игру, чтобы получить бонусы и отметиться!"
        )

    def _check_absence(self):
        """Проверяет, когда была последняя сессия, и напоминает, если давно."""
        try:
            sessions = self.app.db_helper.get_sessions(1)  # последняя сессия
            if sessions:
                last_end = datetime.strptime(sessions[0]["end"], "%d.%m.%Y %H:%M")
                if datetime.now() - last_end > timedelta(hours=24):
                    self.send_notification(
                        "Давно не играли!",
                        "В LIVE RUSSIA произошло много событий. Возвращайтесь скорее!"
                    )
            else:
                # Нет записей – никогда не играли? Тогда не спамим
                pass
        except Exception as e:
            print(f"Absence check error: {e}")

    def stop_all(self):
        if self._payday_event:
            Clock.unschedule(self._payday_event)
        if self._absence_event:
            Clock.unschedule(self._absence_event)