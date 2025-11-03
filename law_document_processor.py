# law_document_processor.py
"""
Strukturovaný document processor pro právní dokumenty.

Využívá LawJsonCrawler pro vytvoření sémanticky konzistentních chunků
místo jednoduchého dělení po X znacích.

Verze: 1.0 - Strukturovaný chunking podle paragrafů, odstavců a bodů
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
import faiss
import json
from pathlib import Path

from akkodis_clients import client_gpt_4o, client_ada_002
from seach_law_json import LawJsonCrawler, NodePath


class LawDocumentProcessor:
    """
    Processor pro právní dokumenty s inteligentním chunkingem.

    Výhody oproti standardnímu DocumentProcessor:
    - ✅ Chunky respektují strukturu zákona (§, odstavce, body)
    - ✅ Každý chunk má metadata (paragraf, odstavec, cesta)
    - ✅ Žádné rozřezávání uprostřed věty/paragrafu
    - ✅ Kontextové informace pro lepší vyhledávání
    """

    def __init__(self):
        # Načtení embeddings clienta
        self.embed_client, self.embed_deployment = client_ada_002()
        self.chunks: List[Dict[str, any]] = []  # Strukturované chunky s metadaty
        self.index: Optional[faiss.Index] = None
        self.embeddings_array: Optional[np.ndarray] = None
        self.crawler: Optional[LawJsonCrawler] = None

    def load_from_json(self, json_path: str) -> None:
        """
        Načte strukturu zákona z JSON (výstup parse_law).

        Args:
            json_path: Cesta k JSON souboru s parsovaným zákonem
        """
        self.crawler = LawJsonCrawler(json_path)
        print(f"📝 Načten zákon z: {json_path}")

    def create_structured_chunks(
        self,
        chunk_strategy: str = "paragraph",
        max_chunk_size: int = 2000,
        include_context: bool = True
    ) -> List[Dict[str, any]]:
        """
        Vytvoří strukturované chunky podle strategie.

        Args:
            chunk_strategy:
                - "paragraph": jeden chunk = jeden paragraf (§)
                - "article_paragraph": jeden chunk = jeden odstavec
                - "point": jeden chunk = jeden bod
                - "mixed": adaptivní podle délky textu
            max_chunk_size: maximální délka chunku v znacích
            include_context: přidat kontextové informace do chunku

        Returns:
            List strukturovaných chunků s metadaty
        """
        if not self.crawler:
            raise ValueError("Nejprve načtěte JSON pomocí load_from_json()")

        chunks = []

        for node_dict, node_path in self.crawler._collect_nodes():
            # Filtrování podle strategie
            if chunk_strategy == "paragraph" and node_path.node_type != "article":
                continue
            elif chunk_strategy == "article_paragraph" and node_path.node_type != "article_paragraph":
                continue
            elif chunk_strategy == "point" and node_path.node_type not in ["point", "article_paragraph"]:
                continue

            # Extrakce textu
            text = node_path.text
            if not text or len(text.strip()) < 10:  # Ignoruj prázdné/krátké
                continue

            # Vytvoření kontextového záhlaví
            context_header = ""
            if include_context:
                context_parts = []
                if node_path.part_title:
                    context_parts.append(f"Část: {node_path.part_title}")
                if node_path.article_title:
                    context_parts.append(node_path.article_title)
                if node_path.chain_titles:
                    context_parts.extend(node_path.chain_titles)

                if context_parts:
                    context_header = " > ".join(context_parts) + "\n\n"

            # Rozdělení dlouhých chunků (zachování struktury)
            full_text = context_header + text

            if len(full_text) <= max_chunk_size:
                # Vejde se do jednoho chunku
                chunks.append({
                    "text": full_text,
                    "raw_text": text,
                    "article_title": node_path.article_title,
                    "part_title": node_path.part_title,
                    "node_type": node_path.node_type,
                    "human_path": node_path.human_path(),
                    "chain_titles": node_path.chain_titles,
                    "title": node_path.title
                })
            else:
                # Rozdělení na věty (zachování sémantiky)
                sentences = self._split_into_sentences(text)
                current_chunk = context_header

                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_chunk_size:
                        current_chunk += sentence + " "
                    else:
                        # Uložení aktuálního chunku
                        if len(current_chunk.strip()) > len(context_header):
                            chunks.append({
                                "text": current_chunk.strip(),
                                "raw_text": current_chunk.replace(context_header, "").strip(),
                                "article_title": node_path.article_title,
                                "part_title": node_path.part_title,
                                "node_type": node_path.node_type,
                                "human_path": node_path.human_path(),
                                "chain_titles": node_path.chain_titles,
                                "title": node_path.title
                            })

                        # Začátek nového chunku s kontextem
                        current_chunk = context_header + sentence + " "

                # Uložení posledního chunku
                if len(current_chunk.strip()) > len(context_header):
                    chunks.append({
                        "text": current_chunk.strip(),
                        "raw_text": current_chunk.replace(context_header, "").strip(),
                        "article_title": node_path.article_title,
                        "part_title": node_path.part_title,
                        "node_type": node_path.node_type,
                        "human_path": node_path.human_path(),
                        "chain_titles": node_path.chain_titles,
                        "title": node_path.title
                    })

        self.chunks = chunks
        print(f"✅ Vytvořeno {len(chunks)} strukturovaných chunků")
        return chunks

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Rozdělí text na věty (jednoduchá heuristika)."""
        import re
        # Rozdělení na věty (zachování teček v číslech, zkratkách)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZČŘŠŽÝÁÍÉÚŮ])', text)
        return [s.strip() for s in sentences if s.strip()]

    def get_embedding(self, text: str) -> np.ndarray:
        """Získá embedding pro text pomocí Azure OpenAI."""
        try:
            response = self.embed_client.embeddings.create(
                input=text,
                model=self.embed_deployment
            )
            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            print(f"⚠️ Chyba při vytváření embeddingu: {e}")
            # Fallback: náhodný vektor
            return np.random.randn(1536).astype(np.float32)

    def create_faiss_index(
        self,
        chunk_strategy: str = "mixed",
        max_chunk_size: int = 1500,
        include_context: bool = True
    ) -> None:
        """
        Vytvoří FAISS index ze strukturovaných chunků.

        Args:
            chunk_strategy: strategie chunkování
            max_chunk_size: max. velikost chunku
            include_context: zahrnout kontextové informace
        """
        # Vytvoření strukturovaných chunků
        if not self.chunks:
            self.create_structured_chunks(
                chunk_strategy=chunk_strategy,
                max_chunk_size=max_chunk_size,
                include_context=include_context
            )

        print("🧠 Vytváření embeddings...")
        embeddings = []

        for i, chunk in enumerate(self.chunks):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(self.chunks)}")

            embedding = self.get_embedding(chunk["text"])
            embeddings.append(embedding)

        # Vytvoření FAISS indexu
        self.embeddings_array = np.array(embeddings, dtype=np.float32)
        dimension = self.embeddings_array.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings_array)

        print(f"✅ FAISS index vytvořen: {len(self.chunks)} chunků, dimenze {dimension}")

    def search_relevant_chunks(
        self,
        query: str,
        k: int = 5,
        filter_by_article: Optional[str] = None
    ) -> Tuple[List[Dict[str, any]], List[float]]:
        """
        Vyhledá nejrelevantnější chunky pro dotaz.

        Args:
            query: vyhledávací dotaz
            k: počet výsledků
            filter_by_article: filtrovat pouze chunky z daného paragrafu (např. "§ 11")

        Returns:
            (seznam chunků s metadaty, vzdálenosti)
        """
        if self.index is None:
            raise ValueError("FAISS index není inicializován. Zavolejte create_faiss_index().")

        # Získání embeddingu pro dotaz
        query_embedding = self.get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)

        # Vyhledání v FAISS
        distances, indices = self.index.search(query_embedding, min(k * 3, len(self.chunks)))

        # Aplikace filtru
        results = []
        result_distances = []

        for distance, idx in zip(distances[0], indices[0]):
            if idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]

            # Filtrování podle článku
            if filter_by_article:
                if chunk.get("article_title") != filter_by_article:
                    continue

            results.append(chunk)
            result_distances.append(float(distance))

            if len(results) >= k:
                break

        return results, result_distances

    def get_chunk_statistics(self) -> Dict[str, any]:
        """Vrátí statistiky o chunkách."""
        if not self.chunks:
            return {}

        stats = {
            "total_chunks": len(self.chunks),
            "chunks_by_type": {},
            "chunks_by_article": {},
            "avg_chunk_length": 0,
            "min_chunk_length": float('inf'),
            "max_chunk_length": 0
        }

        total_length = 0

        for chunk in self.chunks:
            # Podle typu
            node_type = chunk.get("node_type", "unknown")
            stats["chunks_by_type"][node_type] = stats["chunks_by_type"].get(node_type, 0) + 1

            # Podle článku
            article = chunk.get("article_title", "N/A")
            stats["chunks_by_article"][article] = stats["chunks_by_article"].get(article, 0) + 1

            # Délka
            length = len(chunk.get("text", ""))
            total_length += length
            stats["min_chunk_length"] = min(stats["min_chunk_length"], length)
            stats["max_chunk_length"] = max(stats["max_chunk_length"], length)

        stats["avg_chunk_length"] = total_length / len(self.chunks) if self.chunks else 0

        return stats

    def export_chunks(self, output_path: str) -> None:
        """Exportuje chunky do JSON pro analýzu."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"📥 Chunky exportovány do: {output_path}")


# Backward compatibility: alias pro původní použití
DocumentProcessor = LawDocumentProcessor
