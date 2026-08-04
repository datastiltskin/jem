# render.py
from playwright.sync_api import sync_playwright

def fetch_rendered(url: str, pol: dict) -> tuple[bytes, int, str, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=pol["user_agent"],
                                   ignore_https_errors=(pol["tls"] == "downgrade"))
        page = ctx.new_page()
        captured = {"json": None, "status": None}

        # opportunistically capture the underlying data XHR — better evidence than DOM
        def on_response(resp):
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct and resp.request.resource_type == "xhr":
                try:
                    captured["json"] = resp.body()
                    captured["status"] = resp.status
                except Exception:
                    pass
        page.on("response", on_response)

        if pol.get("warmup_url"):
            page.goto(pol["warmup_url"], wait_until="networkidle")
        resp = page.goto(url, wait_until="networkidle", timeout=pol["timeout_s"] * 1000)
        if pol.get("wait_for_selector"):
            page.wait_for_selector(pol["wait_for_selector"], timeout=15000)

        # if we caught the JSON feed, that IS the evidence — cleaner than HTML
        if captured["json"]:
            body, ctype = captured["json"], "application/json"
        else:
            body, ctype = page.content().encode("utf-8"), "text/html; charset=utf-8"

        status = resp.status if resp else 0
        final_url = page.url
        browser.close()
        return body, status, final_url, ctype