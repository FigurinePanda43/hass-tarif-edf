"""Constants for the Tarif EDF integration."""

from homeassistant.const import Platform

DOMAIN = "tarif_edf"

CONTRACT_TYPE_BASE="base"
CONTRACT_TYPE_HPHC="hphc"
CONTRACT_TYPE_TEMPO="tempo"

TARIF_BASE_URL="https://www.data.gouv.fr/fr/datasets/r/c13d05e5-9e55-4d03-bf7e-042a2ade7e49"
TARIF_HPHC_URL="https://www.data.gouv.fr/fr/datasets/r/f7303b3a-93c7-4242-813d-84919034c416"
TARIF_TEMPO_URL="https://www.data.gouv.fr/fr/datasets/r/0c3d1d36-c412-4620-8566-e5cbb4fa2b5a"

TEMPO_COLOR_API_URL="https://www.api-couleur-tempo.fr/api/jourTempo"
TEMPO_COLORS_MAPPING={
    0: "indéterminé",
    1: "bleu",
    2: "blanc",
    3: "rouge"
}
TEMPO_DAY_START_AT="06:00"
TEMPO_TOMRROW_AVAILABLE_AT="11:00"
TEMPO_OFFPEAK_HOURS="22:00-06:00"

DEFAULT_REFRESH_INTERVAL=1

# Tarifs Tempo février 2026 (en attendant la mise à jour de data.gouv.fr)
# Source: grille tarifaire EDF applicable au 01/02/2026
# Abonnement en €/an, prix kWh en €/kWh
TEMPO_TARIFS_2026 = {
    "date_debut": "2026-02-01",
    "puissances": {
        "6": {
            "fixe_ttc": 187.08,          # 15,59 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "9": {
            "fixe_ttc": 232.56,          # 19,38 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "12": {
            "fixe_ttc": 276.84,          # 23,07 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "15": {
            "fixe_ttc": 317.64,          # 26,47 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "18": {
            "fixe_ttc": 360.48,          # 30,04 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "30": {
            "fixe_ttc": 536.76,          # 44,73 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
        "36": {
            "fixe_ttc": 629.04,          # 52,42 €/mois × 12
            "hc_bleu_ttc": 0.1325,
            "hp_bleu_ttc": 0.1612,
            "hc_blanc_ttc": 0.1499,
            "hp_blanc_ttc": 0.1871,
            "hc_rouge_ttc": 0.1575,
            "hp_rouge_ttc": 0.7060,
        },
    }
}

# Storage constants
STORAGE_VERSION = 1
STORAGE_KEY = "tarif_edf_tempo_cache"

PLATFORMS = [Platform.SENSOR]
