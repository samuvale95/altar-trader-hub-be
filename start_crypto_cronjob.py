#!/usr/bin/env python3
"""
Script per avviare il cronjob di raccolta dati cripto.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def start_redis():
    """Avvia Redis se non è già in esecuzione."""
    
    try:
        # Verifica se Redis è già in esecuzione
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis è già in esecuzione")
            return True
    except FileNotFoundError:
        print("⚠️ Redis non trovato, provo ad avviarlo...")
    
    try:
        # Prova ad avviare Redis
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        # Verifica se è partito
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis avviato con successo")
            return True
        else:
            print("❌ Impossibile avviare Redis")
            return False
            
    except Exception as e:
        print(f"❌ Errore nell'avvio di Redis: {e}")
        return False

def start_celery_worker():
    """Avvia il worker Celery."""
    
    print("🚀 Avvio Celery Worker...")
    
    try:
        # Avvia il worker Celery
        cmd = [
            'celery', '-A', 'app.tasks.crypto_data_cronjob',
            'worker', '--loglevel=info', '--concurrency=2'
        ]
        
        worker_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Celery Worker avviato")
        return worker_process
        
    except Exception as e:
        print(f"❌ Errore nell'avvio del Celery Worker: {e}")
        return None

def start_celery_beat():
    """Avvia il scheduler Celery Beat."""
    
    print("⏰ Avvio Celery Beat Scheduler...")
    
    try:
        # Avvia il scheduler Beat
        cmd = [
            'celery', '-A', 'app.tasks.crypto_data_cronjob',
            'beat', '--loglevel=info'
        ]
        
        beat_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Celery Beat Scheduler avviato")
        return beat_process
        
    except Exception as e:
        print(f"❌ Errore nell'avvio del Celery Beat: {e}")
        return None

def main():
    """Funzione principale."""
    
    print("🚀 Avvio Cronjob Raccolta Dati Cripto")
    print("=" * 50)
    
    # 1. Avvia Redis
    if not start_redis():
        print("❌ Impossibile continuare senza Redis")
        return
    
    # 2. Avvia Celery Worker
    worker_process = start_celery_worker()
    if not worker_process:
        print("❌ Impossibile continuare senza Celery Worker")
        return
    
    # 3. Avvia Celery Beat
    beat_process = start_celery_beat()
    if not beat_process:
        print("❌ Impossibile continuare senza Celery Beat")
        worker_process.terminate()
        return
    
    print("\n🎉 Cronjob avviato con successo!")
    print("📊 Dati cripto verranno raccolti automaticamente:")
    print("   • Simboli principali: ogni 5 minuti")
    print("   • Simboli ad alto volume: ogni 15 minuti")
    print("   • Aggiornamento simboli: ogni ora")
    print("   • Pulizia dati vecchi: ogni giorno alle 2:00")
    print("\n⏹️  Premi Ctrl+C per fermare")
    
    try:
        # Mantieni i processi in esecuzione
        while True:
            time.sleep(1)
            
            # Verifica se i processi sono ancora attivi
            if worker_process.poll() is not None:
                print("❌ Celery Worker si è fermato")
                break
                
            if beat_process.poll() is not None:
                print("❌ Celery Beat si è fermato")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Fermata del cronjob...")
        
        # Termina i processi
        if worker_process:
            worker_process.terminate()
            print("✅ Celery Worker fermato")
            
        if beat_process:
            beat_process.terminate()
            print("✅ Celery Beat fermato")
        
        print("👋 Cronjob fermato")

if __name__ == "__main__":
    main()

