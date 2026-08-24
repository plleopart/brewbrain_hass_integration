"""Constants for the BrewBrain integration."""

from datetime import timedelta

DOMAIN = "brew_brain"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

SCAN_INTERVAL = timedelta(minutes=15)

URL_BASE = "https://my.brewbrain.nl"
URL_LOGIN = f"{URL_BASE}/user/login"
URL_FLOATS = f"{URL_BASE}/float"
URL_FLOAT = f"{URL_BASE}/mothership/show/"

CLASS_FLOAT_IDENTIFIER = "FloatIdentifier"
CLASS_MEASUREMENT = "LatestMeasurementsContainer"
CLASS_LATEST_MEASUREMENT = "BrewShowLatestMeasurement"
CLASS_MEASUREMENT_NAME = "MeasurementMeasurand"

MEASUREMENT_TEMPERATURE = "Temperature"
MEASUREMENT_SPECIFIC_GRAVITY = "SG"
MEASUREMENT_VOLTAGE = "Voltage"
