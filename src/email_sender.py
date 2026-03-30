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


def _li(items, numbered=False):
    """Build simple list items."""
    html = ""
    for i, item in enumerate(items):
        title = item.get("title", "")
        url = item.get("url", "")
        score = item.get("score", "")
        extra = item.get("extra", "")
        num = f"{i+1}. " if numbered else ""
        link = f'<a href="{url}" style="color:#2563eb;text-decoration:none;">{title}</a>' if url else title
        meta_parts = [str(score)] if score else []
        if extra:
            meta_parts.append(str(extra))
        meta = f' <span style="color:#9ca3af;font-size:12px;">— {" · ".join(meta_parts)}</span>' if meta_parts else ""
        html += f'<div style="padding:5px 0;font-size:13px;line-height:1.5;">{num}{link}{meta}</div>\n'
    return html


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
    source_status=None,
    to=None,
):
    trending_topics = trending_topics or []
    ideas = ideas or []

    # Brand colors — blue palette from logo
    C = "#2563eb"    # electric blue (primary)
    C2 = "#1e40af"   # deep blue (headings)
    CL = "#3b82f6"   # lighter blue (accents)
    CB = "#eff6ff"   # blue tint background

    # ── Trending Topics ──
    topics_html = ""
    for t in trending_topics:
        score = t.get("score", 0)
        sc = "#1e40af" if score >= 80 else "#3b82f6" if score >= 60 else "#94a3b8"
        topics_html += f"""
        <div style="padding:16px;margin-bottom:10px;background:{CB};border-radius:8px;border-left:4px solid {sc};">
            <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:5px;">{t.get('emoji','')} {t.get('name','')}</div>
            <div style="font-size:11px;color:{sc};font-weight:600;margin-bottom:8px;">{score}/100 &middot; {t.get('velocity','')}{(' &middot; ' + t.get('days','')) if t.get('days') else ''}</div>
            <div style="font-size:13px;color:#334155;line-height:1.65;margin-bottom:8px;">{t.get('summary','')}</div>
            <div style="font-size:11px;color:#64748b;line-height:1.5;">
                {t.get('sources','')}{(' &middot; via ' + t.get('newsletters','')) if t.get('newsletters') else ''}
            </div>
            {'<div style="font-size:11px;color:#059669;font-weight:500;margin-top:5px;">' + t.get('gap','') + '</div>' if t.get('gap') else ''}
        </div>"""

    # ── Ideas ──
    ideas_html = ""
    cat_colors = {"SaaS": "#2563eb", "saas": "#2563eb", "Dev-tools": "#0891b2", "dev-tools": "#0891b2", "Mobile App": "#7c3aed", "App": "#7c3aed", "app": "#7c3aed", "BaaS": "#d97706", "Gaming": "#ea580c"}
    for idea in ideas:
        cc = cat_colors.get(idea.get("category", ""), "#2563eb")
        ideas_html += f"""
        <div style="padding:14px 16px;margin-bottom:12px;background:#f8fafc;border-radius:8px;border-left:4px solid {cc};">
            <div style="font-size:14px;font-weight:600;color:#0f172a;margin-bottom:3px;">{idea.get('title','')}</div>
            <div style="font-size:11px;color:{cc};font-weight:600;margin-bottom:8px;">{idea.get('category','')} &middot; {idea.get('score','')}/100</div>
            <div style="font-size:12px;color:#475569;line-height:1.6;margin-bottom:6px;">{idea.get('problem','')}</div>
            <div style="font-size:12px;color:#475569;line-height:1.6;margin-bottom:6px;">{idea.get('gap','')}</div>
            <div style="font-size:12px;color:#475569;line-height:1.6;margin-bottom:6px;">{idea.get('how','')}</div>
            <div style="font-size:12px;color:#334155;line-height:1.6;"><strong>Next step:</strong> {idea.get('next_step','')}</div>
            <div style="font-size:11px;color:#64748b;margin-top:4px;">{idea.get('revenue','')}</div>
        </div>"""

    # ── Source sections ──
    sections = ""

    def _section(label, items, numbered=True):
        if not items:
            return ""
        return f"""
        <div style="margin-top:28px;">
            <div style="font-size:13px;font-weight:600;color:{C2};margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #dbeafe;">{label}</div>
            {_li(items, numbered=numbered)}
        </div>"""

    sections += _section("Hacker News", hackernews)
    sections += _section("Product Hunt", producthunt, numbered=False)
    sections += _section("GitHub Trending", github_trending)
    sections += _section("HuggingFace Papers", huggingface)
    sections += _section("Reddit", reddit)

    if youtube:
        yt_html = ""
        for v in youtube:
            yt_html += f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9;">'
            yt_html += f'<div style="font-size:13px;"><a href="{v.get("url","")}" style="color:{C};text-decoration:none;">{v.get("title","")}</a> <span style="color:#94a3b8;font-size:12px;">&middot; {v.get("channel","")}</span></div>'
            if v.get("quote"):
                yt_html += f'<div style="margin:6px 0 4px 0;padding:6px 10px;border-left:3px solid {CL};background:{CB};color:#475569;font-size:12px;font-style:italic;border-radius:0 4px 4px 0;">"{v["quote"]}"</div>'
            if v.get("summary"):
                yt_html += f'<div style="font-size:12px;color:#64748b;margin-top:4px;line-height:1.5;">{v["summary"]}</div>'
            yt_html += '</div>'
        sections += f"""
        <div style="margin-top:28px;">
            <div style="font-size:13px;font-weight:600;color:{C2};margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #dbeafe;">YouTube</div>
            {yt_html}
        </div>"""

    if twitter:
        tw_html = ""
        for tw in twitter:
            tw_html += f'<div style="padding:6px 0;font-size:13px;line-height:1.5;border-bottom:1px solid #f1f5f9;"><span style="color:{C};font-weight:500;">@{tw.get("handle","")}</span> <span style="color:#94a3b8;font-size:12px;">&middot; {tw.get("likes","")} likes</span><br><span style="color:#475569;font-size:12px;">{tw.get("text","")[:180]}</span></div>\n'
        sections += f"""
        <div style="margin-top:28px;">
            <div style="font-size:13px;font-weight:600;color:{C2};margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #dbeafe;">X / Twitter</div>
            {tw_html}
        </div>"""

    if newsletters:
        nl_html = ""
        for nl in newsletters:
            nl_html += f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9;">'
            nl_html += f'<div style="font-size:13px;font-weight:500;color:#0f172a;">{nl.get("sender","")} <span style="color:#94a3b8;font-size:12px;font-weight:400;">&middot; {nl.get("subject","")}</span></div>'
            if nl.get("takeaways"):
                nl_html += f'<div style="font-size:12px;color:#64748b;margin-top:4px;line-height:1.6;">{nl["takeaways"]}</div>'
            nl_html += '</div>'
        sections += f"""
        <div style="margin-top:28px;">
            <div style="font-size:13px;font-weight:600;color:{C2};margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #dbeafe;">Newsletters</div>
            {nl_html}
        </div>"""

    sections += _section("smol.ai", smolai, numbered=False)
    sections += _section("App Charts", app_charts, numbered=False)

    # Source status
    status_html = ""
    if source_status:
        rows = " &middot; ".join([f'{s.get("name","")} ({s.get("items","")})' for s in source_status if s.get("status") == "OK"])
        status_html = f'<div style="font-size:11px;color:#64748b;margin-top:24px;padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">{rows}</div>'

    # ── Full email ──
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0f172a;">
<div style="max-width:620px;margin:0 auto;background:#ffffff;">

    <div style="background:#f8fafc;padding:36px 24px 28px;text-align:center;border-bottom:3px solid #2563eb;">
        <div style="font-size:13px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#2563eb;">Signal Hunter</div>
        <div style="width:40px;height:2px;background:#2563eb;margin:10px auto;border-radius:1px;"></div>
        <div style="font-size:22px;font-weight:300;color:#0f172a;letter-spacing:-0.3px;">{date}</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px;letter-spacing:1px;text-transform:uppercase;">daily digest</div>
    </div>

    <div style="padding:28px 24px;">

        <div style="font-size:14px;line-height:1.75;color:#334155;margin-bottom:28px;padding-bottom:20px;border-bottom:2px solid #dbeafe;">
            {executive_summary}
        </div>

        <div style="font-size:13px;font-weight:700;color:{C2};margin-bottom:14px;letter-spacing:0.3px;">TRENDING SIGNALS</div>
        {topics_html}

        <div style="font-size:13px;font-weight:700;color:{C2};margin:32px 0 14px 0;letter-spacing:0.3px;">IDEAS</div>
        {ideas_html}

        {sections}

        {status_html}

    </div>

    <div style="padding:16px 24px;background:#f8fafc;border-top:3px solid #2563eb;text-align:center;">
        <div style="font-size:11px;color:#64748b;">Signal Hunter &mdash; Daily Digest</div>
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
