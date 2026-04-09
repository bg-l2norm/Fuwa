import pytest
from unittest.mock import Mock, patch
from collections import deque
from pathlib import Path
from watchdog.events import FileSystemEvent

from observer import ChangeHandler, FileSystemObserver

def test_change_handler_ignores_directories():
    events = deque()
    handler = ChangeHandler(events)

    event = FileSystemEvent("some/path")
    event.is_directory = True
    event.event_type = "modified"

    handler.on_modified(event)

    assert len(events) == 0

def test_change_handler_ignores_git_and_pycache():
    events = deque()
    handler = ChangeHandler(events)

    event_git = FileSystemEvent(".git/config")
    event_git.is_directory = False
    event_git.event_type = "modified"

    handler.on_modified(event_git)

    event_pycache = FileSystemEvent("__pycache__/main.cpython-310.pyc")
    event_pycache.is_directory = False
    event_pycache.event_type = "modified"

    handler.on_modified(event_pycache)

    assert len(events) == 0

@patch("observer.time.strftime")
def test_change_handler_records_events(mock_strftime):
    mock_strftime.return_value = "12:34:56"
    events = deque()
    handler = ChangeHandler(events)

    event_mod = FileSystemEvent("test.txt")
    event_mod.is_directory = False
    event_mod.event_type = "modified"

    handler.on_modified(event_mod)

    assert len(events) == 1
    assert events[0] == "[12:34:56] File modified: test.txt"

    event_cre = FileSystemEvent("new_file.txt")
    event_cre.is_directory = False
    event_cre.event_type = "created"

    handler.on_created(event_cre)

    assert len(events) == 2
    assert events[1] == "[12:34:56] File created: new_file.txt"

    event_del = FileSystemEvent("old_file.txt")
    event_del.is_directory = False
    event_del.event_type = "deleted"

    handler.on_deleted(event_del)

    assert len(events) == 3
    assert events[2] == "[12:34:56] File deleted: old_file.txt"


def test_filesystem_observer_get_recent_observations():
    observer = FileSystemObserver(["."])

    # Initially empty
    assert observer.get_recent_observations() == "No recent file activity."

    # Add some events
    observer.recent_events.append("[12:00:00] File modified: a.txt")
    observer.recent_events.append("[12:01:00] File created: b.txt")

    expected_output = "[12:00:00] File modified: a.txt\n[12:01:00] File created: b.txt"
    assert observer.get_recent_observations() == expected_output

    # Check that events are cleared after reading
    assert len(observer.recent_events) == 0
    assert observer.get_recent_observations() == "No recent file activity."

@patch("observer.Observer")
@patch("observer.Path")
def test_filesystem_observer_start_stop(mock_path_cls, mock_observer_cls):
    mock_observer_instance = Mock()
    mock_observer_cls.return_value = mock_observer_instance

    mock_path_instance = Mock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = True
    mock_path_cls.return_value = mock_path_instance

    fs_observer = FileSystemObserver(["folder_a"])

    # Test start
    fs_observer.start()
    mock_observer_instance.schedule.assert_called_once_with(
        fs_observer.handler, str(mock_path_instance), recursive=True
    )
    mock_observer_instance.start.assert_called_once()

    # Test stop
    mock_observer_instance.is_alive.return_value = True
    fs_observer.stop()
    mock_observer_instance.stop.assert_called_once()
    mock_observer_instance.join.assert_called_once()
