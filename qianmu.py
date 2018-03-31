import requests
import lxml.etree

START_URL = "http://qianmu.iguye.com/2018USNEWS%E4%B8%96%E7%95%8C%E5%A4%A7%E5%AD%A6%E6%8E%92%E5%90%8D"
link_queue = []

def fetch(url):
    print(url)
    response = requests.get(url)
    return response.text.replace("\t","")

def parse(html):
    global link_queue

    html = lxml.etree.HTML(html)
    links = html.xpath('//*[@id="content"]/table/tbody//a/@href')[1:]
    link_queue = links



def parse_university(html):
    page = lxml.etree.HTML(html)
    tabel = page.xpath('//*[@id="wikiContent"]/div[1]/table/tbody')
    if not tabel:
        return
    tabel = tabel[0]
    keys = tabel.xpath('./tr/td[1]//text()')
    cols = tabel.xpath('./tr/td[2]')
    values = [''.join(col.xpath('.//text()')) for col in cols]
    info = dict(zip(keys,values))
    print(info)



if __name__ == '__main__':
    parse(fetch(START_URL))

    for link in link_queue:
        if not link.startswith('http://'):
            link = 'http://qianmu.iguye.com/%s' % link

        parse_university(fetch(link))


