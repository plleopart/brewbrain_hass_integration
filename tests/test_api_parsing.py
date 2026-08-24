"""Tests for BrewBrain HTML parsing."""

from importlib import util
from pathlib import Path
import sys
from types import ModuleType

import pytest

COMPONENT_PATH = Path(__file__).parents[1] / "custom_components" / "brew_brain"
PACKAGE_NAME = "brew_brain_parser_tests"


def _load_module(name: str):
    package = sys.modules.setdefault(PACKAGE_NAME, ModuleType(PACKAGE_NAME))
    package.__path__ = [str(COMPONENT_PATH)]
    module_name = f"{PACKAGE_NAME}.{name}"
    spec = util.spec_from_file_location(module_name, COMPONENT_PATH / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_load_module("const")
api = _load_module("api")


def test_parse_float_list() -> None:
    """Parse device identifiers and names."""
    result = api._parse_float_list(
        """
        <div class="FloatIdentifier">
          <a href="/mothership/show/12345">Fermenter</a>
        </div>
        """
    )

    assert result == [api.BrewBrainFloat("12345", "Fermenter")]


def test_parse_latest_measurements_url() -> None:
    """Convert the embedded relative API path to an absolute URL."""
    result = api._parse_latest_measurements_url(
        '<script>load("/APIKey/latestMeasurements/6789")</script>'
    )

    assert result == "https://my.brewbrain.nl/APIKey/latestMeasurements/6789"


def test_parse_numeric_measurements() -> None:
    """Parse dot, comma and four-decimal measurements as numbers."""
    result = api._parse_measurements(
        """
        <div class="LatestMeasurementsContainer">
          <div class="BrewShowLatestMeasurement">
            <span class="MeasurementMeasurand">Temperature</span>
            <b><span>20,4 °C</span></b>
          </div>
          <div class="BrewShowLatestMeasurement">
            <span class="MeasurementMeasurand">SG</span>
            <b><span>1.0523</span></b>
          </div>
          <div class="BrewShowLatestMeasurement">
            <span class="MeasurementMeasurand">Voltage</span>
            <b><span>2.91 V</span></b>
          </div>
        </div>
        """
    )

    assert result == {"Temperature": 20.4, "SG": 1.0523, "Voltage": 2.91}


def test_missing_devices_raises_parse_error() -> None:
    """Reject a response that is not the expected Float list."""
    with pytest.raises(api.BrewBrainParseError):
        api._parse_float_list("<html><body>No devices</body></html>")
