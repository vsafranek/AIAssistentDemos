from typing import Dict, List, Optional
from akkodis_clients import client_gpt_4o
import json
import re


class InformationCollectorAgent:
    """Aktivní konverzační agent pro sběr informací"""

    def __init__(self, required_fields: Dict[str, str]):
        """
        Args:
            required_fields: Dictionary s poli, které agent má získat
                           {"pole_nazev": "Popis pole pro agenta"}
        """
        self.client, self.deployment = client_gpt_4o()
        self.required_fields = required_fields
        self.collected_data: Dict[str, Optional[str]] = {field: None for field in required_fields.keys()}
        self.conversation_history: List[Dict[str, str]] = []
        self.conversation_started = False

    def get_system_prompt(self) -> str:
        """Vytvoří system prompt pro aktivního agenta"""
        missing_fields = [field for field, value in self.collected_data.items() if value is None]
        completed_fields = [field for field, value in self.collected_data.items() if value is not None]

        prompt = f"""Jsi proaktivní a přátelský AI asistent, který vede konverzaci a postupně získává tyto informace od uživatele:

POŽADOVANÁ POLE A JEJICH VÝZNAM:
"""
        for field, description in self.required_fields.items():
            status = "✓ ZÍSKÁNO" if self.collected_data[field] else "☐ POTŘEBUJI"
            current_value = f" (aktuální hodnota: {self.collected_data[field]})" if self.collected_data[field] else ""
            prompt += f"- {field}: {description} [{status}]{current_value}\n"

        prompt += f"""

TVOJE ÚKOLY:
1. Buď aktivní - sám veď konverzaci směrem k získání všech potřebných informací
2. Pokud uživatel poskytne informaci, okamžitě ji extrahuj a potvrď
3. Pokud uživatel odpoví stručně nebo neúplně, aktivně se doptej na další pole
4. Reaguj přirozeně na odpovědi, ale vždy se posouvej k dalším chybějícím polím
5. Když získáš novou informaci, ihned se zeptej na další chybějící pole
6. Buď příjemný, ale efektivní - netlač, ale veď konverzaci
7. Na začátku konverzace se představ a řekni, co potřebuješ získat

AKTUÁLNÍ STAV:
Počet získaných polí: {len(completed_fields)}/{len(self.required_fields)}
Získaná pole: {', '.join(completed_fields) if completed_fields else 'žádná'}
Chybějící pole: {', '.join(missing_fields) if missing_fields else 'žádná'}

PRAVIDLO EXTRAKCE:
Když získáš informaci, VŽDY ji označ takto:
[EXTRACT]nazev_pole: hodnota[/EXTRACT]

Můžeš extrahovat více polí najednou, pokud uživatel poskytne více informací.

PŘÍKLAD KONVERZACE:
Uživatel: "Ahoj"
Ty: "Dobrý den! Pomohu vám vyplnit zákaznickou kartu. Začněme prosím - jak se jmenujete?"

Uživatel: "Jan Novák"
Ty: "[EXTRACT]jmeno: Jan Novák[/EXTRACT] Skvělé, děkuji pane Nováku! Můžete mi prosím poskytnout váš email?"

TVOJE STRATEGIE:
{'- Představ se a vysvětli, co potřebuješ' if not self.conversation_started else ''}
{'- Pokračuj v získávání: ' + missing_fields[0] if missing_fields else '- Máš všechny informace, shrň je a potvrď'}
"""

        return prompt

    def start_conversation(self) -> Dict:
        """Zahájí konverzaci - agent se sám představí"""
        self.conversation_started = True

        system_prompt = self.get_system_prompt()

        # Agent začíná konverzaci
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Ahoj"}
        ]

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        assistant_message = response.choices[0].message.content

        # Extrakce dat (kdyby náhodou)
        extracted = self._extract_data(assistant_message)

        # Uložení do historie
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return {
            "message": assistant_message,
            "extracted_fields": extracted,
            "progress": self.get_progress(),
            "is_complete": self.is_complete()
        }

    def chat(self, user_message: str) -> Dict:
        """Zpracuje zprávu od uživatele a aktivně získává další informace"""
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

        # Extrakce dat z odpovědi
        extracted = self._extract_data(assistant_message)

        # Odstranění extract tagů z zobrazované zprávy
        display_message = re.sub(r'\[EXTRACT\].*?\[/EXTRACT\]', '', assistant_message).strip()
        display_message = re.sub(r'\s+', ' ', display_message).strip()

        # Uložení odpovědi do historie (s tagy pro kontext)
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return {
            "message": display_message,
            "extracted_fields": extracted,
            "progress": self.get_progress(),
            "is_complete": self.is_complete()
        }

    def _extract_data(self, message: str) -> Dict[str, str]:
        """Extrahuje data z odpovědi agenta"""
        extracted = {}

        # Hledání [EXTRACT]pole: hodnota[/EXTRACT] tagů
        pattern = r'\[EXTRACT\](.*?):\s*(.*?)\[/EXTRACT\]'
        matches = re.findall(pattern, message, re.DOTALL | re.IGNORECASE)

        for field, value in matches:
            field = field.strip()
            value = value.strip()
            if field in self.required_fields:
                self.collected_data[field] = value
                extracted[field] = value

        return extracted

    def get_progress(self) -> Dict:
        """Vrací progress sběru dat"""
        total = len(self.required_fields)
        collected = sum(1 for v in self.collected_data.values() if v is not None)

        return {
            "total": total,
            "collected": collected,
            "percentage": int((collected / total) * 100) if total > 0 else 0,
            "remaining": total - collected
        }

    def is_complete(self) -> bool:
        """Zkontroluje, zda jsou všechna data sebrána"""
        return all(value is not None for value in self.collected_data.values())

    def get_collected_data(self) -> Dict[str, Optional[str]]:
        """Vrátí sebraná data"""
        return self.collected_data.copy()

    def get_missing_fields(self) -> List[str]:
        """Vrátí seznam chybějících polí"""
        return [field for field, value in self.collected_data.items() if value is None]

    def reset(self):
        """Resetuje agenta"""
        self.collected_data = {field: None for field in self.required_fields.keys()}
        self.conversation_history = []
        self.conversation_started = False
