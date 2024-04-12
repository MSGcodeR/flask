from flask import Flask, request, jsonify
import requests
import time
import hmac
import hashlib
import base64
import sys
import pandas as pd
from lxml import html
import urllib.parse
from powernad.API import RelKwdStat
import xml.etree.ElementTree as ET
import datetime
from playwright.sync_api import sync_playwright


application = Flask(__name__)


class NaverSearchAdAPI:
    def __init__(self, base_url, api_key, secret_key, customer_id):
        self.base_url = base_url
        self.api_key = api_key
        self.secret_key = secret_key
        self.customer_id = customer_id

    def get_keyword_search_volume(self, keyword):
        endpoint = "/keywordstool"
        url = self.base_url + endpoint
        headers = self._generate_headers("GET", endpoint)
        params = {
            "hintKeywords": keyword,
            "showDetail": 1
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            search_stats = data.get('keywordList', [])
            if search_stats:
                pc_search_volume = search_stats[0]['monthlyPcQcCnt']
                mobile_search_volume = search_stats[0]['monthlyMobileQcCnt']
                return pc_search_volume, mobile_search_volume
            else:
                return None, None
        else:
            return None, None

    def _generate_signature(self, timestamp, method, path):
        sign = f"{timestamp}.{method}.{path}"
        signature = hmac.new(self.secret_key.encode(), sign.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def _generate_headers(self, method, path):
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path)
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.api_key,
            "X-Customer": str(self.customer_id),
            "X-Signature": signature
        }


BASE_URL = "https://api.searchad.naver.com"
API_KEY = "0100000000f1b76c59956c966d9684007339f1ae37fb047600514c38b3f42e359886a2adfc"
SECRET_KEY = "AQAAAADxt2xZlWyWbZaEAHM58a43p2dgCtowNcLExLFTrb4nIQ=="
CUSTOMER_ID = 3116243


def get_blog_search_results(keyword):
    url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={urllib.parse.quote(keyword)}"
    response = requests.get(url)
    tree = html.fromstring(response.content)
    xpath_list = [
        '//*[@id="main_pack"]/section/div[1]/ul/li[1]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[2]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[3]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[4]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[5]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[6]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[7]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[8]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[9]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[10]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[11]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[12]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[13]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[14]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[15]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[16]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[17]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[18]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[19]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[20]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[21]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[22]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[23]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[24]/div/div[2]/div[1]/a',
        '//*[@id="main_pack"]/section/div[1]/ul/li[25]/div/div[2]/div[1]/a',
    ]
    results = []
    idx = 1  # 번호를 순차적으로 부여하기 위한 변수
    for xpath in xpath_list:
        element = tree.xpath(xpath)
        if element:
            result_text = f"{idx}. {element[0].text_content().strip()}"
            results.append(result_text)
            idx += 1

    results_text = "\n\n".join(results[:10])  # 최대 10개의 결과만 가져옴
    search_url = f"\n\n*검색결과 URL : {url}"
    return results_text, search_url


def get_place_search_results(keyword):
    url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={urllib.parse.quote(keyword)}"

    response = requests.get(url)
    tree = html.fromstring(response.content)

    count = 1
    top_results = []

    for i in range(1, 9):  # 1부터 8까지의 순번에 해당하는 결과를 가져옴
        result_element_xpath = f'//*[@id="loc-main-section-root"]/section/div/div[3]/ul/li[{i}]'
        result_element = tree.xpath(result_element_xpath)
        if not result_element:
            # 첫 번째 XPath로 결과를 가져오지 못하면 두 번째 XPath를 사용하여 가져옴
            result_element_xpath = f'//*[@id="place-main-section-root"]/section/div/div[4]/ul/li[{i}]'
            result_element = tree.xpath(result_element_xpath)
            if not result_element:
                # 두 번째 XPath로 결과를 가져오지 못하면 세 번째 XPath를 사용하여 가져옴
                result_element_xpath = f'//*[@id="place-main-section-root"]/section[1]/div/div[6]/ul/li[{i}]'
                result_element = tree.xpath(result_element_xpath)
                if not result_element:
                    # 두 번째 XPath로 결과를 가져오지 못하면 세 번째 XPath를 사용하여 가져옴
                    result_element_xpath = f'//*[@id="loc-main-section-root"]/section/div/div[4]/ul/li[{i}]'
                    result_element = tree.xpath(result_element_xpath)

        if result_element:
            # 결과가 존재하면 광고인지 확인하고 출력
            ad_element_xpath = f'{result_element_xpath}//span[contains(text(), "광고")]'
            ad_element = tree.xpath(ad_element_xpath)
            if not ad_element:
                # 만약 광고에 해당하는 텍스트가 없으면 결과를 추가
                result_text_xpath = f'{result_element_xpath}//a[1]/div/div/span[1]'
                result_text = tree.xpath(result_text_xpath)
                if result_text:
                    top_results.append(f"TOP{count}: {result_text[0].text_content().strip()}")
                    count += 1
                else:
                    top_results.append(f"TOP{count}: No text content found for result {i}.")
        else:
            top_results.append(f"TOP{count}: 등록되지 않았습니다.")
            break

    return top_results


