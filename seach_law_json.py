# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


@dataclass
class NodePath:
    part_title: Optional[str]
    article_title: Optional[str]      # číslo/paragraf článku (např. "§ 11")
    chain_titles: List[str]           # např. ["point a", "subpoint 1"]
    node_type: str                    # "article" | "article_paragraph" | "paragraph" | "point" | "subpoint"
    title: Optional[str]              # u article_paragraph číslo "1", u point písmeno "a", u subpoint číslo "1"
    text: Optional[str]               # extrahovaný text obsahu

    def human_path(self) -> str:
        parts = []
        if self.part_title:
            parts.append(f"Část: {self.part_title}")
        if self.article_title:
            parts.append(f"Článek: {self.article_title}")
        for t in self.chain_titles:
            parts.append(t)
        return " > ".join(parts)


class LawJsonCrawler:
    """
    Čisté programové API bez CLI.

    Podporované varianty článku:
      A) Článek s odstavci a (sub)body:
         - article -> children: article_paragraph (číslo odstavce), point (písmeno), subpoint (číslo) dle vnoření,
         - article_paragraph -> children: paragraph (text odstavce), point (písmeno),
         - point -> children: paragraph (text bodu), subpoint,
         - subpoint -> children: paragraph (text sub-bodu).
      B) Článek bez odstavců (úvodní paragraph a hned body):
         - article -> children: paragraph (úvod) a buď point/subpoint nebo paragraph s prefixy "a)", "1.", atd.

    Identifikace článku:
      - primárně meta.article_number (např. "§ 11"), fallback title/meta.raw_text.

    Výpis get_text:
      - pořadí: článek -> odstavec -> body -> sub-body,
      - prefixy normalizovány na variantu s tabulátorem:
         odstavec: "(n)\t"
         bod:      "a)\t"
         sub-bod:  "1.\t"
      - zachování obsahu (bez přebytečného strip), bezpečné odstranění původních prefixů z textu, aby nevzniklo zdvojení.
    """

    # Detekce různých prefixů na začátku textu
    _PARA_SIGN_RE = re.compile(r"^\s*§\s*([0-9]+)\s*([a-zA-Z]?)\s*$")
    _POINT_PREFIX_RE = re.compile(r"^\s*([A-Za-z])\)\s+")    # "a)    text"
    _SUBPOINT_PREFIX_RE = re.compile(r"^\s*([0-9]+)\.\s+")   # "1.    text"
    _PARAGRAPH_NUM_PREFIX_RE = re.compile(r"^\s*\((\d+)\)\s+")  # "(1)    text"

    def __init__(self, file: Union[str, Path]) -> None:
        self.path = Path(file)
        self.data: Dict[str, Any] = self._load_json(self.path)

    # ---------- I/O a utility ----------
    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Soubor neexistuje: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _normalize(s: Optional[str]) -> str:
        return (s or "").strip()

    @staticmethod
    def _iter_children(node: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        for ch in node.get("children", []) or []:
            if isinstance(ch, dict):
                yield ch

    @staticmethod
    def _node_title_generic(node: Dict[str, Any]) -> Optional[str]:
        t = node.get("title")
        if isinstance(t, str) and t.strip():
            return t
        meta = node.get("meta")
        if isinstance(meta, dict):
            rt = meta.get("raw_text")
            if isinstance(rt, str) and rt.strip():
                return rt
        return None

    @staticmethod
    def _node_title_article(node: Dict[str, Any]) -> Optional[str]:
        meta = node.get("meta")
        if isinstance(meta, dict):
            art_num = meta.get("article_number")
            if isinstance(art_num, str) and art_num.strip():
                return art_num.strip()
        t = node.get("title")
        if isinstance(t, str) and t.strip():
            return t.strip()
        if isinstance(meta, dict):
            rt = meta.get("raw_text")
            if isinstance(rt, str) and rt.strip():
                return rt.strip()
        return None

    @staticmethod
    def _get_text_from_node(node: Dict[str, Any]) -> Optional[str]:
        # 1) node["text"] – zachovat, neodstraňovat mezery uvnitř
        t = node.get("text")
        if isinstance(t, str) and t != "":
            return t

        # 2) preferuj meta.segments s label == "valid_text" – vrátit beze změn (včetně mezer)
        meta = node.get("meta")
        if isinstance(meta, dict):
            segs = meta.get("segments")
            if isinstance(segs, list):
                valid_texts: List[str] = []
                for s in segs:
                    if isinstance(s, dict) and s.get("label") == "valid_text":
                        st = s.get("text")
                        if isinstance(st, str):
                            valid_texts.append(st)
                if valid_texts:
                    # mezi segmenty vložíme jednu mezeru (segments už zpravidla obsahují celé věty)
                    return " ".join(valid_texts)

            # 3) fallback: meta.raw_text
            rt = meta.get("raw_text")
            if isinstance(rt, str) and rt != "":
                return rt

        # 4) fallback: spoj texty z children typu paragraph
        buf: List[str] = []
        for ch in (node.get("children") or []):
            if isinstance(ch, dict) and ch.get("type") == "paragraph":
                pt = LawJsonCrawler._get_text_from_node(ch)
                if pt is not None:
                    buf.append(pt)
        if buf:
            return " ".join(buf)

        return None

    # ---------- detektory typů ----------
    @staticmethod
    def _is_article(node: Dict[str, Any]) -> bool:
        return node.get("type") == "article"

    @staticmethod
    def _is_article_paragraph(node: Dict[str, Any]) -> bool:
        return node.get("type") == "article_paragraph"

    @staticmethod
    def _is_paragraph(node: Dict[str, Any]) -> bool:
        return node.get("type") == "paragraph"

    @staticmethod
    def _is_point(node: Dict[str, Any]) -> bool:
        return node.get("type") == "point"

    @staticmethod
    def _is_subpoint(node: Dict[str, Any]) -> bool:
        return node.get("type") == "subpoint"

    # ---------- průchod a sběr uzlů ----------
    def _collect_nodes(self) -> Iterable[Tuple[Dict[str, Any], NodePath]]:
        parts = self.data.get("parts") or []
        for part in parts:
            part_title = self._node_title_generic(part)
            for art in self._iter_children(part):
                if not self._is_article(art):
                    for sub in self._iter_children(art):
                        yield from self._walk(sub, part_title, None, [])
                    continue
                article_title = self._node_title_article(art)
                yield art, NodePath(
                    part_title=part_title,
                    article_title=article_title,
                    chain_titles=[],
                    node_type="article",
                    title=article_title,   # např. "§ 11"
                    text=self._get_text_from_node(art),
                )
                for ch in self._iter_children(art):
                    yield from self._walk(ch, part_title, article_title, [])

    def _walk(
        self,
        node: Dict[str, Any],
        part_title: Optional[str],
        article_title: Optional[str],
        chain: List[str],
    ) -> Iterable[Tuple[Dict[str, Any], NodePath]]:
        t = node.get("type")

        if t == "article_paragraph":
            np = NodePath(
                part_title=part_title,
                article_title=article_title,
                chain_titles=list(chain),
                node_type="article_paragraph",
                title=self._node_title_generic(node),   # "1", "2", ...
                text=self._get_text_from_node(node),
            )
            yield node, np
            for ch in self._iter_children(node):
                yield from self._walk(ch, part_title, article_title, chain)

        elif t == "point":
            label = self._normalize(node.get("title"))  # "a", "b", ...
            chain2 = list(chain)
            if label:
                chain2.append(f"point {label}")
            np = NodePath(
                part_title=part_title,
                article_title=article_title,
                chain_titles=list(chain2),
                node_type="point",
                title=label,
                text=self._get_text_from_node(node),
            )
            yield node, np
            for ch in self._iter_children(node):
                yield from self._walk(ch, part_title, article_title, chain2)

        elif t == "subpoint":
            sublab = self._normalize(node.get("title"))  # "1", "2", ...
            chain2 = list(chain)
            if sublab:
                chain2.append(f"subpoint {sublab}")
            np = NodePath(
                part_title=part_title,
                article_title=article_title,
                chain_titles=list(chain2),
                node_type="subpoint",
                title=sublab,
                text=self._get_text_from_node(node),
            )
            yield node, np
            for ch in self._iter_children(node):
                yield from self._walk(ch, part_title, article_title, chain2)

        elif t == "paragraph":
            np = NodePath(
                part_title=part_title,
                article_title=article_title,
                chain_titles=list(chain),
                node_type="paragraph",
                title=self._node_title_generic(node),
                text=self._get_text_from_node(node),
            )
            yield node, np

        else:
            for ch in self._iter_children(node):
                yield from self._walk(ch, part_title, article_title, chain)

    # ---------- API vyhledávání ----------
    def find_articles(self, query: str, exact: bool = False) -> List[NodePath]:
        qn = self._normalize(query).lower()
        res: List[NodePath] = []
        for _, np in self._collect_nodes():
            if np.node_type == "article":
                title = self._normalize(np.title).lower()
                if (title == qn) if exact else (qn in title):
                    res.append(np)
        return res

    def list_article_paragraphs(self, article_title: Optional[str] = None) -> List[NodePath]:
        res: List[NodePath] = []
        for _, np in self._collect_nodes():
            if np.node_type == "article_paragraph":
                if article_title is None or self._normalize(np.article_title) == self._normalize(article_title):
                    res.append(np)
        return res

    def list_points(self, article_title: Optional[str] = None) -> List[NodePath]:
        res: List[NodePath] = []
        for _, np in self._collect_nodes():
            if np.node_type == "point":
                if article_title is None or self._normalize(np.article_title) == self._normalize(article_title):
                    res.append(np)
        return res

    def list_subpoints(self, article_title: Optional[str] = None) -> List[NodePath]:
        res: List[NodePath] = []
        for _, np in self._collect_nodes():
            if np.node_type == "subpoint":
                if article_title is None or self._normalize(np.article_title) == self._normalize(article_title):
                    res.append(np)
        return res

    def get_paragraph_titles(self) -> List[str]:
        titles: List[str] = []
        seen = set()
        for _, np in self._collect_nodes():
            if np.node_type != "article":
                continue
            t = self._normalize(np.title)
            if self._PARA_SIGN_RE.match(t) and t not in seen:
                seen.add(t)
                titles.append(t)

        def keyfun(s: str):
            m = self._PARA_SIGN_RE.match(s)
            if not m:
                return (10**9, "")
            return (int(m.group(1)), (m.group(2) or "").lower())

        titles.sort(key=keyfun)
        return titles

    # ---------- pomocné: extrakce prefixu z paragraph title (pro bezodstavcové články) ----------
    @staticmethod
    def _extract_point_prefix_from_paragraph_title(title: Optional[str]) -> Optional[str]:
        if not title:
            return None
        m = LawJsonCrawler._POINT_PREFIX_RE.match(title)
        if m:
            return m.group(1).lower()
        return None

    @staticmethod
    def _extract_subpoint_prefix_from_paragraph_title(title: Optional[str]) -> Optional[str]:
        if not title:
            return None
        m = LawJsonCrawler._SUBPOINT_PREFIX_RE.match(title)
        if m:
            return m.group(1)  # číslo jako string
        return None

    # ---------- formátovaný výpis s tabulátorem ----------
    @staticmethod
    def _strip_paragraph_number_prefix(text: str) -> Tuple[Optional[str], str]:
        """
        Odstraní počáteční "(n)   " a vrátí (n, zbytek).
        """
        m = LawJsonCrawler._PARAGRAPH_NUM_PREFIX_RE.match(text)
        if m:
            n = m.group(1)
            rest = text[m.end():]
            return n, rest
        return None, text

    @staticmethod
    def _strip_point_prefix(text: str) -> Tuple[Optional[str], str]:
        """
        Odstraní počáteční "a)   " a vrátí (a, zbytek).
        """
        m = LawJsonCrawler._POINT_PREFIX_RE.match(text)
        if m:
            letter = m.group(1).lower()
            rest = text[m.end():]
            return letter, rest
        return None, text

    @staticmethod
    def _strip_subpoint_prefix(text: str) -> Tuple[Optional[str], str]:
        """
        Odstraní počáteční "1.   " a vrátí ("1", zbytek).
        """
        m = LawJsonCrawler._SUBPOINT_PREFIX_RE.match(text)
        if m:
            num = m.group(1)
            rest = text[m.end():]
            return num, rest
        return None, text

    # ---------- API: get_text s tabulátorem mezi prefixem a textem ----------
    def get_text(
        self,
        article: Optional[str] = None,      # např. "§ 11"
        paragraph: Optional[str] = None,    # např. "1"
        point: Optional[str] = None,        # např. "a"
        subpoint: Optional[str] = None,     # např. "1"
    ) -> str:
        """
        Výstup v pořadí: článek -> (n)\t odstavec -> a)\t bod -> 1.\t sub-bod.
        - Pouze article: celý článek.
        - article + paragraph: daný odstavec a jeho body a sub-body.
        - article + paragraph + point: daný bod a jeho sub-body.
        - article + paragraph + point + subpoint: pouze daný sub-bod.
        Prefix je vždy oddělen tabulátorem.
        """
        art_norm = self._normalize(article) if article else None
        par_norm = self._normalize(paragraph) if paragraph else None
        point_norm = self._normalize(point) if point else None
        subpoint_norm = self._normalize(subpoint) if subpoint else None

        # ověření existence článku
        if art_norm:
            if not any(
                np.node_type == "article" and self._normalize(np.title) == art_norm
                for _, np in self._collect_nodes()
            ):
                return ""

        # když chybí článek a je dán nižší filtr, najdi článek
        if art_norm is None and (par_norm or point_norm or subpoint_norm):
            active_article: Optional[str] = None
            active_paragraph: Optional[str] = None
            found_article: Optional[str] = None
            found_paragraph: Optional[str] = None

            for _, np in self._collect_nodes():
                if np.node_type == "article":
                    active_article = self._normalize(np.title)
                    active_paragraph = None
                elif np.node_type == "article_paragraph":
                    active_paragraph = self._normalize(np.title)
                    if par_norm and active_paragraph == par_norm and active_article:
                        found_article = active_article
                        found_paragraph = active_paragraph
                        if not (point_norm or subpoint_norm):
                            break
                elif np.node_type == "paragraph":
                    if point_norm:
                        # prefix v title textu
                        pref = self._extract_point_prefix_from_paragraph_title(np.title)
                        if pref and pref == point_norm and active_article:
                            found_article = active_article
                            if par_norm:
                                found_paragraph = active_paragraph
                            break
                    if subpoint_norm:
                        pref2 = self._extract_subpoint_prefix_from_paragraph_title(np.title)
                        if pref2 and pref2 == subpoint_norm and active_article:
                            found_article = active_article
                            if par_norm:
                                found_paragraph = active_paragraph
                            break

            if found_article:
                art_norm = found_article
                if par_norm and found_paragraph:
                    par_norm = found_paragraph
            else:
                return ""

        # Predikáty filtrů
        def article_ok(title: Optional[str]) -> bool:
            return (art_norm is None) or (self._normalize(title) == art_norm)

        def paragraph_ok(title: Optional[str]) -> bool:
            return (par_norm is None) or (self._normalize(title) == par_norm)

        def point_ok(label: Optional[str]) -> bool:
            return (point_norm is None) or (self._normalize(label) == point_norm)

        def subpoint_ok(label: Optional[str]) -> bool:
            return (subpoint_norm is None) or (self._normalize(label) == subpoint_norm)

        # Stav
        lines: List[str] = []
        active_article: Optional[str] = None
        active_paragraph: Optional[str] = None
        seen_any_article_paragraph_in_current_article = False
        printed_article_text = False
        need_only_subpoint = (art_norm is not None and par_norm is not None and point_norm is not None and subpoint_norm is not None)
        in_intro_block = False  # pro články bez odstavců

        for _, np in self._collect_nodes():
            if np.node_type == "article":
                active_article = self._normalize(np.title)
                active_paragraph = None
                seen_any_article_paragraph_in_current_article = False
                in_intro_block = True
                if not article_ok(active_article):
                    continue
                if par_norm is None and point_norm is None and subpoint_norm is None and np.text and not printed_article_text:
                    # text článku, pokud existuje
                    lines.append((np.text or ""))
                    printed_article_text = True

            elif np.node_type == "article_paragraph":
                if not article_ok(active_article):
                    continue
                seen_any_article_paragraph_in_current_article = True
                in_intro_block = False
                pkey = self._normalize(np.title)  # "1", "2", ...
                if not paragraph_ok(pkey):
                    active_paragraph = None
                    continue
                active_paragraph = pkey

            elif np.node_type == "point":
                if not article_ok(active_article):
                    continue
                in_intro_block = False
                # tisk bodu až na paragraph (child)
                continue

            elif np.node_type == "subpoint":
                if not article_ok(active_article):
                    continue
                in_intro_block = False
                # tisk sub-bodu až na paragraph (child)
                continue

            elif np.node_type == "paragraph":
                if not article_ok(active_article):
                    continue

                # Urči kontext paragraphu
                point_labels = [ct.split(" ", 1)[1] for ct in np.chain_titles if ct.startswith("point ")]
                subpoint_labels = [ct.split(" ", 1)[1] for ct in np.chain_titles if ct.startswith("subpoint ")]

                is_from_point = len(point_labels) > 0
                is_from_subpoint = len(subpoint_labels) > 0

                raw = np.text
                if raw is None:
                    continue

                if seen_any_article_paragraph_in_current_article:
                    # Režim s odstavci
                    if is_from_subpoint:
                        # sub-bod
                        sp_label = self._normalize(subpoint_labels[-1])
                        if active_paragraph is None:
                            continue
                        if not subpoint_ok(sp_label):
                            continue
                        # odstranit případný původní subpoint prefix z raw a nahradit "X.\t"
                        _, clean = self._strip_subpoint_prefix(raw)
                        line = "      " + f"{sp_label}.\t" + clean
                        lines.append(line)
                        if need_only_subpoint:
                            break

                    elif is_from_point:
                        # bod
                        p_label = self._normalize(point_labels[-1])
                        if active_paragraph is None:
                            continue
                        if not point_ok(p_label):
                            continue
                        _, clean = self._strip_point_prefix(raw)
                        line = "    " + f"{p_label})\t" + clean
                        lines.append(line)

                    else:
                        # text odstavce (první paragraph po article_paragraph)
                        if active_paragraph is None:
                            continue
                        # odstranit případný "(n)    " a nahradit "(n)\t"
                        _, clean = self._strip_paragraph_number_prefix(raw)
                        line = "  " + f"({active_paragraph})\t" + clean
                        lines.append(line)

                else:
                    # Režim bez odstavců (intro + body/sub-body)
                    pref_point = self._extract_point_prefix_from_paragraph_title(np.title)
                    pref_sub = self._extract_subpoint_prefix_from_paragraph_title(np.title)

                    if is_from_subpoint or pref_sub is not None:
                        # sub-bod bez explicitních odstavců
                        label = self._normalize(subpoint_labels[-1]) if is_from_subpoint else pref_sub
                        if not subpoint_ok(label):
                            continue
                        _, clean = self._strip_subpoint_prefix(raw)
                        line = "      " + f"{label}.\t" + clean
                        lines.append(line)

                    elif is_from_point or pref_point is not None:
                        # bod bez explicitních odstavců
                        label = self._normalize(point_labels[-1]) if is_from_point else pref_point
                        if not point_ok(label):
                            continue
                        _, clean = self._strip_point_prefix(raw)
                        line = "    " + f"{label})\t" + clean
                        lines.append(line)
                        in_intro_block = False

                    else:
                        # úvodní paragraph(e)
                        if par_norm is not None:
                            continue
                        # bez prefixu; jen úroveň odsazení pro odstavec
                        lines.append("  " + raw)

        # Omezení výstupu na přesný sub-bod při plné specifikaci
        if art_norm and par_norm and point_norm and subpoint_norm:
            lines = [ln for ln in lines if ln.startswith("      ")]

        return "\n".join(lines)

    # ---------- Export výsledků (volitelné) ----------
    @staticmethod
    def export_results_to_json(nodes: List[NodePath], path: Union[str, Path]) -> None:
        p = Path(path)
        rows = [asdict(n) for n in nodes]
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def export_results_to_csv(nodes: List[NodePath], path: Union[str, Path]) -> None:
        import csv
        p = Path(path)
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["part_title", "article_title", "chain_titles", "node_type", "title", "text", "human_path"])
            for n in nodes:
                w.writerow([
                    n.part_title or "",
                    n.article_title or "",
                    " > ".join(n.chain_titles),
                    n.node_type,
                    n.title or "",
                    (n.text or "").replace("\n", " ").strip(),
                    n.human_path(),
                ])


