import os

try:
    from celery import Celery
except Exception:  # pragma: no cover - optional dependency fallback
    Celery = None

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

if Celery is None:
    class _DummyAsyncResult:
        def __init__(self, task_id: str):
            self.id = task_id
            self.status = "PENDING"
            self.state = "PENDING"
            self.result = None
            self.info = None

    class _DummyTask:
        def __init__(self, task_id: str = "dummy-task-id"):
            self.id = task_id

    class _DummyCeleryApp:
        class _Conf:
            def update(self, **kwargs):
                _ = kwargs

        def __init__(self):
            self.conf = self._Conf()

        def task(self, *args, **kwargs):
            _ = (args, kwargs)

            def decorator(func):
                def delay(_payload):
                    return _DummyTask()

                func.delay = delay  # type: ignore[attr-defined]
                return func

            return decorator

        def AsyncResult(self, task_id: str):
            return _DummyAsyncResult(task_id)

    celery_app = _DummyCeleryApp()
else:
    celery_app = Celery(
        "vn_digitize_tasks",
        broker=REDIS_URL,
        backend=REDIS_URL,
        include=["app.tasks"]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Ho_Chi_Minh",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600, # 1 hour max
    )
