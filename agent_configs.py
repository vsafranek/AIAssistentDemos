"""Konfigurace různých demo agentů"""

# Demo 1: Document Q&A Agent
DOCUMENT_QA_CONFIG = {
    "name": "Document Q&A Agent",
    "description": "Agent pro dotazy nad dokumenty s RAG",
    "icon": "📄"
}

# Demo 2: Information Collector Agent - Zákaznická karta
CUSTOMER_INFO_CONFIG = {
    "name": "Zákaznická karta",
    "description": "Agent získá informace o zákazníkovi konverzací",
    "icon": "👤",
    "required_fields": {
        "jmeno": "Celé jméno zákazníka",
        "email": "Emailová adresa",
        "telefon": "Telefonní číslo",
        "firma": "Název firmy (pokud relevantní)",
        "pozice": "Pracovní pozice",
        "zajem": "Co zákazníka zajímá / důvod kontaktu"
    }
}

# Demo 3: Information Collector Agent - Objednávka produktu
ORDER_INFO_CONFIG = {
    "name": "Objednávka produktu",
    "description": "Agent pomůže vyplnit objednávku",
    "icon": "🛒",
    "required_fields": {
        "produkt": "Název produktu nebo služby",
        "mnozstvi": "Požadované množství",
        "doruceni_adresa": "Adresa doručení",
        "doruceni_datum": "Preferované datum doručení",
        "poznamka": "Speciální požadavky nebo poznámky"
    }
}

# Demo 4: Information Collector Agent - IT Support ticket
IT_SUPPORT_CONFIG = {
    "name": "IT Support Ticket",
    "description": "Agent vytvoří IT support ticket z konverzace",
    "icon": "🖥️",
    "required_fields": {
        "problem": "Popis problému",
        "priorita": "Priorita (nízká/střední/vysoká/kritická)",
        "software": "Dotčený software/systém",
        "kdy_nastalo": "Kdy problém nastal",
        "dotceni_uzivatele": "Kolik uživatelů to ovlivňuje",
        "kroky_replikace": "Kroky k reprodukci problému"
    }
}

# Seznam všech dostupných konfigurací
AVAILABLE_CONFIGS = {
    "customer": CUSTOMER_INFO_CONFIG,
    "order": ORDER_INFO_CONFIG,
    "it_support": IT_SUPPORT_CONFIG
}
