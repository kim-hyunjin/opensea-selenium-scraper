from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
from dotenv import load_dotenv

from opensea_collection import OpenseaCollectionScraper
from utils import createFolder

logging.basicConfig(
  level = logging.INFO
)

load_dotenv()
numOfCollections = int(input('컬렉션 수'))
maxNumOfAssets = int(input("최대 토큰 개수"))
driver = webdriver.Chrome(service=Service(executable_path='./chromedriver'))

def main():
    try:
        createFolder('dist')
        scraper = OpenseaCollectionScraper(driver, numOfCollections, maxNumOfAssets)
        scraper.scrapeCollection()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
