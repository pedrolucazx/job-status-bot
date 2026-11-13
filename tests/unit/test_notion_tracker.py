import unittest
from datetime import date
from unittest.mock import Mock

import requests

from src.bot.main import notify_and_label
from src.bot.notion_tracker import NotionTracker, pick_row, should_update, target_status


def row(empresa, cargo="Dev", status="Aplicado", rid=None, feedback=""):
    return {"id": rid or empresa, "empresa": empresa, "cargo": cargo, "status": status,
            "feedback": [{"plain_text": feedback}] if feedback else []}


def page(r):
    return {"id": r["id"], "properties": {
        "Empresa": {"type": "title", "title": [{"plain_text": r["empresa"]}]},
        "Cargo": {"type": "rich_text", "rich_text": [{"plain_text": r["cargo"]}]},
        "Status": {"type": "select", "select": {"name": r["status"]}},
        "Feedback": {"type": "rich_text", "rich_text": r["feedback"]},
    }}


def fake_session(rows):
    session = Mock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {"results": [page(r) for r in rows], "has_more": False}
    session.patch.return_value.status_code = 200
    session.patch.return_value.json.return_value = {}
    return session


class TestMatching(unittest.TestCase):
    def test_company_words_either_way(self):
        rows = [row("FCamara", "Desenvolvedor(a) Fullstack (Node/React) - Pleno")]
        self.assertEqual(pick_row(rows, "Grupo FCamara", "Fullstack Pleno")["id"], "FCamara")
        self.assertEqual(pick_row([row("Grupo Boticário")], "Boticario", "Dev")["id"], "Grupo Boticário")

    def test_short_names_need_whole_words(self):
        self.assertIsNone(pick_row([row("Raia Drogasil")], "AI", "Dev"))
        self.assertIsNone(pick_row([row("Acme")], "", "Dev"))

    def test_role_breaks_the_tie_between_rows_of_one_company(self):
        rows = [row("FCamara", "Pessoa Desenvolvedora Backend Java Microsserviços - Pleno", rid="java"),
                row("FCamara", "Desenvolvedor(a) Fullstack (Node/React) - Pleno", rid="node")]
        self.assertEqual(pick_row(rows, "FCamara", "Desenvolvedor Fullstack Node React")["id"], "node")

    def test_tie_writes_nothing(self):
        rows = [row("Acme", "Backend Pleno", rid="a"), row("Acme", "Frontend Pleno", rid="b")]
        self.assertIsNone(pick_row(rows, "Acme", "Engenheiro"))

    def test_exact_title_wins(self):
        rows = [row("Brisanet Telecomunicações", "Desenvolvedor(a) de Sistemas | BACKEND", rid="i"),
                row("Brisanet Telecomunicações", "Desenvolvedor(a) de Sistemas | BACKEND II", rid="ii")]
        self.assertEqual(pick_row(rows, "Brisanet", "Desenvolvedor(a) de Sistemas | BACKEND")["id"], "i")

    def test_tie_between_rows_closed_alike_reports_closed(self):
        rows = [row("Acme", "Dev Pleno", status="Rejeitado", rid="a"), row("Acme", "Dev Pleno II", status="Rejeitado", rid="b")]
        self.assertEqual(pick_row(rows, "Acme", "Dev")["status"], "Rejeitado")

    def test_confidential_never_matches(self):
        rows = [row("Confidencial (via Togger)", "Backend Node Pleno"), row("Confidencial (via ASM Talent)", "Frontend"),
                row("Empresa não identificada", "Backend Pleno")]
        self.assertIsNone(pick_row(rows, "Confidencial", "Desenvolvedor Backend Pleno"))
        self.assertIsNone(pick_row(rows, "Empresa não identificada", "Backend Pleno"))
        # The employer is unknown in all of them: manual, never a guess.
        self.assertIsNone(pick_row(rows, "Togger", "Backend Node Pleno"))

    def test_different_employers_sharing_a_word_need_an_exact_key(self):
        rows = [row("Compass UOL", "Node Backend"), row("Grupo UOL", "Front-end")]
        self.assertEqual(pick_row(rows, "UOL", "Engenheiro")["empresa"], "Grupo UOL")
        self.assertIsNone(pick_row([row("Compass UOL", "Node"), row("UOL EdTech", "Node")], "UOL", "Node"))

    def test_company_suffix_is_not_part_of_the_name(self):
        rows = [row("TOTVS", "[Tech] Engenharia de Desenvolvimento de Software Júnior | NodeJs", rid="node"),
                row("TOTVS - Analista", "Analista de Desenvolvimento de Software", status="Rejeitado", rid="analista")]
        self.assertEqual(pick_row(rows, "TOTVS", "Analista de Desenvolvimento de Software")["id"], "analista")
        rows = [row("Grupo Taking", "Desenvolvedor Back-end Pleno", rid="pleno"),
                row("Grupo Taking - Java Jr", "Desenvolvedor(a) Back-end Java (Júnior/Pleno)", rid="java")]
        self.assertEqual(pick_row(rows, "Grupo Taking", "Desenvolvedor(a) Back-end Java (Júnior/Pleno)")["id"], "java")

    def test_same_title_at_two_different_employers(self):
        rows = [row("AP - Amazing People", "Desenvolvedor(a) FullStack Pleno", status="Rejeitado", rid="amazing"),
                row("AP Digital Services", "Desenvolvedor(a) FullStack Pleno", rid="digital")]
        self.assertEqual(pick_row(rows, "AP", "Desenvolvedor(a) FullStack Pleno")["id"], "amazing")

    def test_no_role_in_common_among_several_rows_is_manual(self):
        rows = [row("TOTVS", "Engenharia de Software Júnior NodeJs", rid="a"),
                row("TOTVS", "Engenharia de Software FullStack Typescript", status="Rejeitado", rid="b")]
        self.assertIsNone(pick_row(rows, "TOTVS", "Analista de Sistemas"))

    def test_generic_role_words_do_not_confirm_a_partial_match(self):
        self.assertIsNone(pick_row([row("Vem ser GX2", "Desenvolvedor Pleno")], "GX2", "Engenheiro de Software Pleno"))

    def test_partial_company_needs_role_overlap(self):
        self.assertIsNone(pick_row([row("Beyond Soluções", "Node PIX")], "Beyond Co.", "Engenheiro de Software II"))
        self.assertEqual(pick_row([row("Vem ser GX2", "Fullstack Developer Java")], "GX2", "Fullstack Developer")["empresa"],
                         "Vem ser GX2")

    def test_reapplication_prefers_the_open_row(self):
        rows = [row("Acme", "Dev Pleno", status="Rejeitado", rid="old"), row("Acme", "Dev Pleno", rid="new")]
        self.assertEqual(pick_row(rows, "Acme", "Dev Pleno")["id"], "new")


