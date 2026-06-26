#!/usr/bin/env python3
"""Local customer support system for travel SIM and eSIM users."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import uuid
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from quote_lookup import format_money, search_products


PROJECT_DIR = Path(__file__).resolve().parent
TICKET_LOG_PATH = PROJECT_DIR / "support_tickets.jsonl"
LOOKUP_PAGE_PATH = PROJECT_DIR / "quote_lookup.html"
BRAND_NAME = "K大叔上網卡"


FAQ_ITEMS = [
    {
        "category": "eSIM 安裝",
        "keywords": ["esim", "e-sim", "qr", "qrcode", "掃碼", "掃描", "安裝", "加入行動方案"],
        "reply": [
            "請先確認手機支援 eSIM，且已連上穩定 Wi-Fi。",
            "到手機設定中選擇加入 eSIM 或行動方案，掃描 QR Code 後依畫面完成安裝。",
            "請依商品頁規則確認安裝與啟用時機；若不確定，請先不要提早掃碼或開啟方案。",
            "若已掃碼，請勿自行刪除 eSIM，避免商品無法恢復。",
        ],
    },
    {
        "category": "無法上網",
        "keywords": ["不能上網", "無法上網", "沒網路", "連不上", "沒有訊號", "沒訊號", "斷線"],
        "reply": [
            "請先確認已抵達方案支援地區，並開啟行動數據與數據漫遊。",
            "請依商品說明確認 APN、描述檔與電信商選擇是否正確。",
            "重新開機或切換飛航模式 30 秒後再關閉，讓手機重新註冊當地網路。",
            "若仍無法連線，請於插卡或 eSIM 綁定後 48 小時內提供手機型號、所在城市、錯誤畫面截圖與訂單資訊。",
        ],
    },
    {
        "category": "APN 設定",
        "keywords": ["apn", "熱點名稱", "存取點", "設定檔"],
        "reply": [
            "請依商品說明或客服提供的 APN 資訊設定。",
            "設定完成後請重開機，並確認此 SIM/eSIM 已被設為行動數據來源。",
            "若商品資料沒有提供 APN，請先不要自行猜測，改由客服向供應商確認。",
        ],
    },
    {
        "category": "熱點分享",
        "keywords": ["熱點", "分享", "wifi 分享", "hotspot", "分享網路"],
        "reply": [
            "是否能熱點分享需依商品描述與備註為準。",
            "若商品描述未明確標示支援熱點，請先列為待確認，避免對客戶保證。",
            "熱點分享可能受公平使用原則影響，且不建議同時分享超過一個裝置。",
        ],
    },
    {
        "category": "效期與啟用",
        "keywords": ["啟用", "激活", "開通", "效期", "到期", "最晚使用", "什麼時候開始"],
        "reply": [
            "方案啟用方式、效期與最晚使用日期需依商品資料為準。",
            "eSIM 通常需確認是安裝即啟用、抵達後啟用，或首次連線後啟用。",
        ],
    },
    {
        "category": "提前啟用風險",
        "keywords": ["台灣先開", "先開通", "提前", "提早", "先掃", "先掃碼", "天數變少", "還沒出國"],
        "reply": [
            "請先確認商品頁的啟用規則；部分商品提早掃碼、插卡或開啟方案可能會開始計算天數。",
            "若因提前操作造成天數短少、訊號錯亂或失效，通常屬高風險案件，需再依商品與供應商規則確認。",
        ],
    },
    {
        "category": "網速與公平使用",
        "keywords": ["網速", "很慢", "速度慢", "限速", "fup", "流量管制", "跑不動", "卡卡"],
        "reply": [
            "網速會受電信商維修、所在地區、尖峰時段、手機支援頻段與當地訊號影響。",
            "若短時間大量觀看影音、直播、遊戲、系統更新或大量下載，可能觸發公平使用原則而被限速。",
            "請提供所在城市、訊號截圖、測速截圖與目前已使用流量，方便進一步判斷。",
        ],
    },
    {
        "category": "裝置相容性",
        "keywords": ["支援", "手機型號", "不能用esim", "不支援", "相容", "iphone", "android", "安卓", "pixel"],
        "reply": [
            "請先提供完整手機型號與購買地區；eSIM 是否可用取決於手機本身是否支援 eSIM。",
            "市售手機型號與販售渠道差異很大，若不確定，建議向手機品牌商或購買通路確認規格。",
        ],
    },
    {
        "category": "退款與更換",
        "keywords": ["退款", "退費", "換卡", "取消", "買錯", "不能用"],
        "reply": [
            "請先確認商品是否已啟用、是否已產生 QR Code，這會影響可否退款或更換。",
            "請保留訂單編號、商品名稱、購買時間與問題截圖，方便客服判斷處理方式。",
        ],
    },
    {
        "category": "防詐騙提醒",
        "keywords": ["詐騙", "atm", "網銀", "驗證碼", "陌生電話", "分期", "解除設定"],
        "reply": [
            "K大叔上網卡不會要求客戶依電話指示操作 ATM、網路銀行，或提供驗證碼。",
            "若接到可疑電話，請勿提供個資或金融資料，並可撥打 165 反詐騙專線確認。",
        ],
    },
]


PAGE = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>K大叔上網卡客服系統</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --line: #d8dee9;
      --text: #202631;
      --muted: #687385;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --danger: #b42318;
      --soft: #e8f3f1;
      --warn-bg: #fff7ed;
      --warn-line: #fdba74;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans TC", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    .wrap {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }
    header .wrap {
      display: flex;
      justify-content: space-between;
      align-items: center;
      min-height: 72px;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }
    .status {
      color: var(--muted);
      font-size: 14px;
      white-space: nowrap;
    }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(340px, 0.95fr);
      gap: 18px;
      padding: 22px 0 36px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    h2 {
      margin: 0 0 14px;
      font-size: 18px;
      letter-spacing: 0;
    }
    label {
      display: block;
      margin: 14px 0 6px;
      font-weight: 650;
      font-size: 14px;
    }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: #fff;
      color: var(--text);
    }
    textarea { min-height: 112px; resize: vertical; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 160px;
      gap: 12px;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 16px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      padding: 10px 14px;
      cursor: pointer;
      min-height: 40px;
    }
    button.secondary {
      background: #e9edf3;
      color: var(--text);
    }
    button:hover { background: var(--accent-strong); }
    button.secondary:hover { background: #dfe5ee; }
    .hint, .empty {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }
    .result-list {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }
    .item {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      background: #fff;
    }
    .item strong {
      display: block;
      line-height: 1.45;
      margin-bottom: 8px;
    }
    .meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 8px;
      background: var(--soft);
      color: #114b47;
      font-size: 12px;
      font-weight: 700;
    }
    .line {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin: 5px 0;
    }
    .reply {
      border-left: 4px solid var(--accent);
      padding: 10px 12px;
      background: #f2faf8;
      line-height: 1.6;
      white-space: pre-line;
      border-radius: 0 6px 6px 0;
    }
    .warning {
      color: var(--danger);
      font-weight: 700;
    }
    .notice {
      border: 1px solid var(--warn-line);
      background: var(--warn-bg);
      border-radius: 8px;
      padding: 11px 12px;
      line-height: 1.55;
      color: #7c2d12;
      font-size: 14px;
    }
    .ticket-id {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--accent-strong);
      font-weight: 700;
    }
    @media (max-width: 900px) {
      header .wrap { align-items: flex-start; flex-direction: column; padding: 16px 0; }
      main { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .status { white-space: normal; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>K大叔上網卡客服系統</h1>
      <div class="status"><a href="/lookup">商品查詢</a>｜商品資料來源：card.xlsx / eSim.xlsx</div>
    </div>
  </header>
  <main class="wrap">
    <section>
      <h2>客戶問題處理</h2>
      <form method="post" action="/support">
        <label for="customer">客戶名稱或訂單編號</label>
        <input id="customer" name="customer" value="{customer}" placeholder="例：王小姐 / KS20260526001">

        <div class="grid">
          <div>
            <label for="destination">目的地 / 商品關鍵字</label>
            <input id="destination" name="destination" value="{destination}" placeholder="例：日本 5天 eSIM">
          </div>
          <div>
            <label for="product_type">商品類型</label>
            <select id="product_type" name="product_type">
              {product_options}
            </select>
          </div>
        </div>

        <label for="issue">客戶問題</label>
        <textarea id="issue" name="issue" placeholder="貼上客戶訊息，例如：我到日本後 eSIM 沒有訊號，請問怎麼辦？">{issue}</textarea>

        <div class="actions">
          <button type="submit">產生客服建議</button>
          <button class="secondary" type="submit" formaction="/ticket">建立工單</button>
        </div>
      </form>
      {support_result}
    </section>
    <section>
      <h2>商品候選方案</h2>
      <p class="hint">輸入目的地、天數、流量或 eSIM / 實體卡等關鍵字後，系統會沿用現有報價工具排序。報價成本仍需依 K大叔上網卡售價策略人工確認，不會自動當成客戶最終售價。</p>
      {product_results}
    </section>
  </main>
</body>
</html>"""


def escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def tokenize(text: str) -> list[str]:
    return [item for item in re.split(r"[\s,，、。/]+", text.strip()) if item]


def classify_issue(issue: str) -> list[dict[str, Any]]:
    normalized = issue.casefold()
    matched = []
    for item in FAQ_ITEMS:
        if any(keyword.casefold() in normalized for keyword in item["keywords"]):
            matched.append(item)
    return matched


def build_reply(customer: str, issue: str, matches: list[dict[str, Any]]) -> str:
    greeting = f"{customer} 您好，" if customer else "您好，"
    if not matches:
        return (
            f"{greeting}\n"
            "我們已收到您的問題。為了更快協助您，請提供訂單編號、使用國家、手機型號、商品名稱、ICCID 或 eSIM 完整信件內容，以及目前畫面截圖。\n"
            "K大叔上網卡客服會依商品資料與供應商規則確認後回覆您。"
        )

    lines = [greeting, "建議您先依以下方式確認："]
    seen: set[str] = set()
    for item in matches:
        for sentence in item["reply"]:
            if sentence not in seen:
                lines.append(f"- {sentence}")
                seen.add(sentence)
    lines.append("若完成以上步驟仍無法排除，請提供訂單編號、商品名稱、手機型號、所在城市、ICCID 或 eSIM 完整信件內容與錯誤畫面截圖，我們會再協助確認。")
    return "\n".join(lines)


