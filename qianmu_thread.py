from queue import Queue
import requests
import lxml.etree
import threading
import time



START_URL = "http://qianmu.iguye.com/2018USNEWS世界大学排名"
# 队列
link_queue = Queue()
# 线程池
threads = []
# 线程数
DOWNLOAD_NUM = 10
downloader_pages = 0


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
        link_queue.put(link)


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

def downloader():
    while True:
        # 如果队列里面没有东西，会阻塞
        link = link_queue.get()

        if link is None:
            break

        parse_university(fetch(link))
        # 请求完毕，会删除
        link_queue.task_done()

        # 打印列表信息
        # qsize 获取队列长度
        print('remaining queue: %s'% link_queue.qsize())

if __name__ == '__main__':
    start_time = time.time()
    parse(fetch(START_URL,raise_err=True))

    for i in range(DOWNLOAD_NUM):
        t = threading.Thread(target=downloader)
        t.start()
        threads.append(t)

    link_queue.join()

    # 走到这里，队列里面已经没有东西了

    for i in range(DOWNLOAD_NUM):
        link_queue.put(None) # None 也是一个值

    for t in threads:
        t.join()

    cost_seconds = time.time() - start_time
    print('download %s pages,cost %s seconds'% (downloader_pages,cost_seconds))



