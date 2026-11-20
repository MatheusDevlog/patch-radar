import patch_radar


def test_package_exposes_version() -> None:
    assert patch_radar.__version__ == "0.1.0"
