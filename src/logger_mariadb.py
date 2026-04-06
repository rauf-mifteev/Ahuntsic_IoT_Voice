"""
src/logger_mariadb.py
Rôle : Subscriber MQTT dédié à l'insertion des logs vocaux dans MariaDB.
"""
import json
import pymysql
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_LOG = "ahuntsic/aec-iot/b3/team01/pi01/lampe/log"

# Paramètres MariaDB
DB_HOST = "localhost"
DB_USER = "iot"
DB_PASSWORD = "iot"
DB_NAME = "iot_b3"

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("[CONNECT] Logger connecté.")
        client.subscribe(TOPIC_LOG)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    commande = payload.get("commande", "")
    intention = payload.get("intention", "")
    resultat = payload.get("resultat", "")
    
    try:
        connection = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, autocommit=True, charset="utf8mb4"
        )
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO journal_vocal (commande_texte, intention, resultat)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (commande, intention, resultat))
        print(f"[DB] Log enregistré : {intention}")
        connection.close()
    except pymysql.MySQLError as e:
        print(f"[ERREUR DB] {e}")

client = mqtt.Client(client_id="logger_vocal", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, 60)
print("[INFO] Logger actif. Attente des logs...")

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    print("\n[STOP] Arrêt du logger.")