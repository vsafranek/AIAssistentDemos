from chatbot import ContextualChatbot


class DocumentAnalyzer:
    """Pokročilé analytické funkce pro demonstraci schopností agenta"""

    def __init__(self, chatbot: ContextualChatbot):
        self.chatbot = chatbot

    def auto_generate_summary(self) -> str:
        """Automatické shrnutí dokumentu"""
        prompt = """Vytvořte komplexní shrnutí celého dokumentu. Zahrňte:
1. Hlavní téma dokumentu
2. Klíčové body a závěry
3. Důležité informace
4. Celkový kontext

Odpověď strukturujte přehledně."""
        return self.chatbot.ask(prompt)["answer"]

    def extract_key_entities(self) -> str:
        """Extrakce klíčových entit"""
        prompt = """Analyzujte dokument a vypište všechny důležité entity:
- Osoby (jména, role)
- Organizace a instituce
- Místa a lokace
- Data a časové údaje
- Čísla a statistiky

Seřaďte je podle kategorií."""
        return self.chatbot.ask(prompt)["answer"]

    def identify_themes(self) -> str:
        """Identifikace hlavních témat"""
        prompt = """Jaká jsou hlavní témata probíraná v tomto dokumentu? 
Uveďte 3-5 hlavních témat s krátkým vysvětlením každého."""
        return self.chatbot.ask(prompt)["answer"]

    def answer_quality_check(self) -> str:
        """Kontrola kvality informací v dokumentu"""
        prompt = """Zhodnoťte tento dokument z hlediska:
1. Struktury a organizace
2. Úplnosti informací
3. Jasnosti a srozumitelnosti
4. Konzistence obsahu"""
        return self.chatbot.ask(prompt)["answer"]
