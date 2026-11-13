"""notion_tracker.py — move the application in the Notion tracker on a verdict.

See specs/002-atualizar-notion/spec.md. Matching is deliberately strict: a
wrong match edits someone else's row, so a tie or a miss writes nothing and
the Telegram message asks for a manual update instead.
"""
import os
import re
import time
import unicodedata
from datetime import date

import requests

API = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"
TIMEOUT = 30

GENERIC_WORDS = {"grupo", "group", "ltda", "sa", "s", "a", "me", "eireli", "inc", "co",
                 "tecnologia", "technologies", "tech", "brasil", "brazil", "de", "da", "do",
                 "e", "the"}
# Words that say nothing about who the employer is. "Confidencial (via e3
# Consultoria RH)" keys on "e3"; "Confidencial" or "Empresa não identificada"
# alone key on nothing and never match.
WEAK_WORDS = {"confidencial", "nao", "identificada", "empresa", "via", "cliente",
              "consultoria", "rh", "recrutamento", "talent", "talentos"}
# A row in one of these is over: a late e-mail must not touch it.
FINAL = {"Rejeitado", "Posição fechada", "Aceito", "Desisti", "Referência para colega"}
ORDER = {"Aplicado": 0, "Congelado": 0, "Sumiu": 0, "Entrevista cultural": 1, "Teste técnico": 2}
# Not bare "teste": "teste de perfil/DISC/inglês" is not a technical round.
TECHNICAL = re.compile(r"t[eé]cnic|desafio|live ?coding|coding|technical|teste (?:pr[aá]tico|online)|"
                       r"hackerrank|codility|coderbyte|challenge", re.I)
# Role words that almost every row shares: they can't confirm a match.
GENERIC_ROLE_WORDS = {"desenvolvedor", "desenvolvedora", "pessoa", "developer", "engenheiro", "engenheira",
                      "engineer", "software", "pleno", "junior", "senior", "analista", "remoto", "remote",
                      "vaga", "para", "com", "and", "the"}
# "TOTVS - Analista", "Stefanini (Fullstack Java)", "Contato Seguro | Canal de Denúncias":
# the employer is the part before the first separator.
COMPANY_SUFFIX = re.compile(r"\s+(?:\(|\||-|–)\s*.*$")
READ_ONLY_RICH_TEXT = ("plain_text", "href")


def _words(text):
    plain = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return [w for w in re.split(r"[^a-z0-9]+", plain) if w]


def company_key(name):
    base = COMPANY_SUFFIX.sub("", name or "")
    return frozenset(w for w in _words(base) if w not in GENERIC_WORDS | WEAK_WORDS)


def same_company(a, b):
    """Whole words, either way round: "Grupo FCamara" ~ "FCamara", never "AI" ~ "Raia"."""
    return bool(a and b) and (a <= b or b <= a)


def role_words(role):
    return {w for w in _words(role) if len(w) > 2 and w not in GENERIC_ROLE_WORDS}


def target_status(result):
    if result.get("resultado") == "rejeitado":
        return "Rejeitado"
    if result.get("resultado") == "avancou":
        return "Teste técnico" if TECHNICAL.search(result.get("proxima_etapa") or "") else "Entrevista cultural"
    return None


def should_update(current, new):
    if current in FINAL:
        return False
    if new == "Rejeitado":
        return True
    return ORDER.get(new, 0) > ORDER.get(current, 0)


def pick_row(rows, empresa, cargo):
    """rows: [{'id', 'empresa', 'cargo', 'status', ...}]. The one row, or None on a miss or a tie."""
    wanted = company_key(empresa)
    candidates = [r for r in rows if same_company(wanted, company_key(r["empresa"]))]
    keys = {company_key(r["empresa"]) for r in candidates}
    if len(keys) > 1:
        # Different employers share a word ("UOL" / "Compass UOL", "AP" / "AP
        # Digital Services"): only an exact company key settles it, never the role.
        candidates = [r for r in candidates if company_key(r["empresa"]) == wanted]
    if not candidates:
        return None
    # Same title, word for word ("BACKEND" vs "BACKEND II"), decides within the company.
    exact = [r for r in candidates if _words(r["cargo"]) == _words(cargo)]
    if exact:
        return _one(exact)
    wanted_role = role_words(cargo)
    if company_key(candidates[0]["empresa"]) != wanted:
        # Partial company match ("GX2" ~ "Vem ser GX2"): the role must agree too.
        candidates = [r for r in candidates if wanted_role & role_words(r["cargo"])]
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    best = max(len(wanted_role & role_words(r["cargo"])) for r in candidates)
    if best == 0:
        return None  # several rows, no role in common: any pick would be a guess
    return _one([r for r in candidates if len(wanted_role & role_words(r["cargo"])) == best])


