"""Parse a saved ChatGPT share page (rendered DOM) into a verbatim JSON export."""
import json, re, sys, datetime as dt
from html.parser import HTMLParser

VOID = {"br","img","input","hr","meta","link","source","wbr","path","circle","rect","line","use"}
BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "tr", "ul", "ol", "pre", "table"}

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.turns, self.cur, self.depth, self.skip = [], None, 0, 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "svg", "button"):
            self.skip += 1
        if "data-message-author-role" in a and self.cur is None:
            self.cur = {"role": a["data-message-author-role"], "buf": []}; self.depth = 1; return
        if self.cur is not None:
            if tag not in VOID: self.depth += 1
            if tag in BLOCK: self.cur["buf"].append("\n")
            if tag == "li": self.cur["buf"].append("- ")
    def handle_endtag(self, tag):
        if tag in VOID: return
        if tag in ("script", "style", "svg", "button") and self.skip: self.skip -= 1
        if self.cur is not None:
            self.depth -= 1
            if tag in BLOCK: self.cur["buf"].append("\n")
            if self.depth == 0:
                t = re.sub(r"\n{3,}", "\n\n", "".join(self.cur["buf"])).strip()
                self.turns.append({"role": self.cur["role"], "text": t}); self.cur = None
    def handle_data(self, d):
        if self.cur is not None and not self.skip: self.cur["buf"].append(d)

p = P(); p.feed(open(sys.argv[1], encoding="utf-8", errors="replace").read())
out = {"tool": "ChatGPT", "title": "Prototype recommendation", "source": "https://chatgpt.com/share/6ae32cc9-fa3c-83eb-98ef-c07e7b8e125c",
       "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "note": "Verbatim text of the shared conversation (formatting flattened).", "turns": p.turns}
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print([(t["role"], len(t["text"])) for t in p.turns])
