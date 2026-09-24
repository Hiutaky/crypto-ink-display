#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
import time
import requests
import traceback
from PIL import Image, ImageDraw, ImageFont

# Configurazione path come nel reference
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V2

logging.basicConfig(level=logging.INFO)

# IDs su CoinGecko per le crypto richieste
# Nota: 'dogecoin' è la coin standard. Se cerchi token specifici su protocollo ordinals, 
# dovresti cercare l'ID esatto su CoinGecko (es. 'dog-go-to-the-moon').
CRYPTO_IDS = ['bitcoin', 'ethereum', 'solana', 'dogecoin', 'monero']
CURRENCY = 'usd'

def fetch_crypto_data():
    """Recupera i dati e i grafici sparkline (ultimi 7 gg) da CoinGecko."""
    logging.info("Scaricamento dati da CoinGecko...")
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': CURRENCY,
        'ids': ','.join(CRYPTO_IDS),
        'sparkline': 'true',
        'price_change_percentage': '24h'
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Errore nel recupero dati: {e}")
        return None

def draw_sparkline(draw, data_points, x_offset, y_offset, width, height):
    """Disegna il grafico dell'andamento dei prezzi."""
    if not data_points:
        return
        
    min_val = min(data_points)
    max_val = max(data_points)
    range_val = max_val - min_val if max_val != min_val else 1
    
    points = []
    num_points = len(data_points)
    
    for i, val in enumerate(data_points):
        x = x_offset + (i / (num_points - 1)) * width
        y = y_offset + height - ((val - min_val) / range_val) * height
        points.append((x, y))
        
    draw.line(points, fill=0, width=2)

def main():
    try:
        epd = epd2in13_V2.EPD()
        logging.info("Inizializzazione display")
        
        # Caricamento font
        try:
            font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
            font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
            font12 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
        except IOError:
            logging.warning("Font personalizzato non trovato, utilizzo font di default")
            font15 = ImageFont.load_default()
            font24 = ImageFont.load_default()
            font12 = ImageFont.load_default()

        # Nota: su epd2in13, height = lato lungo (250), width = lato corto (122) in orizzontale
        disp_width = epd.height 
        disp_height = epd.width

        while True:
            # 1. Recupero Dati
            crypto_data = fetch_crypto_data()
            
            if crypto_data:
                # Pulizia schermo e inizializzazione per Base Image (FULL UPDATE)
                # È importante farlo periodicamente per evitare il ghosting del display e-ink
                epd.init(epd.FULL_UPDATE)
                epd.Clear(0xFF)
                
                # Creiamo un'immagine di base bianca per i partial update successivi
                base_image = Image.new('1', (disp_width, disp_height), 255)
                epd.displayPartBaseImage(epd.getbuffer(base_image))
                
                # Attiviamo la modalità PART_UPDATE per rotazioni fluide e senza sfarfallio
                epd.init(epd.PART_UPDATE)
                
                for coin in crypto_data:
                    # Immagine temporanea per il display
                    image = Image.new('1', (disp_width, disp_height), 255)
                    draw = ImageDraw.Draw(image)
                    
                    symbol = coin.get('symbol', '').upper()
                    price = coin.get('current_price', 0)
                    change_24h = coin.get('price_change_percentage_24h', 0)
                    sparkline = coin.get('sparkline_in_7d', {}).get('price', [])
                    
                    # Formattazione prezzo e change
                    price_str = f"${price:,.2f}" if price > 0.01 else f"${price:.6f}"
                    change_str = f"{change_24h:+.2f}%"
                    
                    # Disegno Testo
                    draw.text((10, 5), f"{symbol}", font=font24, fill=0)
                    draw.text((10, 35), price_str, font=font24, fill=0)
                    
                    # Cambio 24h allineato a destra
                    draw.text((160, 10), change_str, font=font15, fill=0)
                    
                    # Disegno Grafico (Occupa la metà inferiore del display)
                    draw_sparkline(draw, sparkline, x_offset=0, y_offset=65, width=disp_width, height=50)
                    
                    # Mostriamo l'immagine con aggiornamento parziale
                    epd.displayPartial(epd.getbuffer(image))
                    
                    logging.info(f"Mostrato {symbol}: {price_str}")
                    time.sleep(10) # Rotazione ogni 10 secondi
            else:
                logging.warning("Impossibile recuperare i dati. Riprovo tra 30 secondi.")
                time.sleep(30)

    except IOError as e:
        logging.error(f"Errore IO: {e}")
    except KeyboardInterrupt:
        logging.info("Chiusura script (Ctrl+C)")
        epd2in13_V2.epdconfig.module_exit(cleanup=True)
        exit()
    except Exception as e:
        logging.error(traceback.format_exc())

if __name__ == '__main__':
    main()