import logging
import requests 
import time
from datetime import timedelta, datetime
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException as TimeExpt
from selenium.webdriver.remote.webelement import WebElement
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from unidecode import unidecode
from .utils import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreshNews():
    def __init__(self, search_phrase=None, category=None, target_months=1):
        self.search_phrase = unidecode(search_phrase.lower())
        self.category = category
        self.BROWSER = Selenium()
        self.URL = 'https://www.latimes.com/'
        self.ALL_DATA = list()
        self.actual_month = int(datetime.now().strftime('%m'))
        self.target_months = target_months
        self.EXCEL = Files()




    def _config_browser(self):
        '''Used to open and set timeout to browser and avoid being stuck on huge load screens'''
        logger.info("Configuring browser")
        timeout = timedelta(seconds=10)
        self.BROWSER.open_available_browser()
        self.BROWSER.set_selenium_page_load_timeout(timeout)


    def _config_months(self) -> None:
        '''Used to set valid months to store'''
        logger.info("Configuring months")
        if self.target_months == 0: 
            self.target_months = 1
        self.target_months = self.target_months
        self.months = range(self.actual_month,
                            self.actual_month-self.target_months, 
                            -1)
        logger.info(f"Selected months {list(self.months)}")

    def _full_routine(self):
        '''Extract selected information'''
        self._config_browser()
        self._config_months()
        self._search_info()
        self._order_search()
        self._extract_from_page()
        while self._has_next_page():
            self._next_page()
            if not self._extract_from_page():
                break
            
        logger.info("Extraction finished")
            


    def _order_search(self) -> bool:
        logger.info("Ordering search")
        try:
            elem = self.BROWSER.find_element('class:select-input')
            elem.send_keys("N")
            time.sleep(4)
            return True
        except Exception as e:
            print(e)
        return False
            

    def _search_info(self) -> bool:
        '''Go to website and perform the search'''
        logger.info("Opening website")
        try:
            self.BROWSER.go_to(self.URL)
        except TimeExpt:
            pass
        logger.info('Performing search')
        self.BROWSER.find_element("css:[data-element='magnify-icon']").click()
        elem = self.BROWSER.find_element("css:[data-element='search-form-input']")
        self.BROWSER.wait_until_element_is_enabled("css:[data-element='search-form-input']")
        elem.send_keys(f'"{self.search_phrase}"')
        try:
            logger.info("Submiting search")
            elem.submit()
        except TimeExpt:
            pass


    def _extract_from_page(self) -> None:
        '''Extracts information from current page'''
        logger.info("Extracting information from page")
        elems = self.BROWSER.find_elements('class:search-results-module-results-menu > li')
        for elem in elems:
            data = self._transform_data(elem)
            if self._news_filter(data['month']):
                logger.debug("Appending data to ALL_DATA")
                self.ALL_DATA.append(data)
            else: 
                return False
        return True
                    

    def _has_next_page(self) -> bool:
        '''Checks if it has another page'''
        try:
            logger.debug("Has next page: True")
            self.BROWSER.find_element('class:search-results-module-next-page > a')
            return True
        except:
            logger.debug("Final page extracted")
            pass
        return False

    def _next_page(self):
        '''Go to next page'''
        logger.info("Next page")
        self.BROWSER.find_element('class:search-results-module-next-page').click()
            

    def _transform_data(self, elem:WebElement) -> dict:
        '''Get element text and convert to an dictionary'''
        logger.info("Extracting information")

        infos = dict()
        title = elem.find_element("css selector", ".promo-title").text
        infos['title'] = title
        infos['description'] = elem.find_element("css selector", ".promo-title").text
        date_raw = elem.find_element("css selector", ".promo-timestamp").text
        infos['date'] = convert_date_to_datetime(date_raw)
        infos['month'] = int(infos['date'].strftime("%m"))
        infos['phrase_count'] = self._count_search_phrases(elem.text)
        infos['has_value'] = has_value(elem.text)
        image = elem.find_element("css selector", "img")
        infos['picture_filename'] = image.get_attribute('alt')
        image_sources = image.get_attribute('srcset')
        image_url = image_sources.split(',')[-1].split(' 840w')[0]
        self._download_image_prefered(image_url, title)
        return infos

    def _news_filter(self,news_month):
        logger.info("Filtering news")
        news_month = int(news_month)
        if news_month in self.months:
            logger.debug("News inside target dates")
            return True
        logger.debug("News outside target dates")
        return False

    def _count_search_phrases(self,text):
        text = unidecode(text.lower())
        return text.count(self.search_phrase)

    def _download_image_prefered(self, image_url:str, file_path:str):
    # This is just a prefered way to handle this situation
        logger.info("Downloading image")
        if not file_path.endswith('.jpg'):
            file_path = f'{file_path}.jpg'

        r = requests.get(image_url)
        if r.ok:
            with open(f'output/{file_path}', 'wb') as f:
                f.write(r.content)
            logger.debug("Image Downloaded")
            return True
        logger.debug("Error downloading image")
        return False

    # def _download_image_worst_way(self, image:WebElement, file_path:str):
    ## This is the worse way I can imagine to handle the download situation, but works fine depending on what we need
    #     return image.screenshot(file_path)

    # def _download_image_selenium(self, image_url:str):
    #     self.BROWSER.open_available_browser(image_url)


if __name__ == '__main__':
    news = FreshNews()