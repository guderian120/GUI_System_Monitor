import pytest
import sys
import os
from unittest.mock import MagicMock, patch
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from sysmon.system_monitor import SystemMonitor

def test_cli_output(capsys, mock_psutil):
    monitor = SystemMonitor(mode='cli')
    monitor.update_cli(10.0, 20.0, 30.0)
    captured = capsys.readouterr()
    assert "CPU:  10.0%" in captured.out
    assert "RAM:  20.0%" in captured.out
    assert "test (PID: 123)" in captured.out

def test_gui_update(mock_psutil):
    monitor = SystemMonitor(mode='gui')
    monitor.cpu_label = MagicMock()
    monitor.ram_label = MagicMock()
    monitor.update_gui(10.0, 20.0, 30.0)
    monitor.cpu_label.config.assert_called_with(text="CPU: 10.0%")
    monitor.ram_label.config.assert_called_with(text="RAM: 20.0%")

def test_settings_save():
    monitor = SystemMonitor(mode='gui')
    monitor.save_settings("15", "25", "10")
    assert monitor.cpu_threshold == 15.0
    assert monitor.ram_threshold == 25.0
    assert monitor.check_interval == 10.0