@application.route('/keyword_analyze', methods=['POST'])
def keyword_analyze():
    # 발화값을 입력값으로 받기
    data = request.get_json()
    keyword = data["userRequest"]["utterance"]

    if '#' in keyword:
        keyword = keyword[:-1]  # '#' 제거
        result = record_keyword(keyword)
    # '@'이 있으면 함수B 실행
    elif '@' in keyword:
        keyword = keyword[:-1]  # 마지막 글자 제거
        result = record_view(keyword)

    # '$'이 있으면 함수C 실행
    elif '$' in keyword:
        keyword = keyword[:-1]  # 마지막 글자 제거
        result = record_place(keyword)

    # '%'이 있으면 함수D 실행
    elif '%' in keyword:
        keyword = keyword[:-1]  # 마지막 글자 제거
        result = related_keywords(keyword)

    # '^'이 있으면 함수E 실행
    elif '^' in keyword:
        keyword = keyword[:-1]  # 마지막 글자 제거
        result = record_visitor(keyword)

    # '&'이 있으면 함수F 실행
    elif '&' in keyword:
        keyword = keyword[:-1]  # 마지막 글자 제거
        result = record_CPC(keyword)

    return result


# '#'이 있을 경우
def record_keyword(keyword):
    # 네이버 검색 광고 API로부터 검색량 가져오기
    naver_api = NaverSearchAdAPI(BASE_URL, API_KEY, SECRET_KEY, CUSTOMER_ID)
    pc_search_volume, mobile_search_volume = naver_api.get_keyword_search_volume(keyword)

    if pc_search_volume is not None and mobile_search_volume is not None:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"■ 키워드 검색량 조회\n\n키워드: {keyword}\nPC: {pc_search_volume},\n모바일: {mobile_search_volume}\n\n*최근 1개월 검색량\n\n______________________\n01. 검색량 조회\n:키워드 + #\n\n02. 블로그 탭 순위\n:키워드 + @\n\n03. 플레이스 순위\n:키워드 + $\n\n04. 쇼핑연관검색어 조회\n:키워드 + %\n\n05. 파워링크 단가 조회\n:키워드 + &\n"
                        }
                    }
                ]
            }
        }
    else:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "키워드에 대한 검색 정보가 없습니다."
                        }
                    }
                ]
            }
        }

    return jsonify(response)


def record_view(keyword):
    # 키워드로 블로그 검색 결과 가져오기
    results_text, search_url = get_blog_search_results(keyword)

    if results_text:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"■ 블로그 탭 1~10위\n\n{results_text}{search_url}\n\n\n______________________\n01. 검색량 조회\n:키워드 + #\n\n02. 블로그 탭 순위\n:키워드 + @\n\n03. 플레이스 순위\n:키워드 + $\n\n04. 쇼핑연관검색어 조회\n:키워드 + %\n\n05. 파워링크 단가 조회\n:키워드 + &\n"
                        }
                    }
                ]
            }
        }
    else:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "검색 결과가 없습니다."
                        }
                    }
                ]
            }
        }
    return jsonify(response)


