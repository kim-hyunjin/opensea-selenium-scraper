from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
from dotenv import load_dotenv

from opensea_collection import OpenseaCollectionScraper

logging.basicConfig(
  level = logging.INFO
)

load_dotenv()
authKey = input('인증키')
numOfCollections = int(input('컬렉션 수'))
maxNumOfAssets = int(input("최대 토큰 개수"))
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def main():
    try:
        scraper = OpenseaCollectionScraper(driver, numOfCollections, maxNumOfAssets, authKey)
        scraper.scrapeCollection()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
