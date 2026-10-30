"""Run a synchronous provider request in a daemon thread with queued Qt signals."""

from threading import Event, Lock, Thread

from PySide6.QtCore import QObject, Signal, Slot

from connections.service import ServiceError


class Worker(QObject):
    succeeded = Signal(object, object)
    failed = Signal(object, object)
    finished = Signal(object)

    def __init__(self, operation, service):
        super().__init__()
        self.operation = operation
        self.service = service
        self.cancelled = Event()
        self._operation_done = Event()
        self._close_lock = Lock()
        self._service_closed = False
        self.thread = Thread(target=self.run, daemon=True, name="connections-request")

    def cancel(self):
        self.cancelled.set()
        if self._operation_done.is_set():
            self._close_service()

    def _close_service(self):
        with self._close_lock:
            if self._service_closed:
                return
            self._service_closed = True
        try:
            self.service.close()
        except Exception:
            pass  # Cleanup errors must not expose provider details or strand the registry.

    def _emit(self, signal: str, *arguments):
        try:
            getattr(self, signal).emit(*arguments)
        except RuntimeError:
            pass  # The Qt receiver may already have been destroyed during application shutdown.

    @Slot()
    def run(self):
        try:
            if self.cancelled.is_set():
                return
            result = self.operation()
            if not self.cancelled.is_set():
                self._emit("succeeded", self, result)
        except (ServiceError, ValueError, OSError) as error:
            if not self.cancelled.is_set():
                self._emit("failed", self, error)
        except Exception:
            # Raw SDK exceptions can include request content; don't display or log them.
            self._emit(
                "failed",
                self,
                ServiceError(
                    "An unexpected error occurred. Your puzzle is still here. "
                    "Check the model in Settings and try again."
                ),
            )
        finally:
            self._operation_done.set()
            if self.cancelled.is_set():
                self._close_service()
            self._emit("finished", self)
