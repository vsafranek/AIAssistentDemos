from typing import Dict, List
from akkodis_clients import client_gpt_4o
import json


class WebpageAssistant:
    """AI asistent pro pomoc s obsahem webové stránky"""

    def __init__(self, page_content: Dict):
        """
        Args:
            page_content: Dictionary s obsahem stránky
        """
        self.client, self.deployment = client_gpt_4o()
        self.page_content = page_content
        self.conversation_history: List[Dict[str, str]] = []

    def get_system_prompt(self) -> str:
        """Vytvoří system prompt s kontextem stránky"""

        content_summary = f"""INFORMACE O SPOLEČNOSTI:
Název: {self.page_content.get('company_name', 'N/A')}
Popis: {self.page_content.get('company_description', 'N/A')}

NABÍZENÉ SLUŽBY:
"""
        for service in self.page_content.get('services', []):
            content_summary += f"- {service['name']}: {service['description']}\n"

        content_summary += f"""\nKONTAKTNÍ INFORMACE:
Email: {self.page_content.get('contact', {}).get('email', 'N/A')}
Telefon: {self.page_content.get('contact', {}).get('phone', 'N/A')}
Adresa: {self.page_content.get('contact', {}).get('address', 'N/A')}

PRODUKTY:
"""
        for product in self.page_content.get('products', []):
            content_summary += f"- {product['name']}: {product['price']} - {product['description']}\n"

        content_summary += f"""\nČASTO KLADENÉ OTÁZKY (FAQ):
"""
        for faq in self.page_content.get('faq', []):
            content_summary += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"

        prompt = f"""Jsi přátelský AI asistent na webové stránce. Pomáháš návštěvníkům najít informace a odpovídáš na jejich otázky.

{content_summary}

TVOJE ÚKOLY:
1. Odpovídej na dotazy návštěvníků na základě informací ze stránky
2. Buď přátelský, nápomocný a rychlý
3. Pokud návštěvník hledá konkrétní službu nebo produkt, aktivně ji nabídni
4. Pokud potřebuje kontakt, poskytni příslušné údaje
5. Pokud informace nemáš, upřímně to řekni a nabídni kontakt na firmu
6. Odpovídej VŽDY česky
7. Buď stručný ale informativní

PŘÍKLADY DOBRÝCH ODPOVĚDÍ:
"Nabízíme tyto služby: AI řešení, Cloud Migration a Data Analytics. Která vás zajímá nejvíce?"
"Naše Enterprise verze stojí 999 Kč/měsíc a zahrnuje..."
"Můžete nás kontaktovat na email: info@company.com nebo zavolat na +420 123 456 789"

Buď proaktivní a nabízej další informace!
"""
        return prompt

    def start_conversation(self) -> str:
        """Zahájí konverzaci"""
        greeting = f"""👋 Dobrý den! Jsem asistent společnosti {self.page_content.get('company_name', 'naší firmy')}.

Rád vám pomohu s čímkoliv! Můžete se mě zeptat na:
• 🔧 Naše služby a produkty
• 💰 Ceny a balíčky
• 📞 Kontaktní informace
• ❓ Časté dotazy
• 📋 Konkrétní detaily

Jak vám mohu pomoci?"""

        self.conversation_history.append({
            "role": "assistant",
            "content": greeting
        })

        return greeting

    def chat(self, user_message: str) -> str:
        """Zpracuje zprávu od uživatele"""
        # Přidání zprávy do historie
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Vytvoření promptu
        system_prompt = self.get_system_prompt()

        # Zavolání API
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        assistant_message = response.choices[0].message.content

        # Uložení odpovědi do historie
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        """Resetuje konverzaci"""
        self.conversation_history = []
