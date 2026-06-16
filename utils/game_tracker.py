# utils/game_tracker.py
from kivy.clock import Clock
from kivy.utils import platform
from datetime import datetime, timedelta

GAME_PACKAGE = "com.liverussia.game.googleplay"

class GameTracker:
    def __init__(self, app):
        self.app = app
        self.is_monitoring = False
        self.session_start_time = None
        self.current_session_minutes = 0
        self._monitor_event = None
        self._was_game_active = False

    def start_monitoring(self):
        if platform == "android":
            self._request_usage_stats_permission()
            self._monitor_event = Clock.schedule_interval(self._check_game_foreground, 5)
        else:
            self._monitor_event = Clock.schedule_interval(self._emulate_desktop, 30)

    def _request_usage_stats_permission(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            activity = PythonActivity.mActivity
            app_ops = activity.getSystemService(Context.APP_OPS_SERVICE)
            mode = app_ops.checkOpNoThrow(
                "android:get_usage_stats",
                activity.getApplicationInfo().uid,
                activity.getPackageName()
            )
            if mode != 0:
                from android import Intent
                intent = Intent("android.settings.USAGE_ACCESS_SETTINGS")
                activity.startActivity(intent)
        except Exception as e:
            print(f"Permission request error: {e}")

    def _check_game_foreground(self, dt):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            activity = PythonActivity.mActivity
            usage_stats = activity.getSystemService(Context.USAGE_STATS_SERVICE)

            now = datetime.now()
            start_millis = int((now - timedelta(seconds=10)).timestamp() * 1000)
            end_millis = int(now.timestamp() * 1000)

            usage_events = usage_stats.queryEvents(start_millis, end_millis)
            is_active_now = False

            while usage_events.hasNextEvent():
                event = usage_events.nextEvent()
                if event.getPackageName() == GAME_PACKAGE:
                    if event.getEventType() == 1:   # MOVE_TO_FOREGROUND
                        is_active_now = True
                    elif event.getEventType() == 2: # MOVE_TO_BACKGROUND
                        is_active_now = False

            if is_active_now and not self.is_monitoring:
                # Игра стала активной
                self.is_monitoring = True
                self.session_start_time = datetime.now()
                self.current_session_minutes = 0
                if hasattr(self.app, 'is_tracking'):
                    self.app.is_tracking = True

                # Push-уведомление и snackbar
                if hasattr(self.app, 'notification_manager'):
                    self.app.notification_manager.send_notification(
                        "Игра запущена",
                        "Не забудь выполнить ежедневные задания и фармить!"
                    )
                    self.app.notification_manager.show_snackbar("Игра запущена! Сессия начата.")

            elif not is_active_now and self.is_monitoring:
                # Игра ушла в фон – завершаем сессию
                self._end_session()

        except Exception as e:
            print(f"Error checking foreground: {e}")

    def _end_session(self):
        if self.session_start_time:
            now = datetime.now()
            delta = now - self.session_start_time
            minutes = int(delta.total_seconds() // 60)

            if self.app.db_helper:
                self.app.db_helper.add_session(
                    self.session_start_time.strftime("%d.%m.%Y %H:%M"),
                    now.strftime("%d.%m.%Y %H:%M"),
                    minutes
                )

            if minutes >= 15:
                self.app.streak_days += 1
                if self.app.db_helper:
                    self.app.db_helper.set_streak_days(self.app.streak_days)

            # Push-уведомление о завершении
            if hasattr(self.app, 'notification_manager'):
                self.app.notification_manager.send_notification(
                    "Сессия завершена",
                    f"Вы играли {minutes} мин. Текущий streak: {self.app.streak_days} дн."
                )
                if minutes >= 15:
                    self.app.notification_manager.show_snackbar(
                        f"Огонёк засчитан! Streak: {self.app.streak_days} дн."
                    )

            self.is_monitoring = False
            self.session_start_time = None
            self.current_session_minutes = 0
            if hasattr(self.app, 'is_tracking'):
                self.app.is_tracking = False

    def _emulate_desktop(self, dt):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.session_start_time = datetime.now()
            self.current_session_minutes = 0
        else:
            self._end_session()

    def stop_monitoring(self):
        if self._monitor_event:
            Clock.unschedule(self._monitor_event)
            self._monitor_event = None
        if self.is_monitoring:
            self._end_session()