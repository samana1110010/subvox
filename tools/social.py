# import subprocess
# import time
# import os
# from playwright.sync_api import sync_playwright
# import ollama
# import requests


# def extract_unread_dm_names(page):
#     unread_badges = page.query_selector_all("span[aria-label*='unread']")
#     print(f"Unread elements found: {len(unread_badges)}")

#     messages = []
#     seen = set()

#     for badge in unread_badges:
#         try:
#             chat = badge.evaluate("""el => {
#                 const row = el.closest('[data-testid="cell-frame-container"]');
#                 if (!row) return null;

#                 const titleEl = row.querySelector('[data-testid="cell-frame-title"]');
#                 const nameEl = titleEl?.querySelector('span[dir="auto"]');
#                 const rawTitle = nameEl?.textContent?.trim() || titleEl?.textContent?.trim() || "";
#                 const parts = rawTitle.split("\\n").map(part => part.trim()).filter(Boolean);
#                 const name = parts.length ? parts[parts.length - 1] : null;
#                 const isGroup = row.querySelector('[data-testid="group-icon"]') !== null;

#                 return { name, isGroup };
#             }""")

#             if chat is None:
#                 continue

#             name = chat.get("name")
#             is_group = chat.get("isGroup", False)

#             if name and not is_group and name not in {"Archived", "Meta AI"} and name not in seen:
#                 messages.append(name)
#                 seen.add(name)
#         except Exception:
#             continue

#     return messages


# def open_chat(page, contact):
#     row = page.locator('[data-testid="cell-frame-container"]').filter(
#         has=page.locator('[data-testid="cell-frame-title"]', has_text=contact)
#     ).first
#     row.click(timeout=10000)
#     page.wait_for_timeout(1000)


# def chrome_path_windows():
#     paths = [
#         os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
#         os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
#         os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
#     ]

#     for path in paths:
#         if path and os.path.exists(path):
#             return path

#     return "chrome.exe"


# def connect_to_whatsapp(cdp_url="http://localhost:9222"):
#     with sync_playwright() as p:
#         browser = p.chromium.connect_over_cdp(cdp_url)
#         # Find WhatsApp page
#         whatsapp_page = None
#         for pg in browser.contexts[0].pages:
#             if "whatsapp" in pg.url:
#                 whatsapp_page = pg
#                 break

#         if whatsapp_page is None:
#             print("WhatsApp not found!")
#             return

#         page = whatsapp_page
#         print(f"Found WhatsApp at: {page.url}")

#        # Wait for WhatsApp to load - try multiple selectors
#         try:
#             page.wait_for_selector("div[aria-label='Chat list']", timeout=30000)
#         except:
#             try:
#                 page.wait_for_selector("#pane-side", timeout=30000)
#             except:
#                 page.wait_for_selector("div[data-tab='7']", timeout=30000)

#         print("WhatsApp loaded!")
#         # Debug: print all chat items
#         chats = page.query_selector_all("div[role='listitem']")
#         print(f"Total chats found: {len(chats)}")

#         messages = extract_unread_dm_names(page)
#         print(f"Unread DMs from: {messages}")

#         if messages:
#             for contact in messages:
#                 open_chat(page, contact)

#                 last_msg = page.query_selector("div.message-in span.selectable-text")
#                 msg_text = last_msg.inner_text() if last_msg else "Hey!"

#                 response = ollama.chat(
#                     model="qwen2.5:7b",
#                     messages=[
#                         {
#                             "role": "system",
#                             "content": (
#                                 "You are a real person texting on WhatsApp. "
#                                 "Reply in 1 short, clear, goal-oriented sentence. "
#                                 "Be casual but not slangy. "
#                                 "No emojis. "
#                                 "No extra explanations. "
#                                 "If the message is unclear, ask a brief follow-up question."
#                             )
#                         },
#                         {
#                             "role": "user",
#                             "content": msg_text
#                         }
#                     ]
#                 )

#                 reply = response['message']['content'].strip()
#                 print(f"Sending to {contact}: {reply}")

#                 msg_box = page.wait_for_selector("div[data-tab='10']")
#                 msg_box.fill(reply)
#                 page.keyboard.press("Enter")
#                 time.sleep(1)


# def social_windows():
#     cdp_url = "http://127.0.0.1:9222"
#     chrome_user_data_dir = os.path.join(os.environ.get("TEMP", "."), "subvox-chrome-debug")

#     subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#     time.sleep(2)

