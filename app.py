import streamlit as st
import os
import json
from datetime import datetime

import subprocess
import webbrowser

# Import pro Document Q&A Agent (ponecháno kvůli kompatibilitě ostatních částí)

# Import pro Information Collector Agent
from information_collector_agent import InformationCollectorAgent

# Import pro Database Search Agent
from database_search_agent import DatabaseSearchAgent

# Import pro Webpage Assistant
from webpage_assistant import WebpageAssistant
from webpage_content import WEBPAGE_CONTENT

# Nový import pro Law Expert Agenta
from law_expert_agent import LawExpertAgent


def main():
    st.set_page_config(
        page_title="Multi-Agent Demo Platform",
        layout="wide",
        page_icon="🤖",
        initial_sidebar_state="expanded",
    )

    # Inicializace session state
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = None

    # Hlavní nadpis
    st.title("🤖 Platforma AI Asistentů")
    st.markdown("*Interaktivní ukázky různých AI agentů*")
    st.markdown("---")

    # Výběr agenta
    render_agent_selector()
    st.markdown("---")

    # Zobrazení vybraného agenta
    if st.session_state.current_agent == "law_expert":
        render_law_expert_agent()
    elif st.session_state.current_agent == "customer":
        render_customer_agent()
    elif st.session_state.current_agent == "database_search":
        render_database_search_agent()
    elif st.session_state.current_agent == "webpage":
        render_webpage_launcher()
    else:
        render_welcome_screen()


def render_agent_selector():
    """Výběr typu agenta"""
    st.subheader("🎯 Vyberte demo agenta")
    col1, col2, col3, col4 = st.columns(4)

    # Law Expert Agent (nahrazuje Document Q&A v prvním slotu)
    with col1:
        if st.button(
            "⚖️ Právní Asistent",
            use_container_width=True,
            type="primary" if st.session_state.current_agent == "law_expert" else "secondary",
        ):
            st.session_state.current_agent = "law_expert"
            st.session_state.law_messages = []
            st.rerun()
        st.caption("Jedoduchá analýza právních dokumentů")

    # Customer Information Collector
    with col2:
        if st.button(
            "👤 Sběr Informací",
            use_container_width=True,
            type="primary" if st.session_state.current_agent == "customer" else "secondary",
        ):
            st.session_state.current_agent = "customer"
            agent = InformationCollectorAgent(
                {
                    "jmeno": "Celé jméno zákazníka",
                    "email": "Emailová adresa",
                    "telefon": "Telefonní číslo",
                    "firma": "Název firmy",
                    "pozice": "Pracovní pozice",
                    "zajem": "Co zákazníka zajímá",
                }
            )
            st.session_state.collector_agent = agent
            initial_response = agent.start_conversation()
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": initial_response["message"],
                    "extracted": initial_response["extracted_fields"],
                }
            ]
            st.rerun()
        st.caption("AI asistent, který vede konverzaci")

    # Database Search Agent
    with col3:
        if st.button(
            "🔍 Hledání v Databázi",
            use_container_width=True,
            type="primary" if st.session_state.current_agent == "database_search" else "secondary",
        ):
            st.session_state.current_agent = "database_search"
            agent = DatabaseSearchAgent()
            st.session_state.search_agent = agent
            initial_response = agent.start_conversation()
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": initial_response["message"],
                }
            ]
            st.rerun()
        st.caption("Vyhledávání pomocí přirozeného jazyka")

    # Webpage Assistant
    with col4:
        if st.button(
            "🌐 Chatbot na Webu",
            use_container_width=True,
            type="primary" if st.session_state.current_agent == "webpage" else "secondary",
        ):
            st.session_state.current_agent = "webpage"
            st.rerun()
        st.caption("Asistent pro návštěvníky webových stránek")

