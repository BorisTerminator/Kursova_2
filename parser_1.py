from playwright.sync_api import Playwright, sync_playwright, expect
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

'''
Забираем толькко ссылки на дела.
'''

def get_links(soup:str)->list:
    soup = BeautifulSoup(soup, 'html.parser')
    items = soup.find_all(class_='megasearch-result-item')
    hrefs = [item.find('a')['href'] for item in items if item.find('a')]

    with open('datalinks.csv', "a", encoding='utf-8') as f:
        for href in hrefs:
            f.write(f"{href}\n")

name = 'Сбербанк'

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(f"https://mos-gorsud.ru/fastsearch?q={name}&page=1")
    time.sleep(25)
    for _ in tqdm(range(676)):
        time.sleep(3)
        html_content = page.content()
        get_links(html_content)
        page.get_by_role("button", name="Следующая").click()

    # ---------------------
    context.close()
    browser.close()



with sync_playwright() as playwright:
    html_content = run(playwright)

