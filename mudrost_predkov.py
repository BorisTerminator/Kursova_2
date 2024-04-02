from playwright.sync_api import Playwright, sync_playwright, expect
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
import aiosqlite
import asyncio

# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=True)
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto(f"https://mos-gorsud.ru/rs/nagatinskij/services/cases/civil/details/e9d807b9-e34c-42b1-b546-60abc9d82a35")
#     page.get_by_role("link", name="Документы").click()
#     time.sleep(5)
#     html =  page.content()
#     # ---------------------
#     context.close()
#     browser.close()
#     return html



# with sync_playwright() as playwright:
#     html_content = run(playwright)

# with open('content3.html', 'w', encoding='utf-8') as f:
#     # for i in res:
#     #     f.write(i)
#     f.write(html_content)



# # Переключаемся на мягкий режим, используя page.locator(). Это позволит нам работать с несколькими элементами.
# links_locator = page.locator('a:has-text("Скачать файл")')

# # Считаем количество элементов, которые соответствуют селектору.
# links_count = await links_locator.count()

# for i in range(links_count):
#     # На каждой итерации цикла ждём новую загрузку.
#     async with page.expect_download() as download_info:
#         # Кликаем по каждой ссылке для скачивания. Используем nth() для выбора конкретного элемента из набора.
#         await links_locator.nth(i).click()
        
#     # Получаем объект загрузки.
#     download = await download_info.value
    
#     # Ожидаем завершения скачивания и получаем путь к файлу.
#     path = await download.path()
    
#     # Далее можете переместить файл из временной папки, если это необходимо,
#     # используя suggested_filename для сохранения файла под исходным именем.
#     print(f'Файл был скачан и сохранён в: {path}')


# Чтобы скачать все файлы, когда на странице присутствует несколько ссылок с одинаковым текстом (например, "Скачать файл"), и вы не можете использовать get_by_role в строгом режиме (strict mode) из-за ошибки о нарушении строгого режима, можно применить следующий подход:

# Используйте page.locator с методом element_handles() для получения всех элементов, соответствующих селектору.
# Переберите все найденные элементы, инициируя скачивание для каждого из них.
# Вот пример кода, который демонстрирует, как это можно сделать:

with open('content3.html','r', encoding='utf-8') as f:
    response = f.read()
soup = BeautifulSoup(response, 'html.parser')


def get_info(html_fragment):
    dict_values = {
    'id':None,
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
    'path':'asdad'}

    html_fragment = soup.find_all(class_='row_card') # ищем всю нужную информацию 

    for html in html_fragment:

        key = html.find(class_='left').get_text(strip=True)
        
        if key == 'Номер дела ~ материала':
            key = key.replace('\n','').replace(' ','')
            
        if key in dict_values.keys():
            value = html.find(class_='right').get_text(strip=True)
            dict_values[key] = value
            
        if key == 'Стороны': # обработка поля Стороны
            strong_tags = html.find_all('strong')
            for strong_tag in strong_tags:
                text = strong_tag.get_text(strip=True)
                next_sibling = strong_tag.next_sibling
                if 'Истец' in text[:5]:
                    dict_values['Истец'] = next_sibling.strip() if next_sibling else None
                if 'Ответ' in text[:5]:
                    dict_values['Ответчик'] = next_sibling.strip() if next_sibling else None
                if 'Заявител' in text[:8]:
                    dict_values['Заявитель'] = next_sibling.strip() if next_sibling else None
    return dict_values
info = get_info(soup)





# async def async_insert_into_db(data):
#     async with aiosqlite.connect('legal_cases.db') as db:  # Асинхронное подключение к базе данных
#         async with db.cursor() as cursor:  # Асинхронное получение курсора
#             unique_ident_case, case_number, complaint_number = data[1:4]
#             sql = f'SELECT Уникальный_идентификатор_дела, Номер_дела, Номер_жалобы WHERE {unique_ident_case, case_number, complaint_number}'
#             placeholders = ', '.join(['?'] * len(data))
#             query = f"INSERT INTO collection VALUES ({placeholders})"
#             await cursor.execute(query, data)  
#             await db.commit()  


# async def main():
#     data = list(info.values())
#     await async_insert_into_db(data)

# asyncio.run(main())

async def async_insert_into_db(data):
    async with aiosqlite.connect('legal_cases.db') as db:  # Асинхронное подключение к базе данных
        async with db.cursor() as cursor:  # Асинхронное получение курсора
            # Извлечение значений для проверки уникальности
            unique_ident_case, case_number, complaint_number = data[1], data[2], data[3]

            # Подготовка SQL-запроса для поиска существующих записей
            sql = '''SELECT Уникальный_идентификатор_дела, Номер_дела, Номер_жалобы FROM collection 
            WHERE Уникальный_идентификатор_дела = ? or Номер_дела = ? or Номер_жалобы = ?'''

            await cursor.execute(sql, (unique_ident_case, case_number, complaint_number))
            result = await cursor.fetchone()
            print(result)

            # Если запись не найдена, выполняем вставку
            if not result:
                placeholders = ', '.join(['?'] * len(data))
                query = f"INSERT INTO collection VALUES ({placeholders})"
                await cursor.execute(query, data)
                await db.commit()
            else:
                print("Запись уже существует в базе данных.")

async def main():
    # Здесь должен быть ваш код для заполнения переменной `data`
    # Пример данных для `data`
    data = list(info.values())
    # data = (None, 'unique_id', 'case_number', 'complaint_number', 'Дополнительные', 'значения', 'и', 'так', 'далее')
    await async_insert_into_db(data)

# Запуск асинхронного main
asyncio.run(main())