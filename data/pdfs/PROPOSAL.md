# Proposal: a sovereign, local AI agent for HAS documentation

**Prepared by:** [Your name] · **Date:** 20 November 2026 · **Status:** working proof of concept

## The problem
Professionals who rely on Haute Autorité de Santé publications (recommandations de bonne pratique,
avis de la Commission de la Transparence, fiches mémo…) lose time searching long PDFs. Cloud LLMs are
often not an option in healthcare: sensitive context, regulatory constraints and the need for traceable
answers.

## The solution
A document assistant that runs **entirely on local hardware**. It answers in French, **cites the exact
document and page for every claim**, says "not found" when the documents do not contain the answer,
and runs a second pass that flags unsupported statements.

## What already works (proof of concept)
- Local ingestion of HAS PDFs, with page-level provenance
- Hybrid retrieval (semantic + keyword) for both meaning and exact medical terms
- Cited answers via a local LLM served by Ollama, with a groundedness verdict
- Chat interface (Streamlit) and CLI, local audit log
- Evaluation harness reporting retrieval and answer-quality metrics on a question set
- Safeguard that blocks any non-local model endpoint by default

## Architecture
PDF → page-aware chunks → bge-m3 embeddings → ChromaDB → hybrid search (dense + BM25, RRF) →
grounded prompt → local LLM → cited answer → verifier → audit log.
No component calls an external service at query time.

## Risk management
| Risk | Mitigation |
|---|---|
| Hallucinated clinical content | Source-only answering, mandatory citations, verifier, "not found" fallback |
| Data leakage | Local-only inference, non-local host blocked by default, optional question-free audit logs |
| Outdated guidance | Planned: publication date and status metadata, filters and warnings |
| Over-reliance | Persistent disclaimer: documentation aid, not a medical device or clinical decision tool |
| Silent quality drift | Evaluation set run on every model or prompt change |

## Roadmap
1. **Weeks 1–2:** index a real HAS corpus, build a 30-question evaluation set with domain experts
2. **Weeks 3–4:** layout-aware parsing for tables, OCR for scans, local reranker
3. **Weeks 5–6:** metadata filters (date, specialty, document type), multi-document comparison
4. **Weeks 7–8:** access control, packaging (Docker / on-prem), pilot with a few users
5. **Later:** fine-tuned embeddings on French medical text, structured extraction, update pipeline for
   newly published HAS documents

## Open questions for the project owner
- Target hardware (laptop, workstation GPU, on-prem server)? It decides the model size.
- Which document families first (RBP, avis CT, parcours de soins)?
- Required level of traceability and compliance (GDPR, HDS, internal policies)?
- Who validates the evaluation questions?

## Why me
[Add 2–3 lines: your relevant experience, and the fact that you built and tested this proof of
concept yourself, including its evaluation harness and tests.]
