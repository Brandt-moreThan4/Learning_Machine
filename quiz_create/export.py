# email_quizzer/export.py
from pathlib import Path
import json, html

def jsonl_to_html(jsonl_path: str, out_path: str | None = None) -> str:
    p = Path(jsonl_path); out = Path(out_path or p.with_suffix(".html"))
    items = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]
    body = []
    for i, q in enumerate(items, 1):
        if q["kind"] == "mcq":
            opts = [q["answer"]] + q["distractors"]
            lis = "".join(f"<li>{html.escape(o)}</li>" for o in opts)
            body.append(f"<h3>{i}. {html.escape(q['question'])}</h3><ol>{lis}</ol>")
        else:
            body.append(f"<h3>{i}. {html.escape(q['question'])}</h3>")
    html_doc = f"<!doctype html><meta charset='utf-8'><body>{''.join(body)}</body>"
    out.write_text(html_doc, encoding="utf-8")
    return str(out)