def _one(top):
    """Settle a tie between equally good rows, or give up."""
    if len(top) > 1:
        # Re-application of the same role: the open row is the live process.
        open_rows = [r for r in top if r["status"] not in FINAL]
        if not open_rows and len({r["status"] for r in top}) == 1:
            return top[0]  # all closed the same way; update() writes nothing to a closed row
        top = open_rows
    return top[0] if len(top) == 1 else None


def _plain(prop):
    kind = (prop or {}).get("type")
    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in prop[kind])
    if kind == "select":
        return ((prop.get("select") or {}).get("name")) or ""
    return ""


def _writable(item):
    """A rich_text item as read, minus the read-only keys, so links and bold survive a rewrite.
    Mentions become plain text: some kinds (link_preview) can't be created through the API."""
    if item.get("type") == "mention":
        return {"type": "text", "text": {"content": item.get("plain_text", "")},
                **({"annotations": item["annotations"]} if "annotations" in item else {})}
    return {k: v for k, v in item.items() if k not in READ_ONLY_RICH_TEXT}


class NotionTracker:
    def __init__(self, token=None, data_source_id=None, session=None, sleep=time.sleep):
        # None means "read the environment"; an explicit "" means "disabled".
        self.token = os.getenv("NOTION_TOKEN") if token is None else token
        self.data_source_id = os.getenv("NOTION_DATA_SOURCE_ID") if data_source_id is None else data_source_id
        self.session = session or requests.Session()
        self.sleep = sleep
        self._cache = None  # rows, fetched once per run

    @property
    def enabled(self):
        return bool(self.token and self.data_source_id)

    def _request(self, method, url, body):
        headers = {"Authorization": f"Bearer {self.token}", "Notion-Version": NOTION_VERSION,
                   "Content-Type": "application/json"}
        for attempt in range(2):
            resp = getattr(self.session, method)(url, json=body, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 429 and attempt == 0:
                self.sleep(min(float(resp.headers.get("Retry-After", 1)), 10))
                continue
            resp.raise_for_status()
            return resp.json()
        return None  # unreachable: the second attempt raises or returns

    def _rows(self):
        if self._cache is not None:
            return self._cache
        rows, cursor = [], None
        while True:
            body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
            payload = self._request("post", f"{API}/data_sources/{self.data_source_id}/query", body)
            for page in payload["results"]:
                props = page["properties"]
                rows.append({"id": page["id"], "empresa": _plain(props.get("Empresa")),
                             "cargo": _plain(props.get("Cargo")), "status": _plain(props.get("Status")),
                             "feedback": (props.get("Feedback") or {}).get("rich_text", [])})
            if not payload.get("has_more"):
                self._cache = rows
                return rows
            cursor = payload["next_cursor"]

    def update(self, result, message_id="", today=None):
        """Apply the verdict. Returns a one-line, user-facing summary for the Telegram message."""
        new_status = target_status(result)
        if not self.enabled or not new_status:
            return None
        try:
            row = pick_row(self._rows(), result.get("empresa", ""), result.get("cargo", ""))
            if row is None:
                return "Notion: candidatura não encontrada, atualize à mão."
            if row["status"] in FINAL:
                return f"Notion: já estava em {row['status']}, nada escrito."
            evidence = " ".join((result.get("evidencia") or "").split())[:1500]
            written = "".join(p.get("plain_text", "") for p in row["feedback"])
            # The Gemini quote can differ on a retry; the e-mail id doesn't.
            marker = f"(bot, e-mail {message_id})" if message_id else "(bot)"
            already_noted = (message_id and marker in written) or (evidence and evidence in written)
            properties = {}
            if should_update(row["status"], new_status):
                properties["Status"] = {"select": {"name": new_status}}
            if evidence and not already_noted:
                note = f"\n{(today or date.today()).isoformat()} {marker}: {evidence}"
                feedback = [_writable(p) for p in row["feedback"]] + [{"type": "text", "text": {"content": note}}]
                properties["Feedback"] = {"rich_text": feedback}
            if not properties:
                return f"Notion: já estava em {row['status']}, nada a mudar."
            self._request("patch", f"{API}/pages/{row['id']}", {"properties": properties})
            previous = row["status"]
            if "Status" in properties:
                row["status"] = new_status
            if "Feedback" in properties:
                added = properties["Feedback"]["rich_text"][-1]
                row["feedback"] = row["feedback"] + [{**added, "plain_text": added["text"]["content"]}]
            if "Status" in properties:
                return f"Notion: {previous or 'sem status'} → {new_status}."
            return f"Notion: mantido em {previous}, trecho anotado no Feedback."
        except (requests.RequestException, KeyError, ValueError, TypeError):
            # Never log the exception: request details can include the token.
            return "Notion: falhou, atualize à mão."
