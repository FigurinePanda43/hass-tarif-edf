"""Data update coordinator for the Tarif EDF integration."""
from __future__ import annotations

from datetime import timedelta, datetime, date
import time
import re
from typing import Any
import json
import logging
import requests
import csv

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_REFRESH_INTERVAL,
    CONTRACT_TYPE_BASE,
    CONTRACT_TYPE_HPHC,
    CONTRACT_TYPE_TEMPO,
    TARIF_BASE_URL,
    TARIF_HPHC_URL,
    TARIF_TEMPO_URL,
    TEMPO_COLOR_API_URL,
    TEMPO_FORECAST_API_URL,
    TEMPO_COLORS_MAPPING,
    TEMPO_DAY_START_AT,
    TEMPO_TOMRROW_AVAILABLE_AT,
    TEMPO_OFFPEAK_HOURS,
    TEMPO_FORECAST_DAYS,
    STORAGE_VERSION,
    STORAGE_KEY,
)

_LOGGER = logging.getLogger(__name__)

def get_remote_file(url: str):
    return requests.get(
        url,
        stream=True,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        },
    )

def str_to_time(str):
    return datetime.strptime(str, '%H:%M').time()

def time_in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end

def get_tempo_color_from_code(code):
    return TEMPO_COLORS_MAPPING[code]


