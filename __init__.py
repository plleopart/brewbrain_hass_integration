"""The Brew Brain non-official integration."""

from bs4 import BeautifulSoup
import re
import logging
from datetime import timedelta
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, SCAN_INTERVAL,URL_BASE, URL_FLOATS, URL_LOGIN, URL_FLOAT, COOKIE_HEADER, CLASS_FLOAT_IDENTIFIER, CLASS_MEASUREMENT, CLASS_BREW_LATES_MEASUREMENTS, CLASS_MEASUEMENT_SINGLE_PAGE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Brew Brain integration from a config entry."""
    
    try:
        username = entry.data.get('username')
        password = entry.data.get('password')
        
        _LOGGER.info("Setting up the Brew Brain integration for user %s", username)
        
        cookie = await login(username, password)
        
        
        floats = await list_floats(cookie)
            
        for float in floats:
            _LOGGER.info("Float: %s", float['name'])

        coordinator = BrewBrainCoordinator(hass, username, password, floats)

        await coordinator.async_config_entry_first_refresh()

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

        return True
    
    except Exception as e:
        _LOGGER.error("Error setting up Brew Brain integration: %s", e)
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload all platforms associated with this config entry.
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    
    # Remove the coordinator from hass.data
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    # If there are no more entries, clean up the domain data
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True

async def login(username, password):
    """Login to the Brew Brain website."""
    payload = {'name': username,
               'password': password,
               'stay_signed_in': 'off'}

    _LOGGER.debug("Logging into Brew Brain")
    _LOGGER.debug("Username: %s", username)
    _LOGGER.debug("Password: %s", '*' * len(password))
    _LOGGER.debug("URL: %s", URL_LOGIN)
    
    async with aiohttp.ClientSession() as session:
         async with session.post(URL_LOGIN, data=payload) as response:
            if response.status == 200:
                _LOGGER.debug("Logged into Brew Brain with status code %d", response.status)
                cookie = response.headers[COOKIE_HEADER]
                cookie = cookie.split(';')[0]
                
                return cookie
            else:
                _LOGGER.error("Error logging in to Brew Brain: %s", response.status)
                return None
    

async def fetch_secured_data(cookie, url):
    """Fetch data from the Brew Brain website using the cookie."""
    headers = {'Cookie': cookie}

    async with aiohttp.ClientSession() as session:
         async with session.post(url, headers=headers) as response:
            if response.status == 200:
                _LOGGER.debug("Fetched data from Brew Brain %s with status code %d", url, response.status)
                return await response.text()
            else:
                _LOGGER.error("Error fetching data from Brew Brain: %s", response.status)
                return None


async def list_floats(cookie):
    """List all floats from the Brew Brain website."""

    html_text = await fetch_secured_data(cookie, URL_FLOATS)

    soup = BeautifulSoup(html_text, 'html.parser')

    floats = soup.findAll('div', class_=CLASS_FLOAT_IDENTIFIER)

    float_ids = []
    
    _LOGGER.debug("Found %d floats", len(floats))

    for float in floats:
        a_element = float.find('a')
        name = a_element.text
        href = a_element['href']
        float_id = href.split('/')[-1]
        float_ids.append({'name': name, 'id': float_id})

    return float_ids

async def fetch_float_data(cookie, float_id):
    """Fetch data for a specific float from the Brew Brain website."""
    float_data = {}
    
    _LOGGER.info("Fetching data for float: %s", float_id)
    float_motherboard_page = await fetch_secured_data(cookie, URL_FLOAT + float_id)


    soup = BeautifulSoup(float_motherboard_page, 'html.parser')
    scripts = soup.findAll('script')

    url_pattern = re.compile(r'/APIKey/latestMeasurements/\d+')

    found_url = ''

    for script in scripts:
        if script.string:
            matches = url_pattern.findall(script.string)
            if matches:
                for match in matches:
                    _LOGGER.debug("Found URL: %s", match)
                    found_url = match

    if found_url:
        url = URL_BASE + found_url

        response = await fetch_secured_data(cookie, url)

        soup = BeautifulSoup(response, 'html.parser')
        container = soup.find('div', class_=CLASS_MEASUREMENT)
        measurements = container.findAll('div', class_=CLASS_BREW_LATES_MEASUREMENTS)
        
        for measurement in measurements:
            name = measurement.find('span', class_=CLASS_MEASUEMENT_SINGLE_PAGE).text.strip()
            value = measurement.find('b').find('span').text.strip()
            value = re.findall(r"[-+]?\d+(?:\.\d{1,3})?", value)[0]

            _LOGGER.info("Measurement: %s: %s", name, value)
            float_data[name] = value
            
    return float_data
    

class BrewBrainCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, username: str, password: str, floats: list):
        """Initialize the coordinator."""
        _LOGGER.info("Initializing coordinator")
        super().__init__(
            hass,
            _LOGGER,
            name="Brew Brain",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.username = username
        self.password = password
        self.floats = floats

    async def _async_update_data(self):
        """Fetch data from the web and update the entities."""
        try:
            data = await self.fetch_data_for_entities()
            return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    

    async def fetch_data_for_entities(self):
        """Fetch data for each entity from the web."""
        
        cookie = await login(self.username, self.password)
        
        data = {}
        for float in self.floats:
            float_id = float['id']
            float_name = float['name']
            
            float_data = await fetch_float_data(cookie, float_id)

            float_data['id'] = float_id
            float_data['name'] = float_name
        
            data[float_id] = float_data
        
        return data
