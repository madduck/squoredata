# needed < 3.14 so that annotations aren't evaluated
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, model_validator


class BatteryStatus(BaseModel):
    """The battery status of a device."""

    percentage: int
    charging: bool


class DeviceInfo(BaseModel):
    """Base information about a device."""

    deviceid: str | None = None
    timestamp: datetime | None = None

    def model_post_init(self, ctx: Any) -> None:
        if self.timestamp is None:
            self.timestamp = (ctx or {}).get("timestamp") or datetime.now()

    @property
    def device(self) -> str | None:
        return self.deviceid

    @property
    def batterystatus(self) -> BatteryStatus | None:
        return None

    def debug_repr(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.device or "(no device ID)"

    def __hash__(self) -> int:
        return hash(self.device)


_NONEXISTENT = object()


class SquoreDeviceInfo(DeviceInfo, extra="forbid"):
    """Device information as reported by a Squore tablet."""

    batteryCharging: bool
    batteryPercentage: int
    customData: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def _rename_device(cls, data: Any) -> Any:
        if (
            isinstance(data, dict)
            and (dev := data.get("device", _NONEXISTENT)) is not _NONEXISTENT
        ):
            data = {k: v for k, v in data.items() if k != "device"} | {"deviceid": dev}
        return data

    @property
    def batterystatus(self) -> BatteryStatus:
        return BatteryStatus(
            percentage=self.batteryPercentage, charging=self.batteryCharging
        )
