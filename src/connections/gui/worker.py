"""Run a single paid operation off the UI thread; the window owns its lifecycle."""

from PySide6.QtCore import QObject, Signal, Slot

from connections.service import ServiceError


class Worker(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    @Slot()
    def run(self):
        try:
            self.succeeded.emit(self.operation())
        except (ServiceError, ValueError, OSError) as error:
            self.failed.emit(error)
        except Exception:
            # Raw SDK exceptions can include request content; don't display or log them.
            self.failed.emit(
                ServiceError(
                    "An unexpected error occurred. Your puzzle is still here. "
                    "Check the model in Settings and try again."
                )
            )
        finally:
            self.finished.emit()