def build_internal_notice(matches: list[dict[str, Any]]) -> str:
    categories = {item["category"] for item in matches}
    notices = []
    if {"無法上網", "eSIM 安裝"} & categories:
        notices.append("確認是否在插卡或 eSIM 綁定後 48 小時內回報，並收齊截圖與 ICCID/eSIM 信件。")
    if {"退款與更換", "提前啟用風險"} & categories:
        notices.append("此案件涉及退換貨或提前啟用風險，回覆前需確認商品狀態、啟用紀錄與供應商規則。")
    if "熱點分享" in categories:
        notices.append("熱點分享不可直接保證可用，請以商品頁與裝置實測為準。")
    if "防詐騙提醒" in categories:
        notices.append("提醒客戶不要提供驗證碼、個資或依陌生電話操作 ATM/網銀。")
    if not notices:
        return ""
    items = "".join(f"<li>{escape(item)}</li>" for item in notices)
    return f'<div class="notice"><strong>客服內部提醒</strong><ul>{items}</ul></div>'


def product_type_options(selected: str) -> str:
    labels = [("all", "全部"), ("esim", "eSIM"), ("card", "實體卡")]
    options = []
    for value, label in labels:
        selected_attr = " selected" if selected == value else ""
        options.append(f'<option value="{value}"{selected_attr}>{label}</option>')
    return "\n".join(options)


def render_products(destination: str, product_type: str) -> str:
    keywords = tokenize(destination)
    if not keywords:
        return '<p class="empty">尚未輸入商品查詢條件。</p>'
    try:
        results = search_products(keywords, product_type=product_type, limit=8)
    except (FileNotFoundError, ValueError) as error:
        return f'<p class="empty warning">資料讀取失敗：{escape(error)}</p>'

    if not results:
        return '<p class="empty">找不到符合條件的商品，請放寬目的地、天數或流量條件。</p>'

    cards = ['<div class="result-list">']
    for result in results:
        product = result.product
        quote = format_money(result.quote_total)
        cost = format_money(product.quote_cost)
        note_line = f'<p class="line">備註：{escape(product.note)}</p>' if product.note else ""
        activation_line = (
            f'<p class="line">激活：{escape(product.activation)}</p>'
            if product.activation
            else ""
        )
        cards.append(
            '<article class="item">'
            f'<strong>{escape(product.name)}</strong>'
            '<div class="meta">'
            f'<span class="pill">{escape(product.source)}</span>'
            f'<span class="pill">{escape(result.quote_label or "報價")}: {escape(quote or "待確認")}</span>'
            f'<span class="pill">成本: {escape(cost or "待確認")}</span>'
            '</div>'
            f'<p class="line">使用地：{escape(product.destinations)}</p>'
            f'<p class="line">內容：{escape(product.description)}</p>'
            f'{note_line}'
            f'{activation_line}'
            '</article>'
        )
    cards.append("</div>")
    return "\n".join(cards)


