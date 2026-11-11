"""The Tarif EDF integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.storage import Store

from datetime import timedelta

from .coordinator import TarifEdfDataUpdateCoordinator

from .const import (
    DOMAIN,
    PLATFORMS,
    DEFAULT_REFRESH_INTERVAL,
    STORAGE_VERSION,
    STORAGE_KEY,
    CONF_TEMPO_FORECAST,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tarif EDF from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = TarifEdfDataUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        # Valeur de l'option au chargement, pour détecter un changement qui
        # nécessite d'ajouter / retirer les capteurs de prévision.
        CONF_TEMPO_FORECAST: coordinator.tempo_forecast_enabled,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry - clean up stored data."""
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
    await store.async_remove()


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    if entry_data['coordinator'].tempo_forecast_enabled != entry_data.get(CONF_TEMPO_FORECAST):
        # Activation / désactivation des prévisions Tempo : recharger
        # l'intégration pour créer ou supprimer les capteurs J+1 à J+9.
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
        return True

    entry_data['coordinator'].update_interval = timedelta(days=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL))

    return True
