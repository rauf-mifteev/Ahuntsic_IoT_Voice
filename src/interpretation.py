"""
src/interpretation.py
Rôle : Nettoyer le texte et détecter l'intention à l'aide d'expressions régulières et de NLTK.
"""
import re
from nltk.tokenize import word_tokenize

def normaliser_texte(texte):
    """
    Nettoie le texte en minuscules, retire les accents, les tirets et les apostrophes.
    """
    return (
        texte.lower().strip()
        .replace("\u00e9", "e").replace("\u00e8", "e").replace("\u00ea", "e")
        .replace("\u00e0", "a").replace("\u00e2", "a")
        .replace("\u00f4", "o").replace("\u00ee", "i")
        .replace("\u00f9", "u").replace("\u00fb", "u")
        .replace("\u00e7", "c")
        .replace("-", " ")
        .replace("'", " ") # Isole les mots attachés par une apostrophe
    )

def detecter_intention(texte):
    """
    Détermine l'intention parmi les 5 commandes obligatoires.
    Utilise une approche hybride (NLTK + Regex) avec une normalisation stricte.
    """
    texte_norm = normaliser_texte(texte)
    
    # 1. Tokenisation avec NLTK
    try:
        tokens = word_tokenize(texte_norm, language="french")
    except LookupError:
        tokens = texte_norm.split()
        
    # 2. Utilisation d'expressions régulières (Regex)
    
    # Commande 1 : Allumer la lampe
    if re.search(r"(allume|allumer)\s+(la\s+)?lampe", texte_norm):
        return "allumer_lampe"
        
    # Commande 2 : Éteindre la lampe (recherche sans accent)
    if re.search(r"(eteins|eteindre)\s+(la\s+)?lampe", texte_norm):
        return "eteindre_lampe"
        
    # Commande 3 : Donner l'état (recherche sans tiret ni apostrophe)
    if re.search(r"donne\s+moi\s+l\s+etat", texte_norm):
        return "etat_lampe"
        
    # 3. Utilisation des tokens NLTK 
    
    # Commande 4 : Faire clignoter
    if "clignoter" in tokens:
        return "clignoter_lampe"
        
    # Commande 5 : Mode nuit
    if "nuit" in tokens:
        return "mode_nuit"
        
    return "inconnue"