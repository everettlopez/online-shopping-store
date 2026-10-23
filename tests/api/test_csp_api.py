import json

import pytest


def report_uri_report(**fields):
    """A violation as browsers send it to the CSP's report-uri."""
    return {"csp-report": {
        "document-uri": "https://shop.example.com/products",
        "effective-directive": "script-src-elem",
        "blocked-uri": "https://evil.example/x.js",
        "source-file": "https://shop.example.com/assets/index.js",
        **fields,
    }}


def send(client, report, content_type="application/csp-report", **headers):
    body = report if isinstance(report, (bytes, str)) else json.dumps(report)
    return client.post("/api/csp-report", content=body, headers={"Content-Type": content_type, **headers})


def test_a_violation_is_logged(client, caplog):
    caplog.set_level("INFO")

    response = send(client, report_uri_report())

    assert response.status_code == 204
    assert ("csp violation directive=script-src-elem blocked=https://evil.example/x.js "
            "page=https://shop.example.com/products source=https://shop.example.com/assets/index.js") in caplog.text


def test_reporting_api_format_is_logged_too(client, caplog):
    caplog.set_level("INFO")
    reports = [
        {"type": "csp-violation", "body": {"documentURL": "https://shop.example.com/cart",
                                           "effectiveDirective": "img-src", "blockedURL": "https://cdn.example/a.png"}},
        {"type": "deprecation", "body": {"message": "not ours"}},
    ]

    assert send(client, reports, "application/reports+json").status_code == 204
    assert "directive=img-src blocked=https://cdn.example/a.png page=https://shop.example.com/cart" in caplog.text
    assert "not ours" not in caplog.text


def test_tokens_in_addresses_stay_out_of_the_logs(client, caplog):
    caplog.set_level("INFO")

    send(client, report_uri_report(**{"document-uri": "https://shop.example.com/track/ab12?token=secret-token#top"}))

    assert "page=https://shop.example.com/track/ab12 " in caplog.text
    assert "secret-token" not in caplog.text


def test_keywords_pass_through(client, caplog):
    caplog.set_level("INFO")

    send(client, report_uri_report(**{"blocked-uri": "inline", "effective-directive": "style-src-attr"}))

    assert "directive=style-src-attr blocked=inline " in caplog.text


@pytest.mark.parametrize("body", [b"not json", b"{}", b"[1, 2]", b'{"csp-report": "nope"}'])
def test_anything_else_is_ignored(client, caplog, body):
    caplog.set_level("INFO")

    assert send(client, body).status_code == 204
    assert "csp violation" not in caplog.text


def test_oversized_reports_are_refused(client, monkeypatch):
    monkeypatch.setattr("app.routes.csp.MAX_REPORT_BYTES", 100)

    assert send(client, report_uri_report(**{"blocked-uri": "x" * 200})).status_code == 413


def test_one_burst_logs_a_few_lines(client, caplog):
    caplog.set_level("INFO")
    reports = [{"type": "csp-violation", "body": {"effectiveDirective": "img-src", "blockedURL": f"https://cdn.example/{n}.png"}}
               for n in range(20)]

    send(client, reports, "application/reports+json")

    assert caplog.text.count("csp violation") == 5


def test_any_page_may_send_reports(client):
    # Browsers don't promise reports an Origin the API knows; the endpoint changes nothing
    assert send(client, report_uri_report(), Origin="https://elsewhere.example").status_code == 204
    # Other writes from unknown origins are still refused
    assert client.post("/api/auth/logout", headers={"Origin": "https://elsewhere.example"}).status_code == 403


def test_reports_are_rate_limited(client, monkeypatch):
    monkeypatch.setenv("REPORTS_RATE_LIMIT_PER_MINUTE", "2")

    codes = [send(client, report_uri_report()).status_code for _ in range(3)]

    assert codes == [204, 204, 429]
