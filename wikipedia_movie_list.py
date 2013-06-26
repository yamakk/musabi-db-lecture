#coding:utf-8

"""
歴代アカデミー作品賞ノミネート映画の予算と売上をDBに保存する
"""
import sys
import os
import re
import urllib2
import urllib
import json
import time
import glob
import pymongo
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup

htmlparser = HTMLParser()
db = pymongo.Connection().academy

coll = db.film

def urlopen(url):
    time.sleep(1)
    print '\trequest...%s'%url
    user_agent = 'Mozilla/5.0 (Windows NT 5.1; rv:14.0) Gecko/20100101 Firefox/14.0.1'
    req = urllib2.Request(url)
    req.add_header("User-agent", user_agent)
    u = urllib2.urlopen(req)
    return u

def save_academy_list():
    """アカデミー賞候補作品一覧 (英語)をDBに保存"""
    n = raw_input('%sを削除ok? (y/n)'%coll)
    if n != 'y':
        print 'skip... save_academy_list'
        return
    coll.remove()
    list_url = 'http://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture'
    u = urlopen(list_url)
    soup = BeautifulSoup(u)
    count = 0
    for table in soup.findAll('table', attrs={'class':'wikitable'}):
        year = table.find('big').find('a').text
        print 'save_academy_list parse...%s' % (year)
        gp_count = 0
        for td in table.findAll('tr')[1:]:
            if gp_count == 0:
                gp = True
            else:
                gp = False
            al = td.findAll('td')[0].find('a', attrs={'href':re.compile('/wiki.*?')})
            movie_link = 'http://en.wikipedia.org%s' % al.get('href')
            movie_title = htmlparser.unescape(al.text)
            movie_html = None
            item = dict(year=int(year),
                        title=movie_title,
                        gp=gp,
                        num=count,
                        poster=None,
                        html=movie_html,
                        link=movie_link)
            coll.save(item)
            gp_count +=1
            count += 1

def save_movie_html():
    """個別映画ページのhtmlをdbへ保存"""
    for item in coll.find({'html':None}):
        html = urlopen(item['link']).read()
        html = unicode(html, errors='replace')
        coll.update(item, {'$set':{'html':html}})
        print '%s %s %s' % ('save_movie_html', item['year'], item['title'])

def clean_numbers(s):
    """金額の表記をまとめる"""
    s = re.sub('\(worldwide\)', ' ', s, re.I)
    #s = re.sub('\(u\.*?s\)', ' ', s, re.I)
    s = re.sub('over', ' ', s, flags=re.I)
    s = re.sub('\(est.*?\)', ' ', s, flags=re.I)
    s = re.sub('\[\d\]',' ',s) # '[1]' -> ''
    s = re.sub('(\d,\d)', lambda m:m.group(1).replace(',',''), s) # '123,456' -> 12345
    s = re.sub('(\d{6,})', lambda m:str(float(m.group(1)) / (10 ** 6)), s)

    s = s.replace('$',' ')
    if 'million' in s:
        try:
            s = float(s.replace('million', ''))
        except ValueError:
            # 手作業しやすいようにERRを付与して元文字列を返す
            return 'ERR %s'%s
    else:
        try:
            s = float(s)
        except ValueError:
            return 'ERR %s'%s
    return s

def parse_budget():
    """db個別映画htmlからbudget, gainをparseしてdb更新
    <tr>
    <th scope="row" style="text-align:left;white-space: nowrap;;">Budget</th>
    <td>$40 million<sup id="cite_ref-boxofficemojo_1-1" class="reference">
    <a href="#cite_note-boxofficemojo-1"><span>[</span>1<span>]</span></a></sup></td>
    </tr>

    <tr>
    <th scope="row" style="text-align:left;white-space: nowrap;;">Box office</th>
    <td>$672,806,292<sup id="cite_" class="reference">
    <a href="#cite_note-boxofficemojo-1"><span>[</span>1<span>]</span></a></sup></td>
    </tr>
    """
    regex_budget = re.compile('budget', re.I)
    regex_boxoffice = re.compile('box *?office', re.I)
    count = 0
    budget_ok, boxoffice_ok = (0, 0)
    for item in coll.find({'year':{'$gt':1}}).skip(0):#{'html':{'$ne':None}}):
        html = item['html']
        soup = BeautifulSoup(html,convertEntities=BeautifulSoup.HTML_ENTITIES)
        bud_th = soup.find('th', text=regex_budget)
        gain_th = soup.find('th', text=regex_boxoffice)
        try:
            #print bud_th.find('td').text
            # budget = clean_numbers(bud_th.find('td').text)
            budget = clean_numbers(bud_th.parent.parent.find('td').text)
            budget_ok += str(budget).replace('.', '').isdigit() and 1 or 0
        except AttributeError:
            budget = None
        try:
            gain = clean_numbers(gain_th.parent.parent.find('td').text)
            boxoffice_ok += str(gain).replace('.', '').isdigit() and 1 or 0
        except AttributeError:
            gain = None
        updates = dict(budget=budget, budget_o=budget,
                       gain=gain, gain_o=gain, num=count)
        coll.update({'_id':item['_id']}, {'$set':updates})
        #print 'pase_budget {:5} b:{:<40} g:{:<40}  {}'.format( \
        #        count, budget, gain, item['link'])
        count += 1
    print budget_ok, boxoffice_ok

