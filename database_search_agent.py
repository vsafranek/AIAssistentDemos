from typing import Dict, List, Optional
from akkodis_clients import client_gpt_4o
from people_database import PeopleDatabase
import json
import re


class DatabaseSearchAgent:
    """AI agent pro konverzační vyhledávání v databázi osob s chytrým parsováním"""

    def __init__(self):
        self.client, self.deployment = client_gpt_4o()
        self.database = PeopleDatabase()
        self.conversation_history: List[Dict[str, str]] = []
        self.last_results = []

    def get_system_prompt(self) -> str:
        """Vytvoří system prompt pro search agenta"""
        stats = self.database.get_statistics()

        prompt = f"""Jsi AI asistent pro vyhledávání v databázi zaměstnanců. Umíš interpretovat přirozené dotazy a najít správnou osobu.

DATABÁZE OBSAHUJE:
- Celkem osob: {stats['total_people']}
- Aktivních zaměstnanců: {stats['active_employees']}
- Oddělení: {', '.join(stats['departments'].keys())}
- Lokace: {', '.join(stats['locations'].keys())}

DOSTUPNÉ VYHLEDÁVACÍ FUNKCE:
1. search_by_name|jméno - hledání podle jména/příjmení
2. filter_by_department|oddělení - filtrování podle oddělení
3. filter_by_position|pozice - filtrování podle pozice
4. filter_by_location|město - filtrování podle města
5. filter_by_skill|skill - hledání podle dovedností
6. get_person_by_id|ID - získání detailu osoby podle ID
7. smart_search|parametry - chytrý search s více filtry
8. list_all - výpis všech osob
9. statistics - statistiky databáze

NOVÁ FUNKCE: smart_search
Použij když uživatel kombinuje více kritérií:
[FUNCTION]smart_search|name:Horák,location:Liberec[/FUNCTION]
[FUNCTION]smart_search|name:Novák,position:architect[/FUNCTION]
[FUNCTION]smart_search|name:Jan,department:IT,location:Praha[/FUNCTION]

Možné parametry:
- name: jméno nebo příjmení
- location: město
- position: pozice (nebo její část)
- department: oddělení
- skill: konkrétní dovednost

PRAVIDLA PRO INTERPRETACI DOTAZŮ:
- "pan Horák z Liberce" → smart_search|name:Horák,location:Liberec
- "architekt Novák" → smart_search|name:Novák,position:architect
- "developeři v Praze" → smart_search|position:developer,location:Praha
- "Jan z IT" → smart_search|name:Jan,department:IT
- "kdo umí Python v Brně" → smart_search|skill:Python,location:Brno

FORMÁT VOLÁNÍ FUNKCE:
[FUNCTION]název_funkce|parametr[/FUNCTION]

DŮLEŽITÉ - PREZENTACE VÝSLEDKŮ:
Po zavolání funkce VŽDY zobraz výsledky přímo v odpovědi ve strukturovaném formátu.
NEČEKEJ, že uživatel bude scrollovat do sidebaru!

Pro 1 osobu:
"Našel jsem:

👤 **Jan Novák**
📧 jan.novak@company.com
📞 +420 123 456 789
💼 Senior Developer
🏢 IT | 📍 Praha
💰 85,000 Kč | 🎯 32 let

Chcete zobrazit detail nebo hledat něco dalšího?"

Pro více osob (max 5):
"Našel jsem 3 osoby:

1. **Jan Novák** - Senior Developer | IT | Praha
2. **Petr Novák** - Data Analyst | Marketing | Brno
3. **Pavel Novák** - Team Lead | Engineering | Ostrava

Pro detail konkrétní osoby zadejte např: 'Ukaž detail Jana Nováka'"

Odpovídej česky a buď přátelský!
"""
        return prompt

    def start_conversation(self) -> Dict:
        """Zahájí konverzaci"""
        initial_message = """👋 Dobrý den! Jsem váš asistent pro vyhledávání v databázi zaměstnanců.

Můžete se ptát přirozeně, například:
- 🔍 "Najdi pana Horáka z Liberce"
- 💼 "Kdo je architekt v Praze?"
- 🎯 "Ukaž mi developery co umí Python"
- 📍 "Kdo pracuje v IT v Brně?"
- 👤 "Najdi Jana Nováka"

Co vás zajímá?"""

        self.conversation_history.append({
            "role": "assistant",
            "content": initial_message
        })

        return {
            "message": initial_message,
            "results": None,
            "function_called": None
        }

    def chat(self, user_message: str) -> Dict:
        """Zpracuje zprávu od uživatele a provede vyhledávání"""
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
            temperature=0.3,
            max_tokens=1000
        )

        assistant_message = response.choices[0].message.content

        # Zpracování funkcí
        results, function_called = self._process_functions(assistant_message)

        # Odstranění function tagů z zobrazované zprávy
        display_message = re.sub(r'\[FUNCTION\].*?\[/FUNCTION\]', '', assistant_message).strip()

        # Pokud agent nezobrazil výsledky sám, přidáme je my
        if results is not None and not self._has_formatted_results(display_message):
            display_message = self._format_results_inline(display_message, results, function_called)

        # Uložení odpovědi do historie
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return {
            "message": display_message,
            "results": results,
            "function_called": function_called
        }

    def _has_formatted_results(self, message: str) -> bool:
        """Zkontroluje, zda zpráva už obsahuje naformátované výsledky"""
        # Hledáme indikátory že agent už výsledky zobrazil
        indicators = ["👤", "📧", "📞", "💼", "**"]
        return any(indicator in message for indicator in indicators)

    def _format_results_inline(self, message: str, results, function_called: str) -> str:
        """Naformátuje výsledky přímo do odpovědi"""

        if function_called == "statistics":
            stats = results
            formatted = f"""\n\n📊 **Statistiky databáze:**

📈 **Celkem:** {stats['total_people']} osob
✅ **Aktivních:** {stats['active_employees']}
💰 **Průměrný plat:** {stats['average_salary']:,} Kč
🎯 **Průměrný věk:** {stats['average_age']} let

🏢 **Oddělení:**
"""
            for dept, count in list(stats['departments'].items())[:5]:
                formatted += f"  • {dept}: {count}\n"

            return message + formatted

        if isinstance(results, list):
            if len(results) == 0:
                return f"{message}\n\n❌ Nebyly nalezeny žádné výsledky."

            # Formátování 1 osoby - plný detail
            if len(results) == 1:
                person = results[0]
                formatted = f"""\n\nNašel jsem:

👤 **{person['full_name']}**
📧 {person['email']}
📞 {person['phone']}
💼 {person['position']}
🏢 {person['department']} | 📍 {person['location']}
💰 {person['salary']:,} Kč | 🎯 {person['age']} let
📅 Nastoupil: {person['hire_date']}

🛠️ **Dovednosti:** {', '.join(person['skills'][:5])}

Chcete zobrazit někoho dalšího nebo hledat něco jiného?"""

                return message + formatted

            # Formátování více osob - kompaktní seznam
            elif len(results) <= 5:
                formatted = f"\n\nNašel jsem {len(results)} osob:\n\n"

                for i, person in enumerate(results, 1):
                    formatted += f"{i}. **{person['full_name']}** - {person['position']} | {person['department']} | {person['location']}\n"

                formatted += "\nPro detail konkrétní osoby zadejte např: 'Ukaž detail [jméno]'"

                return message + formatted

            # Více než 5 osob
            else:
                formatted = f"\n\nNašel jsem {len(results)} osob. Tady je prvních 5:\n\n"

                for i, person in enumerate(results[:5], 1):
                    formatted += f"{i}. **{person['full_name']}** - {person['position']} | {person['department']} | {person['location']}\n"

                formatted += f"\n... a dalších {len(results) - 5} osob.\n"
                formatted += "\nZkuste zúžit hledání (např. přidat město nebo oddělení)"

                return message + formatted

        return message

    def _process_functions(self, message: str) -> tuple:
        """Zpracuje volání funkcí v odpovědi"""
        pattern = r'\[FUNCTION\](.*?)\|(.*?)\[/FUNCTION\]'
        matches = re.findall(pattern, message, re.IGNORECASE)

        if not matches:
            return None, None

        # Zpracujeme první funkci
        function_name, parameter = matches[0]
        function_name = function_name.strip()
        parameter = parameter.strip()

        results = None

        if function_name == "search_by_name":
            results = self.database.search_by_name(parameter)

        elif function_name == "filter_by_department":
            results = self.database.filter_by_department(parameter)

        elif function_name == "filter_by_position":
            results = self.database.filter_by_position(parameter)

        elif function_name == "filter_by_location":
            results = self.database.filter_by_location(parameter)

        elif function_name == "filter_by_skill":
            results = self.database.filter_by_skill(parameter)

        elif function_name == "get_person_by_id":
            try:
                person_id = int(parameter)
                person = self.database.get_person_by_id(person_id)
                results = [person] if person else []
            except:
                results = []

        elif function_name == "smart_search":
            results = self._smart_search(parameter)

        elif function_name == "list_all":
            results = self.database.get_all_people()

        elif function_name == "statistics":
            results = self.database.get_statistics()

        self.last_results = results
        return results, function_name

    def _smart_search(self, parameters: str) -> List[Dict]:
        """Chytrý search s více filtry"""
        # Parse parametrů: "name:Horák,location:Liberec"
        filters = {}
        for param in parameters.split(','):
            if ':' in param:
                key, value = param.split(':', 1)
                filters[key.strip().lower()] = value.strip()

        # Začneme se všemi lidmi
        results = self.database.get_all_people()

        # Postupně aplikujeme filtry
        if 'name' in filters:
            name_filter = filters['name'].lower()
            results = [p for p in results if
                      name_filter in p['first_name'].lower() or
                      name_filter in p['last_name'].lower() or
                      name_filter in p['full_name'].lower()]

        if 'location' in filters:
            location_filter = filters['location'].lower()
            results = [p for p in results if
                      location_filter in p['location'].lower()]

        if 'position' in filters:
            position_filter = filters['position'].lower()
            results = [p for p in results if
                      position_filter in p['position'].lower()]

        if 'department' in filters:
            dept_filter = filters['department'].lower()
            results = [p for p in results if
                      dept_filter in p['department'].lower()]

        if 'skill' in filters:
            skill_filter = filters['skill'].lower()
            results = [p for p in results if
                      any(skill_filter in s.lower() for s in p['skills'])]

        return results

    def get_last_results(self):
        """Vrátí poslední výsledky vyhledávání"""
        return self.last_results

    def reset(self):
        """Resetuje agenta"""
        self.conversation_history = []
        self.last_results = []
