from app.ai.tasks.background_removal import BackgroundRemovalTask
from app.ai.tasks.base import TaskHandler
from app.ai.tasks.product_recognition import ProductRecognitionResult, ProductRecognitionTask
from app.ai.tasks.product_text import ProductDescriptionTask, ProductNameTask
from app.ai.types import AITask

TASK_HANDLERS: dict[AITask, TaskHandler] = {
    h.task: h
    for h in (
        ProductRecognitionTask(),
        ProductNameTask(),
        ProductDescriptionTask(),
        BackgroundRemovalTask(),
    )
}

__all__ = ["TASK_HANDLERS", "ProductRecognitionResult", "TaskHandler"]
