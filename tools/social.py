import subprocess
import time
from playwright.sync_api import sync_playwright
import ollama
import requests


def extract_unread_dm_names(page):
    unread_badges = page.query_selector_all("span[aria-label*='unread']")
    print(f"Unread elements found: {len(unread_badges)}")

    messages = []
    seen = set()

    for badge in unread_badges:
        try:
            chat = badge.evaluate("""el => {
                const row = el.closest('[data-testid="cell-frame-container"]');
                if (!row) return null;

                const titleEl = row.querySelector('[data-testid="cell-frame-title"]');
                const nameEl = titleEl?.querySelector('span[dir="auto"]');
                const rawTitle = nameEl?.textContent?.trim() || titleEl?.textContent?.trim() || "";
                const parts = rawTitle.split("\\n").map(part => part.trim()).filter(Boolean);
                const name = parts.length ? parts[parts.length - 1] : null;
                const isGroup = row.querySelector('[data-testid="group-icon"]') !== null;

                return { name, isGroup };
            }""")

            if chat is None:
                continue

            name = chat.get("name")
            is_group = chat.get("isGroup", False)

            if name and not is_group and name not in {"Archived", "Meta AI"} and name not in seen:
                messages.append(name)
                seen.add(name)
        except Exception:
            continue

    return messages


def open_chat(page, contact):
    row = page.locator('[data-testid="cell-frame-container"]').filter(
        has=page.locator('[data-testid="cell-frame-title"]', has_text=contact)
    ).first
    row.click(timeout=10000)
    page.wait_for_timeout(1000)


def social():
    # Kill existing Brave
    subprocess.run(["pkill", "brave"])
    time.sleep(2)
    
    # Open Brave with debugging port
    subprocess.Popen(["brave", "--remote-debugging-port=9222", "https://web.whatsapp.com"])
    time.sleep(5)
    
    # Verify port is ready
    for i in range(10):
        try:
            requests.get("http://localhost:9222/json")
            print("Brave ready!")
            break
        except:
            print(f"Waiting... {i+1}")
            time.sleep(2)
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        # Find WhatsApp page
        whatsapp_page = None
        for pg in browser.contexts[0].pages:
            if "whatsapp" in pg.url:
                whatsapp_page = pg
                break

        if whatsapp_page is None:
            print("WhatsApp not found!")
            return

        page = whatsapp_page
        print(f"Found WhatsApp at: {page.url}")
        
       # Wait for WhatsApp to load - try multiple selectors
        try:
            page.wait_for_selector("div[aria-label='Chat list']", timeout=30000)
        except:
            try:
                page.wait_for_selector("#pane-side", timeout=30000)
            except:
                page.wait_for_selector("div[data-tab='7']", timeout=30000)

        print("WhatsApp loaded!")
        # Debug: print all chat items
        chats = page.query_selector_all("div[role='listitem']")
        print(f"Total chats found: {len(chats)}")

        messages = extract_unread_dm_names(page)
        print(f"Unread DMs from: {messages}")

        if messages:
            for contact in messages:
                open_chat(page, contact)
                
                last_msg = page.query_selector("div.message-in span.selectable-text")
                msg_text = last_msg.inner_text() if last_msg else "Hey!"
                
                response = ollama.chat(
                    model="tinyllama",
                    messages=[{
                        "role": "user",
                        "content": f"Generate a casual one line reply to this whatsapp message: '{msg_text}'. Just the reply, nothing else."
                    }]
                )
                
                reply = response['message']['content'].strip()
                print(f"Sending to {contact}: {reply}")
                
                msg_box = page.wait_for_selector("div[data-tab='10']")
                msg_box.fill(reply)
                page.keyboard.press("Enter")
                time.sleep(1)

if __name__ == "__main__":
    social()