def render_welcome_screen():
    """Úvodní obrazovka"""
    st.info("👆 Vyberte AI asistenta pro zobrazení ukázky")
    st.markdown("### 📚 Dostupné ukázky AI asistentů:")
    st.markdown("""
    Každá ukázka demonstruje jiný způsob, jak AI může pomáhat s každodenními úkoly.
    Vyberte si a vyzkoušejte interaktivní demo bez nutnosti instalace nebo programování.
    """)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚖️ Právní Asistent")
        st.write("""
        **Co dělá:**
        - Načte právní dokument (např. zákon) a porozumí jeho struktuře
        - Odpovídá na otázky ohledně obsahu dokumentu
        - Najde konkrétní paragrafy a ustanovení
        - Vyhledává podle tématu i podle čísla paragrafu

        **Jak to funguje:**
        1. Nahrajete Word dokument (.docx) se zákonem
        2. AI automaticky rozpozná strukturu (části, paragrafy, odstavce)
        3. Můžete se ptát přirozeným jazykem: "Co říká § 11 o majetku?"
        4. AI odpoví s odkazem na konkrétní části zákona

        **Použití v praxi:**
        - Právní kanceláře - rychlé hledání v zákonech
        - Firmy - analýza smluv a předpisů
        - Studenti práva - učení a reference
        """)

    with col2:
        st.markdown("**🔍 Database Search**")
        st.write(
            """
- 50 dummy osob v databázi
- Konverzační vyhledávání
- Přirozené dotazy (pan Horák z Liberce)
- Smart filtering (kombinace filtrů)
- Hledání podle jména, pozice, lokace
- Skill matching a statistiky
"""
        )

        st.markdown("**🌐 Webpage Demo**")
        st.write(
            """
- Samostatná HTML stránka
- Floating chatbot v rohu stránky
- AI asistent pomáhá s obsahem
- Quick action buttons
- Modern responsive design
- Real-time komunikace s API
"""
        )


def render_webpage_launcher():
    """Launcher pro webpage demo s integrovaným Flask backendem"""
    st.subheader("🌐 Webpage Assistant Demo")
    st.markdown(
        """
Toto demo je **samostatná HTML stránka** s integrovaným floating chatbotem.

### 🎯 Co obsahuje:
- **Kompletní firemní webová stránka** (TechFlow Solutions)
- **Floating chatbot** v pravém dolním rohu
- **AI asistent** který odpovídá na otázky o obsahu stránky
- **Quick action buttons** pro rychlé dotazy
- **Modern design** s gradienty a animacemi
"""
    )

    st.markdown("---")



    # ========================================================================
    # PŮVODNÍ SEKCE: HTML Stránka
    # ========================================================================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Spuštění HTML stránky")
        st.markdown(
            """
** Otevřete HTML stránku**
Po spuštění backendu (zelený status výše) můžete otevřít ukázkovou webovou stránku
"""
        )

        if st.button("🌐 Otevřít Demo Web", type="primary", use_container_width=True):
            try:
                html_path = os.path.abspath("webpage_demo.html")
                webbrowser.open(f"file://{html_path}")
                st.success("✅ HTML stránka otevřena v prohlížeči!")
            except Exception as e:
                st.error(f"Chyba při otevírání: {str(e)}")

        st.markdown("---")

        # Automatická kontrola statusu
        if st.button("🔄 Obnovit status", use_container_width=True):
            check_flask_api()

    with col2:
        st.markdown("### 📋 Obsah stránky")
        st.markdown(
            """
**🏢 TechFlow Solutions**
- Inovativní tech společnost
- AI & Cloud řešení

**💼 Služby:**
- AI & Machine Learning
- Cloud Migration
- Data Analytics
- Chatbot Development

**📦 Produkty:**
- TechFlow AI Suite - 2,499 Kč/měsíc
- Cloud Starter - 999 Kč/měsíc
- Enterprise Package - 9,999 Kč/měsíc

**❓ FAQ + 📞 Kontakt**
"""
        )

    st.markdown("---")

    # Preview sekce
    st.markdown("### 👀 Náhled funkcí")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
**🎨 Design features:**
- Gradient color scheme (fialová/modrá)
- Animované přechody
- Responzivní layout
- Modern card design
"""
        )
    with col_b:
        st.markdown(
            """
**💬 Chatbot features:**
- Floating button (vždy viditelný)
- Slide-up animace okna
- Typing indicator (• • •)
- Quick action buttons
- Enter key support
"""
        )

    st.markdown("---")

    # Status check
    st.markdown("### 🔍 Status check")
    col_x, col_y = st.columns(2)
    with col_x:
        if st.button("🔍 Zkontrolovat Flask API", use_container_width=True):
            check_flask_api()
    with col_y:
        if st.button("📁 Zkontrolovat HTML soubor", use_container_width=True):
            check_html_file()

    st.markdown("---")

    # Dokumentace
    with st.expander("📖 Kompletní dokumentace"):
        st.markdown(
            """
### API Endpoints

**GET /api/init**
- Inicializuje chat
- Vrací úvodní pozdrav

**POST /api/chat**
- Odesílá zprávu chatbotovi
- Body: `{"message": "text"}`
- Vrací: `{"response": "odpověď", "status": "success"}`

**POST /api/reset**
- Resetuje konverzaci

