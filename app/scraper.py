import logging
import requests 
import time
from datetime import timedelta, datetime
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.remote.webelement import WebElement
from RPA.Browser.Selenium import Selenium
from unidecode import unidecode
from .utils import *
from .excel_handler import ExcelHandler
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FreshNews(ExcelHandler):
    def __init__(self, search_phrase, category='', target_months=1):
        self.search_phrase = unidecode(search_phrase.lower())
        self.category = category.lower()
        self.BROWSER = Selenium()
        self.URL = 'https://www.latimes.com/'
        self.ALL_DATA = list()
        self.actual_month = int(datetime.now().strftime('%Y%m')) # "millenial bug" avoidant, jk
        self._config_months(int(target_months))
        self._config_browser()
        excel_file = f"output/{datetime.now().strftime('%Y-%m-%d %H:%M')}.xlsx"
        super().__init__(excel_file)


    def _category_filter_select(self) -> None:
        self._see_all_topics()
        topics = self.BROWSER.find_elements('class:search-filter-menu > li')
        idx_to_click = list()
        for topic in topics:
            if self.category in topic.text.lower():
                idx_to_click.append(topics.index(topic))
        logging.info(f'indexes to click {idx_to_click}')
        return idx_to_click

    def _click_all_topics(self, idx_to_click:list):
        locator = 'class:search-filter-menu > li'
        topics = self.BROWSER.find_elements(locator)
        for idx in idx_to_click:
            elem = topics[idx].find_element('css selector','.checkbox-input')
            elem.click()
            self.BROWSER.wait_for_expected_condition('staleness_of', topics[idx])
            self._see_all_topics()
            topics = self.BROWSER.find_elements(locator)

    def _see_all_topics(self) -> None:
        try:
            self.BROWSER.wait_and_click_button('class:see-all-button')
        except NoSuchElementException:
            pass

    def _category_filter(self) -> None:
        '''Filter by category'''
        if not self.category: return
        self.BROWSER.find_element('class:search-results-module-aside').click()
        idx_to_click = self._category_filter_select()
        self._click_all_topics(idx_to_click)

        

    def _check_year_month(self,web_elem_idx:int)-> bool:
        '''Checks if news date is inside our target dates'''
        elems = self.BROWSER.find_elements('class:search-results-module-results-menu > li')
        elem = elems[web_elem_idx]
        date_raw = elem.find_element("css selector", ".promo-timestamp").text
        converted_date = convert_date_to_datetime(date_raw)
        year_month = int(converted_date.strftime("%Y%m"))
        return self._news_filter(year_month)

    def _config_browser(self):
        '''Used to open and set timeout to browser and avoid being stuck on huge load screens'''
        logger.info("Configuring browser")
        timeout = timedelta(seconds=10)
        self.BROWSER.open_available_browser(headless=True)
        self.BROWSER.set_selenium_page_load_timeout(timeout)

    def _config_months(self, target_months:int) -> None:
        '''Used to set valid months to store'''
        logger.info("Configuring months")
        if target_months == 0: 
            target_months = 1
        self.months = range(self.actual_month,
                            self.actual_month-target_months, 
                            -1)
        logger.info(f"Selected months {list(self.months)}")

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
            with open(f'{file_path}', 'wb') as f:
                f.write(r.content)
            logger.debug("Image Downloaded")
            return True
        logger.debug("Error downloading image")
        return False
    
    def _extract_from_page(self) -> None:
        '''Extracts information from current page'''
        logger.info("Extracting information from page")
        
        idx_elems = len(self.BROWSER.find_elements('class:search-results-module-results-menu > li'))
        for idx_elem in range(idx_elems):
            if self._check_year_month(idx_elem):
                data = self._transform_data(idx_elem)            
                logger.debug("Appending data to excel")
                self._update_row(data)
                self.ALL_DATA.append(data)
            else: 
                return False
        return True

    def _full_routine(self):
        '''Extract selected information'''

        self._goto_website()
        self._search_info()
        self._category_filter()
        self._order_search()
        if self._extract_from_page():
            while self._has_next_page():
                self._next_page()
                if not self._extract_from_page():
                    break
        self.BROWSER.close_all_browsers()
        self._save_and_close_workbook()
        logger.info(f"Extraction finished, extracted {len(self.ALL_DATA)} news")

    def _get_image(self, elem:WebElement, filename:str) -> dict:
        logging.info("Checking if there's image to download")
        image_dict = dict()
        try:
            image = elem.find_element("css selector", "img")
            logging.debug("Yes, it does")
            image_sources = image.get_attribute('srcset')
            image_url = image_sources.split(',')[-1].split(' 840w')[0]
            self._download_image_prefered(image_url, filename)
            image_dict['picture_filename'] = image.get_attribute('alt')
            image_dict['saved_filename'] = filename
            
        except NoSuchElementException: 
            logging.debug("No, it doesn't")
            image_dict['picture_filename'] = 'No image'
            image_dict['saved_filename'] = 'No saved image'
        return image_dict
    
    def _has_next_page(self) -> bool:
        '''Checks if it has another page'''
        try:
            logger.debug("Has next page: True")
            self.BROWSER.find_element('class:search-results-module-next-page > a')
            return True
        except:
            logger.debug("Has next page: False")
            pass
        return False

    def _goto_website(self):
        '''Go to website'''
        logger.info("Opening website")
        try:
            self.BROWSER.go_to(self.URL)
            self.BROWSER.maximize_browser_window()
        except TimeoutException:
            logger.info("Website took too long to respond, it was stopped to begin interaction")
            pass
        

    def _order_search(self) -> bool:
        logger.info("Ordering search")
        try:
            locator = 'class:select-input'
            self.BROWSER.wait_until_element_is_enabled(locator,timeout=15)
            self.BROWSER.find_element(locator).send_keys("N")
            self.BROWSER.wait_until_page_contains_element(locator)
            self.BROWSER.wait_until_page_contains_element('class:loading-icon')
            self.BROWSER.wait_until_page_does_not_contain_element('class:loading-icon')
            return True
        except Exception as e:
            logger.info(f"Error on order_search: {e}")
            logger.debug(f"Error on order_search: {traceback.format_exc()}")
        return False
            

    def _search_info(self) -> bool:
        '''Perform the search'''
        logger.info(f'Performing search. Search phrase: {self.search_phrase}')
        self.BROWSER.find_element("css:[data-element='magnify-icon']").click()
        search_input = self.BROWSER.find_element("css:[data-element='search-form-input']")
        self.BROWSER.wait_until_element_is_enabled("css:[data-element='search-form-input']")
        search_input.send_keys(f'"{self.search_phrase}"')
        try:
            logger.info("Submiting search")
            time.sleep(5) ## TODO: set timeout
            search_input.submit()
        except TimeoutException:
            logger.info("Took much time to respond, browser stopped to continue interaction")
            pass
        self.BROWSER.wait_until_element_contains('class:search-results-module-count','results')

    def _next_page(self):
        '''Go to next page'''
        logger.info("Next page")
        self.BROWSER.execute_javascript('window.scrollTo(0, document.body.scrollHeight);')
        next_page_button = self.BROWSER.find_element('class:search-results-module-next-page')
        try:
            next_page_button.click()
        except ElementClickInterceptedException:
            url = next_page_button.find_element(by='tag name',value='a').get_attribute('href')
            self.BROWSER.go_to(url)
            # self.BROWSER.screenshot()
            # next_page_button.click()
        self.BROWSER.wait_for_expected_condition('staleness_of', next_page_button)
            
    def _news_filter(self,news_month) -> bool:
        logger.info("Filtering news")
        if news_month in self.months:
            logger.debug("News inside target dates")
            return True
        logger.debug("News outside target dates")
        return False

    def _transform_data(self, web_elem_idx:int) -> dict:
        '''Get element text and convert to an dictionary'''
        logger.info("Extracting information")
        infos = dict()
        elems = self.BROWSER.find_elements('class:search-results-module-results-menu > li')
        elem = elems[web_elem_idx]
        title = elem.find_element("css selector", ".promo-title").text
        description = elem.find_element("css selector", ".promo-description").text
        date_raw = elem.find_element("css selector", ".promo-timestamp").text
        converted_date = convert_date_to_datetime(date_raw)
        phrase_count = self._count_search_phrases(elem.text)
        text_has_value = has_value(elem.text)
        filename = f'output/{title}.jpg'
        image_dict = self._get_image(elem, filename)

        infos['title'] = title
        infos['description'] = description
        infos['date'] = converted_date
        infos['phrase_count'] = phrase_count
        infos['has_value'] = text_has_value
        infos.update(image_dict)

        return infos


    # def _download_image_selenium(self, image_url:str):
    #     self.BROWSER.open_available_browser(image_url)


if __name__ == '__main__':
    news = FreshNews()