## Usage

```python
from iqua_softener import IquaSoftener

# Create object
softener = IquaSoftener('username', 'password', 'serial_number')

# Download data from API (returns IquaSoftenerData object)
data = softener.get_data()

# Timestamp of received data [datetime.datetime]
print(data.timestamp)

# Model with model code [str]
print(data.model)

# State [iqua_softener.IquaSoftenerState]
print(data.state)

# Device date/time [datetime.datetime]
print(data.device_date_time)

# Volume unit [iqua_softener.IquaSoftenerVolumeUnit]
print(data.volume_unit)

# Current water flow (in volume_unit's) [float]
print(data.current_water_flow)

# Today use (in volume_unit's) [int]
print(data.today_use)

# Average daily use (in volume_unit's) [int]
print(data.average_daily_use)

# Total water available (in volume_unit's) [int]
print(data.total_water_available)

# Days since last regeneration [int]
print(data.days_since_last_regeneration)

# Salt level [int]
print(data.salt_level)

# Salt level percentage [int]
print(data.salt_level_percent)

# Out of salt estimated days [int]
print(data.out_of_salt_estimated_days)

# Hardness grains [int]
print(data.hardness_grains)

# Water shut off valve state [int] (0 - Off, 1 - On, 2 - Not present?)
print(data.water_shutoff_valve_state)

# Enable water shut off valve
softener.set_water_shutoff_valve(1)

# Disable water shut off valve
softener.set_water_shutoff_valve(0)
```

## License
[MIT](https://choosealicense.com/licenses/mit/)