#     chrome = chrome_path_windows()
#     subprocess.Popen([
#         chrome,
#         "--remote-debugging-address=127.0.0.1",
#         "--remote-debugging-port=9222",
#         f"--user-data-dir={chrome_user_data_dir}",
#         "--no-first-run",
#         "--no-default-browser-check",
#         "https://web.whatsapp.com",
#     ])
#     time.sleep(5)

#     # Verify port is ready
#     for i in range(10):
#         try:
#             requests.get(f"{cdp_url}/json")
#             print("Chrome ready!")
#             break
#         except:
#             print(f"Waiting... {i+1}")
#             time.sleep(2)
#     else:
#         print("Chrome debugging port did not open. Check that Chrome launched and port 9222 is not blocked.")
#         return

#     connect_to_whatsapp(cdp_url)


# def social():
#     if os.name == "nt":
#         social_windows()
#         return

#     # Kill existing Brave
#     subprocess.run(["pkill", "brave"])
#     time.sleep(2)
    
#     # Open Brave with debugging port
#     subprocess.Popen(["brave", "--remote-debugging-port=9222", "https://web.whatsapp.com"])
#     time.sleep(5)
    
#     # Verify port is ready
#     for i in range(10):
#         try:
#             requests.get("http://localhost:9222/json")
#             print("Brave ready!")
#             break
#         except:
#             print(f"Waiting... {i+1}")
#             time.sleep(2)
    
#     with sync_playwright() as p:
#         browser = p.chromium.connect_over_cdp("http://localhost:9222")
#         # Find WhatsApp page
#         whatsapp_page = None
#         for pg in browser.contexts[0].pages:
#             if "whatsapp" in pg.url:
#                 whatsapp_page = pg
#                 break

#         if whatsapp_page is None:
#             print("WhatsApp not found!")
#             return

#         page = whatsapp_page
#         print(f"Found WhatsApp at: {page.url}")
        
#        # Wait for WhatsApp to load - try multiple selectors
#         try:
#             page.wait_for_selector("div[aria-label='Chat list']", timeout=30000)
#         except:
#             try:
#                 page.wait_for_selector("#pane-side", timeout=30000)
#             except:
#                 page.wait_for_selector("div[data-tab='7']", timeout=30000)

#         print("WhatsApp loaded!")
#         # Debug: print all chat items
#         chats = page.query_selector_all("div[role='listitem']")
#         print(f"Total chats found: {len(chats)}")

#         messages = extract_unread_dm_names(page)
#         print(f"Unread DMs from: {messages}")

#         if messages:
#             for contact in messages:
#                 open_chat(page, contact)
                
#                 last_msg = page.query_selector("div.message-in span.selectable-text")
#                 msg_text = last_msg.inner_text() if last_msg else "Hey!"
                
#                 response = ollama.chat(
#                     model="qwen2.5:7b",
#                     messages=[
#                         {
#                             "role": "system",
#                             "content": (
#                                 "You are a real person texting on WhatsApp. "
#                                 "Reply in 1 short, clear, goal-oriented sentence. "
#                                 "Be casual but not slangy. "
#                                 "No emojis. "
#                                 "No extra explanations. "
#                                 "If the message is unclear, ask a brief follow-up question."
#                             )
#                         },
#                         {
#                             "role": "user",
#                             "content": msg_text
#                         }
#                     ]
#                 )
                
#                 reply = response['message']['content'].strip()
#                 print(f"Sending to {contact}: {reply}")
                
#                 msg_box = page.wait_for_selector("div[data-tab='10']")
#                 msg_box.fill(reply)
#                 page.keyboard.press("Enter")
#                 time.sleep(1)

# if __name__ == "__main__":
#     social()

import subprocess
import time
import os
from playwright.sync_api import sync_playwright
import ollama
import requests


# ---------------- CONTEXT EXTRACTION ---------------- #

def get_chat_context(page, limit=6):
    try:
        page.wait_for_selector("[data-testid='msg-container'], div.message-in, div.message-out", timeout=5000)
    except:
        pass

    chat_history = page.evaluate("""(limit) => {
        const nodes = Array.from(
            document.querySelectorAll("div[data-testid='msg-container'], div.message-in, div.message-out")
        );

        const uniqueNodes = nodes.filter((node, index) => !nodes.slice(index + 1).some(other => other.contains(node)));

        return uniqueNodes.slice(-limit).map((node) => {
            const bubble = node.matches('.message-in, .message-out')
                ? node
                : node.querySelector('.message-in, .message-out');

            const role = bubble?.classList.contains('message-in') ? 'user' : 'assistant';

            const selectableParts = Array.from(node.querySelectorAll('span.selectable-text'))
                .map(el => (el.innerText || el.textContent || '').trim())
                .filter(Boolean);

            const fallbackParts = selectableParts.length ? selectableParts : Array.from(
                node.querySelectorAll("div.copyable-text span[dir='auto'], div.copyable-text span[dir='ltr']")
            )
                .map(el => (el.innerText || el.textContent || '').trim())
                .filter(Boolean);

            const text = fallbackParts.join('\\n').trim();
            if (!text) return null;

            return { role, content: text };
        }).filter(Boolean);
    }""", limit)

    # 🔥 MERGE consecutive messages
    merged = []
    for msg in chat_history:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n" + msg["content"]
        else:
            merged.append(msg)
    print("FINAL INPUT TO MODEL:\n", merged)

    return merged

