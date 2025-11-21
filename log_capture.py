"""
Log Capture Utility

Captures console output for display in Streamlit
"""

import sys
from io import StringIO
from contextlib import contextmanager


class LogCapture:
    """Captures print statements to a string buffer"""
    
    def __init__(self):
        self.buffer = StringIO()
        self.original_stdout = None
    
    def start(self):
        """Start capturing stdout"""
        self.original_stdout = sys.stdout
        sys.stdout = self.buffer
    
    def stop(self):
        """Stop capturing and return to original stdout"""
        if self.original_stdout:
            sys.stdout = self.original_stdout
        return self.buffer.getvalue()
    
    def get_logs(self):
        """Get current captured logs without stopping"""
        return self.buffer.getvalue()
    
    def clear(self):
        """Clear the buffer"""
        self.buffer = StringIO()


@contextmanager
def capture_logs():
    """
    Context manager for log capture
    
    Usage:
        with capture_logs() as capturer:
            print("This will be captured")
            # Do work
        logs = capturer.get_logs()
    """
    capturer = LogCapture()
    capturer.start()
    try:
        yield capturer
    finally:
        capturer.stop()