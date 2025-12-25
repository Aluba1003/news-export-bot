import requests
import urllib3
from bs4 import BeautifulSoup
import sys, os
import re
from playwright.async_api import async_playwright

# 路徑設定：優先載入上層模組
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 常用正則集中化
DATE_RE = re.compile(r"\d{4}[./]\d{2}[./]\d{2}")
CAPTION_RE = re.compile(r"（[^）]*(?:攝|提供)[^）]*）$")

# 各新聞來源的過濾字典
EXCLUDE_KEYWORDS = {
    "ctinews": ["標籤","留言","追蹤我們","新聞分類","影音專區","關於我們","客服資訊","聯絡我們","版權","China Times Group"],
    "knews": ["延伸閱讀","相關新聞","版權","客服","追蹤","推薦新聞","下載","App","◎加入"],
    "ebc": ["延伸閱讀","相關新聞","版權","更多新聞","App","下載","優惠","折扣","滿額","品牌","活動"],
    "ctwant": ["延伸閱讀","相關新聞","更多精彩內容","版權","客服","追蹤","下載","App","立即訂閱","精彩影音","圖／","請用微信掃描","掃描 QR Code","更多 CTWANT 報導","安裝我們的 CTWANT APP","下一則新聞","人氣新聞","關鍵熱搜","隱私權政策","©","iPhone立即安裝","Android立即安裝"],
    "setn": ["保護被害人隱私","拒絕家庭暴力","請撥打110","請撥打113","彰化夫妻","活春宮","更多新聞","延伸閱讀","版權所有","三立新聞網"],
    "ettoday": ["延伸閱讀","相關新聞","更多新聞","版權所有","ETtoday新聞雲","請用微信掃描","掃描 QR Code","安裝我們的 APP","精彩影音","隱私權政策","©","iPhone立即安裝","Android立即安裝","▲"],
    "udn": ["延伸閱讀","相關新聞","更多新聞","版權所有","聯合新聞網","隱私權政策","©","App下載","立即訂閱","精彩影音","本報資料照片"],
    "chinatimes": ["延伸閱讀","相關新聞","更多新聞","版權所有","中時新聞網","隱私權政策","©","App下載","立即訂閱","精彩影音"],
    "mirrordaily": ["猜你喜歡","其他人都在看","相關新聞","延伸閱讀","推薦","更多","追蹤","分享","版權","隱私權","服務條款","留言","訂閱","App","下載","TOP","返回","社群","熱門","最新"],
    "tvbs": ["延伸閱讀","相關新聞","更多新聞","版權所有","TVBS新聞網","隱私權政策","©","App下載","立即訂閱","精彩影音","◤","👉","優惠","折扣","滿額","活動","旅遊優惠","加入TVBS新聞LINE","TVBS鐵粉","下載APP","免費拿點數","抽iPhone","eSIM","韓亞航空","訂房最便宜","省錢攻略"],
    "mirrormedia": ["延伸閱讀","相關新聞","更多新聞","版權所有","鏡週刊","隱私權政策","©","App下載","立即訂閱","精彩影音","留言","熱門新聞","TOP","返回","社群分享","翻攝","照片","圖片","臉書","Instagram"],
    "mnews": ["延伸閱讀","相關新聞","更多新聞","版權所有","鏡新聞","隱私權政策","©","App下載","立即訂閱","精彩影音","留言","熱門新聞","TOP","返回","社群分享","翻攝","照片","圖片","臉書","Instagram"]
}