def save_poster(image_dir):
    """db個別映画htmlから写真を取得しローカルフォルダに保存 dbにファイル名保存"""
    if not os.path.isdir(image_dir):
        os.mkdir(image_dir)
    for item in coll.find({'poster':None}):
        html = item['html']
        soup = BeautifulSoup(html,convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            table = soup.find('table',{'class':re.compile('infobox.*?')}).findAll('img')
        except AttributeError:
            table = []
        for img in table:
            img_url = 'http:'+img.get('src')
            img_name = os.path.basename(img_url)
            img_name = urllib.unquote(img_name)
            img_data = urlopen(img_url).read()
            fp = open(os.path.join(image_dir, img_name), 'wb')
            fp.write(img_data)
            fp.close()
            coll.update({'link':item['link']},{'$set':{'poster':img_name}})
            print item['title'], '....OK'

def save_json(saved_path):
    """受賞作品を最初に、候補作品は収益,A-Z順に並べJSONへ"""
    l = []
    order = {}
    for item in coll.find({'year':{'$gt':1000}}).sort([('year',-1),('gain',1)]):
        if item['gp']:
            # gpは0番目
            odr = 0
        else:
            # それ以外(ノミネート)はA-Z順
            y = '%s'%item['year']
            order.setdefault(y, 1)
            odr = order[y]
            order[y] += 1
        item['order'] = odr
        item.pop('_id')
        item.pop('html')
        l.append(item)
        print item['order'], item['gp'], item['year'], item['budget']
    fp = open(saved_path,'w')
    js = json.dumps(l, ensure_ascii=False, indent=True)
    print js
    fp.write(js)
    fp.close()

def print_tsv(saved_path):
    """エクセル作業しやすいようにCSVに"""
    lines=[]
    keys = 'num, year, budget, budget_o, order, gp, gain_o, gain, link, title, poster'.split(',')
    keys = [k.strip() for k in keys]
    for i in json.load(open(saved_path)):
        line = []
        for k in keys:
            line.append(str(i[k]))
        lines.append('\t'.join(line))
    print '\t'.join(keys)
    print '\n'.join(lines)

def rename_image():
    """管理しやすいファイル名に変更 {year}-{gp}-{title}"""
    for item in coll.find():
        old = item['poster']
        if old:
            ext = re.search('\.(jpg|jpeg|gif|png|bmp)$',old,flags=re.I)
            ext = ext.group(1).lower()
            gp = item['gp'] and 'gp' or 'nm'
            new = '%s-%s-%s.%s' % (item['year'], gp,
                    re.sub('[\W]', '', item['title']), ext)
            item['poster'] = new
            coll.update({'_id':item['_id']}, item)
            _old = os.path.join('poster', old)
            _new = os.path.join('poster', new)
            os.rename(_old, _new)
            print item['title']
            print new
            print ''
def read_cpi():
    """消費者物価指数を取得
    US Consumer Price Index (CPI) / All Urban Consumer (CPI-U) - normalized CSV
    Main Consumer Price Index (there are many) from U.S. Department Of Labor Bureau
    of Labor Statistics for "All Urban Consumers - (CPI-U)". U.S. city average for all items and 1982-84=100.
    """
    url = "http://datahub.io/api/action/datastore_search?resource_id=27e14656-ba2a-4b81-855d-0f167809d87d&limit=5000"
    #for i in range():
    years = {}
    response = json.load(urllib.urlopen(url))
    for item in response['result']['records']:
        year = item['Date'].split('-')[0]
        value = item['Value']
        years.setdefault(int(year), value)
    return years

if __name__ == '__main__':
    #pass
    #save_academy_list()
    #save_movie_html()
    #parse_budget()
    #save_poster(image_dir='poster')
    #save_json('film.json')
    #print_tsv('film.json')
    #print read_cpi()