class TestStatus(unittest.TestCase):
    def test_target(self):
        self.assertEqual(target_status({"resultado": "rejeitado"}), "Rejeitado")
        self.assertEqual(target_status({"resultado": "avancou", "proxima_etapa": "teste técnico online"}), "Teste técnico")
        self.assertEqual(target_status({"resultado": "avancou", "proxima_etapa": "conversa com RH"}), "Entrevista cultural")
        self.assertEqual(target_status({"resultado": "avancou", "proxima_etapa": "teste de perfil comportamental"}), "Entrevista cultural")
        for step in ("teste prático", "teste online na HackerRank", "coding challenge"):
            self.assertEqual(target_status({"resultado": "avancou", "proxima_etapa": step}), "Teste técnico", step)
        self.assertIsNone(target_status({"resultado": "indefinido"}))

    def test_never_regresses(self):
        self.assertFalse(should_update("Rejeitado", "Entrevista cultural"))
        self.assertFalse(should_update("Posição fechada", "Rejeitado"))
        self.assertFalse(should_update("Teste técnico", "Entrevista cultural"))
        self.assertTrue(should_update("Aplicado", "Entrevista cultural"))
        self.assertTrue(should_update("Teste técnico", "Rejeitado"))
        self.assertTrue(should_update("Congelado", "Rejeitado"))


