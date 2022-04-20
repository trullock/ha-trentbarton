"""Example Load Platform integration."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import *

DOMAIN = "trentbarton"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERVICE): cv.string,
                vol.Required(CONF_STOPID): cv.string,
                vol.Required(CONF_NUMBUSES): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    hass.data[DOMAIN] = {
        CONF_SERVICE: config[DOMAIN][CONF_SERVICE],
        CONF_STOPID: config[DOMAIN][CONF_STOPID],
        CONF_NUMBUSES: config[DOMAIN][CONF_NUMBUSES],
    }

    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    return True
