import time
import random
import csv
import bs4
from requests_html import HTMLSession
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from proxy_info_password import login, password
import lxml
import requests
from random import randint
from time import sleep
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd

ua = UserAgent()

s = HTMLSession()

with open("proxy_list.txt", "r") as f:
    proxies = f.read().split("\n")

counter = 0

proxy = {"http": f'http://{login}:{password}@{proxies[counter]}',
         "https": f'http://{login}:{password}@{proxies[counter]}'}

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(f"user-agent={ua.random}")

ser = Service(executable_path="r'/Parser_test/chromedriver")
driver = webdriver.Chrome(service=ser, seleniumwire_options=proxy)


#  Получение страницы Металлопрокат в виде html файла (metalloprokat.html)
def get_page():
    url = 'https://23met.ru/price'

    r = s.get(url)

    # base_section_link = r.html.find('ul.tabs  li')
    #
    # for link in base_section_link:
    #     print(link.find('a'))

    with open('metalloprokat.html', 'w', encoding='utf-8') as file:
        file.write(r.text)

    time.sleep(1)
    base_section_urls(file_path="metalloprokat.html")


#  Получение ссылок подразделов страницы Металлопрокат в виде txt файла (metalloprokat_urls.txt)
def base_section_urls(file_path):
    with open(file_path, encoding="utf-8") as file:
        src = file.read()

    soup = BeautifulSoup(src, "lxml")
    base_section = soup.find_all("a")

    urls = []
    for item in base_section:
        base_section_url = item.get("href")
        urls.append(base_section_url)

    with open('metalloprokat_urls.txt', 'w') as file:
        for full_url in urls:
            if "https://" in full_url:
                continue
            else:
                file.write(f"https://23met.ru{full_url}\n")

    time.sleep(1)
    get_base_section_urls()


#  Переход по ссылкам подразделов страницы Металлопрокат для получения списка ссылок
#  размеров в виде txt файла (metalloprokat_size_url.txt), для дальнейшего прохода по ссылкам с просмотром информации
#  ПО ВСЕМ ГОРОДАМ.
#  Используются random для пауз, ротация proxy и смена UserAgent

def get_base_section_urls():
    headers = {'User-Agent': f"user-agent={ua.random}"}

    global counter

    list_item = open(file='metalloprokat_urls.txt', mode='r', encoding="utf-8").read().splitlines()

    for base_section_url in list_item:
        try:
            time.sleep(1)
            print(f"Using the proxy: {proxies[counter]}")
            time.sleep((random.randrange(5, 10)))
            r = s.get(base_section_url, headers=headers,
                      proxies={"http": f'http://{login}:{password}@{proxies[counter]}',
                               "https": f'http://{login}:{password}@{proxies[counter]}'})
            print(r.status_code)
            print(counter)

            block_div = r.html.find('div.panes  a')

            url_size = []
            for size_link in block_div:
                act = size_link.find('a', first=True).attrs['href']
                print(act)
                url_size.append(act)

            with open('metalloprokat_size_url.txt', 'a', encoding="utf-8") as file:
                for full_size_url in url_size:
                    file.write(f"https://23met.ru{full_size_url}\n")

        except Exception as ex:
            print(ex)
            print("Failed")
        finally:
            if counter == 149:
                counter = 0
            else:
                counter += 1

    # time.sleep(1)
    # get_size_url()


# Получение html страницы, с выбором всех городов.По ссылкам из metalloprokat_size_url.txt.Используются random для пауз,
# ротация proxy и смена UserAgent
def get_size_url():
    global counter

    list_item = open(file='metalloprokat_size_url.txt', mode='r', encoding='utf-8').read().splitlines()

    for base_section_url in list_item:
        try:
            print(f"Using the proxy: {proxies[counter]}")
            time.sleep((random.randrange(10, 20)))
            driver.get(base_section_url)
            driver.find_element(by=By.CSS_SELECTOR,
                                value="#load-dop-positions-container > div.load-dop-positions-input-radius-pretext."
                                      "citychooser_opener").click()
            time.sleep((random.randrange(5, 9)))
            driver.find_element(by=By.XPATH, value="/html/body/div[5]/table/tbody/tr/td[10]/div/input[1]").click()
            time.sleep((random.randrange(5, 9)))
            driver.find_element(by=By.XPATH, value="/html/body/div[5]/table/tbody/tr/td[10]/div/input[11]").click()
            time.sleep((random.randrange(5, 9)))

            if counter != 209:
                counter += 1
            else:
                counter = 0

            name = driver.title
            page_name = name.replace("/", "")

            print(driver.current_url)

            name_p = []

            with open(f'page/{page_name}.html', 'w', encoding='utf-8') as file:
                file.write(driver.page_source)

            name_p.append(f"{page_name}.html")
            with open('page/metalloprokat_page_name.txt', 'a', encoding='utf-8') as file:
                for i in name_p:
                    if i is not None:
                        file.write(f"{i}\n")
                    else:
                        continue

            print(name_p)
        except Exception as ex:
            print(ex)
            print("Failed")

    # time.sleep(1)
    # pars_page(file_path='page/metalloprokat_page_name.txt')


# Проход по полученным страницам. Преобразование их в csv файл.
def pars_page(file_path):
    with open(file_path, "r", encoding='utf-8') as fi:
        html_pages = fi.read().split("\n")

    name_csv_file = []

    for html_page in html_pages:
        try:
            table_data = pd.read_html(f'page/{html_page}')[0]

            name_doc = html_page.replace(" — купить. Цены .html", "")

            table_data.to_csv(f"page/ready_csv/metalloprokat_csv/{name_doc}.csv", index=False,
                              mode='a', encoding='cp1251')

            name_csv_file.append(f"{name_doc}.csv")
            with open('page/csv_file_metalloprokat_name.txt', 'a', encoding='utf-8') as file_csv:
                for i in name_csv_file:
                    file_csv.write(f"{i}\n")

        except Exception as ex:
            print(f"Failed: {ex}")


def main():
    # get_page()
    pars_page(file_path='page/metalloprokat_page_name.txt')


if __name__ == "__main__":
    main()
