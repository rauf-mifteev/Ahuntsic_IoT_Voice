"""
src/lampe_actionneur.py
Rôle : Subscriber MQTT qui contrôle la DEL via GPIO selon les commandes reçues.
"""
import json
import paho.mqtt.client as mqtt
from gpiozero import LED

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_CMD = "ahuntsic/aec-iot/b3/team01/pi01/lampe/cmd"
TOPIC_STATE = "ahuntsic/aec-iot/b3/team01/pi01/lampe/state"

led = LED(17) 
etat_interne = "éteinte"

def publier_etat(client):
    """Publie l'état actuel de la lampe sur le topic dédié."""
    payload = {"etat": etat_interne}
    client.publish(TOPIC_STATE, json.dumps(payload), qos=1, retain=True)
    print(f"[ETAT] {etat_interne}")

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("[CONNECT] Actionneur connecté.")
        client.subscribe(TOPIC_CMD)
        publier_etat(client)

def on_message(client, userdata, msg):
    global etat_interne
    payload = json.loads(msg.payload.decode())
    action = payload.get("action")
    
    if action == "on":
        led.on()
        etat_interne = "allumée"
    elif action == "off":
        led.off()
        etat_interne = "éteinte"
    elif action == "blink":
        led.blink(on_time=0.5, off_time=0.5)
        etat_interne = "en clignotement"
    elif action == "night":
        # Le mode nuit utilise un clignotement lent au lieu d'une intensité réduite 
        led.blink(on_time=2.0, off_time=2.0) 
        etat_interne = "en mode nuit"
        
    publier_etat(client)

client = mqtt.Client(client_id="lampe_actionneur", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)
print("[INFO] Actionneur prêt. Attente des commandes...")

try:
    client.loop_forever()
except KeyboardInterrupt:
    led.close()
    client.disconnect()
    print("\n[STOP] Arrêt de l'actionneur.")