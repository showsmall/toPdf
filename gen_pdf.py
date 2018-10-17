#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# created on '2018/10/11'
__author__ = 'turbobin'

from bs4 import BeautifulSoup
import requests
from lxml import etree
import pdfkit
import os


def parse_url(url):
    header = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
    }
    response = requests.get(url, headers=header)
    return response.content


def get_url_list(url):
    response = parse_url(url)
    soup = BeautifulSoup(response, 'html.parser')
    urls = []
    for li in soup.find_all(class_="toctree-l1"):
        href = url + li.a.get("href")
        urls.append(href)

    # print(urls)
    return urls


def create_htmls(url, name):
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link href="https://pythonguidecn.readthedocs.io/zh/latest/_static/alabaster.css" rel="stylesheet" type="text/css">
    <link href="https://pythonguidecn.readthedocs.io/zh/latest/_static/pygments.css" rel="stylesheet" type="text/css">
    <link href="https://media.readthedocs.org/css/badge_only.css" rel="stylesheet" type="text/css">
    <link href="https://media.readthedocs.org/css/readthedocs-doc-embed.css" rel="stylesheet" type="text/css">
</head>
<body style>
    <div class="body" role="main">
    {content}
    </div>
</body>
</html>
    """
    print('正在请求:', url)
    response = parse_url(url)
    # 方法一：使用xpath
    # content = use_xpath_get_content(response)

    # 方法二：使用BeautifulSoup
    content = use_beautifulsoup_get_content(response)

    html = html_template.format(content=content)
    # 将图片链接补全
    html = html.replace('../_images/', 'https://pythonguidecn.readthedocs.io/zh/latest/_images/')

    with open(name, 'w', encoding='utf-8') as f:
        f.write(html)

    print('已生成', name)
    return name


def use_beautifulsoup_get_content(response):
    soup = BeautifulSoup(response, 'html.parser')
    body = soup.find_all(class_="body")[0]  # 获取内容体
    sections = body.find_all('div', {'class': 'section'}, recursive=False)
    content = ''
    for section in sections:
        content = content + str(section)
    return content


def use_xpath_get_content(response):
    element = etree.HTML(response)  # 返回一个element对象
    sections = element.xpath('//div[@class="body"]/div[@class="section"]')
    content = ''
    for section in sections:
        string = etree.tostring(section, encoding='utf-8', method='html', pretty_print=True, with_tail=False)
        content = content + string.decode('utf-8')
    return content


def save_to_pdf(htmls, file_name):
    """
    把所有html文件转成pdf文件
    :param htmls:  html文件列表
    :param file_name: pdf文件名
    :return:
    """
    print('正在转成pdf,请等待...')
    path_wkthmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    pdfkit.from_file(htmls, file_name, configuration=config)


def main():
    url = 'https://pythonguidecn.readthedocs.io/zh/latest/'
    url_list = get_url_list(url)
    # 其中有一个url请求的是相同的页面，将它剔除
    repeat_url = 'https://pythonguidecn.readthedocs.io/zh/latest/dev/virtualenvs.html#virtualenv'
    url_list = list(filter(lambda x: x != repeat_url, url_list))
    print('urls:', len(url_list))

    file_name = "Python编程之美-最佳实践指南.pdf"
    htmls = [create_htmls(url, f"{i}.html") for i, url in enumerate(url_list, start=1)]
    save_to_pdf(htmls, file_name)

    # 将生成的html文件删除
    for html in htmls:
        os.remove(html)


if __name__ == '__main__':
    main()