### Backend Management
- **Spustit**: Klikněte na "🚀 Spustit Flask API"
- **Zastavit**: Klikněte na "🛑 Zastavit Flask API"
- **Port**: 5000 (výchozí)
- **Auto-start**: Backend se spustí v novém procesu

### Příklady dotazů
- "Jaké služby nabízíte?"
- "Kolik stojí Enterprise balíček?"
- "Kontaktní informace"
- "Nabízíte bezplatnou konzultaci?"
- "Jak dlouho trvá implementace?"

### Troubleshooting
**Chatbot se nepřipojuje:**
1. Zkontrolujte, že Flask API běží (zelený status)
2. Otevřete console v prohlížeči (F12)
3. Zkontrolujte CORS nastavení

**Flask se nespustí:**
- Zkontrolujte, že máte `flask` a `flask-cors` nainstalované
- `pip install flask flask-cors`
- Zkontrolujte, že port 5000 není obsazený
- Zkontrolujte, že soubor `chatbot_api.py` existuje

**CORS chyby:**
- Ujistěte se, že máte `flask-cors` nainstalovaný
- `pip install flask-cors`
"""
        )


def start_flask_backend():
    """Spustí Flask backend server v samostatném procesu"""
    try:
        # Kontrola, zda chatbot_api.py existuje
        if not os.path.exists("chatbot_api.py"):
            st.error("❌ Pomocný soubor nebyl nalezen!")
            st.info("💡 Kontaktujte technickou podporu - chybí soubor 'chatbot_api.py'")
            return

        # Kontrola, zda Flask není již spuštěný
        if st.session_state.flask_running:
            st.warning("⚠️ Flask API již běží!")
            return

        # Spuštění Flask serveru v samostatném procesu
        import sys
        flask_process = subprocess.Popen(
            [sys.executable, "chatbot_api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Uložení procesu do session state
        st.session_state.flask_process = flask_process
        st.session_state.flask_running = True

        # Čekání na start (2 sekundy)
        import time
        time.sleep(2)

        # Ověření, že proces běží
        if flask_process.poll() is None:
            st.success("✅ Backend úspěšně spuštěn!")
            st.info("🎉 Chatbot je nyní připojený a připravený odpovídat!")
        else:
            # Proces skončil s chybou
            st.session_state.flask_running = False
            st.session_state.flask_process = None
            stderr_output = flask_process.stderr.read() if flask_process.stderr else "Žádné chybové hlášení"
            st.error(f"❌ Flask API se nepodařilo spustit!")
            with st.expander("🔍 Zobrazit chybovou zprávu"):
                st.code(stderr_output)

    except Exception as e:
        st.session_state.flask_running = False
        st.session_state.flask_process = None
        st.error(f"❌ Chyba při spouštění Flask API: {str(e)}")
        st.info("💡 Zkontrolujte, že máte nainstalované: pip install flask flask-cors")


def stop_flask_backend():
    """Zastaví Flask backend server"""
    try:
        if st.session_state.flask_process is None:
            st.warning("⚠️ Flask API není spuštěné!")
            return

        # Ukončení procesu
        st.session_state.flask_process.terminate()

        # Čekání na ukončení (max 5 sekund)
        import time
        for _ in range(5):
            if st.session_state.flask_process.poll() is not None:
                break
            time.sleep(1)

        # Pokud proces stále běží, vynutit ukončení
        if st.session_state.flask_process.poll() is None:
            st.session_state.flask_process.kill()

        # Reset session state
        st.session_state.flask_process = None
        st.session_state.flask_running = False

        st.success("✅ Flask API bylo zastaveno!")

    except Exception as e:
        st.error(f"❌ Chyba při zastavování Flask API: {str(e)}")
        # Pokus o reset i při chybě
        st.session_state.flask_process = None
        st.session_state.flask_running = False

def check_flask_api():
    """Zkontroluje, zda Flask API běží"""
    try:
        import requests

        response = requests.get("http://localhost:5000/api/init", timeout=2)
        if response.status_code == 200:
            st.success("✅ Flask API běží správně na http://localhost:5000")
        else:
            st.warning(f"⚠️ Flask API odpovídá, ale s kódem: {response.status_code}")
    except ImportError:
        st.error("❌ Balíček 'requests' není nainstalován. Spusťte: pip install requests")
    except:
        st.error("❌ Flask API není spuštěné nebo neodpovídá na http://localhost:5000")
    st.info("💡 Spusťte: python chatbot_api.py")


def check_html_file():
    """Zkontroluje existenci HTML souboru"""
    if os.path.exists("webpage_demo.html"):
        st.success("✅ webpage_demo.html nalezen")
        file_size = os.path.getsize("webpage_demo.html")
        st.info(f"📊 Velikost souboru: {file_size:,} bytů")
    else:
        st.error("❌ webpage_demo.html nenalezen v aktuálním adresáři")


# ============================================================================
# LAW EXPERT AGENT (nahrazuje Document Q&A)
# ============================================================================

def render_law_expert_agent():
    """Zobrazení Právního expert agenta"""
    st.subheader("⚖️ Právní Asistent")

    col1, col2 = st.columns([3, 1])

    with col2:
        render_law_expert_sidebar()

    with col1:
        render_law_expert_chat()


def render_law_expert_sidebar():
    """Sidebar pro Právní expert agenta"""
    st.markdown("### ⚙️ Nastavení")

    # Upload zákona
    uploaded_file = st.file_uploader(
        "Nahrajte zákon (DOCX):", type=["docx"], key="law_docx_upload"
    )

    if st.button("🚀 Zpracovat zákon", type="primary", use_container_width=True):
        if uploaded_file:
            process_law_document(uploaded_file)
        else:
            st.error("Nejprve nahrajte DOCX soubor!")

    # Status načtení
    if st.session_state.get("law_agent_loaded"):
        st.success("✅ Zákon načten")

        # Statistiky
        if "law_agent" in st.session_state:
            agent = st.session_state.law_agent
            metadata = agent.law_metadata

            st.markdown("---")
            st.markdown("### 📊 Statistiky")
            st.metric("Počet částí", metadata.get("parts_count", 0))
            st.metric("Počet paragrafů", len(metadata.get("laws_list", [])))

    st.markdown("---")

    # Navigace strukturou
    if st.session_state.get("law_agent_loaded"):
        st.markdown("### 🗂️ Navigace")

        agent = st.session_state.law_agent
        laws = agent.get_available_laws()

        if laws:
            selected_law = st.selectbox(
                "Vyberte paragraf:", [""] + laws, key="selected_law"
            )

            if selected_law:
                articles = agent.get_articles_for_law(selected_law)
                if articles:
                    selected_article = st.selectbox(
                        "Vyberte odstavec:", ["Vše"] + articles, key="selected_article"
                    )

                    if st.button("📄 Zobrazit obsah", use_container_width=True):
                        show_law_content(selected_law, selected_article)

    st.markdown("---")

    # Rychlé akce
    if st.session_state.get("law_agent_loaded"):
        st.markdown("### ⚡ Rychlé akce")

        if st.button("📋 Přehled struktury", use_container_width=True):
            st.session_state.show_law_structure = True

        if st.button("📚 Seznam paragrafů", use_container_width=True):
            st.session_state.show_laws_list = True

        if st.button("📊 Statistiky paragrafů", use_container_width=True):
            st.session_state.show_para_stats = True

    st.markdown("---")

    # Reset
    if st.button("🗑️ Reset", use_container_width=True):
        reset_law_agent()


def render_law_expert_chat():
    """Chat interface pro Právní expert agenta"""

    # Zobrazení speciálních pohledů
    if st.session_state.get("show_law_structure"):
        show_law_structure_view()
        st.session_state.show_law_structure = False
        return

    if st.session_state.get("show_laws_list"):
        show_laws_list_view()
        st.session_state.show_laws_list = False
        return

    if st.session_state.get("show_para_stats"):
        show_paragraph_stats_view()
        st.session_state.show_para_stats = False
        return

    # Hlavní chat interface
    if "law_messages" not in st.session_state:
        st.session_state.law_messages = []

    # Zobrazení zpráv
    for message in st.session_state.law_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                # Zobrazení metadat odpovědi
                if "method" in message:
                    st.caption(f"🔧 Metoda: {message['method']}")

                # Zobrazení zdrojů
                if "sources" in message and message["sources"]:
                    with st.expander("🔍 Zobrazit zdroje"):
                        for i, source in enumerate(message["sources"][:5], 1):
                            if isinstance(source, str):
                                st.text(f"{i}. {source[:300]}...")

    # Input pro nové dotazy
    if prompt := st.chat_input("Položte otázku k zákonu..."):
        if not st.session_state.get("law_agent_loaded"):
            st.error("⚠️ Nejprve nahrajte a zpracujte zákon!")
        else:
            handle_law_question(prompt)


def process_law_document(uploaded_file):
    """Zpracování nahraného DOCX souboru se zákonem s detailním zobrazením pokroku"""
    try:
        # Kontejnery pro progress display
        progress_container = st.container()

        with progress_container:
            # Hlavní progress bar
            main_progress = st.progress(0)
            status_text = st.empty()
            details_text = st.empty()

            # Spinner pro vizuální feedback
            with st.spinner("⏳ Zpracovávám dokument..."):

                # === KROK 1: Uložení souboru ===
                status_text.markdown("### 📝 Krok 1/4: Ukládám soubor")
                details_text.info("Nahrávám dokument do dočasného úložiště...")
                main_progress.progress(5)

                temp_path = f"temp_law_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                details_text.success(f"✅ Soubor uložen: {uploaded_file.name}")
                main_progress.progress(10)

                # === KROK 2: Parsování struktury ===
                status_text.markdown("### 🔍 Krok 2/4: Analyzuji strukturu dokumentu")
                details_text.info("Rozpoznávám části, paragrafy a odstavce...")
                main_progress.progress(15)

                from parse_law import parse_doc_to_structure
                parsed_structure = parse_doc_to_structure(temp_path)

                parts_count = len(parsed_structure.get("parts", []))
                details_text.success(f"✅ Struktura analyzována: {parts_count} částí nalezeno")
                main_progress.progress(25)

                # Uložení do JSON
                import tempfile
                temp_json = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.json',
                    delete=False,
                    encoding='utf-8'
                )
                json.dump(parsed_structure, temp_json, ensure_ascii=False, indent=2)
                temp_json.close()

                # === KROK 3: Inicializace agenta ===
                status_text.markdown("### 🤖 Krok 3/4: Inicializuji AI asistenta")
                details_text.info("Připravuji crawler a dokumentový procesor...")
                main_progress.progress(30)

                agent = LawExpertAgent()

                # Načtení crawleru
                from seach_law_json import LawJsonCrawler
                agent.crawler = LawJsonCrawler(temp_json.name)
                agent.parsed_json_path = temp_json.name

                paragraph_titles = agent.crawler.get_paragraph_titles()
                para_count = len(paragraph_titles)

                details_text.success(f"✅ Nalezeno {para_count} paragrafů")
                main_progress.progress(35)

                # Metadata
                agent.law_metadata = {
                    "parts_count": parts_count,
                    "laws_list": paragraph_titles,
                    "paragraph_titles": paragraph_titles,
                    "paragraph_count": para_count,
                    "document_path": temp_path,
                    "document_name": os.path.basename(temp_path)
                }

                # === KROK 4: Vytváření embeddings (NEJDELŠÍ ČÁST) ===
                status_text.markdown("### 🧠 Krok 4/4: Vytvářím AI embeddings")
                main_progress.progress(40)

                # Sub-progress pro chunkování
                chunk_progress = st.progress(0)
                chunk_status = st.empty()

                # Inicializace processoru
                from law_chatbot_adapter import LawChatbotAdapter
                agent.doc_processor = LawChatbotAdapter()
                agent.doc_processor.load_from_json(temp_json.name)

                chunk_status.text("🔨 Vytvářím strukturované chunky...")
                chunk_progress.progress(10)
                main_progress.progress(45)

                # Vytvoření chunků
                chunks = agent.doc_processor.create_structured_chunks(
                    chunk_strategy="mixed",
                    max_chunk_size=1500,
                    include_context=True
                )

                total_chunks = len(chunks)
                chunk_status.success(f"✅ Vytvořeno {total_chunks} chunků")
                chunk_progress.progress(30)
                main_progress.progress(50)

                # Vytváření embeddings (s progress updaty)
                chunk_status.text("🧮 Počítám AI embeddings pro vyhledávání...")

                import numpy as np
                embeddings = []

                for i, chunk in enumerate(chunks):
                    # Update každých 5 chunků
                    if i % 5 == 0:
                        progress_pct = int((i / total_chunks) * 100)
                        chunk_progress.progress(30 + int(progress_pct * 0.5))  # 30-80%
                        main_progress.progress(50 + int(progress_pct * 0.35))  # 50-85%
                        chunk_status.text(f"🧮 Zpracováno {i}/{total_chunks} chunků ({progress_pct}%)")

                    embedding = agent.doc_processor.get_embedding(chunk["text"])
                    embeddings.append(embedding)

                chunk_status.success(f"✅ Embeddings vytvořeny pro {total_chunks} chunků")
                chunk_progress.progress(80)
                main_progress.progress(85)

                # Vytvoření FAISS indexu
                chunk_status.text("📊 Vytvářím vyhledávací index...")

                import faiss
                agent.doc_processor.processor.embeddings_array = np.array(embeddings, dtype=np.float32)
                dimension = agent.doc_processor.processor.embeddings_array.shape[1]

                agent.doc_processor.processor.index = faiss.IndexFlatL2(dimension)
                agent.doc_processor.processor.index.add(agent.doc_processor.processor.embeddings_array)

                chunk_status.success(f"✅ Vyhledávací index vytvořen (dimenze: {dimension})")
                chunk_progress.progress(100)
                main_progress.progress(90)

                # Statistiky
                chunk_stats = agent.doc_processor.get_chunk_statistics()
                agent.law_metadata["chunk_stats"] = chunk_stats

                details_text.success(
                    f"📊 Statistiky: {chunk_stats.get('total_chunks', 0)} chunků, "
                    f"průměrná délka {chunk_stats.get('avg_chunk_length', 0):.0f} znaků"
                )

                # === KROK 5: Inicializace chatbota ===
                status_text.markdown("### 💬 Finalizace: Inicializuji chatbota")
                details_text.info("Připravuji konverzační rozhraní...")
                main_progress.progress(95)

                from chatbot import ContextualChatbot
                agent.chatbot = ContextualChatbot(agent.doc_processor)

                # Uložení do session state
                st.session_state.law_agent = agent
                st.session_state.law_agent_loaded = True
                st.session_state.law_messages = []

                main_progress.progress(100)
                details_text.success("✅ Všechno hotovo!")

                # Úvodní zpráva
                welcome_msg = f"""
