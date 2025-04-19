import importlib
import logging

from django.conf import settings


def handle_task(module: str, function: str, queue: str, **kwargs):
    module_imported = importlib.import_module(module)
    task_obj = getattr(module_imported, function)

    if settings.USE_CELERY:
        try:
            async_result = task_obj.apply_async(queue=queue, kwargs=kwargs)
            return async_result
        except Exception as e:
            logging.error(f"Error queuing task: {e}")
            return task_obj.run(**kwargs)

    return task_obj.run(**kwargs)