def render_support_result(customer: str, issue: str, saved_ticket_id: str | None = None) -> str:
    if not issue.strip() and not saved_ticket_id:
        return ""
    matches = classify_issue(issue)
    categories = "、".join(item["category"] for item in matches) if matches else "待人工判斷"
    reply = build_reply(customer, issue, matches)
    ticket_line = (
        f'<p>已建立工單：<span class="ticket-id">{escape(saved_ticket_id)}</span></p>'
        if saved_ticket_id
        else ""
    )
    return (
        '<div class="result-list">'
        '<article class="item">'
        f"{ticket_line}"
        f'<p class="line">問題分類：{escape(categories)}</p>'
        f"{build_internal_notice(matches)}"
        f'<div class="reply">{escape(reply)}</div>'
        '</article>'
        '</div>'
    )


def save_ticket(form: dict[str, str]) -> str:
    ticket_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    record = {
        "id": ticket_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "customer": form.get("customer", ""),
        "destination": form.get("destination", ""),
        "product_type": form.get("product_type", "all"),
        "issue": form.get("issue", ""),
        "categories": [item["category"] for item in classify_issue(form.get("issue", ""))],
    }
    with TICKET_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return ticket_id


def render_page(form: dict[str, str] | None = None, saved_ticket_id: str | None = None) -> bytes:
    form = form or {}
    customer = form.get("customer", "")
    destination = form.get("destination", "")
    issue = form.get("issue", "")
    product_type = form.get("product_type", "all")
    page = (
        PAGE.replace("{customer}", escape(customer))
        .replace("{destination}", escape(destination))
        .replace("{issue}", escape(issue))
        .replace("{product_options}", product_type_options(product_type))
        .replace("{support_result}", render_support_result(customer, issue, saved_ticket_id))
        .replace("{product_results}", render_products(destination, product_type))
    )
    return page.encode("utf-8")


def parse_form(body: bytes) -> dict[str, str]:
    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items()}


def serialize_result(result: Any) -> dict[str, str]:
    product = result.product
    return {
        "source": product.source,
        "name": product.name,
        "quote": format_money(result.quote_total),
        "quote_label": result.quote_label or "報價",
        "cost": format_money(product.quote_cost),
        "unit_price": product.unit_price,
        "destinations": product.destinations,
        "description": product.description,
        "note": product.note,
        "activation": product.activation,
    }


class SupportHandler(BaseHTTPRequestHandler):
    def is_authorized(self) -> bool:
        username = os.environ.get("SUPPORT_USERNAME")
        password = os.environ.get("SUPPORT_PASSWORD")
        if not username or not password:
            return True

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return False

        try:
            decoded = base64.b64decode(auth_header.removeprefix("Basic ")).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False
        return decoded == f"{username}:{password}"

    def require_authorization(self) -> bool:
        if self.is_authorized():
            return True
        body = "需要登入才能使用客服系統。".encode("utf-8")
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="K Support"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    def do_GET(self) -> None:
        if not self.require_authorization():
            return
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self.send_html(render_page())
            return
        if parsed_url.path == "/lookup":
            self.send_lookup_page()
            return
        if parsed_url.path == "/api/products":
            self.send_product_results(parse_qs(parsed_url.query))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if not self.require_authorization():
            return
        path = urlparse(self.path).path
        if path not in {"/support", "/ticket"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_form(self.rfile.read(length))
        ticket_id = save_ticket(form) if path == "/ticket" else None
        self.send_html(render_page(form, ticket_id))

    def send_html(self, body: bytes) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_lookup_page(self) -> None:
        if not LOOKUP_PAGE_PATH.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "找不到商品查詢頁面")
            return
        self.send_html(LOOKUP_PAGE_PATH.read_bytes())

    def send_product_results(self, query: dict[str, list[str]]) -> None:
        keyword_text = query.get("q", [""])[0].strip()
        product_type = query.get("type", ["all"])[0]
        if product_type not in {"all", "esim", "card"}:
            product_type = "all"
        try:
            limit = max(1, min(int(query.get("limit", ["20"])[0]), 30))
        except ValueError:
            limit = 20

        if not keyword_text:
            self.send_json({"results": [], "message": "請輸入目的地或方案關鍵字。"})
            return

        try:
            results = search_products(
                tokenize(keyword_text), product_type=product_type, limit=limit
            )
        except (FileNotFoundError, ValueError) as error:
            self.send_json({"results": [], "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_json(
            {
                "results": [serialize_result(result) for result in results],
                "message": "" if results else "找不到符合條件的商品。",
            }
        )

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the local support system.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), SupportHandler)
    print(f"客服系統已啟動：http://{args.host}:{args.port}")
    print("按 Ctrl+C 可停止服務。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n客服系統已停止。")


if __name__ == "__main__":
    main()
