import time

import requests
import lxml.etree
import threading

import redis
import signal

# 连接数据库
r = redis.Redis()


START_URL = "http://qianmu.iguye.com/2018USNEWS世界大学排名"

# 线程池
threads = []
# 线程数
DOWNLOAD_NUM = 10
downloader_pages = 0
DOWNLOAD_DELAY = 0.3

thread_on = True


def fetch(url,raise_err=False):
    global downloader_pages
    print(url)
    try:
        response = requests.get(url)
    except Exception as e:
        # 网页页面的异常不会报错，try检测的是代码的异常
        print(e)
    else:
        downloader_pages += 1

        if raise_err:
            # 若页面不是200,会报错
            response.raise_for_status()

    return response.text.replace("\t","")

def parse(html):
    global link_queue

    html = lxml.etree.HTML(html)
    links = html.xpath('//*[@id="content"]/table/tbody//a/@href')[1:]

    for link in links:
        if not link.startswith('http://'):
            link = 'http://qianmu.iguye.com/%s' % link
        # link_queue.put(link)

        # 判断有咩有爬取过的
        if r.sadd('qianmu.seen',link):
            # 即将爬取的连接，有顺序
            r.lpush('qianmu.queue',link)


def parse_university(html):
    page = lxml.etree.HTML(html)
    school = page.xpath('//h1[@class="wikiTitle"]/text()')
    tabel = page.xpath('//*[@id="wikiContent"]/div[1]/table/tbody')
    if not tabel:
        return
    tabel = tabel[0]
    keys = tabel.xpath('./tr/td[1]//text()')
    cols = tabel.xpath('./tr/td[2]')
    values = [''.join(col.xpath('.//text()')) for col in cols]
    info = dict(zip(keys,values))
    print(school, info)
    r.lpush('qianmu.item',info)

def downloader(i):
    print('Thread-%s started' % i)

    while thread_on:
        link = r.rpop('qianmu.queue')
        if link :
            link = link.decode('utf-8')
            parse_university(fetch(link))
            print('Thread-%s %s remaing queue: %s' % (i,link,r.llen('qianmu.queue')))

        time.sleep(DOWNLOAD_DELAY)
    print('Thread-%s exited now' % i)


def sigint_handler(signum,frame):
    print('Recevied Ctrl+C,wait for exit gracefully')
    global thread_on
    thread_on = False

if __name__ == '__main__':
    start_time = time.time()
    parse(fetch(START_URL,raise_err=True))

    for i in range(DOWNLOAD_NUM):
        t = threading.Thread(target=downloader,args=(i+1,))
        t.start()
        threads.append(t)

    # 我们主动停止 就是给个信号
    signal.signal(signal.SIGINT,sigint_handler)

    for t in threads:
        t.join()

    cost_seconds = time.time() - start_time
    print('download %s pages,cost %s seconds'% (downloader_pages,cost_seconds))



