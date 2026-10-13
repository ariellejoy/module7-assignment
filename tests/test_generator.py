import logging 
import sys 
from datetime import datetime as RealDateTime
from pathlib import Path
import pytest 
import main as generator
from unittest.mock import patch, Mock

def test_setup_logging(): 
    with patch("main.logging.basicConfig") as mock_config:
        generator.setup_logging() 
    assert mock_config.call_args.kwargs["level"] == logging.INFO
    assert mock_config.call_args.kwargs["format"] == '%(asctime)s - %(levelname)s - %(message)s'

def test_main(monkeypatch, tmp_path):
    # Arrange: use a temporary working directory
    monkeypatch.chdir(tmp_path)

    # Simulate command-line arguments
    test_url = "https://github.com/ariellejoy/module7-assignment"
    monkeypatch.setattr(
        sys, "argv", ["generator.py", "--url", test_url]
    )

    # Fix the timestamp for predictable test results
    class FakeDateTime:
        @staticmethod
        def now():
            return RealDateTime(2025, 1, 2, 3, 4, 5)

    monkeypatch.setattr(generator, "datetime", FakeDateTime)

    # Mock dependencies
    mock_setup_logging = Mock()
    mock_create_directory = Mock()
    mock_generate_qr_code = Mock()

    monkeypatch.setattr(
        generator, "setup_logging", mock_setup_logging
    )
    monkeypatch.setattr(
        generator, "create_directory", mock_create_directory
    )
    monkeypatch.setattr(
        generator, "generate_qr_code", mock_generate_qr_code
    )

    # Act
    generator.main()

    # Assert: logging setup was called
    mock_setup_logging.assert_called_once()

    # Assert: the output directory was created
    expected_dir = tmp_path / generator.QR_DIRECTORY
    mock_create_directory.assert_called_once_with(expected_dir)

    # Assert: QR code generation received the expected arguments
    expected_file = expected_dir / "QRCode_20250102030405.png"

    mock_generate_qr_code.assert_called_once_with(
        test_url,
        expected_file,
        generator.FILL_COLOR,
        generator.BACK_COLOR,
    )


def test_main_uses_default_url(monkeypatch, tmp_path):
    # Arrange: use a temporary working directory
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["generator.py"])

    # Mock dependencies
    monkeypatch.setattr(generator, "setup_logging", Mock())
    monkeypatch.setattr(generator, "create_directory", Mock())

    mock_generate = Mock()
    monkeypatch.setattr(
        generator, "generate_qr_code", mock_generate
    )

    # Act
    generator.main()

    # Assert: the default URL is used
    assert mock_generate.call_args.args[0] == (
        "https://github.com/ariellejoy/module7-assignment"
    )

def test_create_directory(tmp_path):
    # Test that the directory is created successfully
    test_dir = tmp_path / "qr_codes"
    generator.create_directory(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()

def test_failed_directory(monkeypatch, tmp_path):
    # Simulate a failure in directory creation by patching the mkdir method to raise an exception
    test_dir = tmp_path / "qr_codes"
    def mock_mkdir(*args, **kwargs):
        raise Exception("Simulated failure")
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    with pytest.raises(SystemExit) as e:
        generator.create_directory(test_dir)
    assert e.type == SystemExit
    assert e.value.code == 1

def test_invalid_url():
    # Test that an invalid URL is handled correctly
    invalid_url = "invalid_url"
    assert not generator.is_valid_url(invalid_url)

def test_create_png(tmp_path):
    # Test that a QR code PNG file is created successfully
    test_dir = tmp_path / "qr_codes"
    generator.create_directory(test_dir)
    test_file = test_dir / "test_qr.png"
    
    # Generate a QR code for a valid URL
    generator.generate_qr_code("https://github.com/ariellejoy/module7-assignment", test_file, fill_color="blue", back_color="yellow")
    assert test_file.exists()
    assert test_file.suffix == ".png"

def test_generate_qr_code_logs_error(monkeypatch, tmp_path, caplog):
    def mock_qrcode(*args, **kwargs):
        raise Exception("Simulated QR code generation failure")

    monkeypatch.setattr(generator.qrcode, "QRCode", mock_qrcode)

    with caplog.at_level(logging.ERROR):
        generator.generate_qr_code(
            data="https://github.com/ariellejoy/module7-assignment",
            path=tmp_path / "test_qr.png"
        )

    assert (
        "An error occurred while generating or saving the QR code: "
        "Simulated QR code generation failure"
    ) in caplog.text

def test_generate_qr_code_invalid_url(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(generator, "is_valid_url", lambda data: False)
    def mock_qrcode(*args, **kwargs):
        raise AssertionError("QR Code generation should not occur")
    monkeypatch.setattr(generator.qrcode, "QRCode", mock_qrcode)
    result = generator.generate_qr_code(
        data="invalid_url",
        path=tmp_path / "test_qr.png"
    )
    assert result is None