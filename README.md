# HAS Agent: a 100 % local assistant for Haute Autorité de Santé documents

Ask questions about HAS publications (recommandations, guides ALD, rapports
d'évaluation…) and get answers **with the document and page cited for every claim**.
Everything runs on your own computer through Ollama: no cloud API,
no data leaving the machine.

## 1. What you need

 **Python 3.10 – 3.12** : Standard Windows / Mac / Linux Python from python.org
 **Ollama** : Download from <https://ollama.com>, install it
 **RAM / GPU**  :16 GB RAM is comfortable. A GPU is optional but makes answers faster.
 **HAS PDFs**  :Public documents from <https://www.has-sante.fr> 
 **Internet** : Only for the one-off downloads (Python packages and Ollama models).

---

## 2. Install (one time)

Open a terminal in the project folder (the one containing `pyproject.toml`).

**Step 1: create and activate a virtual environment**

Windows PowerShell : **python -m venv .venv` then `.venv\Scripts\Activate.ps1**
Windows Git Bash : **python -m venv .venv` then `source .venv/Scripts/activate**
Mac / Linux : **python -m venv .venv` then `source .venv/bin/activate**

**Step 2: install the project**

```bash
pip install -e ".[dev]"
```

This creates the `has-agent` command. If the shell later says `has-agent: command not found`,
run `hash -r` (bash) or open a new terminal, or use `python -m has_agent` instead of `has-agent`.

**Step 3: download the models (needs internet, one time)**

```bash
ollama pull qwen3.5:4b      # chat model, about 3 GB, good for 4 GB VRAM / 16 GB RAM
ollama pull bge-m3          # embedding model, about 1.2 GB, multilingual
```

## 5. Run it

**Check that everything is ready**

```bash
has-agent status

**Build the index (once, and again whenever you add PDFs)**

```bash
has-agent ingest
```

**Option A: web interface (recommended)**

```bash
streamlit run src/has_agent/ui.py
```

Your browser opens at <http://localhost:8501>. Type a question at the bottom. You get a
streamed answer, a green / orange / red verification banner and an expandable list of sources
with file and page. The sidebar has the number of excerpts used (top-k), a verification switch
and the indexed-chunk count.

**Option B: terminal**

```bash
has-agent ask "Pendant combien de temps l'exonération du ticket modérateur est-elle accordée ?"
has-agent chat          # conversation with follow-up questions, empty line to quit
```

## 6. Questions Examples
  # /eval/questions.example.json

- "Quels professionnels sont impliqués dans le parcours de soins ?"
- "Quelle commission de la HAS évalue les produits avant remboursement ?"
- "Que dit la recommandation sur [un médicament ou un acte] ?"
- Follow-ups in `chat` mode: "Et pour les enfants ?"

Try also a question that is **not** in your documents. The expected reply is
*« Je ne trouve pas cette information dans les documents indexés. »*