class TarifEdfDataUpdateCoordinator(TimestampDataUpdateCoordinator):
    """Data update coordinator for the Tarif EDF integration."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=entry.title,
            update_interval=timedelta(minutes=1),
        )
        self.config_entry = entry
        self.tempo_prices: dict[str, dict] = {}
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._tempo_cache_loaded = False

    async def _async_load_tempo_cache(self) -> None:
        """Charge le cache Tempo depuis le stockage persistant."""
        if self._tempo_cache_loaded:
            return

        stored_data = await self._store.async_load()
        if stored_data:
            self.logger.info("Chargement du cache Tempo depuis le stockage persistant")
            if self.data is None:
                self.data = {}
            # Restaurer les couleurs Tempo sauvegardées
            if 'tempo_demain_date' in stored_data:
                self.data['tempo_demain_date'] = stored_data.get('tempo_demain_date')
                self.data['tempo_couleur_demain'] = stored_data.get('tempo_couleur_demain')
                self.logger.info(
                    f"Cache Tempo restauré: demain={self.data.get('tempo_couleur_demain')} "
                    f"pour le {self.data.get('tempo_demain_date')}"
                )
            if 'tempo_aujourdhui_date' in stored_data:
                self.data['tempo_aujourdhui_date'] = stored_data.get('tempo_aujourdhui_date')
                self.data['tempo_couleur_aujourdhui'] = stored_data.get('tempo_couleur_aujourdhui')
                self.logger.info(
                    f"Cache Tempo restauré: aujourd'hui={self.data.get('tempo_couleur_aujourdhui')} "
                    f"pour le {self.data.get('tempo_aujourdhui_date')}"
                )
        self._tempo_cache_loaded = True

    async def _async_save_tempo_cache(self) -> None:
        """Sauvegarde le cache Tempo dans le stockage persistant."""
        if self.data is None:
            return

        cache_data = {
            'tempo_demain_date': self.data.get('tempo_demain_date'),
            'tempo_couleur_demain': self.data.get('tempo_couleur_demain'),
            'tempo_aujourdhui_date': self.data.get('tempo_aujourdhui_date'),
            'tempo_couleur_aujourdhui': self.data.get('tempo_couleur_aujourdhui'),
        }
        await self._store.async_save(cache_data)
        self.logger.debug(f"Cache Tempo sauvegardé: {cache_data}")

    async def get_tempo_day(self, date):
        date_str = date.strftime('%Y-%m-%d')
        now = dt_util.now().time()
        check_limit = str_to_time(TEMPO_TOMRROW_AVAILABLE_AT)

        cached = self.tempo_prices.get(date_str)
        if cached is not None:
            codeJour = cached['codeJour']
            # Use cache if color is known, or if indéterminé and before the recheck limit
            if codeJour in [1, 2, 3] or (codeJour == 0 and now < check_limit):
                return cached

        url = f"{TEMPO_COLOR_API_URL}/{date_str}"
        response = await self.hass.async_add_executor_job(get_remote_file, url)
        response_json = response.json()

        # Only overwrite cache if new result has a known color, or no cache exists
        if cached is None or response_json.get('codeJour', 0) in [1, 2, 3]:
            self.tempo_prices[date_str] = response_json

        return response_json

    async def get_tempo_forecast(self) -> list:
        """Récupère les prévisions Tempo depuis open-dpe.fr."""
        try:
            response = await self.hass.async_add_executor_job(
                get_remote_file, TEMPO_FORECAST_API_URL
            )
            if response.status_code == 200:
                forecast_data = response.json()
                self.logger.debug(f"Prévisions Tempo récupérées: {len(forecast_data)} jours")
                return forecast_data
            else:
                self.logger.warning(
                    f"Erreur lors de la récupération des prévisions Tempo: {response.status_code}"
                )
                return []
        except Exception as e:
            self.logger.error(f"Exception lors de la récupération des prévisions Tempo: {e}")
            return []

    async def _async_update_data(self) -> dict[Platform, dict[str, Any]]:
        """Get the latest data from Tarif EDF and updates the state."""
        data = self.config_entry.data
        previous_data = None if self.data is None else self.data.copy()

        # Charger le cache Tempo depuis le stockage persistant au premier démarrage
        if data['contract_type'] == CONTRACT_TYPE_TEMPO:
            await self._async_load_tempo_cache()

        if previous_data is None:
            # Préserver les données du cache si elles existent
            cached_tempo_demain_date = self.data.get('tempo_demain_date') if self.data else None
            cached_tempo_couleur_demain = self.data.get('tempo_couleur_demain') if self.data else None
            cached_tempo_aujourdhui_date = self.data.get('tempo_aujourdhui_date') if self.data else None
            cached_tempo_couleur_aujourdhui = self.data.get('tempo_couleur_aujourdhui') if self.data else None

            self.data = {
                "contract_power": data['contract_power'],
                "contract_type": data['contract_type'],
                "last_refresh_at": None,
                "tarif_actuel_ttc": None
            }

            # Restaurer les données du cache
            if cached_tempo_demain_date:
                self.data['tempo_demain_date'] = cached_tempo_demain_date
                self.data['tempo_couleur_demain'] = cached_tempo_couleur_demain
            if cached_tempo_aujourdhui_date:
                self.data['tempo_aujourdhui_date'] = cached_tempo_aujourdhui_date
                self.data['tempo_couleur_aujourdhui'] = cached_tempo_couleur_aujourdhui

        fresh_data_limit = dt_util.now() - timedelta(days=self.config_entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL))

        tarif_needs_update = self.data['last_refresh_at'] is None or self.data['last_refresh_at'] < fresh_data_limit

        self.logger.info('EDF tarif_needs_update '+('yes' if tarif_needs_update else 'no'))

        if tarif_needs_update:
            if data['contract_type'] == CONTRACT_TYPE_BASE:
                url = TARIF_BASE_URL
            elif data['contract_type'] == CONTRACT_TYPE_HPHC:
                    url = TARIF_HPHC_URL
            elif data['contract_type'] == CONTRACT_TYPE_TEMPO:
                    url = TARIF_TEMPO_URL

            response = await self.hass.async_add_executor_job(get_remote_file, url)
            parsed_content = csv.reader(response.content.decode('utf-8').splitlines(), delimiter=';')
            rows = list(parsed_content)

            for row in rows:
                if row[1] == '' and row[2] == data['contract_power']:
                    if data['contract_type'] == CONTRACT_TYPE_BASE:
                        self.data['base_fixe_ttc'] = float(row[4].replace(",", "." ))
                        self.data['base_variable_ttc'] = float(row[6].replace(",", "." ))
                    elif data['contract_type'] == CONTRACT_TYPE_HPHC:
                        self.data['hphc_fixe_ttc'] = float(row[4].replace(",", "." ))
                        self.data['hphc_variable_hc_ttc'] = float(row[6].replace(",", "." ))
                        self.data['hphc_variable_hp_ttc'] = float(row[8].replace(",", "." ))
                    elif data['contract_type'] == CONTRACT_TYPE_TEMPO:
                        self.data['tempo_fixe_ttc'] = float(row[4].replace(",", "." ))
                        self.data['tempo_variable_hc_bleu_ttc'] = float(row[6].replace(",", "." ))
                        self.data['tempo_variable_hp_bleu_ttc'] = float(row[8].replace(",", "." ))
                        self.data['tempo_variable_hc_blanc_ttc'] = float(row[10].replace(",", "." ))
                        self.data['tempo_variable_hp_blanc_ttc'] = float(row[12].replace(",", "." ))
                        self.data['tempo_variable_hc_rouge_ttc'] = float(row[14].replace(",", "." ))
                        self.data['tempo_variable_hp_rouge_ttc'] = float(row[16].replace(",", "." ))

                    self.data['last_refresh_at'] = dt_util.now()

                    break
            response.close

        if data['contract_type'] == CONTRACT_TYPE_TEMPO:
            today = dt_util.now().date()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)
            today_str = today.strftime('%Y-%m-%d')

            tempo_yesterday = await self.get_tempo_day(yesterday)
            tempo_today = await self.get_tempo_day(today)
            tempo_tomorrow = await self.get_tempo_day(tomorrow)

            yesterday_color = get_tempo_color_from_code(tempo_yesterday['codeJour'])
            today_color = get_tempo_color_from_code(tempo_today['codeJour'])
            tomorrow_color = get_tempo_color_from_code(tempo_tomorrow['codeJour'])
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')

            # Si la couleur d'aujourd'hui est indéterminée, essayer de la résoudre
            # depuis les caches (couleur de demain de la veille, ou couleur déjà résolue)
            if today_color == "indéterminé":
                # D'abord vérifier si on a déjà résolu la couleur d'aujourd'hui
                if self.data.get('tempo_aujourdhui_date') == today_str:
                    cached_today_color = self.data.get('tempo_couleur_aujourdhui')
                    if cached_today_color and cached_today_color != "indéterminé":
                        self.logger.info(f"Réutilisation de la couleur d'aujourd'hui déjà résolue: {cached_today_color}")
                        today_color = cached_today_color
                # Sinon vérifier la couleur de demain connue la veille
                elif self.data.get('tempo_demain_date') == today_str:
                    previous_tomorrow_color = self.data.get('tempo_couleur_demain')
                    if previous_tomorrow_color and previous_tomorrow_color != "indéterminé":
                        self.logger.info(f"Réutilisation de la couleur de demain connue la veille: {previous_tomorrow_color}")
                        today_color = previous_tomorrow_color

            # Si la couleur de demain est indéterminée mais qu'on l'avait déjà
            # récupérée et qu'elle est valide, on réutilise cette valeur du cache
            if tomorrow_color == "indéterminé" and self.data.get('tempo_demain_date') == tomorrow_str:
                cached_tomorrow_color = self.data.get('tempo_couleur_demain')
                if cached_tomorrow_color and cached_tomorrow_color != "indéterminé":
                    self.logger.info(f"Réutilisation de la couleur de demain déjà connue: {cached_tomorrow_color}")
                    tomorrow_color = cached_tomorrow_color

            self.data['tempo_couleur_hier'] = yesterday_color
            self.data['tempo_couleur_aujourdhui'] = today_color
            # Sauvegarder la couleur résolue d'aujourd'hui pour les mises à jour suivantes
            self.data['tempo_aujourdhui_date'] = today_str
            self.data['tempo_couleur_demain'] = tomorrow_color
            # Stocker la date de demain pour pouvoir la réutiliser après minuit
            self.data['tempo_demain_date'] = tomorrow_str

            # Sauvegarder le cache Tempo sur disque pour survivre aux redémarrages
            save_cache = False
            if tomorrow_color != "indéterminé":
                save_cache = True
            if today_color != "indéterminé":
                save_cache = True
            if save_cache:
                await self._async_save_tempo_cache()
            else:
                self.logger.debug("Cache Tempo non sauvegardé: couleurs indéterminées")

            if dt_util.now().time() >= str_to_time(TEMPO_DAY_START_AT):
                self.logger.info("Using today's tempo prices")
                current_color = today_color
            else:
                self.logger.info("Using yesterday's tempo prices")
                current_color = yesterday_color

            if current_color != "indéterminé":
                self.data['tempo_couleur'] = current_color
                self.data['tempo_variable_hp_ttc'] = self.data[f"tempo_variable_hp_{current_color}_ttc"]
                self.data['tempo_variable_hc_ttc'] = self.data[f"tempo_variable_hc_{current_color}_ttc"]
                self.data['last_refresh_at'] = dt_util.now()

            # Récupérer les prévisions Tempo (J+1 à J+9)
            forecast_data = await self.get_tempo_forecast()
            if forecast_data:
                for i, forecast in enumerate(forecast_data[:TEMPO_FORECAST_DAYS]):
                    day_num = i + 1
                    self.data[f'tempo_prevision_j{day_num}_couleur'] = forecast.get('couleur', 'indéterminé')
                    self.data[f'tempo_prevision_j{day_num}_probabilite'] = round(forecast.get('probability', 0) * 100)
                    self.data[f'tempo_prevision_j{day_num}_date'] = forecast.get('date', '')
                self.logger.info(f"Prévisions Tempo mises à jour pour {len(forecast_data)} jours")
            else:
                # En cas d'erreur, initialiser avec des valeurs par défaut
                for i in range(TEMPO_FORECAST_DAYS):
                    day_num = i + 1
                    if f'tempo_prevision_j{day_num}_couleur' not in self.data:
                        self.data[f'tempo_prevision_j{day_num}_couleur'] = 'indéterminé'
                        self.data[f'tempo_prevision_j{day_num}_probabilite'] = 0
                        self.data[f'tempo_prevision_j{day_num}_date'] = ''

        default_offpeak_hours = None
        if data['contract_type'] == CONTRACT_TYPE_TEMPO:
            default_offpeak_hours = TEMPO_OFFPEAK_HOURS
        off_peak_hours_ranges = self.config_entry.options.get("off_peak_hours_ranges", default_offpeak_hours)

        if data['contract_type'] == CONTRACT_TYPE_BASE:
            self.data['tarif_actuel_ttc'] = self.data['base_variable_ttc']
        elif data['contract_type'] in [CONTRACT_TYPE_HPHC, CONTRACT_TYPE_TEMPO] and off_peak_hours_ranges is not None:
            contract_type_key = 'hphc' if data['contract_type'] == CONTRACT_TYPE_HPHC else 'tempo'
            tarif_actuel = self.data[contract_type_key+'_variable_hp_ttc']
            now = dt_util.now().time()
            for range in off_peak_hours_ranges.split(','):
                if not re.match(r'([0-1]?[0-9]|2[0-3]):[0-5][0-9]-([0-1]?[0-9]|2[0-3]):[0-5][0-9]', range):
                    continue

                hours = range.split('-')
                start_at = str_to_time(hours[0])
                end_at = str_to_time(hours[1])

                if time_in_between(now, start_at, end_at):
                    tarif_actuel = self.data[contract_type_key+'_variable_hc_ttc']
                    break

            self.data['tarif_actuel_ttc'] = tarif_actuel

        self.logger.info('EDF Tarif')
        self.logger.info(self.data)

        return self.data