class TestUpdate(unittest.TestCase):
    VERDICT = {"resultado": "rejeitado", "empresa": "Grupo FCamara", "cargo": "Fullstack Pleno",
               "evidencia": "optamos por não avançar"}

    def test_disabled_without_token(self):
        self.assertIsNone(NotionTracker(token="", data_source_id="ds", session=Mock()).update(self.VERDICT))

    def test_updates_status_and_appends_feedback(self):
        session = fake_session([row("FCamara", "Fullstack Pleno", feedback="Score real 74%.")])
        line = NotionTracker("t", "ds", session).update(self.VERDICT, message_id="m1", today=date(2026, 11, 13))
        self.assertEqual(line, "Notion: Aplicado → Rejeitado.")
        props = session.patch.call_args.kwargs["json"]["properties"]
        self.assertEqual(props["Status"], {"select": {"name": "Rejeitado"}})
        self.assertEqual(props["Feedback"]["rich_text"][-1]["text"]["content"],
                         "\n2026-11-13 (bot, e-mail m1): optamos por não avançar")

    def test_existing_feedback_keeps_links_and_bold(self):
        item = {"type": "text", "text": {"content": "x", "link": {"url": "mailto:a@b.c"}},
                "annotations": {"bold": True}, "plain_text": "x", "href": "mailto:a@b.c"}
        r = row("FCamara", "Fullstack Pleno")
        r["feedback"] = [item]
        session = fake_session([r])
        NotionTracker("t", "ds", session).update(self.VERDICT, message_id="m1")
        first = session.patch.call_args.kwargs["json"]["properties"]["Feedback"]["rich_text"][0]
        self.assertEqual(first, {"type": "text", "text": {"content": "x", "link": {"url": "mailto:a@b.c"}},
                                 "annotations": {"bold": True}})

    def test_mentions_are_written_back_as_text(self):
        r = row("FCamara", "Fullstack Pleno")
        r["feedback"] = [{"type": "mention", "mention": {"type": "link_preview", "link_preview": {"url": "u"}},
                          "annotations": {"bold": False}, "plain_text": "u", "href": "u"}]
        session = fake_session([r])
        NotionTracker("t", "ds", session).update(self.VERDICT, message_id="m1")
        first = session.patch.call_args.kwargs["json"]["properties"]["Feedback"]["rich_text"][0]
        self.assertEqual(first, {"type": "text", "text": {"content": "u"}, "annotations": {"bold": False}})

    def test_second_write_on_the_same_row_in_one_run_is_valid(self):
        session = fake_session([row("FCamara", "Fullstack Pleno")])
        tracker = NotionTracker("t", "ds", session)
        advance = {**self.VERDICT, "resultado": "avancou", "proxima_etapa": "conversa com RH", "evidencia": "convite"}
        tracker.update(advance, message_id="m1")
        tracker.update({**advance, "proxima_etapa": "teste técnico", "evidencia": "convite 2"}, message_id="m2")
        second = session.patch.call_args.kwargs["json"]["properties"]
        self.assertEqual(second["Status"], {"select": {"name": "Teste técnico"}})
        self.assertNotIn({}, second["Feedback"]["rich_text"])
        self.assertTrue(all("plain_text" not in item for item in second["Feedback"]["rich_text"]))

    def test_closed_row_gets_no_write_at_all(self):
        session = fake_session([row("FCamara", "Fullstack Pleno", status="Rejeitado")])
        line = NotionTracker("t", "ds", session).update(self.VERDICT, message_id="m1")
        self.assertEqual(line, "Notion: já estava em Rejeitado, nada escrito.")
        session.patch.assert_not_called()

    def test_retry_with_a_different_quote_does_not_duplicate(self):
        session = fake_session([row("FCamara", "Fullstack Pleno", status="Entrevista cultural",
                                    feedback="2026-11-13 (bot, e-mail m1): optamos por não avançar")])
        verdict = {**self.VERDICT, "resultado": "avancou", "proxima_etapa": "", "evidencia": "outro recorte"}
        self.assertIn("nada a mudar", NotionTracker("t", "ds", session).update(verdict, message_id="m1"))
        session.patch.assert_not_called()

    def test_rows_fetched_once_per_run(self):
        session = fake_session([row("FCamara", "Fullstack Pleno"), row("Acme", "Dev")])
        tracker = NotionTracker("t", "ds", session)
        tracker.update(self.VERDICT, message_id="m1")
        tracker.update({**self.VERDICT, "empresa": "Acme", "cargo": "Dev"}, message_id="m2")
        self.assertEqual(session.post.call_count, 1)
        # the cache reflects the first write: a second verdict on the same row is a no-op
        self.assertIn("nada escrito", tracker.update(self.VERDICT, message_id="m3"))

    def test_rate_limit_is_retried_once(self):
        session = fake_session([row("FCamara", "Fullstack Pleno")])
        limited = Mock(status_code=429, headers={"Retry-After": "0"})
        session.patch.side_effect = [limited, session.patch.return_value]
        sleeps = []
        line = NotionTracker("t", "ds", session, sleep=sleeps.append).update(self.VERDICT, message_id="m1")
        self.assertEqual(line, "Notion: Aplicado → Rejeitado.")
        self.assertEqual(sleeps, [0.0])

    def test_miss_asks_for_manual_update(self):
        session = fake_session([row("Outra Empresa")])
        self.assertIn("não encontrada", NotionTracker("t", "ds", session).update(self.VERDICT))
        session.patch.assert_not_called()

    def test_api_failure_is_reported_not_raised(self):
        session = Mock()
        session.post.side_effect = requests.ConnectionError("https://api.notion.com?token=secret")
        line = NotionTracker("t", "ds", session).update(self.VERDICT)
        self.assertEqual(line, "Notion: falhou, atualize à mão.")
        self.assertNotIn("secret", line)


class TestWiring(unittest.TestCase):
    def test_notion_line_goes_in_the_message(self):
        tracker, notifier = Mock(), Mock()
        tracker.update.return_value = "Notion: Aplicado → Rejeitado."
        notify_and_label({"job_related": True, "resultado": "rejeitado", "empresa": "A", "cargo": "B"},
                         Mock(), notifier, "msg", tracker=tracker)
        self.assertIn("Notion: Aplicado → Rejeitado.", notifier.send_message.call_args.args[0])

    def test_no_verdict_no_notion_call(self):
        tracker = Mock()
        notify_and_label({"job_related": True, "resultado": "indefinido"}, Mock(), Mock(), "msg", tracker=tracker)
        tracker.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
