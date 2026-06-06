import pytest


@pytest.fixture
def fake_drive_storage():
    from apps.financial_account.tests.fake_gdrive_storage import FakeGoogleDriveStorage

    return FakeGoogleDriveStorage()
