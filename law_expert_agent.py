# law_expert_agent.py
"""
Právní expert agent s vylepšeným strukturovaným chunkingem.

Verze: 2.3 - Oprava kompatibility s chatbotem pomocí adapteru
"""

import os
import json
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re

# Import existujících modulů
try:
    from parse_law import parse_doc_to_structure
    from seach_law_json import LawJsonCrawler
    from law_chatbot_adapter import LawChatbotAdapter  # ZMĚNA: používáme adapter!
    from chatbot import ContextualChatbot
except ImportError as e:
    print(f"⚠️ Warning: Some modules not found: {e}")


class LawExpertAgent:
    """
    Právní expert agent s inteligentním strukturovaným chunkingem.

    Verze 2.3:
    - Používá LawChatbotAdapter pro kompatibilitu s chatbotem
    - Opraveno: TypeError při volání chatbot.ask()
    """

    def __init__(self):
        self.parsed_json_path: Optional[str] = None
        self.crawler: Optional[LawJsonCrawler] = None
        self.doc_processor: Optional[LawChatbotAdapter] = None  # ZMĚNA: adapter!
        self.chatbot: Optional[ContextualChatbot] = None
        self.law_metadata: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, str]] = []

    def load_law_from_docx(
        self,
        docx_path: str,
        chunk_strategy: str = "mixed",
        max_chunk_size: int = 1500,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Načte zákon z DOCX souboru a provede kompletní inicializaci.

        Args:
            docx_path: Cesta k DOCX souboru
            chunk_strategy: Strategie chunkování ("paragraph", "article_paragraph", "point", "mixed")
            max_chunk_size: Maximální velikost chunku
            include_context: Přidat kontextové záhlaví do chunků
        """
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"Soubor nenalezen: {docx_path}")

        # 1. Parsování struktury pomocí parse_law
        print("📝 Krok 1/4: Parsování struktury zákona...")
        try:
            parsed_structure = parse_doc_to_structure(docx_path)
        except Exception as e:
            raise Exception(f"Chyba při parsování: {str(e)}")

        # Uložení do dočasného JSON
        temp_json = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        )
        json.dump(parsed_structure, temp_json, ensure_ascii=False, indent=2)
        temp_json.close()
        self.parsed_json_path = temp_json.name

        # 2. Inicializace strukturovaného crawleru
        print("🔍 Krok 2/4: Inicializace strukturovaného vyhledávače...")
        try:
            self.crawler = LawJsonCrawler(self.parsed_json_path)
        except Exception as e:
            raise Exception(f"Chyba při inicializaci crawleru: {str(e)}")

        # Extrakce metadat
        paragraph_titles = self.crawler.get_paragraph_titles()

        self.law_metadata = {
            "parts_count": len(parsed_structure.get("parts", [])),
            "laws_list": paragraph_titles,
            "paragraph_titles": paragraph_titles,
            "paragraph_count": len(paragraph_titles),
            "document_path": docx_path,
            "document_name": os.path.basename(docx_path),
            "chunk_strategy": chunk_strategy,
            "max_chunk_size": max_chunk_size
        }

        # 3. Inicializace adapteru (místo přímého processoru)
        print("🧠 Krok 3/4: Vytváření strukturovaných embeddings...")
        try:
            self.doc_processor = LawChatbotAdapter()  # ZMĚNA!
            self.doc_processor.load_from_json(self.parsed_json_path)

            # Vytvoření FAISS indexu se strukturovaným chunkingem
            self.doc_processor.create_faiss_index(
                chunk_strategy=chunk_strategy,
                max_chunk_size=max_chunk_size,
                include_context=include_context
            )

            # Získání statistik o chunkách
            chunk_stats = self.doc_processor.get_chunk_statistics()
            self.law_metadata["chunk_stats"] = chunk_stats

            print(f"  ✅ Vytvořeno {chunk_stats.get('total_chunks', 0)} strukturovaných chunků")
            print(f"  📏 Průměrná délka: {chunk_stats.get('avg_chunk_length', 0):.0f} znaků")

        except Exception as e:
            raise Exception(f"Chyba při vytváření embeddings: {str(e)}")

        # 4. Inicializace chatbota s kontextem
        print("🤖 Krok 4/4: Inicializace chatbota...")
        try:
            self.chatbot = ContextualChatbot(self.doc_processor)  # Adapter funguje jako processor!
        except Exception as e:
            raise Exception(f"Chyba při inicializaci chatbota: {str(e)}")

        print("✅ Dokument úspěšně načten a zpracován!")

        return {
            "status": "success",
            "metadata": self.law_metadata,
            "parsed_json": self.parsed_json_path
        }

    # ========================================================================
    # API PRO PARAGRAFY (zachováno)
    # ========================================================================

    def get_available_paragraphs(self) -> List[str]:
        if not self.crawler:
            return []
        try:
            return self.crawler.get_paragraph_titles()
        except AttributeError:
            return []

    def get_available_laws(self) -> List[str]:
        return self.get_available_paragraphs()

    def get_articles_for_law(self, law_title: str) -> List[str]:
        if not self.crawler:
            return []
        try:
            paras = self.crawler.list_article_paragraphs(article_title=law_title)
            result = []
            for p in paras:
                if p.title:
                    result.append(f"Odstavec {p.title}")
            return result if result else ["Celý paragraf"]
        except Exception:
            return ["Celý paragraf"]

    def get_paragraph_details(self, paragraph_title: str) -> Dict[str, Any]:
        if not self.crawler:
            return {}
        try:
            full_text = self.crawler.get_text(article=paragraph_title)
            article_paragraphs = self.crawler.list_article_paragraphs(article_title=paragraph_title)
            points = self.crawler.list_points(article_title=paragraph_title)
            subpoints = self.crawler.list_subpoints(article_title=paragraph_title)
            return {
                "title": paragraph_title,
                "full_text": full_text,
                "article_paragraphs_count": len(article_paragraphs),
                "points_count": len(points),
                "subpoints_count": len(subpoints),
                "has_structure": len(article_paragraphs) > 0 or len(points) > 0
            }
        except Exception as e:
            return {"error": str(e)}

    def get_paragraph_statistics(self) -> Dict[str, Any]:
        if not self.crawler:
            return {}
        try:
            return self.crawler.get_paragraph_statistics()
        except AttributeError:
            paragraphs = self.get_available_paragraphs()
            return {"total_paragraphs": len(paragraphs), "paragraph_titles": paragraphs}

    def search_by_structure(
        self,
        part_title_query: Optional[str] = None,
        article_label: Optional[str] = None,
        article: Optional[str] = None,
        paragraph: Optional[str] = None,
        point: Optional[str] = None,
        subpoint: Optional[str] = None
    ) -> str:
        if not self.crawler:
            return ""
        if article or paragraph or point or subpoint:
            return self.crawler.get_text(article=article, paragraph=paragraph, point=point, subpoint=subpoint)
        if article_label:
            return self.crawler.get_text(article=article_label)
        if part_title_query:
            return self.crawler.get_text(article=part_title_query)
        return ""

    def find_paragraph_by_number(self, para_number: str) -> Dict[str, Any]:
        para_clean = para_number.strip().replace("§", "").strip()
        para_normalized = f"§ {para_clean}"
        available = self.get_available_paragraphs()
        if para_normalized in available:
            return self.get_paragraph_details(para_normalized)
        for p in available:
            if para_clean in p:
                return self.get_paragraph_details(p)
        return {"error": f"Paragraf {para_normalized} nebyl nalezen"}

    # ========================================================================
    # SÉMANTICKÉ VYHLEDÁVÁNÍ
    # ========================================================================

    def search_by_semantic(
        self,
        query: str,
        top_k: int = 5,
        filter_by_article: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.chatbot:
            return {"answer": "Agent není inicializován", "sources": [], "confidence": 0.0}

        # Pokud je zadán filtr
        if filter_by_article:
            try:
                # Adapter vrací už stringy!
                chunks, distances = self.doc_processor.search_relevant_chunks(
                    query=query,
                    k=top_k,
                    filter_by_article=filter_by_article
                )
                context = "\n\n".join(chunks)  # Teď funguje, protože chunks jsou stringy!
                return {
                    "answer": f"Výsledky pro {filter_by_article}:\n\n{context}",
                    "sources": chunks,
                    "distances": distances
                }
            except Exception as e:
                return {"answer": f"Chyba: {str(e)}", "sources": []}

        # Standardní vyhledávání (adapter vrací stringy automaticky)
        return self.chatbot.ask(query)

    # ========================================================================
    # HYBRIDNÍ PŘÍSTUP
    # ========================================================================

    def ask(self, question: str) -> Dict[str, Any]:
        if not self.crawler or not self.chatbot:
            return {"answer": "❌ Agent není inicializován.", "sources": [], "method": "error"}

        self.conversation_history.append({"role": "user", "content": question})
        query_type = self._classify_query(question)

        if query_type == "list_paragraphs":
            result = self._handle_list_paragraphs()
        elif query_type == "paragraph_ref":
            result = self._handle_paragraph_reference(question)
        elif query_type == "paragraph_stats":
            result = self._handle_paragraph_statistics()
        elif query_type == "chunk_stats":
            result = self._handle_chunk_statistics()
        elif query_type == "structural":
            result = self._handle_structural_query(question)
        else:
            result = self._handle_semantic_query(question)

        self.conversation_history.append({
            "role": "assistant",
            "content": result["answer"],
            "method": result.get("method", "unknown")
        })
        return result

    def _classify_query(self, question: str) -> str:
        q_lower = question.lower()
        if any(kw in q_lower for kw in ["statistiky chunků", "přehled chunků"]):
            return "chunk_stats"
        if any(kw in q_lower for kw in ["seznam paragrafů", "všechny paragrafy", "seznam zákonů"]):
            return "list_paragraphs"
        if any(kw in q_lower for kw in ["statistika", "statistiky paragrafů"]):
            return "paragraph_stats"
        if re.search(r"§\s*\d+", question):
            return "paragraph_ref"
        if any(kw in q_lower for kw in ["odstavec", "bod", "písmeno"]):
            return "structural"
        return "semantic"

    def _handle_chunk_statistics(self) -> Dict[str, Any]:
        if not self.doc_processor:
            return {"answer": "Processor není inicializován", "sources": [], "method": "error"}
        stats = self.doc_processor.get_chunk_statistics()
        answer = "📊 **Statistiky chunkování:**\n\n"
        answer += f"**Celkem chunků:** {stats.get('total_chunks', 0)}\n"
        answer += f"**Průměrná délka:** {stats.get('avg_chunk_length', 0):.0f} znaků\n"
        answer += f"**Min/Max:** {stats.get('min_chunk_length', 0)} / {stats.get('max_chunk_length', 0)}\n\n"
        answer += "**Podle typu:**\n"
        for node_type, count in stats.get('chunks_by_type', {}).items():
            answer += f"- {node_type}: {count}\n"
        return {"answer": answer, "sources": [], "method": "chunk_stats", "stats": stats}

    def _handle_list_paragraphs(self) -> Dict[str, Any]:
        paragraphs = self.get_available_paragraphs()
        if not paragraphs:
            answer = "V dokumentu nebyly nalezeny žádné paragrafy."
        else:
            answer = f"📋 **Seznam paragrafů ({len(paragraphs)} celkem):**\n\n"
            for i in range(0, len(paragraphs), 10):
                chunk = paragraphs[i:i+10]
                answer += ", ".join(chunk)
                if i + 10 < len(paragraphs):
                    answer += "\n"
        return {"answer": answer, "sources": paragraphs, "method": "structural_list", "count": len(paragraphs)}

    def _handle_paragraph_statistics(self) -> Dict[str, Any]:
        stats = self.get_paragraph_statistics()
        answer = "📊 **Statistiky paragrafů:**\n\n"
        answer += f"**Celkem:** {stats.get('total_paragraphs', 0)}\n\n"
        by_article = stats.get('paragraphs_by_article', {})
        if by_article:
            answer += "**Rozložení:**\n"
            for article, count in sorted(by_article.items(), key=lambda x: x[1], reverse=True)[:10]:
                answer += f"- {article}: {count}\n"
        return {"answer": answer, "sources": [], "method": "structural_stats", "stats": stats}

    def _handle_paragraph_reference(self, question: str) -> Dict[str, Any]:
        match = re.search(r"§\s*(\d+[a-z]?)", question, re.IGNORECASE)
        if not match:
            return self._handle_semantic_query(question)
        para_num = match.group(1)
        details = self.find_paragraph_by_number(para_num)
        if "error" in details:
            return {"answer": details["error"], "sources": [], "method": "paragraph_reference"}
        answer = f"📖 **§ {para_num}**\n\n**Struktura:**\n"
        answer += f"- Odstavců: {details.get('article_paragraphs_count', 0)}\n"
        answer += f"- Bodů: {details.get('points_count', 0)}\n\n"
        full_text = details.get('full_text', '')
        if full_text:
            answer += f"**Text:**\n{full_text[:1000]}..." if len(full_text) > 1000 else f"**Text:**\n{full_text}"
        return {"answer": answer, "sources": [full_text] if full_text else [], "method": "paragraph_reference"}

    def _handle_structural_query(self, question: str) -> Dict[str, Any]:
        para_match = re.search(r"§\s*(\d+[a-z]?)", question, re.IGNORECASE)
        article = f"§ {para_match.group(1)}" if para_match else None
        if article:
            text = self.search_by_structure(article=article)
            if text:
                return {"answer": f"📜 **{article}**\n\n{text}", "sources": [text], "method": "structural"}
        return self._handle_semantic_query(question)

    def _handle_semantic_query(self, question: str) -> Dict[str, Any]:
        result = self.search_by_semantic(question, top_k=5)
        result["method"] = "semantic_rag"
        return result

    def get_law_structure_summary(self) -> str:
        if not self.law_metadata:
            return "Dokument nebyl načten."
        paragraphs = self.get_available_paragraphs()
        chunk_stats = self.law_metadata.get("chunk_stats", {})
        summary = f"""
📊 **Přehled struktury**

📄 Dokument: {self.law_metadata.get('document_name', 'N/A')}
📁 Části: {self.law_metadata.get('parts_count', 0)}
📋 Paragrafy: {len(paragraphs)}
🧩 Chunky: {chunk_stats.get('total_chunks', 0)}

**Paragrafy:**
"""
        for i in range(0, min(len(paragraphs), 60), 15):
            chunk = paragraphs[i:i+15]
            summary += ", ".join(chunk) + "\n"
        if len(paragraphs) > 60:
            summary += f"... +{len(paragraphs) - 60}"
        return summary

    def cleanup(self):
        if self.parsed_json_path and os.path.exists(self.parsed_json_path):
            try:
                os.unlink(self.parsed_json_path)
            except Exception:
                pass

    def __del__(self):
        self.cleanup()
