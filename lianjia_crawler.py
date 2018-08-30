import requests
import time
import re
from lxml import etree

import toolkit_text
import toolkit_sqlite

import urllib3
urllib3.disable_warnings()

base_url = 'https://nj.lianjia.com'
zufang_url = base_url + '/zufang'

DEPLOY_SQL = 'deploy.sql'
DB_FILE = 'rent_house.db'

headers = {
    'Host': 'nj.lianjia.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',

}


def get_district():
    '''Return the district of the target city'''
    resposne = requests.get(zufang_url, headers=headers, verify=False)
    content = etree.HTML(resposne.text)
    districts = content.xpath('//*[@id="filter-options"]/dl[1]/dd/div')
    district_dict = []
    for i in districts[0].iter():
        district_dict.append({'district': i.text, 'district_url_suffix': i.attrib.get('href')})

    # print(district_dict)
    district_dict.remove({'district': None, 'district_url_suffix': None})
    district_dict.remove({'district': '不限', 'district_url_suffix': '/zufang/'})
    # print('Found district: ' + str(district_dict))
    # {'district': '秦淮', 'district_url_suffix': '/zufang/qinhuai/'}
    return district_dict


def get_total_page(district_url_suffix):
    '''Get the total page count'''
    district_full_url = base_url + district_url_suffix
    # print(district_full_url)
    resposne = requests.get(district_full_url, headers=headers, verify=False)
    content = etree.HTML(resposne.text)
    page_total = content.xpath('/html/body/div[4]/div[2]/div[2]/div[2]/div[2]')
    page_data = eval(page_total[0].attrib.get('page-data'))
    return page_data['totalPage']


def get_page_html(district_url_suffix, pageNo):
    '''Return the html page'''
    page_full_url = base_url + district_url_suffix + 'pg' + str(pageNo) + '/'
    print(page_full_url)
    resposne = requests.get(page_full_url, headers=headers, verify=False)
    # content = etree.HTML(resposne.text)
    return resposne.text


def get_house_list(district_url_suffix, html):
    '''Return the list of house id in every page'''
    content = etree.HTML(html)
    house_id = content.xpath('//*[@id="house-lst"]')
    house_id_list = []
    for i in house_id[0]:
        house_id_list.append(i.attrib.get('data-id'))
    # https://nj.lianjia.com/zufang/103102712630.html
    return house_id_list


def get_house_id(html_page):
    '''Retrieve all house ids on the webpage'''
    return toolkit_text.regex_find(r'(?<=data-housecode=").+?(?=")', html_page)


def get_house_detail(house_id, html_page):
    '''Return the detail of a house'''
    house_detail = {}
    root_xpath = '//*[@id="house-lst"]/li[@data-housecode="{}"]'.format(house_id)
    # print(content)
    content = etree.HTML(html_page)
    house_list = content.xpath(root_xpath)[0]
    # print(len(house_list))
    # print(dir(house_list[0]))
    # print(dir(house_list))
    # print(house_list.itertext)
    try:
        house_detail['house_id'] = house_id
        house_detail['complex'] = content.xpath(root_xpath + '/div[2]/div[1]/div[1]/a/span')[0].text.strip()
        house_detail['house_type'] = content.xpath(root_xpath + '/div[2]/div[1]/div[1]/span[1]/span')[0].text.strip()
        house_detail['area'] = content.xpath(root_xpath + '/div[2]/div[1]/div[1]/span[2]')[0].text.strip().replace('平米', '')
        house_detail['direction'] = content.xpath(root_xpath + '/div[2]/div[1]/div[1]/span[3]')[0].text.strip()
        house_detail['max_floor'] = toolkit_text.regex_find(r'\d+', content.xpath(root_xpath + '/div[2]/div[1]/div[2]/div/text()[1]')[0])[0]
        house_detail['floor_area'] = toolkit_text.regex_replace(r'\(.*\)', '', content.xpath(root_xpath + '/div[2]/div[1]/div[2]/div/text()[1]')[0])
        house_detail['rent'] = content.xpath(root_xpath + '/div[2]/div[2]/div[1]/span')[0].text.strip()
        house_detail['year'] = toolkit_text.regex_replace(r'\D+', '', content.xpath(root_xpath + '/div[2]/div[1]/div[2]/div/text()[2]')[0])
        house_detail['url'] = 'https://nj.lianjia.com/zufang/{}.html'.format(house_id)

    except Exception as e:
        # print(e)
        with open(time.strftime('%Y%m%d') + '.log', 'a') as f:
            f.write('-'*30 + ' ' + time.strftime('%Y%m%d_%H%M%S') + '' + '-'*30 + '\n')
            f.write(html_page)
            f.write('\n' + '.'*80)
            f.write(e)
            f.write('\n' + '.'*80)
    else:
        pass
    return house_detail


def get_house_detail_from_page(district_url_suffix, pageNo):
    # html_page = open('onepage.html', encoding = 'utf-8').read()
    # Get the district from suffix
    html_page = get_page_html(district_url_suffix, pageNo)

    g = lambda x: [i for i in district_dict if i['district_url_suffix'] == x][0]['district']
    house_detail_list = []
    for _house_id in get_house_id(html_page):
        detail_dict = get_house_detail(_house_id, html_page)
        detail_dict['district'] = g(district_url_suffix)
        house_detail_list.append(detail_dict)
    return house_detail_list


def insert_into_DB(house_detail_list):
    '''Insert house_detail_list dict into datebase'''
    insert_sql = '''INSERT INTO rent_info_nanjing (
                                  house_id,
                                  district,
                                  complex,
                                  house_type,
                                  area,
                                  direction,
                                  max_floor,
                                  floor_area,
                                  rent,
                                  year,
                                  url
                              )
                              VALUES (?,?,?,?,?,?,?,?,?,?,?);'''
    records = [(
                    i['house_id'],
                    i['district'],
                    i['complex'],
                    i['house_type'],
                    i['area'],
                    i['direction'],
                    i['max_floor'],
                    i['floor_area'],
                    i['rent'],
                    i['year'],
                    i['url'],
                    ) for i in house_detail_list]
    with toolkit_sqlite.SqliteDB(DB_FILE) as sqlitedb:
        sqlitedb.executemany(insert_sql, records)


if __name__ == '__main__':
    district_dict = get_district()
    with toolkit_sqlite.SqliteDB(DB_FILE) as sqlitedb:
        sqlitedb.create_database(DEPLOY_SQL)

    for d in district_dict:
        print('Fetching houses in district in {}'.format(d['district']))
        for pg in range(get_total_page(d['district_url_suffix'])):
            page = pg + 1
            print('Page #{}'.format(page))
            district_url_suffix, pageNo = d['district_url_suffix'], page
            insert_into_DB(get_house_detail_from_page(district_url_suffix, pageNo))
