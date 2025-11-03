from typing import List, Dict, Optional
from akkodis_clients import client_gpt_4o
from document_processor import DocumentProcessor
import time


class ContextualChatbot:
    def __init__(self, doc_processor: DocumentProcessor):
        # Načtení GPT clienta z akkodis_clients
        self.client, self.deployment = client_gpt_4o()
        self.doc_processor = doc_processor
        self.conversation_history: List[Dict[str, str]] = []

    def ask(self, question: str) -> dict:
        """Položí otázku s kontextem z dokumentu a historie konverzace"""
        start_time = time.time()

        # Vyhledání relevantních chunks z dokumentu
        relevant_chunks, distances = self.doc_processor.search_relevant_chunks(question, k=3)
        context = "\n\n".join(relevant_chunks)

        # Příprava system promptu s kontextem dokumentu
        system_message = {
    "role": "system",
    "content": f"""Jsi specializovaný AI asistent pro právní dokumentaci. Tvým úkolem je poskytovat přesné odpovědi na otázky týkající se zákonů na základě poskytnutého kontextu.

## Kontext z právního dokumentu:
{context}

## Instrukce pro odpovědi:

### Přesnost a relevance:
- Odpovídej VÝHRADNĚ na základě poskytnutého kontextu
- Cituj konkrétní paragrafy, články nebo sekce, pokud je to relevantní
- Pokud informace v kontextu NENÍ, explicitně to uveď: "Tato informace není obsažena v poskytnutém dokumentu."
- Nikdy nededukuj ani nedoplňuj informace, které v kontextu nejsou

### Struktura odpovědi:
- Začni stručnou přímou odpovědí na položenou otázku
- Následuj s relevantními detaily z dokumentu
- Při odkazování na konkrétní ustanovení použij formát: "Podle §X/Článku X..."

### Srozumitelnost:
- Vysvětluj právní termíny jednoduchým jazykem
- Používej českou právní terminologii korektně
- Strukturuj delší odpovědi pomocí odrážek nebo číslování

### Omezení:
- Neposkytuj právní rady - pouze informace z dokumentu
- Neinterpretuj zákon mimo rámec poskytnutého kontextu
- Při nejasnostech raději přiznej nedostatek informací než spekuluj"""
}

        # Přidání aktuální otázky do historie
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        # Sestavení zpráv pro API (system + historie konverzace)
        messages = [system_message] + self.conversation_history

        # Zavolání GPT API
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )

        # Získání odpovědi
        answer = response.choices[0].message.content

        # Uložení odpovědi do historie
        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        # Výpočet confidence a response time
        confidence = self._calculate_confidence(relevant_chunks, distances)
        response_time = time.time() - start_time

        return {
            "answer": answer,
            "sources": relevant_chunks,
            "confidence": confidence,
            "distances": distances,
            "response_time": response_time
        }

    def ask_streaming(self, question: str):
        """Streamovaná odpověď pro real-time efekt"""
        relevant_chunks, distances = self.doc_processor.search_relevant_chunks(question, k=3)
        context = "\n\n".join(relevant_chunks)

        system_message = {
            "role": "system",
            "content": f"""Jsi pokročilý AI asistent.

Kontext z dokumentu:
{context}

Odpovídej pouze na základě kontextu."""
        }

        self.conversation_history.append({"role": "user", "content": question})
        messages = [system_message] + self.conversation_history

        # Streaming response
        stream = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            stream=True
        )

        full_answer = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_answer += content
                yield content

        # Uložení celé odpovědi do historie
        self.conversation_history.append({"role": "assistant", "content": full_answer})

        # Vrácení metadat jako poslední yield
        confidence = self._calculate_confidence(relevant_chunks, distances)
        yield {
            "metadata": True,
            "sources": relevant_chunks,
            "confidence": confidence,
            "distances": distances
        }

    def _calculate_confidence(self, chunks: List[str], distances: List[float]) -> str:
        """Vypočítá confidence scoring na základě kvality retrievalu"""
        avg_distance = sum(distances) / len(distances)
        total_length = sum(len(chunk) for chunk in chunks)

        if avg_distance < 0.5 and total_length > 2000:
            return "Vysoká"
        elif avg_distance < 1.0 and total_length > 1000:
            return "Střední"
        else:
            return "Nízká"

    def classify_query_type(self, question: str) -> str:
        """Klasifikuje typ dotazu pro multi-agent routing"""
        classification_prompt = f"""Klasifikuj tento dotaz do jedné z kategorií:
- summary: shrnutí, přehled, celkový obsah
- analysis: analýza, porovnání, vyhodnocení
- extraction: hledání konkrétních dat, čísel, jmen
- explanation: vysvětlení konceptů, jak/proč otázky

Dotaz: {question}
Odpověz pouze názvem kategorie."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.3,
            max_tokens=20
        )

        return response.choices[0].message.content.strip().lower()

    def ask_with_agent_routing(self, question: str) -> dict:
        """Položí otázku s inteligentním multi-agent routingem"""
        query_type = self.classify_query_type(question)

        # Vylepšení otázky podle typu
        enhanced_prompts = {
            "summary": f"Jako expert na sumarizaci: {question}\nPoskytni strukturované shrnutí s klíčovými body.",
            "analysis": f"Jako analytik: {question}\nProveď hloubkovou analýzu s argumenty a závěry.",
            "extraction": f"Jako data specialista: {question}\nNajdi a vypiš všechny relevantní konkrétní údaje.",
            "explanation": f"Jako učitel: {question}\nVysvětli jednoduše a srozumitelně s příklady."
        }

        enhanced_question = enhanced_prompts.get(query_type, question)
        result = self.ask(enhanced_question)
        result["agent_type"] = query_type

        return result

    def compare_with_without_context(self, question: str) -> dict:
        """Demo funkce: porovnání odpovědi s kontextem a bez"""
        # Odpověď BEZ kontextu z dokumentu
        messages_no_context = [
            {"role": "system", "content": "Jsi AI asistent. Odpověz na otázku."},
            {"role": "user", "content": question}
        ]

        response_no_context = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages_no_context,
            temperature=0.7,
            max_tokens=500
        )

        # Odpověď S kontextem (normální funkce)
        response_with_context = self.ask(question)

        return {
            "without_context": response_no_context.choices[0].message.content,
            "with_context": response_with_context["answer"],
            "sources": response_with_context["sources"],
            "confidence": response_with_context["confidence"]
        }

    def clear_history(self):
        """Vymaže historii konverzace"""
        self.conversation_history = []
