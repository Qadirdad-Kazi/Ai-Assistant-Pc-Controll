import asyncio
from playwright.async_api import async_playwright
import sys

async def test_chat_ui():
    print("[TEST] Starting Wolf AI Chat UI Test...")
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. Navigate to chat page
            print("[TEST] Navigating to http://localhost:5173/chat...")
            await page.goto("http://localhost:5173/chat", wait_until="networkidle")
            
            # 2. Check for chat input visibility
            # Assuming a standard textarea or input for chat
            chat_input = await page.wait_for_selector('textarea, input[placeholder*="message"]', timeout=10000)
            if chat_input:
                print("[OK] Chat interface loaded successfully.")
            else:
                print("[FAIL] Chat input not found.")
                return False

            # 3. Send a test message
            test_message = "Logic Check: Are you functioning correctly?"
            print(f"[TEST] Sending message: {test_message}")
            await chat_input.fill(test_message)
            await page.get_by_role("button", name=lambda x: "send" in x.lower() or "submit" in x.lower() or not x).first.click()
            
            # Or just press Enter
            await page.keyboard.press("Enter")

            # 4. Wait for AI response
            print("[TEST] Waiting for AI response...")
            # We look for a new message bubble that wasn't there before
            # This is generic; we wait for a reasonable time and check if more than 1 message exists
            await asyncio.sleep(8)
            
            # Assuming messages have a common class or tag
            messages = await page.query_selector_all('.message, .chat-bubble, p')
            if len(messages) > 1:
                print(f"[OK] Received response from AI. Total messages: {len(messages)}")
                # Log the last message text
                last_msg = await messages[-1].inner_text()
                print(f"[AI] Last Response Snippet: {last_msg[:50]}...")
                return True
            else:
                print("[FAIL] No response detected after 8 seconds.")
                return False

        except Exception as e:
            print(f"[ERROR] Test crashed: {e}")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(test_chat_ui())
    sys.exit(0 if success else 1)
