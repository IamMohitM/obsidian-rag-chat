import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fnmatch
from collections import deque

class FileChangeTracker:
    def __init__(self):
        self.changes = deque()
        self.file_status = {}

    def add_change(self, event_type, file_path):
        self.changes.append((event_type, file_path))
        self.file_status[file_path] = event_type

    def get_changes(self):
        return list(self.changes)

    def clear_changes(self):
        self.changes.clear()
        self.file_status.clear()

class MyHandler(FileSystemEventHandler):
    def __init__(self, tracker, ignore_patterns=None):
        self.tracker = tracker
        self.ignore_patterns = ignore_patterns or []

    def should_ignore(self, path):
        return any(fnmatch.fnmatch(os.path.basename(path), pattern) for pattern in self.ignore_patterns)

    def on_modified(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.tracker.add_change('modified', event.src_path)

    def on_created(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.tracker.add_change('created', event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.tracker.add_change('deleted', event.src_path)

    def on_moved(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.tracker.add_change('moved', (event.src_path, event.dest_path))

def watch_directory(path, ignore_patterns, interval=10):
    event_handler = MyHandler(ignore_patterns=ignore_patterns)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    
    
if __name__ == "__main__":
    ignore_patterns = [".obsidian/*"]
    path = os.path.join("/Users/mo/Library/Mobile Documents/iCloud~md~obsidian/Documents/MainVault")
    watch_directory(path, ignore_patterns)
    