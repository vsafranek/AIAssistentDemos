import numpy as np
from docx import Document
import faiss
from typing import List, Tuple, Dict, Optional
from akkodis_clients import client_gpt_4o, client_ada_002


class DocumentProcessor:
    def __init__(self):
        # Načtení embeddings clienta z akkodis_clients
        self.embed_client, self.embed_deployment = client_ada_002()
        self.chunks = []
        self.index = None
        self.embeddings_array = None

    def load_docx(self, file_path: str) -> str:
        """Načte text z DOCX souboru"""
        doc = Document(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text)
        return '\n'.join(full_text)

    def split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Rozdělí text na chunks s překryvem"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Získá embedding pro text pomocí OpenAI API"""
        response = self.embed_client.embeddings.create(
            model=self.embed_deployment,
            input=text
        )
        return response.data[0].embedding

    def create_faiss_index(self, text: str):
        """Vytvoří FAISS index z textu"""
        # Rozdělení textu na chunks
        self.chunks = self.split_text(text)

        # Vytvoření embeddingů pro každý chunk
        embeddings = []
        print(f"Zpracovávám {len(self.chunks)} chunks...")
        for i, chunk in enumerate(self.chunks):
            embedding = self.get_embedding(chunk)
            embeddings.append(embedding)
            if (i + 1) % 10 == 0:
                print(f"Zpracováno {i + 1}/{len(self.chunks)} chunks")

        # Převod na numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        self.embeddings_array = embeddings_array  # Uložení pro vizualizaci

        # Vytvoření FAISS indexu
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)

        print(f"FAISS index vytvořen s {self.index.ntotal} vektory")

    def search_relevant_chunks(self, query: str, k: int = 3) -> Tuple[List[str], List[float]]:
        """Vyhledá k nejrelevantnějších chunks pro dotaz včetně vzdáleností"""
        # Získání embeddingu pro dotaz
        query_embedding = np.array([self.get_embedding(query)]).astype('float32')

        # Vyhledání nejbližších chunks
        distances, indices = self.index.search(query_embedding, k)

        # Vrácení relevantních chunks a jejich vzdáleností
        relevant_chunks = [self.chunks[idx] for idx in indices[0]]
        return relevant_chunks, distances[0].tolist()

    def compare_retrieval_strategies(self, query: str) -> Dict:
        """Porovná různé retrieval strategie"""
        results = {}

        # Strategie 1: Top-K nejpodobnějších
        chunks_topk, dist_topk = self.search_relevant_chunks(query, k=3)
        results["top_k"] = {
            "chunks": chunks_topk,
            "avg_distance": sum(dist_topk) / len(dist_topk),
            "method": "Top-K Nejpodobnější"
        }

        # Strategie 2: Threshold-based
        all_chunks, all_distances = self.search_relevant_chunks(query, k=10)
        threshold = 1.5
        chunks_threshold = [c for c, d in zip(all_chunks, all_distances) if d < threshold]
        results["threshold"] = {
            "chunks": chunks_threshold[:3] if chunks_threshold else chunks_topk[:3],
            "count": len(chunks_threshold),
            "method": "Threshold-Based (d < 1.5)"
        }

        return results
