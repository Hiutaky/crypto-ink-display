# Piano Implementazione: Crypto Display E-Ink

## Hardware
- Raspberry Pi Zero (o Zero 2 W)
- Display e-ink Waveshare 2.9" (296x128 pixel, SPI)
- Cavo SPI per connessione display-Pi

## Software Stack
- **Linguaggio:** Python 3
- **Librerie principali:**
  - `Pillow` (PIL) - generazione grafica e testo
  - `requests` - chiamate API CoinGecko
  - `waveshare-e-paper` o driver SPI custom per il display
- **Gestione avvio:** systemd service

## Architettura

```
crypto-ink-display/
├── main.py              # Entry point, loop principale con rotazione
├── config.py            # Configurazione (cripto da tracciare, intervalli)
├── display_driver.py    # Wrapper per il display e-ink Waveshare 2.9"
├── price_fetcher.py     # Fetch prezzi da CoinGecko API
├── chart_renderer.py    # Genera mini-grafico linea con Pillow
├── ui_renderer.py       # Composizione UI completa (prezzo + grafico)
├── requirements.txt     # Dipendenze Python
└── systemd/
    └── crypto-ink.service  # Unit file systemd
```

## Specifiche Funzionali

### Crypto Tracciate
BTC, ETH, SOL, XRP, ADA, DOT, DOG (7 asset)

### Rotazione Display
- Ogni crypto mostrata per **10 secondi**
- Ciclo completo: 70 secondi
- Full refresh display ad ogni cambio di crypto

### Aggiornamento Prezzi
- Fetch da CoinGecko API ogni **60 secondi**
- Cache locale dei prezzi (mostra ultimi dati noti se fetch fallisce)
- Endpoint: `/simple/price` per prezzi, `/market_chart` per storico 15 min

### UI per Ogni Crypto
```
┌─────────────────────────────────────┐
│ BTC/USD              ▲ +2.3%       │
│ $67,432.18                              │
│ ┌───────────────────────────────┐   │
│ │     [mini grafico linea]      │   │
│ │     ultimi 15 minuti          │   │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Gestione Errori
- Timeout fetch: 10 secondi
- Retry automatico su errore API (max 3 tentativi)
- Messaggio "Updating..." durante refresh prezzi
- Fallback a dati cached se API non disponibile

## Task di Implementazione

### Fase 1: Setup Base
1. [ ] Inizializzare repo con struttura base e README
2. [ ] Creare `config.py` con lista crypto e intervalli
3. [ ] Installare dipendenze Python su Raspberry Pi Zero
4. [ ] Test connessione SPI con display Waveshare 2.9"

### Fase 2: Fetch Prezzi
5. [ ] Implementare `price_fetcher.py` con CoinGecko API
6. [ ] Test fetch prezzi per tutte le crypto configurate
7. [ ] Implementare cache locale e gestione errori

### Fase 3: Rendering Grafico
8. [ ] Implementare `chart_renderer.py` (grafico linea Pillow)
9. [ ] Implementare `ui_renderer.py` (composizione UI completa)
10. [ ] Test rendering su display fisico

### Fase 4: Loop Principale
11. [ ] Implementare `main.py` con loop di rotazione
12. [ ] Integrare fetch prezzi + refresh display
13. [ ] Test ciclo completo (7 crypto x 10 sec)

### Fase 5: Deploy e Automazione
14. [ ] Creare systemd service file
15. [ ] Configurare auto-start all'avvio del Pi
16. [ ] Test crash recovery e log rotation

## Note Tecniche

### CoinGecko API (gratuita)
- Rate limit: ~30 req/min su endpoint pubblici
- Nessun API key necessario per uso base
- Endpoint prezzi: `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,...&vs_currencies=usd`
- Endpoint storico: `https://api.coingecko.com/api/v3/coins/{id}/market_chart?vs_currency=usd&interval=15m`

### Display Waveshare 2.9"
- Risoluzione: 296x128 pixel
- Interfaccia: SPI
- Refresh time: ~3-5 sec (full), ~0.5 sec (partial)
- Driver Python disponibile da Waveshare o community

### Raspberry Pi Zero Constraints
- CPU: single-core ARM @ 1GHz
- RAM: 512MB
- Python + Pillow funzionano bene per questo uso case
- Evitare operazioni CPU-intensive durante refresh display
