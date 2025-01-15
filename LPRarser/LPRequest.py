from bs4 import BeautifulSoup
import requests
from urllib.parse import quote


class RequestsException(Exception):

    def __init__(self, message, code=500):
        super(RequestsException, self).__init__(message)
        self.code = code



class LPRequest():
    def __init__(self, appname, game):
        self.appname = appname
        self.game = game
        self.__headers = {'User-Agent': appname, 'Accept-Encoding': 'gzip'}
        self.__base_url = 'https://liquipedia.net/' + game + '/api.php?'

    def parse(self, page):
        url = self.__base_url + 'action=parse&format=json&page=' + page
        response = requests.get(url, headers=self.__headers)
        if response.status_code == 200:
            try:
                page_html = response.json()['parse']['text']['*']
            except KeyError:
                raise RequestsException(response.json(), response.status_code)
            soup = BeautifulSoup(page_html, features="lxml")
            redirect = soup.find('ul', class_="redirectText")
            if redirect is None:
                return soup, None
            else:
                redirect_value = soup.find('a').get_text()
                redirect_value = quote(redirect_value)
                soup, __ = self.parse(redirect_value)
                return soup, redirect_value
        else:
            raise RequestsException(response.json(), response.status_code)