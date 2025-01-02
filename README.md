# Brew Brain Integration

This is a custom integration for Home Assistant to connect with Brew Brain devices.

## Scraping BrewBrain Webpage

This integration scrapes the BrewBrain webpage to retrieve data. It uses the `aiohttp` library to make HTTP requests and `beautifulsoup4` to parse the HTML content. The data is then extracted and converted into sensor readings that can be used within Home Assistant.


To perform secured calls to the webpage, this integration uses your Brew Brain username and password to obtain the `PHPSESSID` cookie. This cookie is required to authenticate and maintain a session with the BrewBrain website.

## Installation

1. Clone this repository into your Home Assistant `custom_components` directory:
    ```sh
    git clone https://github.com/plleopart/brewbrain_hass_integration.git
    ```

2. Restart Home Assistant.

3. Add the Brew Brain integration via the Home Assistant UI.

## Configuration

1. Go to the Home Assistant UI.
2. Navigate to `Configuration` -> `Integrations`.
3. Click on `Add Integration` and search for `Brew Brain`.
4. Follow the setup instructions to provide your Brew Brain username and password.

## Files

- [__init__.py](): Initializes the Brew Brain integration and handles setup and teardown.
- [config_flow.py](): Manages the configuration flow for setting up the integration.
- [const.py](): Contains constants used throughout the integration.
- [manifest.json](): Metadata for the integration.
- [sensor.py](): Defines the sensor entities for Brew Brain data.

## Dependencies

This integration requires the following Python packages:
- [bs4](https://pypi.org/project/beautifulsoup4)
- [aiohttp](https://docs.aiohttp.org/en/stable/)

These dependencies will be installed automatically when you add the integration.

## Usage

Once the integration is set up, you will have access to the following sensors:
- Temperature
- Specific Gravity (SG)
- Voltage

These sensors will be updated at regular intervals as defined in [const.py]().

## License

This project is licensed under the MIT License.
