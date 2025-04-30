import pytest
from unittest.mock import MagicMock, patch
import psutil
import sys

@pytest.fixture
def mock_psutil():
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_mem, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.process_iter') as mock_procs:
        
        mock_cpu.return_value = 10.0
        mock_mem.return_value = MagicMock(percent=20.0)
        mock_disk.return_value = MagicMock(percent=30.0)
        mock_procs.return_value = [
            MagicMock(info={'pid': 123, 'name': 'test', 'cpu_percent': 5.0, 'memory_percent': 1.0})
        ]
        yield mock_cpu, mock_mem, mock_disk, mock_procs

@pytest.fixture
def mock_resend():
    with patch('resend.Emails.send') as mock_send:
        mock_send.return_value = {'id': 'mock_email_id'}
        yield mock_send

@pytest.fixture
def mock_tkinter():
    with patch('tkinter.Tk'), \
         patch('tkinter.ttk.Frame'), \
         patch('tkinter.messagebox'):
        yield
