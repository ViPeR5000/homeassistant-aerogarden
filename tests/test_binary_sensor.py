import pytest
import asyncio
from collections.abc import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import BinarySensorDeviceClass


from custom_components.aerogarden.aerogarden import Aerogarden
from custom_components.aerogarden.binary_sensor import (
    async_setup_entry,
    AerogardenBinarySensor,
)

from custom_components.aerogarden.const import (
    DOMAIN,
    GARDEN_KEY_NUTRI_STATUS,
    GARDEN_KEY_PUMP_HYDRO,
    GARDEN_KEY_LIGHT_STAT,
    GARDEN_KEY_PUMP_STAT,
)

CONFIG_ID = 123456
DEVICES = [
    {
        "configID": CONFIG_ID,
        "airGuid": "12:34:56:78:10:AB",
        "lightCycle": "08000801",
        "pumpCycle": "00050019",
        "lightTemp": 1,
        "lightStat": 1,
        "clock": "0a0006",
        "pumpStat": 1,
        "pumpHydro": 1,
        "pumpTest": None,
        "pumpDrain": None,
        "pumpDrainState": None,
        "pumpLevel": 1,
        "pumpRemind4Hour": 0,
        "gardenType": 5,
        "plantedType": 10,
        "plantedName": "KCDNocKwIM2cypYgzaHCsCkgSGVsbG8gdGhlcmU=",
        "totalDay": 120,
        "plantedDay": 43,
        "nutriCycle": 7,
        "nutriRemindDay": 6,
        "nutriStatus": 1,
        "alarmAllow": 0,
        "plantedDate": None,
        "nutrientDate": None,
        "updateDate": "2023-08-25T00:27:24",
        "createDate": None,
        "swVersion": "MFW-V0.37",
        "hwVersion": "SW-V1.01",
        "bwVersion": "HW-V5.0",
        "oldPlantedDay": 43,
        "deviceID": "123456789ABCEFG",
        "deviceIP": "http://10.10.2.20",
        "chooseGarden": 0,
        "oldlightCycle": "",
        "vacationMode": 0,
        "bwConnectedSsid": "Pretty Fly for a Wifi",
        "nutriStatusFlag": "0",
        "nutriStatusDate": "2023-08-23T14:05:02",
        "remark": None,
        "imgUrl": None,
        "timezone": "0",
        "audioAlarmStat": 0,
        "audioAlarmCycle": "08001400",
        "audioAlarmCycleSet": 0,
        "clientIP": "555.55.55.5",
        "latlng": None,
        "lightDimming": 0,
        "sunRise": 0,
        "sunSet": 0,
        "sunFunStatus": 0,
        "sunFunSwitch": 0,
        "pumpSafetyMode": 0,
    }
]
HOST = "https://unittest.abcxyz"
EMAIL = "myemail@unittest.com"
PASSWORD = "hunter2"
ENTRY_ID = f"aerogarden-{EMAIL}"


class EntitiesTracker:
    def __init__(self) -> None:
        self._added_entities = []

    def add_entities_callback(
        self,
        new_entities: Iterable[AerogardenBinarySensor],
        update_before_add: bool = False,
    ):
        self._added_entities = new_entities


@pytest.fixture
def setup(mocker):
    future = asyncio.Future()
    future.set_result(None)

    mocker.patch.object(Aerogarden, "update", return_value=future)
    mocker.patch.object(ConfigEntry, "__init__", return_value=None)
    mocker.patch.object(HomeAssistant, "__init__", return_value=None)

    aerogarden = Aerogarden(HOST, EMAIL, PASSWORD)
    aerogarden._data = {CONFIG_ID: DEVICES[0]}

    hass = HomeAssistant()
    hass.data = {DOMAIN: {ENTRY_ID: aerogarden}}

    configEntry = ConfigEntry()
    configEntry.entry_id = ENTRY_ID

    entities = EntitiesTracker()

    return (hass, configEntry, entities)


@pytest.mark.asyncio
class TestClient:
    async def __execute_and_get_sensor(
        self, setup, garden_key: str
    ) -> AerogardenBinarySensor:
        entities: EntitiesTracker
        (hass, configEntry, entities) = setup

        await async_setup_entry(hass, configEntry, entities.add_entities_callback)

        found = list(
            (
                sensor
                for sensor in entities._added_entities
                if garden_key in sensor._attr_unique_id
            )
        )
        assert len(found) == 1

        return found[0]

    async def test_async_setup_all_sensors_created(self, setup):
        """All sensors created"""
        entities: EntitiesTracker
        (hass, configEntry, entities) = setup

        await async_setup_entry(hass, configEntry, entities.add_entities_callback)

        assert len(entities._added_entities) == 4

    async def test_async_setup_entry_pump_created(self, setup):
        """Sensor for if the garden pump is on is created on setup"""

        sensor = await self.__execute_and_get_sensor(setup, GARDEN_KEY_PUMP_STAT)

        assert "Pump" in sensor._attr_name
        assert sensor._attr_icon == "mdi:water-pump"
        assert sensor._attr_device_class is BinarySensorDeviceClass.RUNNING

    async def test_async_update_pump_value_Correct(self, setup):
        """Reported sensor value matches the value in the json payload"""

        sensor: AerogardenBinarySensor = await self.__execute_and_get_sensor(
            setup, GARDEN_KEY_PUMP_STAT
        )
        await sensor.async_update()

        assert sensor._attr_is_on

    async def test_async_setup_entry_needs_nutrients_created(self, setup):
        """Sensor for if the garden needs nutrients is created on setup"""

        sensor = await self.__execute_and_get_sensor(setup, GARDEN_KEY_NUTRI_STATUS)

        assert "Needs Nutrients" in sensor._attr_name
        assert sensor._attr_icon == "mdi:cup-water"
        assert sensor._attr_device_class is BinarySensorDeviceClass.PROBLEM

    async def test_async_update_needs_nutrients_value_Correct(self, setup):
        """Reported sensor value matches the value in the json payload"""

        sensor: AerogardenBinarySensor = await self.__execute_and_get_sensor(
            setup, GARDEN_KEY_NUTRI_STATUS
        )
        await sensor.async_update()

        assert sensor._attr_is_on

    async def test_async_setup_entry_needs_water_created(self, setup):
        """Sensor for if the garden needs water is created on setup"""

        sensor = await self.__execute_and_get_sensor(setup, GARDEN_KEY_PUMP_HYDRO)

        assert "Needs Water" in sensor._attr_name
        assert sensor._attr_icon == "mdi:water"
        assert sensor._attr_device_class is BinarySensorDeviceClass.PROBLEM

    async def test_async_update_needs_water_value_Correct(self, setup):
        """Reported sensor value matches the value in the json payload"""

        sensor: AerogardenBinarySensor = await self.__execute_and_get_sensor(
            setup, GARDEN_KEY_PUMP_HYDRO
        )
        await sensor.async_update()

        assert sensor._attr_is_on

    async def test_async_setup_entry_light_created(self, setup):
        """Sensor for if the garden light is on is created on setup"""

        sensor = await self.__execute_and_get_sensor(setup, GARDEN_KEY_LIGHT_STAT)

        assert "Light" in sensor._attr_name
        assert sensor._attr_icon == "mdi:lightbulb"
        assert sensor._attr_device_class is None

    async def test_async_update_needs_light_Correct(self, setup):
        """Reported sensor value matches the value in the json payload"""

        sensor: AerogardenBinarySensor = await self.__execute_and_get_sensor(
            setup, GARDEN_KEY_LIGHT_STAT
        )
        await sensor.async_update()

        assert sensor._attr_is_on