👋 Právní asistent je připravený!

📊 **Statistiky dokumentu:**
- Počet částí: {parts_count}
- Počet paragrafů: {para_count}
- Vytvořeno chunků: {total_chunks}
- Průměrná délka chunku: {chunk_stats.get('avg_chunk_length', 0):.0f} znaků

💡 **Co můžete dělat:**
- Ptát se na konkrétní paragrafy (např. "§ 11")
- Hledat podle tématu (např. "najdi ustanovení o majetku")
- Zobrazit seznam paragrafů
- Procházet strukturu dokumentu

**Zkuste:**
- "Jaké paragrafy obsahuje tento dokument?"
- "Co říká § 11?"
- "Statistiky paragrafů"
"""

                st.session_state.law_messages.append({
                    "role": "assistant",
                    "content": welcome_msg,
                })

                # Cleanup
                os.remove(temp_path)

        # Success s balónky
        st.success(f"🎉 Zákon '{uploaded_file.name}' úspěšně zpracován!")


        # Clear progress display po chvíli
        import time
        time.sleep(2)
        progress_container.empty()

        st.rerun()

    except Exception as e:
        st.error(f"❌ Chyba při zpracování: {str(e)}")
        import traceback
        with st.expander("🔍 Zobrazit technické detaily"):
            st.code(traceback.format_exc())


def handle_law_question(prompt: str):
    """Zpracování dotazu pro Law experta"""
    agent = st.session_state.law_agent

    # Přidání dotazu do historie
    st.session_state.law_messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Zobrazení dotazu
    with st.chat_message("user"):
        st.markdown(prompt)

    # Zpracování odpovědi
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzuji..."):
            response = agent.ask(prompt)

            st.markdown(response["answer"])

            # Metadata
            st.caption(f"🔧 Metoda: {response.get('method', 'unknown')}")

            # Zdroje
            if response.get("sources"):
                with st.expander("🔍 Zobrazit zdroje"):
                    for i, source in enumerate(response["sources"][:5], 1):
                        if isinstance(source, str):
                            st.text(f"{i}. {source[:300]}...")

    # Přidání odpovědi do historie
    st.session_state.law_messages.append(
        {
            "role": "assistant",
            "content": response["answer"],
            "sources": response.get("sources", []),
            "method": response.get("method", "unknown"),
        }
    )


def show_law_content(law_title: str, article: str):
    """Zobrazí obsah vybrané části zákona"""
    agent = st.session_state.law_agent

    article_label = None if article == "Vše" else article

    content = agent.search_by_structure(part_title_query=law_title, article_label=article_label)

    if content:
        display_text = f"📄 **{law_title}**"
        if article_label:
            display_text += f" - {article_label}"
        display_text += "\n\n"

        # Pokud je to string, zobrazíme ho přímo
        if isinstance(content, str):
            display_text += content
        else:
            # Pokud je to list, iterujeme
            for i, block in enumerate(content[:5], 1):
                display_text += f"**Bod {i}:**\n{block}\n\n---\n\n"

        st.session_state.law_messages.append(
            {
                "role": "assistant",
                "content": display_text,
                "sources": [content] if isinstance(content, str) else content,
                "method": "structural",
            }
        )

        st.rerun()
    else:
        st.warning("Nebyl nalezen žádný obsah.")


def show_law_structure_view():
    """Zobrazí přehled struktury zákona"""
    agent = st.session_state.law_agent
    structure = agent.get_law_structure_summary()

    st.markdown(structure)

    if st.button("🔙 Zpět na chat"):
        st.rerun()


def show_laws_list_view():
    """Zobrazí seznam všech paragrafů"""
    agent = st.session_state.law_agent
    laws = agent.get_available_laws()

    st.markdown("## 📚 Seznam paragrafů v dokumentu")
    st.markdown("---")

    # Zobrazení po skupinách
    cols = st.columns(3)
    for i, law in enumerate(laws):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"**{law}**")

    st.markdown("---")
    if st.button("🔙 Zpět na chat"):
        st.rerun()


def show_paragraph_stats_view():
    """Zobrazí statistiky o paragrafech"""
    agent = st.session_state.law_agent
    stats = agent.get_paragraph_statistics()

    st.markdown("## 📊 Statistiky paragrafů")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Celkový počet paragrafů", stats.get('total_paragraphs', 0))

    with col2:
        by_article = stats.get('paragraphs_by_article', {})
        st.metric("Počet článků s paragrafy", len(by_article))

    st.markdown("---")

    # Rozložení podle článků
    if by_article:
        st.markdown("### 📈 Top 10 článků podle počtu paragraph uzlů:")
        sorted_items = sorted(by_article.items(), key=lambda x: x[1], reverse=True)[:10]

        for article, count in sorted_items:
            st.markdown(f"**{article}**: {count} paragraph uzlů")

    st.markdown("---")
    if st.button("🔙 Zpět na chat"):
        st.rerun()


def reset_law_agent():
    """Reset právního expert agenta"""
    if "law_agent" in st.session_state:
        st.session_state.law_agent.cleanup()
        del st.session_state.law_agent

    st.session_state.law_agent_loaded = False
    st.session_state.law_messages = []
    st.session_state.pop("selected_law", None)
    st.session_state.pop("selected_article", None)

    st.rerun()


# ============================================================================
# OSTATNÍ AGENTY (Customer, Database Search) - beze změn
# ============================================================================

def render_customer_agent():
    """Zobrazení Zákaznické karty agenta"""
    st.subheader("👤 Zákaznická karta")
    col1, col2 = st.columns([3, 1])

    with col2:
        render_customer_card()

    with col1:
        render_customer_chat()


def render_customer_card():
    """Zobrazení zákaznické karty (read-only)"""
    st.markdown("**👤 Zákaznická karta**")

    if "collector_agent" not in st.session_state:
        st.warning("Agent není inicializován")
        return

    agent = st.session_state.collector_agent
    progress = agent.get_progress()

    st.progress(progress["percentage"] / 100)
    st.markdown(f"**Získáno:** {progress['collected']}/{progress['total']} ({progress['percentage']}%)")

    if progress["remaining"] > 0:
        st.caption(f"⏳ Zbývá: {progress['remaining']} polí")

    st.markdown("---")
    st.markdown("### 📝 Informace o zákazníkovi")

    fields_info = {
        "jmeno": ("👤", "Jméno"),
        "email": ("📧", "Email"),
        "telefon": ("📞", "Telefon"),
        "firma": ("🏢", "Firma"),
        "pozice": ("💼", "Pozice"),
        "zajem": ("🎯", "Zájem"),
    }

    collected_data = agent.get_collected_data()
    for field, (icon, label) in fields_info.items():
        value = collected_data.get(field)
        st.markdown(f"**{icon} {label}**")
        if value:
            st.success(value)
        else:
            st.info("Čekám na informaci...")
        st.markdown("")

    st.markdown("---")

    if agent.is_complete():
        st.success("🎉 Všechna data úspěšně získána!")
        st.markdown("### ✅ Souhrn")
        for field, (icon, label) in fields_info.items():
            value = collected_data[field]
            st.text(f"{icon} {label}: {value}")

        st.markdown("---")
        if st.button("📥 Export do JSON", use_container_width=True, type="primary"):
            export_customer_data(collected_data)

        if st.button("🔄 Nový zákazník", use_container_width=True):
            reset_customer_agent()
    else:
        missing = agent.get_missing_fields()
        if missing:
            st.markdown("### 🎯 Ještě potřebuji:")
            for field in missing:
                icon, label = fields_info.get(field, ("📝", field))
                st.markdown(f"- {icon} **{label}**")

        st.markdown("---")
        if st.button("🗑️ Reset", use_container_width=True):
            reset_customer_agent()


def render_customer_chat():
    """Chat interface pro zákaznickou kartu"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "extracted" in message:
                if message["extracted"]:
                    extracted_list = []
                    for k in message["extracted"].keys():
                        emoji_map = {
                            "jmeno": "👤",
                            "email": "📧",
                            "telefon": "📞",
                            "firma": "🏢",
                            "pozice": "💼",
                            "zajem": "🎯",
                        }
                        extracted_list.append(emoji_map.get(k, "📝"))
                    st.caption(f"✨ Získáno: {' '.join(extracted_list)}")

    if prompt := st.chat_input("Napište zprávu..."):
        handle_customer_question(prompt)


