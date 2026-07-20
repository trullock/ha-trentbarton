"""Trentbarton integration - supports multiple stop configurations."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import load_platform

from .const import *

DOMAIN = "trentbarton"

STOP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERVICE): cv.string,
        vol.Required(CONF_STOPID): cv.string,
        vol.Required(CONF_NUMBUSES): cv.positive_int,
    }
)

# Accept either a single mapping or a list of mappings under `trentbarton:`
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [STOP_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up one or more trentbarton stop configurations."""
    hass.data[DOMAIN] = config[DOMAIN]

    for stop_config in config[DOMAIN]:
        # Pass each stop's own config as the discovery payload so the
        # sensor platform knows which stop it's building entities for.
        load_platform(hass, "sensor", DOMAIN, stop_config, config)

    return True