# Assistant vocal de lampe intelligente

Coauteurs: Rauf Mifteev, Jean-Jacques Arquero

Le lien vers le dépôt GitHub : **https://github.com/rauf-mifteev/Ahuntsic_IoT_Voice**

## Description

Ce projet est un prototype fonctionnel d'assistant vocal développée dans le cadre du cours "Développement d'objets intelligents" (AEC IoT au Collège Ahuntsic). Le système permet d'interagir avec une lampe connectée (sur Raspberry Pi) à la voix, en utilisant un mot d'activation, la reconnaissance vocale, une communication MQTT, un retour vocal et une journalisation.

Le système comprend trois composantes principales qui tournent sur le Pi :
* un assistant vocal qui écoute le hot-word, transcrit la commande, l'interprète, publie l'ordre MQTT et donne un retour vocal.
* un actionneur (subscriber) qui reçoit les commandes MQTT et pilote physiquement la DEL via les broches GPIO.
* un logger qui écoute le topic de journalisation et enregistre les commandes et résultats dans une base MariaDB.

Tous les composants communiquent via un broker Mosquitto qui tourne localement sur le Pi.

## Architecture

    +-------------------+   voix             +-------------------+   MQTT (QoS 1)   +------------------+
    | Utilisateur       | ──> "allume..." ──>| assistant         | ───cmd─────────► | Mosquitto Broker |
    |                   | <── TTS ────────── | (Python + STT)    | ───log─────────► | localhost:1883   |
    +-------------------+                    +-------------------+ ◄──state──────── |                  |
                                                                                    +------------------+
                                                                                             │
      +------------------+   INSERT          +-------------------+                           │
      | MariaDB          | ◄──────────────── | logger_mariadb    | ◄──log────────────────────┤
      | table            |                   | (Python)          |                           │
      | journal_vocal    |                   +-------------------+                           │
      +------------------+                                                                   │
                                                                                             │
      +------------------+   GPIO            +-------------------+                           │
      | Lampe DEL        | ◄──────────────── | lampe_actionneur  | ◄──cmd────────────────────┤
      | (Broche 17)      |                   | (Python + GPIO)   | ───state───────────────►  |
      +------------------+                   +-------------------+                           +

## Contrat MQTT (topics)

Préfixe commun : ahuntsic/aec-iot/b3/team01/pi01/lampe

Topic | Direction | QoS | Retained | Description
--- | --- | --- | --- | ---
.../cmd | Assistant -> broker | 1 | Non | Commande JSON d'action (on, off, blink, night)
.../state | Actionneur -> broker | 1 | Oui | État réel de la DEL pour confirmation locale
.../log | Assistant -> broker | 1 | Non | Données de journalisation JSON pour MariaDB

### Qui publie / qui s'abonne

Script | Publie sur | S'abonne à
--- | --- | ---
assistant.py | cmd, log | state
lampe_actionneur.py | state | cmd
logger_mariadb.py | — | log

### Exemples de payload JSON

Commande DEL (envoyée par l'assistant) :

    {
      "action": "on"
    }

État DEL (publié par l'actionneur) :

    {
      "etat": "allumée"
    }

Journalisation (envoyée vers la base de données) :

    {
      "commande": "allume la lampe",
      "intention": "allumer_lampe",
      "resultat": "Succès"
    }

## Installation

1. Cloner le dépôt et installer les dépendances système

```
git clone https://github.com/rauf-mifteev/Ahuntsic_IoT_Voice
cd Ahuntsic_IoT_Voice
sudo apt update
sudo apt install -y python3-pyaudio flac python3-nltk espeak-ng mosquitto mosquitto-clients mariadb-server
```
    
2. Créer l'environnement virtuel et installer les paquets Python

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```
    
3. Démarrer les services Mosquitto, MariaDB et initialiser la BD

```
sudo systemctl enable --now mosquitto
sudo systemctl enable --now mariadb
sudo mariadb < db/schema.sql
```
    
4. Identifier l'index du microphone USB

```
python3 -c "import speech_recognition as sr; print(list(enumerate(sr.Microphone.list_microphone_names())))"
```
(Mettre à jour la variable MIC_INDEX dans src/assistant_vocal.py avec le bon numéro).

## Exécution

Ouvrir 3 terminaux (ou 3 sessions SSH) sur le Pi. Il est fortement recommandé de respecter cet ordre de lancement .

Terminal 1 — Logger MariaDB

    source .venv/bin/activate
    python3 src/logger_mariadb.py

Terminal 2 — Actionneur GPIO

    source .venv/bin/activate
    python3 src/lampe_actionneur.py

Terminal 3 — Assistant Vocal

    source .venv/bin/activate
    python3 src/assistant.py

## Scénario utilisateur (Test fonctionnel)

Le système utilise le mot d'activation : "assistant".

1. Dites "Assistant".
2. Le système répond vocalement : "Je vous écoute".
3. Prononcez l'une des 5 commandes obligatoires :
   * "Allume la lampe"
   * "Éteins la lampe"
   * "Fais clignoter la lampe"
   * "Donne-moi l'état"
   * "Active le mode nuit"
4. La DEL s'ajuste physiquement, l'assistant confirme vocalement l'action, et le logger enregistre la transaction.

## Vérifier MariaDB

Ouvrir la console MariaDB :

    sudo mariadb iot_b3

Afficher les commandes enregistrées par l'assistant :

    SELECT id, date_heure, commande_texte, intention, resultat FROM journal_vocal ORDER BY id DESC LIMIT 10;

## Tester MQTT manuellement (Débogage)

Observer tous les messages liés à la lampe :

    mosquitto_sub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/lampe/#" -v

Simuler l'assistant en envoyant une commande de clignotement :

    mosquitto_pub -h localhost -t "ahuntsic/aec-iot/b3/team01/pi01/lampe/cmd" -m '{"action":"blink"}' -q 1