def render_database_search_agent():
    """Zobrazení Database Search agenta"""
    st.subheader("🔍 Inteligentní Vyhledávání v Databázi")
    col1, col2 = st.columns([3, 1])

    with col2:
        render_database_sidebar()

    with col1:
        render_database_chat()


def render_database_sidebar():
    """Sidebar pro Database Search"""
    st.markdown("### 📊 Výsledky vyhledávání")

    if "search_agent" not in st.session_state:
        st.warning("Agent není inicializován")
        return

    agent = st.session_state.search_agent
    results = agent.get_last_results()

    if results is None:
        st.info("💡 Zkuste:\n- Najdi Jana\n- Kdo je v IT?\n- pan Horák z Liberce")
        return

    if isinstance(results, dict) and "total_people" in results:
        st.markdown("### 📈 Statistiky databáze")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Celkem", results["total_people"])
            st.metric("Aktivních", results["active_employees"])
        with col_b:
            st.metric("Průměrný plat", f"{results['average_salary']:,} Kč")
            st.metric("Průměrný věk", results["average_age"])
        return

    if isinstance(results, list):
        st.markdown(f"**Nalezeno:** {len(results)} osob")
        if len(results) == 0:
            st.warning("Žádné výsledky")
            return

        if len(results) == 1:
            person = results[0]
            st.markdown("---")
            st.markdown(f"### {person['full_name']}")
            st.text(f"📧 {person['email']}")
            st.text(f"📞 {person['phone']}")
            st.text(f"💼 {person['position']}")
            st.text(f"🏢 {person['department']}")
            st.text(f"📍 {person['location']}")
            st.text(f"💰 {person['salary']:,} Kč")
        else:
            display_count = min(len(results), 10)
            st.caption(f"Zobrazuji prvních {display_count}")
            for person in results[:display_count]:
                with st.expander(f"{person['full_name']} - {person['position']}"):
                    st.text(f"📧 {person['email']}")
                    st.text(f"🏢 {person['department']} | 📍 {person['location']}")

    st.markdown("---")
    if st.button("🗑️ Reset", use_container_width=True):
        agent.reset()
        st.session_state.messages = []
        initial = agent.start_conversation()
        st.session_state.messages = [{"role": "assistant", "content": initial["message"]}]
        st.rerun()


