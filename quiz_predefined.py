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
        "question": "Le délai d'annonce maximum est de :",
        "options": [
            "30 secondes",
            "45 secondes",
            "60 secondes",
            "90 secondes"
        ],
        "correct": 2,  # C
        "explanation": "Le délai d'annonce maximum est de 60 secondes"
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

# Quiz sur les documents et sigles
QUIZ_DOCUMENTS = [
    {
        "question": "Le PGC signifie :",
        "options": [
            "Plan Général de Coordination",
            "Programme Général de Chantier",
            "Plan de Gestion des Conflits",
            "Protocole Général de Communication"
        ],
        "correct": 0,  # A
        "explanation": "PGC = Plan Général de Coordination"
    },
    {
        "question": "La CSF signifie :",
        "options": [
            "Consigne de Sécurité Ferroviaire",
            "Commission de Sûreté Française",
            "Certificat de Sécurité Ferroviaire",
            "Code de Sécurité Ferroviaire"
        ],
        "correct": 0,  # A
        "explanation": "CSF = Consigne de Sécurité Ferroviaire"
    },
    {
        "question": "L'ISF signifie :",
        "options": [
            "Information Sécurité Ferroviaire",
            "Instruction de Sécurité Ferroviaire",
            "Inspection de Sécurité Ferroviaire",
            "Intervention de Sécurité Ferroviaire"
        ],
        "correct": 1,  # B
        "explanation": "ISF = Instruction de Sécurité Ferroviaire"
    },
    {
        "question": "Le PDP signifie :",
        "options": [
            "Plan de Protection",
            "Programme de Prévention",
            "Plan de Prévention",
            "Protocole de Protection"
        ],
        "correct": 2,  # C
        "explanation": "PDP = Plan de Prévention"
    }
]

# Quiz sur les zones et emplacements
QUIZ_ZONES = [
    {
        "question": "La zone dangereuse pour V ≤ 40 km/h est de :",
        "options": [
            "1,25 m",
            "1,50 m",
            "1,75 m",
            "2,00 m"
        ],
        "correct": 1,  # B
        "explanation": "Pour V ≤ 40 km/h, la zone dangereuse est de 1,50 m"
    },
    {
        "question": "La zone dangereuse pour 40 < V ≤ 160 km/h est de :",
        "options": [
            "1,50 m",
            "1,75 m",
            "2,00 m",
            "2,25 m"
        ],
        "correct": 1,  # B
        "explanation": "Pour 40 < V ≤ 160 km/h, la zone dangereuse est de 1,75 m"
    },
    {
        "question": "Une voie banalisée est :",
        "options": [
            "Une voie interdite aux trains",
            "Une voie à sens unique",
            "Une voie parcourue dans les deux sens",
            "Une voie de garage"
        ],
        "correct": 2,  # C
        "explanation": "Une voie banalisée est une voie parcourue dans les deux sens"
    },
    {
        "question": "L'interdiction de circulation est obligatoire pour :",
        "options": [
            "Les pièces de moins de 50 kg",
            "Les pièces de plus de 100 kg",
            "Les pièces manipulables par un agent",
            "Toutes les pièces"
        ],
        "correct": 1,  # B
        "explanation": "L'interdiction est obligatoire pour les pièces lourdes (> 100 kg)"
    }
]

# Fonction pour obtenir un quiz aléatoire
def get_random_quiz():
    """Retourne 3 questions aléatoires"""
    import random
    all_questions = QUIZ_ASP + QUIZ_DELAIS
    return random.sample(all_questions, min(3, len(all_questions)))

# Fonction pour obtenir TOUTES les questions
def get_full_quiz():
    """Retourne TOUTES les questions du quiz"""
    return QUIZ_ASP + QUIZ_DELAIS + QUIZ_DOCUMENTS + QUIZ_ZONES