async def fetch_content(url: str) -> str:
    try:
        # 壹蘋網：Playwright（async）
        if "nextapple.com" in url:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                html = await page.content()
                await page.close()
                await browser.close()

            soup = BeautifulSoup(html, "html.parser")

            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "（未能抓取標題）"

            lead = ""
            for div in soup.find_all(["div", "h2"]):
                text = div.get_text(strip=True)
                if text.startswith("【記者") and "報導" in text:
                    lead = text
                    break

            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    if text.startswith("【記者") and "報導" in text and paragraphs:
                        break
                    paragraphs.append(text)

            return "\n".join([title, lead] + paragraphs)

        # 中天網
        elif "ctinews.com" in url or "ctitv.com.tw" in url or "cti.com.tw" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["ctinews"]
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 知新聞
        elif "knews.com.tw" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1") or soup.find("h2")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["knews"]
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 東森新聞
        elif "ebc.net.tw" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["ebc"]
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 周刊王（必要時用 Playwright async 重抓）
        elif "ctwant.com" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1") or soup.find("h2")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["ctwant"]
            paragraphs = []
            content_div = soup.select_one("div.article-content") or soup
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if text and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            if len(paragraphs) < 3:
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page()
                    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    html = await page.content()
                    await page.close()
                    await browser.close()

                soup = BeautifulSoup(html, "html.parser")
                paragraphs = []
                content_div = soup.select_one("div.article-content") or soup
                for p in content_div.find_all("p"):
                    text = p.get_text(strip=True)
                    if text and not any(kw in text for kw in exclude_keywords):
                        paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 三立新聞網
        elif "setn.com" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1") or soup.find("h2")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["setn"]
            paragraphs = []
            content_div = soup.select_one("div.NewsContent") or soup.select_one("div.Content") or soup
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # ETtoday新聞雲
        elif "ettoday.net" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1") or soup.find("h2")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS["ettoday"]
            paragraphs = []
            content_div = soup.select_one("div.story") or soup
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # UDN 聯合新聞網：Playwright（async）
        elif "udn.com" in url:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                html = await page.content()
                await page.close()
                await browser.close()

            soup = BeautifulSoup(html, "html.parser")

            title = soup.find("h1") or soup.find("h2")
            if title:
                title_text = title.get_text(strip=True)
            else:
                og_title = soup.select_one('meta[property="og:title"]')
                title_text = og_title["content"].strip() if og_title and og_title.get("content") else "（未能抓取標題）"

            content_divs = soup.select("div.story-content, section.article-content__editor, div.article-content")
            if not content_divs:
                return title_text

            paragraphs = []
            for div in content_divs:
                for p in div.find_all("p", recursive=True):
                    if p.find_parent("figure") or p.find_parent("figcaption"):
                        continue
                    text = p.get_text(strip=True)
                    if text:
                        paragraphs.append(text)

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        # 中時新聞網：Playwright（async，自訂 context/headers）
        elif "chinatimes.com" in url:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    is_mobile=False,
                    has_touch=False,
                    java_script_enabled=True
                )
                page = await context.new_page()
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.6099.71 Safari/537.36 Edg/120.0.6099.71",
                    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                    "Referer": "https://www.google.com/"
                })
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await page.wait_for_selector("div.article-body, div.article-content", timeout=10000)
                html = await page.content()
                await page.close()
                await context.close()
                await browser.close()

            soup = BeautifulSoup(html, "html.parser")
            title_text = "（未能抓取標題）"
            og_title = soup.select_one('meta[property="og:title"]')
            if og_title and og_title.get("content"):
                title_text = og_title["content"].strip()
            else:
                meta_title = soup.select_one('meta[name="title"]')
                if meta_title and meta_title.get("content"):
                    title_text = meta_title["content"].strip()

            exclude_keywords = EXCLUDE_KEYWORDS["chinatimes"]
            paragraphs = []
            content_div = soup.select_one("div.article-body") or soup.select_one("div.article-content") or soup
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) >= 6 and not any(kw in text for kw in exclude_keywords):
                    paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 鏡報 Mirror Daily
        elif "mirrordaily.news" in url:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/",
            }, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.find("h1") or soup.find("title")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS.get("mirrordaily", [])
            paragraphs = []

            brief = soup.find("article", class_="brief story-renderer")
            if brief:
                for t in brief.stripped_strings:
                    if t.strip():
                        paragraphs.append(t.strip())

            article_body = soup.find(attrs={"itemprop": "articleBody"}) or soup.find("div", class_="articleBody")
            if article_body:
                for t in article_body.stripped_strings:
                    if t.strip():
                        paragraphs.append(t.strip())

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        # TVBS新聞網
        elif "tvbs.com.tw" in url:
            resp = requests.get(url, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.select_one("h1.title") or soup.select_one("h1.news-title")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS.get("tvbs", [])
            paragraphs = []
            content_div = soup.select_one("div#news_detail_div")
            if content_div:
                for p in content_div.find_all("p"):
                    text = p.get_text(strip=True)
                    if text and len(text) > 6 and not any(kw in text for kw in exclude_keywords):
                        paragraphs.append(text)
                for node in content_div.stripped_strings:
                    text = node.strip()
                    if text and len(text) > 6 and not any(kw in text for kw in exclude_keywords):
                        if text not in paragraphs:
                            paragraphs.append(text)

            extra_divs = soup.select("div.article_content, div[align=center]")
            for div in extra_divs:
                for p in div.find_all("p"):
                    text = p.get_text(strip=True)
                    if text and len(text) > 6 and not any(kw in text for kw in exclude_keywords):
                        if text not in paragraphs:
                            paragraphs.append(text)

            return "\n".join([title_text] + paragraphs)

        # 鏡週刊 Mirror Media
        elif "mirrormedia.mg" in url:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/",
            }, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.select_one("h1.story__title")
            if title:
                title_text = title.get_text(strip=True)
            else:
                og_title = soup.select_one('meta[property="og:title"]')
                title_text = og_title["content"].strip() if og_title and og_title.get("content") else "（未能抓取標題）"

            exclude_keywords = EXCLUDE_KEYWORDS.get("mirrormedia", [])
            paragraphs = []

            brief_div = soup.select_one("div.brief__BriefContainer-sc-e5902095-0, div.brief__BriefContainer")
            if brief_div:
                for node in brief_div.stripped_strings:
                    text = node.strip()
                    if text and len(text) > 6 and not any(kw in text for kw in exclude_keywords):
                        paragraphs.append(text)

            content_sections = soup.select("section.article-content__Wrapper-sc-f590bf19-0, section.article-content__Wrapper")
            for sec in content_sections:
                for node in sec.stripped_strings:
                    text = node.strip()
                    if text and len(text) > 6 and not any(kw in text for kw in exclude_keywords):
                        paragraphs.append(text)

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        # 鏡新聞 mnews.tw
        elif "mnews.tw" in url:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/",
            }, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.select_one("h1")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            paragraphs = []
            brief_div = soup.select_one("div.article-brief_briefWrapper__Gm_Bu")
            if brief_div:
                for node in brief_div.stripped_strings:
                    text = node.strip()
                    if text and len(text) > 6:
                        paragraphs.append(text)

            content_articles = soup.select("section.story_contentWrapper__dvkWW > article")
            for article in content_articles:
                for p in article.find_all("p"):
                    if p.find("a"):
                        continue
                    text = p.get_text(strip=True)
                    if text and len(text) >= 6 and not DATE_RE.search(text):
                        paragraphs.append(text)

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        # 自由時報 LTN
        elif "ltn.com.tw" in url:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/",
            }, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.select_one("h1")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            paragraphs = []
            content_ps = soup.select("div.text p")
            for p in content_ps:
                if p.find("a"):
                    continue
                text = p.get_text(strip=True)
                if not text or len(text) < 6:
                    continue
                if DATE_RE.search(text):
                    continue
                if "攝" in text or "提供" in text:
                    continue
                paragraphs.append(text)

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        # 中央社 CNA
        elif "cna.com.tw" in url:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.google.com/",
            }, timeout=15, verify=False)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            title = soup.select_one("h1")
            title_text = title.get_text(strip=True) if title else "（未能抓取標題）"

            paragraphs = []
            content_ps = soup.select("div.paragraph p, div.article p")
            for p in content_ps:
                if p.find("a"):
                    continue
                text = p.get_text(strip=True)
                if not text or len(text) < 6:
                    continue
                if DATE_RE.search(text) or re.search(r"\(\d{2}/\d{2}\s+\d{2}:\d{2}\s+更新\)", text):
                    continue
                if text.startswith("（中央社記者"):
                    paragraphs.append(text)
                    continue
                if CAPTION_RE.search(text) or ("翻攝照片" in text):
                    continue
                if "不得轉載" in text or "版權" in text:
                    continue
                paragraphs.append(text)

            seen, clean_paragraphs = set(), []
            for para in paragraphs:
                if para not in seen:
                    clean_paragraphs.append(para)
                    seen.add(para)

            return "\n".join([title_text] + clean_paragraphs)

        else:
            return "（目前尚未支援此來源）"

    except requests.RequestException as e:
        return f"（網路錯誤: {e}）"
    except Exception as e:
        return f"（抓取失敗: {e}）"

# ✅ 提供別名，讓 Bot 可以用 fetch_news_content
fetch_news_content = fetch_content
