from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def get_ct_tokens(url: str = "https://www.w88kaya.com/Sports/Launcher?provider=btiSports&game=btiSports&t=1&f=0&matchId="):
    options = Options()
    # options.add_argument("--headless")  # comment out to see browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # Run headless for background execution
    options.add_argument("--incognito")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        print(f"Opened: {url}")
        time.sleep(5)

        TARGET_ORIGIN = "https://prod20262.442hattrick.com"

        def extract_tokens(drv):
            return drv.execute_script("""
                return {
                    CT_APP_AUTHORIZATION: localStorage.getItem('CT_APP_AUTHORIZATION'),
                    CT_APP_SESSION: localStorage.getItem('CT_APP_SESSION')
                };
            """)

        tokens = {"CT_APP_AUTHORIZATION": None, "CT_APP_SESSION": None}
        found = False

        def search_iframes(drv, depth=0):
            nonlocal found
            if found:
                return

            iframes = drv.find_elements("tag name", "iframe")
            print(f"{'  ' * depth}Scanning {len(iframes)} iframe(s) at depth {depth}")

            for i, iframe in enumerate(iframes):
                if found:
                    break
                try:
                    drv.switch_to.frame(iframe)

                    current_origin = drv.execute_script("return window.location.origin")
                    print(f"{'  ' * depth}  iframe #{i}: {current_origin}")

                    if current_origin == TARGET_ORIGIN:
                        print(f"{'  ' * depth}  ✅ Matched target: {TARGET_ORIGIN}")
                        result = extract_tokens(drv)
                        tokens.update(result)
                        found = True
                        return  # stop immediately, no need to go deeper

                    # Not matched — recurse into nested iframes
                    search_iframes(drv, depth + 1)

                    drv.switch_to.parent_frame()

                except Exception as e:
                    print(f"{'  ' * depth}  ⚠️  iframe #{i} error: {e}")
                    drv.switch_to.default_content()

        search_iframes(driver)

        if not found:
            print(f"\n❌ Could not find frame origin: {TARGET_ORIGIN}")
            print("   Try increasing time.sleep() if the page loads slowly.")
        else:
            print("\n=== Extracted Tokens ===")
            print(f"CT_APP_AUTHORIZATION : {tokens['CT_APP_AUTHORIZATION']}")
            print(f"CT_APP_SESSION       : {tokens['CT_APP_SESSION']}")

        return tokens

    finally:
        driver.quit()


if __name__ == "__main__":
    target_url = "https://www.w88kaya.com/Sports/Launcher?provider=btiSports&game=btiSports&t=1&f=0&matchId="

    tokens = get_ct_tokens(target_url)

    with open("ct_tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)
    print("\n✅ Saved to ct_tokens.json")