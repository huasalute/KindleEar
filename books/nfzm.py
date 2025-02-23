#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from books.base_book import BaseFeedBook, UrlOpener

def getBook():
    return NFZM

class NFZM(BaseFeedBook):
    title               = '南方周末'
    description         = '在这里读懂中国 | 每周五更新 | 需要登录'
    __author__          = 'mcfloundinho'
    language            = 'zh-cn'
    masthead_file       = "mh_nfzm.gif"
    cover_file          = "cv_nfzm.jpg"
    deliver_days        = ['Friday']
    needs_subscription  = True

    def ParseFeedUrls(self):
        login_url = "http://passport.infzm.com/passport/login"
        content_url = "http://www.infzm.com/enews/infzm"
        urls = []
        opener = UrlOpener(self.host, timeout=60)
        login_form = {"loginname":self.account, "password":self.password}
        login_response = opener.open(login_url, data=login_form)
        #opener.SaveCookies(login_response.header_msg.getheaders('Set-Cookie'))
        result = opener.open(content_url)
        content = result.content.decode(self.feed_encoding)
        soup = BeautifulSoup(content, "lxml")
        sec_titles = []
        for sec_name in soup.find_all('h2'):
            sec_titles.append(sec_name.get_text())
        for top_news in soup.find_all('dl', {'class': 'topnews'}):
            url = top_news.a['href']
            result = self.FetchArticle(url, opener)
            if not result:
                continue
            feed_soup = BeautifulSoup(result.text, "lxml")
            urls.append((sec_titles[0], top_news.a['title'], url, feed_soup.find(id="articleContent")))
        sec_count = 0
        for sec_content in soup.find_all('ul', {'class': 'relnews'}):
            for a in sec_content.find_all('a'):
                url = a['href']
                result = self.FetchArticle(url, opener)
                if not result:
                    continue
                feed_soup = BeautifulSoup(result.text, "lxml")
                urls.append((sec_titles[sec_count], a['title'], url, feed_soup.find(id="articleContent")))
            sec_count += 1
        return urls
