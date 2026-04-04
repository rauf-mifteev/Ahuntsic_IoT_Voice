"""
src/assistant.py
Rôle : Pipeline principal (Hot-word -> STT -> Interprétation -> MQTT -> TTS).
"""
import json
import subprocess
import speech_recognition as sr
import paho.mqtt.client as mqtt
from interpretation import detecter_intention

# Paramètres MQTT
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_CMD = "ahuntsic/aec-iot/b3/team01/pi01/lampe/cmd"
TOPIC_LOG = "ahuntsic/aec-iot/b3/team01/pi01/lampe/log"
TOPIC_STATE = "ahuntsic/aec-iot/b3/team01/pi01/lampe/state"

HOTWORD = "assistant"
etat_actuel = "inconnu"

# --- Fonctions TTS ---
def speak(text, langue="fr", debit=150):
    """Prononce un texte à l'aide de espeak-ng [cite: 860-861]."""
    subprocess.run(["espeak-ng", "-v", langue, "-s", str(debit), text])

# --- Callbacks MQTT ---
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(TOPIC_STATE)

def on_message(client, userdata, msg):
    """Met à jour l'état local quand la lampe publie son état."""
    global etat_actuel
    if msg.topic == TOPIC_STATE:
        payload = json.loads(msg.payload.decode())
        etat_actuel = payload.get("etat", "inconnu")

# --- Configuration MQTT ---
client = mqtt.Client(client_id="assistant_vocal", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message
client.connect_async(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

# --- Configuration STT ---
r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold = 1200
r.pause_threshold = 0.8
MIC_INDEX = 1 # Remplacer par l'index correct du microphone 

def traiter_intention(intention, texte_original):
    """Exécute l'action MQTT appropriée et le retour vocal."""
    resultat = "Succès"
    
    if intention == "allumer_lampe":
        client.publish(TOPIC_CMD, json.dumps({"action": "on"}), qos=1)
        speak("Lampe allumée")
    elif intention == "eteindre_lampe":
        client.publish(TOPIC_CMD, json.dumps({"action": "off"}), qos=1)
        speak("Lampe éteinte")
    elif intention == "clignoter_lampe":
        client.publish(TOPIC_CMD, json.dumps({"action": "blink"}), qos=1)
        speak("La lampe clignote")
    elif intention == "mode_nuit":
        client.publish(TOPIC_CMD, json.dumps({"action": "night"}), qos=1)
        speak("Mode nuit activé")
    elif intention == "etat_lampe":
        speak(f"L'état actuel de la lampe est {etat_actuel}")
    else:
        speak("Commande non reconnue")
        resultat = "Échec: inconnue"

    # Publier le log pour le module MariaDB
    log_data = {
        "commande": texte_original,
        "intention": intention,
        "resultat": resultat
    }
    client.publish(TOPIC_LOG, json.dumps(log_data), qos=1)

# --- Boucle Principale ---
print("[INFO] Démarrage de l'assistant vocal. Dites le mot d'activation.")
try:
    with sr.Microphone(device_index=MIC_INDEX) as source:
        r.adjust_for_ambient_noise(source, duration=2)
        while True:
            try:
                # Écoute continue en attente du mot d'activation
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
                texte = r.recognize_google(audio, language="fr-FR").lower()
                
                if HOTWORD in texte:
                    speak("Je vous écoute")
                    print("[SYSTEM] Écoute de la commande...")
                    
                    # Écoute de la commande réelle
                    audio_cmd = r.listen(source, timeout=8, phrase_time_limit=6)
                    commande_texte = r.recognize_google(audio_cmd, language="fr-FR")
                    print(f"[USER] {commande_texte}")
                    
                    intention = detecter_intention(commande_texte)
                    print(f"[INTENT] {intention}")
                    
                    traiter_intention(intention, commande_texte)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Erreur service STT: {e}")

except KeyboardInterrupt:
    print("\n[STOP] Arrêt de l'assistant.")
finally:
    client.loop_stop()
    client.disconnect()