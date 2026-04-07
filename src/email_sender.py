"""Send daily digest via Gmail SMTP with App Password."""
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def _load_credentials() -> tuple:
    address = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if address and password:
        return address, password
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GMAIL_ADDRESS="):
                    address = line.split("=", 1)[1]
                elif line.startswith("GMAIL_APP_PASSWORD="):
                    password = line.split("=", 1)[1]
    return address, password


def send_email(subject, body_html, to=None, body_text=None):
    address, password = _load_credentials()
    if not address or not password:
        print("[WARN] email: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set", file=sys.stderr)
        return False
    if not to:
        to = [address]
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Signal Hunter <{address}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(address, password)
            server.sendmail(address, to, msg.as_string())
        print(f"[OK] email: sent to {', '.join(to)}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[WARN] email: failed to send: {e}", file=sys.stderr)
        return False


def send_full_digest(
    date="",
    executive_summary="",
    trending_topics=None,
    ideas=None,
    hackernews=None,
    producthunt=None,
    github_trending=None,
    huggingface=None,
    reddit=None,
    youtube=None,
    twitter=None,
    newsletters=None,
    smolai=None,
    app_charts=None,
    api_tools=None,
    source_status=None,
    to=None,
    **_ignored,
):
    from src.substack_publisher import (
        _build_trending_html, _build_ideas_html, _build_sections,
    )

    trending_topics = trending_topics or []
    ideas = ideas or []

    C2 = "#1e40af"

    topics_html = _build_trending_html(trending_topics)
    ideas_html = _build_ideas_html(ideas)
    sections = _build_sections(
        hackernews=hackernews, producthunt=producthunt,
        github_trending=github_trending, huggingface=huggingface,
        reddit=reddit, youtube=youtube, twitter=twitter,
        newsletters=newsletters, smolai=smolai, api_tools=api_tools,
        app_charts=app_charts, source_status=source_status,
    )

    ideas_block = f"""
        <div style="font-size:15px;font-weight:700;color:{C2};margin:32px 0 18px 0;letter-spacing:0.3px;">IDEAS</div>
        {ideas_html}""" if ideas_html else ""

    # ── Full email ──
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0f172a;">
<div style="max-width:640px;margin:0 auto;background:#ffffff;">

    <div style="background:#f8fafc;padding:40px 28px 32px;text-align:center;border-bottom:3px solid #2563eb;">
        <div style="font-size:14px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#2563eb;">Signal Hunter</div>
        <div style="width:40px;height:2px;background:#2563eb;margin:12px auto;border-radius:1px;"></div>
        <div style="font-size:24px;font-weight:300;color:#0f172a;letter-spacing:-0.3px;">{date}</div>
        <div style="font-size:12px;color:#94a3b8;margin-top:6px;letter-spacing:1px;text-transform:uppercase;">daily digest</div>
    </div>

    <div style="padding:32px 28px;">

        <div style="font-size:15px;line-height:1.8;color:#334155;margin-bottom:32px;padding-bottom:24px;border-bottom:2px solid #dbeafe;">
            {executive_summary}
        </div>

        <div style="font-size:15px;font-weight:700;color:{C2};margin-bottom:18px;letter-spacing:0.3px;">TRENDING SIGNALS</div>
        {topics_html}

        {ideas_block}

        {sections}

    </div>

    <div style="padding:18px 28px;background:#f8fafc;border-top:3px solid #2563eb;text-align:center;">
        <div style="font-size:12px;color:#64748b;">Signal Hunter &mdash; Daily Digest</div>
    </div>

</div></body></html>"""

    return send_email(f"Signal Hunter \u2014 {date}", html, to=to)


send_digest_summary = send_full_digest


if __name__ == "__main__":
    success = send_full_digest(
        date="2026-03-25",
        executive_summary="Test digest. Clean, minimal design with all details.",
        trending_topics=[
            {"emoji": "🆕", "name": "Sora Shutdown", "score": 95, "velocity": "New", "summary": "OpenAI shut down Sora, ended Disney deal.", "sources": "HN, Reddit, YouTube", "newsletters": "The Neuron, AI Secret", "gap": "🟢 GAP — no video AI gateway"},
        ],
        ideas=[
            {"title": "AI Security Scanner", "category": "SaaS", "score": 92, "gap": "No existing tool", "next_step": "Build PoC CLI"},
        ],
        hackernews=[
            {"title": "Goodbye to Sora", "url": "https://example.com", "score": "985 pts", "extra": "734 comments"},
            {"title": "LiteLLM compromised", "url": "https://example.com", "score": "864 pts", "extra": "462 comments"},
        ],
        twitter=[
            {"handle": "bcherny", "likes": "2,648", "text": "Today was a good day"},
        ],
        newsletters=[
            {"sender": "The Neuron", "subject": "Sam Altman dropped safety", "takeaways": "Sora killed, LiteLLM attack, Claude Cowork launched"},
        ],
        source_status=[
            {"name": "HN", "status": "OK", "items": 15},
            {"name": "Reddit", "status": "OK", "items": 17},
            {"name": "X", "status": "OK", "items": 76},
        ],
    )
    print(f"Test: {success}")
