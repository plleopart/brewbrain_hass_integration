# BrewBrain for Home Assistant

Unofficial Home Assistant integration for BrewBrain Float hydrometers. It signs
in to the BrewBrain web application and exposes the latest temperature, specific
gravity and battery voltage measurements as Home Assistant sensors.

## HACS installation

1. Open **HACS**.
2. Open the menu in the top-right corner and select **Custom repositories**.
3. Add this repository:

   ```text
   https://github.com/plleopart/brewbrain_hass_integration
   ```

4. Select category **Integration** and add the repository.
5. Install **BrewBrain**.
6. Restart Home Assistant.
7. Open **Settings > Devices & services > Add integration**.
8. Search for **BrewBrain** and enter your BrewBrain credentials.

## Manual installation

Copy `custom_components/brew_brain` into Home Assistant's
`/config/custom_components` directory and restart Home Assistant.

The final path must be:

```text
/config/custom_components/brew_brain/manifest.json
```

## Entities

Each BrewBrain Float creates a device containing three sensors:

- Temperature in degrees Celsius.
- Specific gravity.
- Battery voltage.

Measurements are refreshed every 15 minutes. The integration communicates with
`https://my.brewbrain.nl` and therefore requires internet access. It is an
unofficial integration based on the current BrewBrain website and may require an
update if that website changes.

## Updates

Versions are published as GitHub releases and can be updated from HACS. Restart
Home Assistant after updating the integration.

## Issues

Report problems through the
[GitHub issue tracker](https://github.com/plleopart/brewbrain_hass_integration/issues).

## License

This project is licensed under the MIT License.