# ---------------- UNREAD DETECTION ---------------- #

def extract_unread_dm_names(page):
    unread_badges = page.query_selector_all("span[aria-label*='unread']")
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
        except:
            continue

    return messages


# ---------------- CHAT OPEN ---------------- #

def open_chat(page, contact):
    row = page.locator('[data-testid="cell-frame-container"]').filter(
        has=page.locator('[data-testid="cell-frame-title"]', has_text=contact)
    ).first
    row.click(timeout=10000)
    page.wait_for_timeout(1500)


# ---------------- LLM CALL ---------------- #

def get_model_name():
    if os.name == "nt":
        return "tinyllama"
    return "qwen2.5:7b"


def generate_reply(chat_history, contact):
    if not chat_history:
        return "Hey"

    last_user_msg = None
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break

    if not last_user_msg:
        last_user_msg = chat_history[-1]["content"]

    response = ollama.chat(
        model=get_model_name(),
        messages=[
                    {
                "role": "system",
                "content": (
                    f"You are texting {contact} on WhatsApp.\n"
                    "Reply like a normal person.\n"
                    "Do NOT start with greetings like 'hey' unless the message is a greeting.\n"
                    "React directly to what they said.\n"
                    "Keep it short and natural.\n"
                    "No emojis."
                )
            },
            *chat_history,
            {
                "role": "user",
                "content": f"Reply to this message: {last_user_msg}"
            }
        ]
    )

    return response['message']['content'].strip()


# ---------------- WINDOWS CHROME ---------------- #

def chrome_path_windows():
    paths = [
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]

    for path in paths:
        if path and os.path.exists(path):
            return path

    return "chrome.exe"


def connect_to_whatsapp(cdp_url="http://localhost:9222"):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)

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

        page.wait_for_selector("#pane-side", timeout=30000)

        messages = extract_unread_dm_names(page)
        print(f"Unread DMs from: {messages}")

        for contact in messages:
            open_chat(page, contact)

            chat_history = get_chat_context(page, limit=4)

            # last user message (fallback safe)
            msg_text = chat_history[-1]["content"] if chat_history else "Hey"

            reply = generate_reply(chat_history, contact)

            print(f"Sending to {contact}: {reply}")

            print(f"\nContact: {contact}")
            print(f"Generated reply: {reply}")

            confirm = input("Send this reply? (y/n): ").strip().lower()

            if confirm == "y":
                msg_box = page.wait_for_selector("div[data-tab='10']")
                msg_box.fill(reply)
                page.keyboard.press("Enter")
                print("Reply sent.")
            else:
                print("Skipped.")


def social_windows():
    cdp_url = "http://127.0.0.1:9222"
    chrome_user_data_dir = os.path.join(os.environ.get("TEMP", "."), "subvox-chrome-debug")

    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(2)

    chrome = chrome_path_windows()

    subprocess.Popen([
        chrome,
        "--remote-debugging-address=127.0.0.1",
        "--remote-debugging-port=9222",
        f"--user-data-dir={chrome_user_data_dir}",
        "https://web.whatsapp.com",
    ])

    time.sleep(5)

    for i in range(10):
        try:
            requests.get(f"{cdp_url}/json")
            break
        except:
            time.sleep(2)

    connect_to_whatsapp(cdp_url)


# ---------------- LINUX ---------------- #

def social():
    if os.name == "nt":
        social_windows()
        return

    subprocess.run(["pkill", "brave"])
    time.sleep(2)

    subprocess.Popen(["brave", "--remote-debugging-port=9222", "https://web.whatsapp.com"])
    time.sleep(5)

    for i in range(10):
        try:
            requests.get("http://localhost:9222/json")
            break
        except:
            time.sleep(2)

    connect_to_whatsapp("http://localhost:9222")


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    social()
