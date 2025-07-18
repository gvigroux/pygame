from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://twitter.com/explore/tabs/trending")
    
    # Extraire les vidéos tendances
    videos = page.locator('//div[@data-testid="videoComponent"]').all()
    for video in videos[:10]:
        print(video.get_attribute('href'))
    
    browser.close()