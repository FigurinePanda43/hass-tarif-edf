# Tarif EDF integration for Home Assistant

Fork de [delphiki/hass-tarif-edf](https://github.com/delphiki/hass-tarif-edf) avec des améliorations pour le tarif Tempo.

## Améliorations de ce fork

### v2.3.0
- **Tarifs Tempo février 2026** : Ajout des nouveaux tarifs Tempo applicables au 01/02/2026 en attendant la mise à jour de data.gouv.fr. Les tarifs locaux sont utilisés automatiquement si la date est >= 01/02/2026.

### v2.2.2
- **Correction de la synchronisation du cache** : La couleur de demain n'est plus écrasée par "indéterminé" quand l'API a des problèmes temporaires. Le cache n'est sauvegardé que si la couleur de demain est une vraie couleur (bleu, blanc, rouge).

### v2.2.1
- **Correction du fuseau horaire** : Le changement de jour Tempo respecte maintenant le fuseau horaire configuré dans Home Assistant (et non plus UTC)

### v2.2.0
- **Persistance du cache Tempo** : La couleur de "demain" connue la veille est sauvegardée sur disque et survit aux redémarrages de Home Assistant
- **Correction du bug "indéterminé"** : Après minuit, si l'API retourne "indéterminé" pour aujourd'hui, l'intégration réutilise la couleur connue la veille comme couleur de "demain"

## Installation

### Using HACS (Dépôt personnalisé)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés"
3. Ajoutez l'URL : `https://github.com/FigurinePanda43/hass-tarif-edf`
4. Catégorie : "Intégration"
5. Cliquez sur "Ajouter"
6. Recherchez "Tarif EDF" et installez

### Manual install

Copiez le dossier `tarif_edf` dans le dossier `custom_components` de votre configuration Home Assistant.

```bash
cd /chemin/vers/config/custom_components/
wget https://github.com/FigurinePanda43/hass-tarif-edf/releases/latest/download/tarif_edf.zip
unzip tarif_edf.zip
rm tarif_edf.zip
```

## Configuration

[![Open your Home Assistant instance and add the integration via the UI.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tarif_edf)

### Paramètres de configuration

| Paramètre | Description | Valeurs possibles |
|-----------|-------------|-------------------|
| `contract_power` | Puissance souscrite | 3, 6, 9, 12, 15, 18, 30, 36 kVA |
| `contract_type` | Type de contrat | Base, Heures pleines/Heures creuses, Tempo |

### Options (après installation)

| Option | Description | Valeur par défaut |
|--------|-------------|-------------------|
| `refresh_interval` | Intervalle de rafraîchissement des tarifs (jours) | 1 |
| `off_peak_hours_ranges` | Plages horaires creuses (format: HH:MM-HH:MM) | 22:00-06:00 (Tempo) |

**Format des plages horaires** : `HH:MM-HH:MM` séparées par des virgules. Exemple : `22:00-06:00` ou `01:30-07:30,12:30-14:30`

## Available Sensors

### Common Sensors (All Contracts)
| Sensor | Description | Unit | Example |
|--------|-------------|------|---------|
| `sensor.tarif_actuel_[type]_[power]kva_ttc` | Current applicable rate | EUR/kWh | `sensor.tarif_actuel_base_6kva_ttc` |

### Base Contract
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.tarif_base_ttc` | Base rate | EUR/kWh |
| `sensor.tarif_base_fixe_ttc` | Fixed subscription rate | EUR/year |

### HP/HC Contract (Peak/Off-Peak)
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.tarif_heures_creuses_ttc` | Off-peak hours rate | EUR/kWh |
| `sensor.tarif_heures_pleines_ttc` | Peak hours rate | EUR/kWh |
| `sensor.tarif_hphc_fixe_ttc` | Fixed subscription rate | EUR/year |

### Tempo Contract
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.tarif_tempo_couleur` | Current Tempo color (based on time of day) | - |
| `sensor.tarif_tempo_couleur_hier` | Yesterday's Tempo color | - |
| `sensor.tarif_tempo_couleur_aujourd_hui` | Today's Tempo color | - |
| `sensor.tarif_tempo_couleur_demain` | Tomorrow's Tempo color | - |
| `sensor.tarif_tempo_heures_creuses_ttc` | Current off-peak hours rate | EUR/kWh |
| `sensor.tarif_tempo_heures_pleines_ttc` | Current peak hours rate | EUR/kWh |
| `sensor.tarif_bleu_tempo_heures_creuses_ttc` | Blue days off-peak rate | EUR/kWh |
| `sensor.tarif_bleu_tempo_heures_pleines_ttc` | Blue days peak rate | EUR/kWh |
| `sensor.tarif_blanc_tempo_heures_creuses_ttc` | White days off-peak rate | EUR/kWh |
| `sensor.tarif_blanc_tempo_heures_pleines_ttc` | White days peak rate | EUR/kWh |
| `sensor.tarif_rouge_tempo_heures_creuses_ttc` | Red days off-peak rate | EUR/kWh |
| `sensor.tarif_rouge_tempo_heures_pleines_ttc` | Red days peak rate | EUR/kWh |
| `sensor.tarif_tempo_fixe_ttc` | Fixed subscription rate | EUR/year |

## Fonctionnement du Tempo

### Couleurs Tempo
- **Bleu** : Jours les moins chers (300 jours/an)
- **Blanc** : Jours intermédiaires (43 jours/an)
- **Rouge** : Jours les plus chers (22 jours/an)

### Horaires
- **Jour Tempo** : De 06:00 à 06:00 le lendemain
- **Heures creuses** : 22:00 - 06:00
- **Heures pleines** : 06:00 - 22:00
- **Couleur de demain disponible** : À partir de 11:00

### Gestion du cache
La couleur de demain est sauvegardée sur disque. Le cache est protégé contre les problèmes de l'API :
- Si Home Assistant redémarre après minuit et avant 11h, l'intégration réutilise la couleur connue la veille au lieu d'afficher "indéterminé"
- Si l'API retourne temporairement "indéterminé" pour demain alors que la couleur était déjà connue, la valeur du cache est préservée

### Tarifs locaux (février 2026)

Les tarifs Tempo de février 2026 sont intégrés directement dans l'intégration car data.gouv.fr n'est pas encore mis à jour. Ces tarifs sont utilisés automatiquement si la date est >= 01/02/2026.

| Puissance | Abonnement | Bleu HC | Bleu HP | Blanc HC | Blanc HP | Rouge HC | Rouge HP |
|-----------|------------|---------|---------|----------|----------|----------|----------|
| 6 kVA     | 187,08 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 9 kVA     | 232,56 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 12 kVA    | 276,84 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 15 kVA    | 317,64 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 18 kVA    | 360,48 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 30 kVA    | 536,76 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |
| 36 kVA    | 629,04 €/an | 0,1325 | 0,1612  | 0,1499   | 0,1871   | 0,1575   | 0,7060   |

*Prix du kWh en €/kWh TTC*

## Sources de données

- Tarifs : [data.gouv.fr](https://www.data.gouv.fr/) (avec tarifs locaux pour février 2026)
- Couleurs Tempo : [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr/)
