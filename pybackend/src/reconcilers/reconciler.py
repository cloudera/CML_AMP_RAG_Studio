import logging
import queue
import threading
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Generic, Set, TypeVar

T = TypeVar("T")


class Reconciler(Generic[T]):
    def __init__(
        self, logger: logging.Logger, batch_size: int = 100, resync_interval: int = 5
    ):
        self.logger = logger
        self.pending_items = set()
        self.running_items = set()
        self.lock = threading.Lock()
        self.batch_size = batch_size
        self.resync_interval = resync_interval

    def submit(self, item: T) -> None:
        with self.lock:
            if item not in self.pending_items and item not in self.running_items:
                self.pending_items.add(item)

    @abstractmethod
    def resync(self) -> None:
        pass

    @abstractmethod
    def reconcile(self, input: T) -> None:
        pass

    def run(self) -> None:
        threading.Thread(target=self._resync_loop, daemon=True).start()
        threading.Thread(target=self._reconcile_loop, daemon=True).start()

    def _resync_loop(self) -> None:
        while True:
            self.resync()
            time.sleep(self.resync_interval)

    def _reconcile_item(self, item: T) -> None:
        try:
            self.reconcile(item)
        except Exception as e:
            # Re-add to pending items if reconciliation fails
            with self.lock:
                self.pending_items.add(item)
            raise e
        finally:
            with self.lock:
                self.running_items.remove(item)

    def _reconcile_loop(self) -> None:
        while True:
            items = set()
            with self.lock:
                while len(items) < self.batch_size:
                    if not self.pending_items:
                        break
                    item = self.pending_items.pop()
                    self.running_items.add(item)
                    items.add(item)
            if items:
                # Reconcile the items in parallel and wait for them to finish
                with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
                    executor.map(self._reconcile_item, items)
            else:
                time.sleep(1)
