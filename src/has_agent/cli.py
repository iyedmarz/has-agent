"""Command line interface: has-agent {status,ingest,ask,chat,eval}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from has_agent.config import get_settings

DISCLAIMER = "Aide à la recherche documentaire — ne remplace pas l'avis d'un professionnel de santé."


def _print_answer(answer) -> None:
    print()
    if answer.verdict:
        print(f"\n[vérification : {answer.verdict}]")
        for claim in answer.unsupported_claims:
            print(f"  ! non soutenu : {claim}")
    shown = answer.cited or list(range(1, len(answer.hits) + 1))
    print("\nSources :")
    for n in shown:
        hit = answer.hits[n - 1]
        print(f"  [{n}] {hit.title} — {hit.source}, p.{hit.page}")
    print(f"\n({answer.seconds:.1f}s) {DISCLAIMER}")


def cmd_status(_args) -> int:
    from has_agent.llm import LocalLLM

    settings = get_settings()
    print(f"Ollama host : {settings.ollama_host}")
    try:
        installed = LocalLLM(settings).installed_models()
    except Exception as exc:  # connection refused, etc.
        print(f"Cannot reach Ollama: {exc}\nStart it with: ollama serve")
        return 1
    ok = True
    for role, name in (("LLM", settings.llm_model), ("Embeddings", settings.embed_model)):
        present = any(m == name or m.startswith(f"{name}:") for m in installed)
        print(f"{role:<11}: {name} -> {'OK' if present else f'missing (ollama pull {name})'}")
        ok &= present
    pdfs = list(settings.pdf_dir.glob("*.pdf"))
    print(f"PDFs        : {len(pdfs)} in {settings.pdf_dir}")
    return 0 if ok else 1


def cmd_ingest(args) -> int:
    from has_agent.ingest import ingest

    stats = ingest(get_settings(), reset=args.reset)
    print(f"Done: {stats['documents']} new documents, {stats['chunks']} chunks, "
          f"{stats['skipped']} skipped.")
    return 0


def cmd_ask(args) -> int:
    from has_agent.agent import HASAgent

    agent = HASAgent()
    answer = agent.ask(
        args.question,
        top_k=args.top_k,
        verify=not args.no_verify,
        on_token=lambda t: print(t, end="", flush=True),
    )
    _print_answer(answer)
    return 0


def cmd_chat(args) -> int:
    from has_agent.agent import HASAgent

    agent = HASAgent()
    history: list[dict] = []
    print("HAS agent (100% local). Ctrl+C or empty line to quit.\n")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            break
        answer = agent.ask(question, history=history, top_k=args.top_k,
                           on_token=lambda t: print(t, end="", flush=True))
        _print_answer(answer)
        history += [{"role": "user", "content": question},
                    {"role": "assistant", "content": answer.text}]
        print()
    return 0


def cmd_eval(args) -> int:
    from has_agent.agent import HASAgent
    from has_agent.evaluate import run_eval

    result = run_eval(HASAgent(), Path(args.questions), args.answers, args.top_k or 6)
    print(json.dumps(result["summary"], indent=2))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Detailed report: {out}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="has-agent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="check Ollama, models and PDFs").set_defaults(func=cmd_status)

    p = sub.add_parser("ingest", help="index PDFs from data/pdfs")
    p.add_argument("--reset", action="store_true", help="rebuild the index from scratch")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("ask", help="ask one question")
    p.add_argument("question")
    p.add_argument("--top-k", type=int)
    p.add_argument("--no-verify", action="store_true", help="skip the groundedness check")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("chat", help="interactive conversation")
    p.add_argument("--top-k", type=int)
    p.set_defaults(func=cmd_chat)

    p = sub.add_parser("eval", help="evaluate on a questions file")
    p.add_argument("questions")
    p.add_argument("--answers", action="store_true", help="also generate and check answers")
    p.add_argument("--top-k", type=int)
    p.add_argument("--out", default="eval/report.json")
    p.set_defaults(func=cmd_eval)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