def render_database_chat():
    """Chat interface pro Database Search"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Napište dotaz..."):
        handle_database_question(prompt)


# Handler functions (ponecháno pro ostatní agenty)
def handle_customer_question(prompt):
    agent = st.session_state.collector_agent
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("💭"):
            response = agent.chat(prompt)
            st.markdown(response["message"])
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response["message"],
                    "extracted": response["extracted_fields"],
                }
            )
    st.rerun()


def handle_database_question(prompt):
    agent = st.session_state.search_agent
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍"):
            response = agent.chat(prompt)
            st.markdown(response["message"])
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response["message"],
                }
            )
    st.rerun()


def export_customer_data(data):
    export = {
        "timestamp": datetime.now().isoformat(),
        "agent": "Zákaznická karta",
        "customer_data": data,
    }

    json_str = json.dumps(export, ensure_ascii=False, indent=2)
    st.download_button(
        "💾 Stáhnout",
        json_str,
        f"zakaznik_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        use_container_width=True,
    )


def reset_customer_agent():
    agent = st.session_state.collector_agent
    agent.reset()
    initial_response = agent.start_conversation()
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": initial_response["message"],
            "extracted": initial_response["extracted_fields"],
        }
    ]
    st.rerun()


if __name__ == "__main__":
    main()
