#encoding=utf-8
#爬取思路
#1、配置参数，向今日头条提交请求
#2、根据返回的数据（JSON）解析出文章的URL，分别向这些URL发送请求
#3、根据返回的数据（HTML）提取出文章标题和所有图片链接
#4、根据图片链接下载图片，保存至本地目录
#5、重新调整参数，获取新的文章，继续第一步
#容易被封，建议学习一下反爬技术

import os
import json
import urllib2
import urllib
import time
import re
import random
import socket
from lxml import etree
from socket import timeout as socket_timeout
import sys
reload(sys)
sys.setdefaultencoding('utf8')


#  网页下载，可复用
def download_page(url,headers,num_retries=2,data=None):
    print 'Downloading: ',url
    request = urllib2.Request(url,headers)
    try:
        response = urllib2.urlopen(request)
        html = response.read()
        code = response.code
    except  urllib2.URLError as e :
        print 'Download error: ',e.reason
        html = None
        if hasattr(e, 'code'):
            code = e.code
            if num_retries > 0 and 500 <= code < 600:
                # retry 5XX HTTP errors
                html = download_page(url, headers, num_retries - 1, data)
        else:
            code = None
    except ValueError:
        print "ValueError: Unknown url type"
        url = "http://"+url
        html = download_page(url, headers, num_retries, data)
    return html

#创建存放图片的文件夹
def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return path

#设置url的请求参数，其中data为参数字典，返回string
def set_params(data):
    return urllib.urlencode(data)

#从json中解析出每篇文章的url
def get_article_urls(url,headers,timeout=10):
    html = download_page(url,headers)
    if html is None:
        return None
    js = json.loads(html.decode())
    data = js.get('data')
    if data is None:
        return None
    else:
        urls = []
        for d in data:
            u = d.get('article_url')
            if u is not None:
                urls.append(u)
        return urls

#获取一篇文章的标题和图片的连接
def get_photo_urls(url,headers,timeout=10):
    html = download_page(url,headers)
    links = []
    if html is None:
        return 'default',links
    dom_tree = etree.HTML(html)

    heading = ''
    heading = dom_tree.xpath('//*[@id="article-main"]/h1/text()')
    links = dom_tree.xpath('//*[@id ="article-main"]/div[2]/div/p/img/@src')
    if len(heading)<= 0:
        return 'default',links
    else:
        return heading[0],links

#保存图片
def save_photos(photo_url,save_dir,timeout=10):
    photo_name = photo_url.rsplit('/', 1)[-1] + '.jpg'
    save_path = save_dir +'/' + photo_name
    print 'Saving file: ' + save_path
    file = open(save_path, 'wb')
    pt = urllib2.urlopen(photo_url).read()
    file.write(pt)
    file.close()

'''
url = "www.baidu.com"
headers = '{"Referer": "http://www.toutiao.com/search/?keyword=%E7%BE%8E%E5%A5%B3","User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}'
html = download_page(url,headers)
print len(html)
'''

if __name__=='__main__':
    headers = '{"Referer": "http://www.toutiao.com/search/?keyword=%E7%BE%8E%E5%A5%B3","User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}'
    keyword = raw_input("请输入搜索关键词：")
    offset = 0 #请求网页的网页偏移量，每次累加20
    root_dir = 'e:/DailyTT/Photos/'+ keyword.decode('utf-8');
    print 'Diretory: '+ root_dir
    create_dir(root_dir)    #创建图片存放目录

    #这是每一次爬取的等待时间，以防反爬
    wait = 2

    while True:
        query_data = {
            'offset':offset,
            'format':'json',
            'keyword':keyword,
            'autoload':'true',
            'count':20,
            'cur_tab':1
        }
        query_url = 'http://www.toutiao.com/search_content/'+  '?' +set_params(query_data)
        article_urls = get_article_urls(query_url,headers)

        # 如果不再返回数据，说明全部数据已经请求完毕，跳出循环
        if article_urls is None:
            break

        for url in article_urls:
            try:
                if url is None:
                    print "error url is None!!!!"
                print url
                article_heading,photo_urls = get_photo_urls(url,headers)
                #文章中没有图片，直接跳到下一篇文章
                if len(photo_urls)<= 0:
                    continue
                # 过滤掉了标题中在 windows 下无法作为目录名的特殊字符。
                dir_name = re.sub(r'[/:*?"<>|]', '', article_heading)
                download_dir = create_dir(root_dir+ '/'+dir_name)
                #开始下载文章中的图片
                for p_url in photo_urls:
                    # 由于图片数据以分段形式返回，在接收数据时可能抛出 IncompleteRead 异常
                    save_photos(p_url, save_dir=download_dir)
            except socket_timeout:
                print("连接超时了，休息一下...")
                time.sleep(random.randint(15, 25))
                continue
            except socket.error:
                print("服务器忙，休息一下...")
                time.sleep(random.randint(15, 25))
                continue

        #等待
        time.sleep(wait)

        # 偏移量每次请求累加20
        offset += 20
