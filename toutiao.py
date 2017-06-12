#encoding=utf-8
#爬取思路
#1、配置参数，向今日头条提交请求
#2、根据返回的数据（JSON）解析出文章的URL，分别向这些URL发送请求
#3、根据返回的数据（HTML）提取出文章标题和所有图片链接
#4、根据图片链接下载图片，保存至本地目录
#5、重新调整参数，获取新的文章，继续第一步

#以下原型，后续可以模块化
import urllib2
import json
import os
from bs4 import BeautifulSoup

url = "http://www.toutiao.com/search_content/?offset=0&format=json&keyword=%E8%A1%97%E6%8B%8D&autoload=true&count=10&cur_tab=1"
headers = '{"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}'

request = urllib2.Request(url,headers)
response = urllib2.urlopen(request)
html = response.read()
js = json.loads(html.decode())

data = js.get('data')
urls = []
for d in data:
    u = d.get('article_url')
    urls.append(u)

#创建目录，存放图片
path = "e:/meinv"
if not os.path.exists(path):
    os.makedirs(path)

for u in urls:
    req = urllib2.Request(u,headers)
    res = urllib2.urlopen(req)
    html = res.read()
    soup = BeautifulSoup(html.decode(errors='ignore'), 'html.parser')
    article_main = soup.find('div',id='article-main')
    if article_main is not None:
        for img in article_main.find_all('img'):
            photo_url = img.get('src')
            photo_name = photo_url.rsplit('/', 1)[-1] + '.jpg'
            save_path = path + "/" + photo_name
            file = open(save_path,'wb')
            pt = urllib2.urlopen(photo_url).read()
            file.write(pt)
            file.close()