# 함수C
def record_place(keyword):
    # 키워드로 플레이스 검색 결과 가져오기
    keyword_info = get_place_search_results(keyword)

    # Generate the response structure
    if keyword_info:
        response_text = f"■ 플레이스 순위\n\n키워드: {keyword}\n\n" + "\n\n".join(
            keyword_info) + "\n\n*플레이스 광고 제외\n\n\n______________________\n01. 검색량 조회\n:키워드 + #\n\n02. 블로그 탭 순위\n:키워드 + @\n\n03. 플레이스 순위\n:키워드 + $\n\n04. 쇼핑연관검색어 조회\n:키워드 + %\n\n05. 파워링크 단가 조회\n:키워드 + &\n"
    else:
        response_text = "플레이스 정보를 찾을 수 없습니다."

    response = {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": response_text}}]}}

    return jsonify(response)


# 함수D
def related_keywords(keyword):
    relKwdsStat = RelKwdStat.RelKwdStat(BASE_URL,
                                        API_KEY,
                                        SECRET_KEY,
                                        CUSTOMER_ID
                                        )
    kwdDataList = relKwdsStat.get_rel_kwd_stat_list(None, hintKeywords=keyword, showDetail='1')
    keyword_info = []
    for outdata in kwdDataList[:10]:  # 최대 10개만 출력
        keyword_info.append({
            "연관 키워드": outdata.relKeyword,
            "PC": outdata.monthlyPcQcCnt,
            "모바일": outdata.monthlyMobileQcCnt,
            "경쟁율": outdata.compIdx
        })

    text = "■ 쇼핑 연관검색어\n\n\n"
    for idx, info in enumerate(keyword_info):
        text += f"연관 키워드: {info['연관 키워드']}\n"
        text += f"PC({info['PC']})\n"
        text += f"모바일({info['모바일']})\n"
        text += f"경쟁율({info['경쟁율']})\n\n"

    text += "\n\n______________________\n01. 검색량 조회\n:키워드 + #\n\n02. 블로그 탭 순위\n:키워드 + @\n\n03. 플레이스 순위\n:키워드 + $\n\n04. 쇼핑연관검색어 조회\n:키워드 + %\n\n05. 파워링크 단가 조회\n:키워드 + &\n"

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    }

    return jsonify(response)


# 함수E
def record_visitor(keyword):
    naver_id = keyword

    try:
        visitor = get_visitor(naver_id)

        response = ""
        # 첫 번째 노드를 제외하고 출력합니다.
        for node in visitor.findall('visitorcnt')[1:]:
            # 날짜 형식을 변경하여 출력합니다.
            date_str = datetime.datetime.strptime(node.get('id'), "%Y%m%d").strftime("%Y.%m.%d")
            response += f"{date_str}: {node.get('cnt')}명\n"

        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": response}}]}})

    except Exception as e:
        print("에러 발생: ", e)
        response = "오류가 발생했습니다."
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": response}}]}})


def get_visitor(naver_id):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://blog.naver.com/NVisitorgp4Ajax.nhn?blogId=" + naver_id, headers=headers, timeout=5)
        return ET.fromstring(res.text)
    except Exception as e:
        print("Error fetching visitor data:", e)
        return None


def get_today():
    return datetime.datetime.today().strftime("%Y%m%d")


def get_now_time():
    return datetime.datetime.today().strftime("%Y.%m.%d에")


# 함수F
def record_CPC(keyword):
    result = search_keyword(keyword)

    # PC 광고 단가 처리
    pc_lines = result["PC"].split('\n')  # 각 줄을 나눔
    pc_text = "PC 광고 단가\n"
    for i, line in enumerate(pc_lines):
        pc_text += "TOP{}. {}\n".format(i + 1, line[2:])  # 맨 앞 글자 제거 후 TOP{i} 출력

    # 모바일 광고 단가 처리
    mobile_lines = result["모바일"].split('\n')  # 각 줄을 나눔
    mobile_text = "모바일 광고 단가\n"
    for i, line in enumerate(mobile_lines):
        mobile_text += "TOP{}. {}\n".format(i + 1, line[2:])  # 맨 앞 글자 제거 후 TOP{i} 출력

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "■ 파워링크 예상단가\n\n키워드: {}\n\n{}\n{}\n\n______________________\n01. 검색량 조회\n:키워드 + #\n\n02. 블로그 탭 순위\n:키워드 + @\n\n03. 플레이스 순위\n:키워드 + $\n\n04. 쇼핑연관검색어 조회\n:키워드 + %\n\n05. 파워링크 단가 조회\n:키워드 + &\n".format(
                            keyword, pc_text, mobile_text)
                    }
                }
            ]
        }
    }
    return jsonify(response)

def search_keyword(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://zzim2.com/adcost/')

        # 검색어 입력란 클릭
        page.click('//*[@id="srchQuery"]')

        # 검색어 입력
        page.type('//*[@id="srchQuery"]', keyword)

        # 검색 버튼 클릭
        page.click('//*[@id="searchAjaxBtn"]')

        # PC 단가 출력
        pc_price = page.inner_text('//*[@id="resultArea"]/tr[2]/td[2]')
        # 모바일 단가 출력
        mobile_price = page.inner_text('//*[@id="resultArea"]/tr[2]/td[3]')

        # 앞뒤 공백 제거
        pc_price = pc_price.strip()
        mobile_price = mobile_price.strip()

        # 첫 번째 항목 앞의 공백 제거
        pc_price = pc_price.lstrip()

        # 결과 반환
        return {"PC": pc_price.replace('\n', '\n'), "모바일": mobile_price.replace('\n', '\n')}


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