# --------------------------- Main s ukázkou ---------------------------
def main() -> None:
    """
    Ukázkové použití:
      - § 11 (odstavce + body + sub-body),
      - § 6 (odstavce bez bodů),
      - § 18 (bez odstavců, úvod + body).
    Upravte cestu k JSON souboru.
    """
    file = "../Parser/output_v5.json"
    api = LawJsonCrawler(file)

    print("Paragrafy:", api.get_paragraph_titles())

    # Článek s odstavci, body i sub-body
    print("\nText celého § 11:\n", api.get_text(article="§ 11"))
    print("\nText § 11 odst. 1 vč. bodů a sub-bodů:\n", api.get_text(article="§ 11", paragraph="2"))
    #print("\nText § 11 odst. 1 písm. a) vč. sub-bodů:\n", api.get_text(article="§ 11", paragraph="1", point="a"))
    #print("\nText § 11 odst. 1 písm. a) bod 3.:\n", api.get_text(article="§ 11", paragraph="1", point="a", subpoint="3"))

    # Článek s odstavci bez bodů – např. § 6 (dle datasetu)
    #print("\nText celého § 6:\n", api.get_text(article="§ 6"))

    # Článek bez odstavců – úvod + body (např. § 18)
    #print("\nText celého § 18 (bez odstavců, úvod + body):\n", api.get_text(article="§ 18"))
    #print("\nText § 18 písm. b):\n", api.get_text(article="§ 18", point="b"))


if __name__ == "__main__":
    main()
