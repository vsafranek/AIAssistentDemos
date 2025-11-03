# law_chatbot_adapter.py
"""
Adapter pro kompatibilitu mezi LawDocumentProcessor a Chatbot.

Problém: LawDocumentProcessor vrací dict chunky, Chatbot očekává string chunky.
Řešení: Wrapper, který poskytuje kompatibilní API.
"""

from typing import List, Tuple
from law_document_processor import LawDocumentProcessor


class LawChatbotAdapter:
    """
    Adapter, který obaluje LawDocumentProcessor a poskytuje API kompatibilní s Chatbot.

    Konverze:
    - dict chunks -> string chunks pro chatbot
    - Zachování všech funkcí z LawDocumentProcessor
    """

    def __init__(self):
        self.processor = LawDocumentProcessor()

    # Delegace všech metod na původní processor
    def load_from_json(self, json_path: str) -> None:
        return self.processor.load_from_json(json_path)

    def create_structured_chunks(self, *args, **kwargs):
        return self.processor.create_structured_chunks(*args, **kwargs)

    def get_embedding(self, text: str):
        return self.processor.get_embedding(text)

    def create_faiss_index(self, *args, **kwargs):
        return self.processor.create_faiss_index(*args, **kwargs)

    def get_chunk_statistics(self):
        return self.processor.get_chunk_statistics()

    def export_chunks(self, output_path: str):
        return self.processor.export_chunks(output_path)

    # Vlastnosti pro zpětnou kompatibilitu
    @property
    def chunks(self):
        return self.processor.chunks

    @property
    def index(self):
        return self.processor.index

    @property
    def embeddings_array(self):
        return self.processor.embeddings_array

    @property
    def crawler(self):
        return self.processor.crawler

    # KLÍČOVÁ METODA: Wrapper pro search_relevant_chunks
    def search_relevant_chunks(
        self,
        query: str,
        k: int = 5,
        filter_by_article: str = None
    ) -> Tuple[List[str], List[float]]:
        """
        Wrapper, který vrací string chunky místo dict chunků.

        Returns:
            (List[str], List[float]): Tuple stringových chunků a vzdáleností
        """
        # Získání dict chunků z processoru
        dict_chunks, distances = self.processor.search_relevant_chunks(
            query=query,
            k=k,
            filter_by_article=filter_by_article
        )

        # Konverze dict -> string
        string_chunks = []
        for chunk_dict in dict_chunks:
            # Použijeme "text" klíč, který obsahuje plný text s kontextem
            text = chunk_dict.get("text", "")
            string_chunks.append(text)

        return string_chunks, distances
