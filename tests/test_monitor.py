import pytest
from unittest.mock import MagicMock, call, patch
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from sysmon.system_monitor import SystemMonitor
import time


def test_quit():
    with patch('sys.exit') as mock_exit:
        monitor = SystemMonitor(mode='cli')
        monitor.quit()
        mock_exit.assert_called_once_with(0)

def test_init_gui_mode(mock_psutil, mock_tkinter):
    monitor = SystemMonitor(mode='gui')
    assert monitor.mode == 'gui'
    assert monitor.running is True
    monitor.quit()

def test_init_cli_mode(mock_psutil, capsys):
    monitor = SystemMonitor(mode='cli')
    assert monitor.mode == 'cli'
    captured = capsys.readouterr()
    assert "System Monitor running in CLI mode" in captured.out
    monitor.quit()

def test_monitor_resources(mock_psutil):
    monitor = SystemMonitor(mode='cli')
    monitor.running = False  # Stop the loop
    monitor.monitor_resources()
    psutil.cpu_percent.assert_called_once_with(interval=1)
    psutil.virtual_memory.assert_called_once()
    psutil.disk_usage.assert_called_once_with('/')

def test_check_thresholds_no_alert(mock_psutil):
    monitor = SystemMonitor(mode='cli')
    monitor.cpu_threshold = 90
    monitor.ram_threshold = 90
    monitor.disk_threshold = 90
    monitor.check_thresholds(10, 20, 30)
    assert not monitor.last_alert_time

def test_check_thresholds_with_alert(mock_psutil, mock_resend):
    monitor = SystemMonitor(mode='cli')
    monitor.cpu_threshold = 5
    monitor.ram_threshold = 5
    monitor.disk_threshold = 5
    monitor.check_thresholds(10, 20, 30)
    assert 'CPU' in monitor.last_alert_time
    mock_resend.assert_called_once()

def test_send_email(mock_resend):
    monitor = SystemMonitor(mode='cli')
    monitor.send_email("Test alert")
    mock_resend.assert_called_once()
    assert "Test alert" in mock_resend.call_args[0][0]["html"]

def test_kill_selected_process(mock_psutil):
    monitor = SystemMonitor(mode='gui')
    mock_proc = MagicMock()
    mock_proc.terminate.return_value = None
    with patch('psutil.Process', return_value=mock_proc):
        monitor.tree = MagicMock()
        monitor.tree.selection.return_value = ['item1']
        monitor.tree.item.return_value = {'values': [123, 'test', 5.0, 1.0]}
        monitor.kill_selected_process()
        mock_proc.terminate.assert_called_once()