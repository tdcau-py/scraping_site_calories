import json
import csv
import os.path
import re

from bs4 import BeautifulSoup
import requests


def dump_data_to_json(file_name: str, data: any, name_dir: str = None, mode: str = 'w'):
    """Записывает данные в json-файл"""
    dir_data = os.getcwd()

    if name_dir:
        dir_data = os.path.join(os.getcwd(), name_dir)

    with open(os.path.join(dir_data, file_name), mode, encoding='utf-8') as json_file:
        json.dump(
            obj=data,
            fp=json_file,
            ensure_ascii=False,
            indent=4,
        )

    return 'Создан json-файл.'


class CalorySiteScrape:
    def __init__(self, url: str) -> None:
        self.url = url

    @property
    def header(self):
        """Возварщает заголовок"""
        return {
            'Accept': '*/*',
            'User-Agent': 'Mozilla / 5.0 (Windows NT 10.0; Win64; x64; rv: 109.0) Gecko / 20100101 Firefox / 111.0',
        }

    def get_html(self) -> 'html':
        """Получает html-код страницы"""
        req = requests.get(self.url, headers=self.header)

        if req.text:
            return req.text

        return False


if __name__ == '__main__':
    site_dns = 'https://calorizator.ru/'
    site_url = 'https://calorizator.ru/product'

    print('Начало работы...\n')

    scrape_site = CalorySiteScrape(site_url)
    html_code = scrape_site.get_html()

    if html_code:
        with open('index.html', 'w', encoding='utf-8') as html_file:
            html_file.write(html_code)

        with open('index.html', 'r', encoding='utf-8') as file:
            html = file.read()

        all_categories_of_food = {}

        bs = BeautifulSoup(html, 'lxml')
        list_links_of_category = bs.find_all('li', class_=re.compile('prod*'))

        for category in list_links_of_category:
            item_name = category.text
            item_url = site_dns + category.a.get('href')

            all_categories_of_food[item_name] = item_url

        dump_data_to_json('all_categories_food.json', all_categories_of_food, mode='w')

        task_count = 1
        count = 0

        for name, url in all_categories_of_food.items():
            if not os.path.exists(os.path.join(os.getcwd(), 'data')):
                os.system('mkdir data')
                print('Создана папка data.')

            symbols = [" ", "-", "'"]

            for symb in symbols:
                if symb in name:
                    name = name.replace(symb, '_')

            parse_category = CalorySiteScrape(url)
            category_html = parse_category.get_html()
            bs = BeautifulSoup(category_html, 'lxml')

            if bs.find(class_='views-table'):
                page_title = bs.find('h1')
                print(f'\nПолучение данных из раздела "{page_title.text}"...')

                with open(f'data/{count}_{name}.html', 'w', encoding='utf-8') as html_file:
                    html_file.write(category_html)

                print('Создан файл html.')

                with open(f'data/{count}_{name}.html', 'r', encoding='utf-8') as html_file:
                    html = html_file.read()

                bs = BeautifulSoup(html, 'lxml')
                table_head = bs.find(class_='views-table').find('tr').find_all('a')
                th_text = [title.text for title in table_head]

                with open(f'data/{count}_{name}.csv', 'w', encoding='utf-8', newline='') as csv_file:
                    csvwriter = csv.writer(csv_file)
                    csvwriter.writerow(th_text)

                table_body = bs.find('table').find('tbody').find_all('tr')

                td_text = []

                for tr in table_body:
                    if tr.text:
                        td_text.append(tr.text.strip().split(' \n\n'))

                product_data = []
                data_titles = ['Title', 'Protein', 'Fat', 'Carbohydrate', 'Calories']

                with open(f'data/{count}_{name}.csv', 'a', encoding='utf-8', newline='') as csv_file:
                    csvwriter = csv.writer(csv_file)

                    for td in td_text:
                        csvwriter.writerow(td)

                        product_data.append(dict(zip(data_titles, td)))

                print('Создан файл csv.')

                dump_result = dump_data_to_json(f'{count}_{name}.json', product_data, 'data', 'w')
                print(dump_result)

                task_count += 1
                count += 1

            else:
                continue

        print('\nПарсинг завершен.')

    else:
        print('Страница не найдена или сервер недоступен.')
