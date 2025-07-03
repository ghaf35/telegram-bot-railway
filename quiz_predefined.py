#!/usr/bin/env python3
"""
Quiz prédéfinis basés sur TESM.pdf pour le bot Telegram
"""

# Quiz sur l'ASP et la sécurité ferroviaire
QUIZ_ASP = [
    {
        "question": "L'ASP :",
        "options": [
            "Peut exercer sa fonction sans être habilité",
            "Peut s'absenter en désignant un agent habilité",
            "Est chargé de mettre en œuvre les mesures de prévention",
            "Peut assurer l'annonce des circulations"
        ],
        "correct": 2,  # C
        "explanation": "L'ASP est chargé de mettre en œuvre les mesures de prévention inhérentes aux risques ferroviaires"
    },
    {
        "question": "L'ASP doit :",
        "options": [
            "Toujours porter un gilet blanc",
            "Annoncer avec une trompe ceinture",
            "Être clairement identifié sur le chantier",
            "Déterminer le délai de dégagement"
        ],
        "correct": 2,  # C
        "explanation": "L'ASP doit être clairement identifié sur le chantier"
    },
    {
        "question": "Qu'est-ce qu'une zone dangereuse ?",
        "options": [
            "Un endroit avec des animaux",
            "Une zone où les agents risquent d'être heurtés",
            "Une zone de repos",
            "Un parking"
        ],
        "correct": 1,  # B
        "explanation": "Une zone dangereuse est une zone où les agents risquent d'être heurtés par une circulation ferroviaire"
    },
    {
        "question": "Le délai de dégagement pour l'outillage de 2ème catégorie ne doit pas excéder :",
        "options": [
            "5 secondes",
            "10 secondes",
            "15 secondes",
            "20 secondes"
        ],
        "correct": 2,  # C
        "explanation": "Le délai de dégagement ne doit pas excéder 15 secondes (P15)"
    },
    {
        "question": "Le PPSPS signifie :",
        "options": [
            "Plan de Prévention et de Sécurité",
            "Plan Particulier de Sécurité et de Protection de la Santé",
            "Programme de Protection et Sécurité du Personnel",
            "Protocole de Prévention et Sûreté du Personnel"
        ],
        "correct": 1,  # B
        "explanation": "Plan Particulier de Sécurité et de Protection de la Santé, rédigé par Fer Expert"
    }
]

# Quiz sur les délais et distances
QUIZ_DELAIS = [
    {
        "question": "Le délai d'annonce minimum est de :",
        "options": [
            "10 secondes",
            "15 secondes",
            "20 secondes",
            "30 secondes"
        ],
        "correct": 1,  # B
        "explanation": "Le délai d'annonce minimum est de 15 secondes"
    },
    {
        "question": "La distance d'annonce dépend de :",
        "options": [
            "La vitesse des circulations uniquement",
            "Le délai d'annonce uniquement",
            "La vitesse et le délai d'annonce",
            "Le type de voie uniquement"
        ],
        "correct": 2,  # C
        "explanation": "La distance d'annonce dépend de la vitesse des circulations et du délai d'annonce"
    },
    {
        "question": "En cas d'obstacle, l'ASP doit :",
        "options": [
            "Continuer les travaux",
            "Avertir son supérieur et couvrir l'obstacle",
            "Attendre la fin des travaux",
            "Ignorer l'obstacle"
        ],
        "correct": 1,  # B
        "explanation": "L'ASP doit avertir son supérieur et assurer la couverture d'obstacle"
    }
]

# Fonction pour obtenir un quiz aléatoire
def get_random_quiz():
    """Retourne 3 questions aléatoires"""
    import random
    all_questions = QUIZ_ASP + QUIZ_DELAIS
    return random.sample(all_questions, min(3, len(all_questions)))