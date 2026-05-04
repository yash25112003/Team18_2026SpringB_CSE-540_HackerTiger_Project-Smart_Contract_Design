from django.apps import AppConfig
import os

class DeployConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deploy'

    def ready(self):
        # Under Django's autoreloader, only start background workers in the
        # child process. In non-debug/server contexts RUN_MAIN may be unset.
        should_start_workers = os.environ.get("RUN_MAIN") == "true" or os.environ.get("RUN_MAIN") is None
        if not should_start_workers:
            return

        try:
            from .services import _ensure_monitors_started, _schedule_timed_block_rotation

            _ensure_monitors_started()
            _schedule_timed_block_rotation()
        except Exception as exc:
            print(f"⚠️ Deploy app startup workers not started: {exc}")
