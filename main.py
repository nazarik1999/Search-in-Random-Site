import os
import re
from stop_words import get_stop_words
import xml.etree.ElementTree as ET
from nltk import FreqDist
import pymorphy2
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

# Создаём список файлов в папке
files = []

# добавляем анализатор слов
morph = pymorphy2.MorphAnalyzer()

# Указываем путь к папке
path_text = 'texts'

# Массив имён файлов
mas_file_name = []

# Массив ключевых слов
mas_name = []

# Массив частот употребления слов в тексте
mas_str_count = []

# Массив для новых файлов
mas_new_keywords = []


def save_page_text(url, limit=2):
    # Проверка ограничения на количество файлов
    if limit <= 0:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Используем BeautifulSoup для извлечения заголовка страницы
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip()

            # Очищаем недопустимые символы из заголовка, чтобы создать имя файла
            title = ''.join(char for char in title if char.isalnum() or char.isspace())
            filename = f"{title}.txt"

            # Создаем и записываем текстовый файл
            with open(path_text + '/' + filename, 'w', encoding='utf-8') as file:
                file.write(soup.get_text())

            print(f"Сохранено: {filename}")

            # Уменьшаем ограничение и ищем ссылки на другие страницы
            limit -= 1
            if limit > 0:
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = link['href']
                    if next_url.startswith("http"):
                        save_page_text(next_url, limit)
    except Exception as e:
        print(f"Ошибка при обработке {url}: {str(e)}")


# Формирование XML и HTML файлов
def keywords_most_freq_with_stop(some_text, file_name):
    stop_words = get_stop_words("ru")

    # Разделение на слова
    tokenized_text = re.findall(r'\b\w+\b', some_text.lower())

    # Приведение к нормальной форме
    tokenized_text = [morph.parse(word)[0].normal_form for word in tokenized_text if word not in stop_words]

    # <keyword "name">
    pair_name = [word_freq_pair[0] for word_freq_pair in FreqDist(tokenized_text).most_common(3)]
    # <keyword "count">
    pair_count = [word_freq_pair[1] for word_freq_pair in FreqDist(tokenized_text).most_common(3)]

    # Формирование XML - файла
    dataXML = ET.Element('data')
    dataXML.text = '\n  '

    textXML = ET.SubElement(dataXML, 'text')
    textXML.text = ' ' + text + '\n  '
    textXML.tail = '\n  '

    keywordsXML = ET.SubElement(dataXML, 'keywords')
    keywordsXML.text = '\n    '

    # В данном цикле используем анализатор слов для приведения к именительному падежу
    for name, count in zip(pair_name, pair_count):
        word_noun = name
        p = morph.parse(word_noun)[0].normal_form
        # Добавляем ключевые слова
        keywordXML = ET.SubElement(keywordsXML, 'keyword')
        keywordXML.set('name', "".join(p))
        str_count = str(count)
        keywordXML.set('count', str_count)
        keywordXML.tail = '\n '
        keywordXML.tail = '\n    '
        keywordsXML.tail = '\n'
        mas_name.append(p)
        mas_file_name.append(file_name)
        mas_str_count.append(str_count)

    # Сохраняем xml - файл
    tree = ET.ElementTree(dataXML)
    tree.write('XML/' + file_name[:-3] + 'xml', xml_declaration=True, encoding='utf-8')

    # Формирование html файла
    dataHTML = ET.Element('html')
    dataHTML.set('lang', 'en')
    dataHTML.text = '\n'

    headHTML = ET.SubElement(dataHTML, 'head')
    headHTML.text = '\n  '
    headHTML.tail = '\n'

    metaHTML = ET.SubElement(headHTML, 'meta')
    metaHTML.set('charset', 'UTF-8')
    metaHTML.set('name', 'viewport')
    metaHTML.set('content', 'width=device-width, initial-scale=1.0')
    metaHTML.tail = '\n  '

    titleHTML = ET.SubElement(headHTML, 'title')
    titleHTML.text = '' + path_text + '/' + file_name
    titleHTML.tail = '\n'

    bodyHTML = ET.SubElement(dataHTML, 'body')
    bodyHTML.text = '\n    '
    bodyHTML.tail = '\n'

    pHTML = ET.SubElement(bodyHTML, 'p')
    pHTML.text = ' ' + text + '\n'

    treeHTML = ET.ElementTree(dataHTML)
    treeHTML.write('HTML/' + file_name[:-3] + 'html', encoding='utf-8')

# Формирование ссылок в HTML
def set_links_in_files():
    # Получаем ссылку на ключевое слово в документе
    res_mas = zip(mas_name, zip(mas_str_count, mas_file_name))
    masDict = defaultdict(list)

    for key, val in res_mas:
        masDict[key].append(val)
    for key in masDict:
        masDict[key] = sorted(masDict[key], reverse=True)
        if (len(masDict[key]) > 1):
            masDictRes = masDict[key]
            # print(masDictRes)
            for i in range(len(masDictRes)):
                key_word = key
                count_key_word = masDictRes[i][0]
                # print(key_word, count_key_word)
                for j in range(len(masDictRes)):
                    if (masDictRes[j][0] < count_key_word):
                        # print(masDictRes[j][0], count_key_word)
                        print(key_word, count_key_word, masDictRes[i][1], masDictRes[j][1])
                        with open('HTML/' + masDictRes[i][1][:-3] + 'html', 'r', encoding='utf-8') as f:
                            textHTML = f.read()
                            f.close()

                        link = '<a href="' + masDictRes[j][1][:-3] + 'html" target="_blank">' + key_word + '</a>'
                        textHTML_new = textHTML.replace(' ' + key_word, ' ' + link)

                        text_file = open('HTML/' + masDictRes[i][1][:-3] + 'html', "w", encoding='utf-8')
                        n = text_file.write(textHTML_new)
                        text_file.close()
                        break


starting_url = input("Введите URL начальной страницы: ")
save_page_text(starting_url)

files = os.listdir(path_text)

for filename in files:
    with open(path_text + '/' + filename, 'r', encoding='utf-8') as f:
        text = f.read()
    # Вызываем функцию создания файлов
    keywords_most_freq_with_stop(text, filename)

# Вызываем функцию генерации ссылок
set_links_in_files()

