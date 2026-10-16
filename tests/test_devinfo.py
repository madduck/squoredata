from datetime import datetime, timezone

from squoredata import BatteryStatus, DeviceInfo, SquoreDeviceInfo


def test_device_is_deviceid() -> None:
    assert DeviceInfo(deviceid="dev").device == "dev"


def test_device_string_without_id() -> None:
    assert str(DeviceInfo()) == "(no device ID)"


def test_device_string_with_id() -> None:
    assert str(DeviceInfo(deviceid="dev")) == "dev"


def test_device_debug_repr_is_string() -> None:
    assert DeviceInfo(deviceid="dev").debug_repr() == "dev"


def test_device_hash_uses_device() -> None:
    assert hash(DeviceInfo(deviceid="dev")) == hash("dev")


def test_device_timestamp_defaults_to_now() -> None:
    before = datetime.now()
    info = DeviceInfo(deviceid="dev")
    assert info.timestamp is not None
    assert info.timestamp >= before


def test_device_timestamp_kept_from_context() -> None:
    ts = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert DeviceInfo(deviceid="dev", timestamp=ts).timestamp == ts


def test_base_batterystatus_is_none() -> None:
    assert DeviceInfo(deviceid="dev").batterystatus is None


def test_squore_batterystatus_from_fields() -> None:
    info = SquoreDeviceInfo(batteryCharging=False, batteryPercentage=42, deviceid="dev")
    assert info.batterystatus == BatteryStatus(percentage=42, charging=False)


def test_squore_device_field_renamed_to_deviceid() -> None:
    info = SquoreDeviceInfo.model_validate(
        {"device": "dev", "batteryCharging": True, "batteryPercentage": 1}
    )
    assert info.deviceid == "dev"


def test_squore_custom_data_defaults_to_none() -> None:
    info = SquoreDeviceInfo(batteryCharging=True, batteryPercentage=42)
    assert info.customData is None


def test_squore_custom_data_is_kept() -> None:
    info = SquoreDeviceInfo(
        batteryCharging=True,
        batteryPercentage=42,
        customData={"table": 7},
    )
    assert info.customData == {"table": 7}
