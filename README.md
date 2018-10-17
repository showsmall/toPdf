
网址：https://pythonguidecn.readthedocs.io/zh/latest/

**准备工作**

爬取HTML页面转成PDF需要用到`wkhtmltopdf`工具，下载地址：https://wkhtmltopdf.org/downloads.html ，`pdfkit`是`wkhtmltopdf`的Python封装包，使用pip安装`pip install pdfkit`,提取网页信息可以用`BeautifulSoup`或`xpath`，安装：
```python
pip install BeautifulSoup
pip install lxml	# 注意，使用xpath，只需要安装lxml
```

**分析**
首先需要在首页提取出各目录的链接，只提取一级目录的URL就够了，子目录的内容在同一个页面：
![](https://i.imgur.com/SeizBs7.png)

**获取目录的所有URL请求列表**
按F12打开开发者工具，发现所有的一级目录链接都在`<li class="toctree-l1">`节点下，使用BeautifulSoup可以很方便把所有URL提取出来，这里URL需要手动补全：
![](https://i.imgur.com/VAATGRe.png)

上代码：
```python
from bs4 import BeautifulSoup
import requests


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
```
**爬取所需内容制作HTML**
接下来是重点。先打开一个目录的链接看看，有三部分组成，1是左边栏，有一些说明介绍，我们不关心，2是广告，忽略，3是主要内容体，也是我们要提取的内容，节点存在于`class="body"`的 `class="section"`中。
![](https://i.imgur.com/uEXOb5C.png)

再来打开一个链接，也是一样的结构，只不过这里有两个`class="section"`。
![](https://i.imgur.com/s7SCx0F.png)

开始写代码：
首先构造一个HTML头，预留出内容体的部分待填充
```python
def create_htmls(url, name):
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body style>
    <div class="body" role="main">
    	{content}	# 预留出内容体占位
    </div>
</body>
</html>
    """

    print('正在请求:', url)
    response = parse_url(url)	# 发送请求。parse_url()函数在上述代码已体现
```
下面分别使用xpath和BeautiSoup来提取内容

方法一：使用xpath。先导入etree,构造一个element对象  
`from lxml import etree`
再用xpath语法提取出所有的section中内容，使用etree.tostring()转成字符串，注意这里转成的是byte类型，需要解码。
```python
def use_xpath_get_content(response):
    element = etree.HTML(response)  # 返回一个element对象
    sections = element.xpath('//div[@class="body"]/div[@class="section"]')
    content = ''
    for section in sections:
        string = etree.tostring(section, encoding='utf-8', method='html', pretty_print=True, with_tail=False)
        content = content + string.decode('utf-8')
    return content
```

方法二：使用BeautifulSoup。先找到`class="body"`，然后使用find_all()找出所有的`class="section"`，recursive=False表示只搜索标签下的直接子节点(一级节点)。

```python
def use_beautifulsoup_get_content(response):
    soup = BeautifulSoup(response, 'html.parser')
    body = soup.find_all(class_="body")[0]  # 获取内容体
    sections = body.find_all('div', {'class': 'section'}, recursive=False)
    content = ''
    for section in sections:
        content = content + str(section)
    return content
```
**生成HTML文件**
取回内容之后，把之前的html头加上，就可以生成文件了。
```python
html = html_template.format(content=content)
# 将图片链接补全
html = html.replace('../_images/', 'https://pythonguidecn.readthedocs.io/zh/latest/_images/')

with open(name, 'w', encoding='utf-8') as f:
    f.write(html)

print('已生成', name)
return name
```

**把HTML转成PDF**
导入pdfkit包，传入HTML文件名(可以是单个也可以是文件名列表)和需要生成的pdf文件名
```python
def save_to_pdf(htmls, file_name):
    """
    把所有html文件转成pdf文件
    :param htmls:  html文件列表
    :param file_name: pdf文件名
    :return:
    """
    print('正在转成pdf,请等待...')
	# 这里配置成你的wkhtmltopdf安装路径
    path_wkthmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    pdfkit.from_file(htmls, file_name, configuration=config)
```

写个主函数把所有步骤串起来。
这里遇到一个问题，有一个URL和前一个URL请求的是同一个页面，生成了多个相同的HTML，在列表中把这个URL全部剔除，还记得上一篇干货Python列表元素的去重吗：
```python
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
```
来看看生成的效果：
![](https://i.imgur.com/oB0oKiW.png)

这...跟网页相比好像有点丑啊，难道忙活了一场就为了这个？
别急，我们在HTML的head部分加上css的链接试试：
```python
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
```
再生成一遍看看效果：
![](https://i.imgur.com/JZ2S5BF.png)

跟原网页一模一样，简直完美~

**后记**
授人以鱼不如授人以渔。
相信做过这个爬虫之后，以后想要网上任何的官方文档、教程，都能爬下来制作PDF电子书。想要廖大神的Python教程？爬！想要Git教程？爬！想要刘江的Django教程？爬！

---
关注本公众号「Python手记」，后台回复：Python指南 即可免费获取，不套路。之后也会送出其他教程，敬请期待。