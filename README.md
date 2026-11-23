# HAS Agent: a 100 % local assistant for Haute Autorité de Santé documents

Ask questions in French about HAS publications (recommandations, guides ALD, rapports
d'évaluation…) and get answers **with the document and page cited for every claim**.
Everything runs on your own computer through [Ollama](https://ollama.com): no cloud API,
no data leaving the machine.

> **Not a medical device.** This is a documentation search aid. It must not be used to
> diagnose or to make clinical decisions.

---

## 1. What you need

| Requirement | Notes |
|---|---|
| **Python 3.10 – 3.12** | Standard Windows / Mac / Linux Python from python.org. |
| **Ollama** | Download from <https://ollama.com>, install it and make sure it is running. |
| **RAM / GPU** | 16 GB RAM is comfortable. A GPU is optional but makes answers faster. |
| **HAS PDFs** | Public documents from <https://www.has-sante.fr> (no account needed). |
| **Internet** | Only for the one-off downloads (Python packages and Ollama models). |

---

## 2. Install (one time)

Open a terminal in the project folder (the one containing `pyproject.toml`).

**Step 1: create and activate a virtual environment**

| Terminal | Commands |
|---|---|
| Windows PowerShell | `python -m venv .venv` then `.venv\Scripts\Activate.ps1` |
| Windows Git Bash / MSYS2 | `python -m venv .venv` then `source .venv/Scripts/activate` |
| Mac / Linux | `python -m venv .venv` then `source .venv/bin/activate` |

When it works, your prompt starts with `(.venv)`.

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

---

## 3. Choose the chat model

The default model in the code is `qwen2.5:7b-instruct`. Tell the project which model you
pulled with an environment variable. **Set it again in every new terminal.**

| Terminal | Command |
|---|---|
| PowerShell | `$env:HAS_LLM_MODEL="qwen3.5:4b"` |
| Git Bash / Mac / Linux | `export HAS_LLM_MODEL=qwen3.5:4b` |

On Windows, also avoid accent-encoding problems:

| Terminal | Command |
|---|---|
| PowerShell | `$env:PYTHONUTF8="1"` |
| Git Bash | `export PYTHONUTF8=1` |

Model suggestions by hardware:

| Your machine | Chat model |
|---|---|
| 8 GB RAM, no GPU | `qwen2.5:3b-instruct` |
| 16 GB RAM, 4 GB VRAM | `qwen3.5:4b` (or `qwen2.5:7b-instruct`, slower: part runs on CPU) |
| 32 GB RAM or a 12 GB+ GPU | `qwen2.5:14b-instruct` or a Mistral model |

> **Known limitation with Qwen3 / Qwen3.5 models:** they can print their reasoning inside
> `<think>…</think>` tags, which may appear in answers or break the verification banner. The
> thinking-mode handling is not implemented yet. If you see this, switch to a
> `qwen2.5` model or ask for the fix.

---

## 4. Add your documents

Copy HAS **PDF** files into `data/pdfs/`.

- Start with 3 to 5 documents on related topics: it makes a better demo and an easier evaluation.
- Only `.pdf` files are read (a `.txt` copy is ignored).
- Scanned PDFs (images of pages) have no text and are skipped with a warning. They need OCR.

---

## 5. Run it

**Check that everything is ready**

```bash
has-agent status
```

You should see the Ollama address, both models marked `OK` and the number of PDFs found.

**Build the index (once, and again whenever you add PDFs)**

```bash
has-agent ingest
```

Each file prints a line such as `+ file.pdf: 12 pages, 34 chunks`. Files already indexed are
skipped. Use `has-agent ingest --reset` to rebuild everything from scratch.

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

Add `--no-verify` to `ask` to skip the verification step and answer faster.

---

## 6. Questions that work well

- "Quels professionnels sont impliqués dans le parcours de soins ?"
- "Quelle commission de la HAS évalue les produits avant remboursement ?"
- "Que dit la recommandation sur [un médicament ou un acte] ?"
- Follow-ups in `chat` mode: "Et pour les enfants ?"

Try also a question that is **not** in your documents. The expected reply is
*« Je ne trouve pas cette information dans les documents indexés. »*

Do not ask it to diagnose ("quelle maladie ai-je ?"). It is built to quote documents, and a
dedicated refusal for diagnosis requests is on the roadmap.

---

## 7. Measure the quality

Edit `eval/questions.json` (examples are included) so each question names the PDF that should
answer it and a keyword the answer must contain. Then:

```bash
has-agent eval eval/questions.json             # retrieval only (fast)
has-agent eval eval/questions.json --answers   # also checks answers and groundedness
```

It prints hit@k, MRR and, with `--answers`, keyword recall and the share of fully grounded
answers. A detailed report is saved to `eval/report.json`. To compare two models, run it once
per model by changing `HAS_LLM_MODEL`.

---

## 8. Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `HAS_LLM_MODEL` | `qwen2.5:7b-instruct` | Chat model |
| `HAS_EMBED_MODEL` | `bge-m3` | Embedding model |
| `HAS_TOP_K` | `6` | Excerpts given to the model |
| `HAS_NUM_CTX` | `8192` | Model context size (lower it, e.g. `6144`, on small machines) |
| `HAS_CHUNK_CHARS` | `1200` | Chunk size at indexing (re-run `ingest --reset` after changing) |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama address (non-local addresses are refused) |
| `HAS_ALLOW_REMOTE` | off | Set to `1` only if you deliberately use a remote server |
| `HAS_AUDIT_LOG_QUESTIONS` | `1` | Set to `0` to keep questions out of the audit log |
| `HAS_DATA_DIR` | `./data` | Where PDFs, index and audit log live |

Every question is recorded in `data/audit.jsonl` on your machine only (sources, verdict,
models, duration).

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `has-agent: command not found` | Activate the virtual environment, run `hash -r`, or use `python -m has_agent …` |
| `Cannot reach Ollama` | Start the Ollama app or run `ollama serve` |
| A model shows as `missing` in `status` | Run the `ollama pull …` command it prints |
| `No PDF found` | Put `.pdf` files in `data/pdfs/` |
| `no extractable text (scanned PDF?)` | The PDF is an image; it needs OCR |
| `fontTools is required…` warnings | Harmless. Run `pip install fonttools` to silence them |
| `streamlit: command not found` | Use `python -m streamlit run src/has_agent/ui.py` |
| Very slow answers | Use a smaller model, set `HAS_TOP_K=4` and `HAS_NUM_CTX=6144`, or turn verification off |
| Answers contain `<think>` text | See the Qwen3 note in section 3 |
| Index looks stale after replacing a PDF | Run `has-agent ingest --reset` |

---

## 10. How it works

```
 PDFs ──► page-aware chunking ──► bge-m3 embeddings ──► ChromaDB (local)
                                                            │
 question ─► (rewrite if follow-up) ─► hybrid search: dense + BM25 + RRF
                                                            │
                         grounded prompt ─► local LLM ─► answer with [n] citations
                                                            │
                               groundedness check ─► verdict ─► audit log (JSONL)
```

| Concern | Design choice |
|---|---|
| Data must stay private | Ollama only; non-local hosts are refused by default |
| Hallucinations | Answers only from retrieved excerpts, mandatory `[n]` citations, explicit "not found" reply |
| Exact medical terms | Hybrid retrieval: semantic vectors plus BM25 keywords, merged with Reciprocal Rank Fusion |
| Trust but verify | A second model pass labels each answer `supported`, `partially_supported` or `unsupported` |
| Traceability | Local append-only audit log |
| Measurability | Evaluation harness with hit@k, MRR, keyword recall, grounded rate |

```
src/has_agent/
  config.py      settings and the local-only guard
  ingest.py      PDF → pages → chunks → embeddings → ChromaDB
  chunking.py    page-aware chunking
  retrieval.py   hybrid search
  agent.py       rewrite → retrieve → answer → verify → audit
  prompts.py     French prompts
  evaluate.py    evaluation metrics
  audit.py       local audit log
  cli.py / ui.py command line and Streamlit interface
tests/           unit tests (run with: pytest)
docs/PROPOSAL.md one-page pitch for a recruiter
```

---

## 11. Limitations and roadmap

- French questions on English documents work through the multilingual embeddings, but keyword
  matching does not help across languages.
- Tables lose their structure and scanned PDFs need OCR.
- The verification is done by an LLM, so it is a safety net, not a guarantee.
- No reranker yet; a local cross-encoder is the next retrieval upgrade.
- To add: refusal of diagnosis requests, thinking-mode handling for Qwen3 models, document
  date and grade metadata with filters.

HAS documents are not included in this repository. Check HAS's reuse conditions on
has-sante.fr before redistributing any document or derived index.
