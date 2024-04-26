import asyncio
from playwright.async_api import Playwright, async_playwright, expect
import pandas as pd
import time
from fake_useragent import UserAgent
import shutil
import os
import aiosqlite
import asyncio
from bs4 import BeautifulSoup
import logging

logging.basicConfig(filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AsyncPageLoader')

data = pd.read_csv('datalinks.csv', header=None, names=['links'])


async def async_insert_into_db(data) -> bool:
    async with aiosqlite.connect('legal_cases.db') as db:  # Асинхронное подключение к базе данных
        async with db.cursor() as cursor:  # Асинхронное получение
            unique_ident_case, case_number, complaint_number = data[1], data[2], data[3]

            sql = '''SELECT Уникальный_идентификатор_дела, Номер_дела, Номер_жалобы FROM collection 
            WHERE Уникальный_идентификатор_дела = ? or Номер_дела = ? or Номер_жалобы = ?'''

            await cursor.execute(sql, (unique_ident_case, case_number, complaint_number))
            result = await cursor.fetchone()

            if not result:
                placeholders = ', '.join(['?'] * len(data))
                query = f"INSERT INTO collection VALUES ({placeholders})"
                await cursor.execute(query, data)
                await db.commit()
                return True
          
def get_info(html_fragment) -> dict:
    dict_values = {
    'id': None,
    'Уникальный идентификатор дела':None,
    'Номер дела ~ материала': None,
    'Номер жалобы': None,
    'Истец':None,
    "Ответчик": None,
    'Заявитель':None,
    'Cудья': None,
    'Статья КоАП РФ': None,
    'Суд, вынесший решение':None,
    'Категория дела': None,
    'Текущее состояние':None,
    'Результат рассмотрения':None,
    'path':None}
    soup = BeautifulSoup(html_fragment, 'html.parser')

    html_fragments = soup.find_all(class_='row_card') # ищем всю нужную информацию 

    for html in html_fragments:

        key = html.find(class_='left').get_text(strip=True)   
            
        if key in dict_values.keys():
            value = html.find(class_='right').get_text(strip=True)
            dict_values[key] = value
        
        if key == 'Номер дела ~ материала' or key == 'Номер дела':
            value_ = html.find(class_='right').get_text(strip=True).replace('\n','').replace(' ','')
            dict_values['Номер дела ~ материала'] = value_
            
        if key == 'Стороны': # обработка поля Стороны
            strong_tags = html.find_all('strong')
            for strong_tag in strong_tags:
                text = strong_tag.get_text(strip=True)
                next_sibling = strong_tag.next_sibling
                if 'Истец' in text[:5]:
                    dict_values['Истец'] = next_sibling.strip() 
                if 'Ответ' in text[:5]:
                    dict_values['Ответчик'] = next_sibling.strip() 
                if 'Заявител' in text[:8]:
                    dict_values['Заявитель'] = next_sibling.strip() 

    return dict_values


async def get_page_title(url, context, semaphore: asyncio.Semaphore):
    """Асинхронно открывает страницу по URL и возвращает её заголовок."""
    async with semaphore:  # Правильное использование семафора с контекстным менеджером
        page = await context.new_page()
        try:
            await page.goto(url)
            await asyncio.sleep(2)
            await page.get_by_role("link", name="Документы").click()
            await asyncio.sleep(1)

            html = await page.content()
           
            async with page.expect_download() as download_info:
                await page.get_by_role("link", name="Скачать файл").click()
            download = await download_info.value
            
            path = await download.path()# Можно дождаться окончания скачивания и получить путь к загруженному файлу
            suggested_filename = download.suggested_filename # Получаем предложенное имя файла
            save_directory = rf'C:\Data\Visual Studio\Kursova_2\documents\{suggested_filename}'
            #======================================================
            path_for_bd = save_directory.split('\\')[-2:]
            path_for_bd = '\\'.join(path_for_bd)

            dict_value = get_info(html)
            dict_value['path'] = path_for_bd

            data = list(dict_value.values())
            flag = await async_insert_into_db(data)
            if flag:
                shutil.move(path, save_directory)

        except Exception as e:
            logger.error(f"Ошибка при открытии {url}: {e}", exc_info=True)
            print(f"Ошибка при открытии {url}: {e}")
        finally:
            await page.close()    
                 
        


async def run(playwright: Playwright, url_list):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(user_agent=UserAgent().random, accept_downloads=True)
    semaphore = asyncio.Semaphore(4)  # Ограничиваем количество одновременных задач
    tasks = [get_page_title(url, context, semaphore) for url in url_list]
    results = await asyncio.gather(*tasks)

    await browser.close()
    return results

# Получаем список ссылок из датафрейма
links = data['links'].tolist()
links = links[100:]
# links = ['https://mos-gorsud.ru/rs/gagarinskij/services/cases/civil/details/50750462-6d18-49a6-8cca-c2f3bb7ff0d2']


async def main(url_list:list):
    async with async_playwright() as playwright:
        results = await run(playwright, url_list)
        return results

# Запускаем асинхронный сбор информации
asyncio.run(main(links))

# with open('content2.html','w', encoding='utf-8') as f:
#     # for i in res:
#     #     f.write(i)
#     f.write(res[0])


