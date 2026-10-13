import logging 
import sys
from pathlib import Path
import pytest 
import main as generator

def test_create_directory(tmp_path):
    # Test that the directory is created successfully
    test_dir = tmp_path / "qr_codes"
    generator.create_directory(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
