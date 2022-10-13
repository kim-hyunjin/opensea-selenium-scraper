from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from PIL import Image # pillow
import json
import random
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging
import time

from opensea_tokens import OpenseaTokenScraper
from utils import createFolder

class OpenseaCollectionScraper:
    def __init__(self, driver: webdriver, numOfCollections: int, maxNumOfAssets: int) -> None:
        self.__driver = driver
        self.__numOfCollections = numOfCollections
        self.__maxNumOfAssets = maxNumOfAssets
        self.tokenScraper = OpenseaTokenScraper(driver)

    def scrapeCollection(self) -> None:
        numOfSuccess = 0
        while numOfSuccess != self.__numOfCollections:
            collectionUrls = self.__getCollectionUrls()
            for url in collectionUrls:
                try:
                    collectionInfo = self.__createCollection(url)
                    logging.info('collectionInfo {}'.format(collectionInfo))
                    self.tokenScraper.scrapeTokens(collectionInfo)
                    numOfSuccess += 1
                    if numOfSuccess == self.__numOfCollections:
                        break
                except RuntimeError as err:
                    logging.warning(err)

        logging.info('num of success: {}'.format(numOfSuccess))

    def __getCollectionUrls(self) -> list:
        self.__driver.get(self.__rancomCategory())
        time.sleep(3)
        for _ in range(random.randrange(0, 10)):
            self.__driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        collectionUrls = []
        while True:
            time.sleep(3)
            
            try:
                collections = self.__driver.find_elements(By.TAG_NAME, "a")
            except:
                raise RuntimeError("error occur while gathering collection link")
            else:
                for collection in collections:
                    url = collection.get_attribute('href')
                    if (isinstance(url, str) and url.startswith('https://opensea.io/collection/')):
                        collectionUrls.append(url)

            if len(collectionUrls) > self.__numOfCollections: break

            self.__driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        return collectionUrls        

    def __rancomCategory(self) -> str:
        self.__driver.get('https://opensea.io/explore-collections')
        time.sleep(3)
        category = self.__driver.find_element(By.CSS_SELECTOR, "#main ul")
        tabLinks = category.find_elements(By.CSS_SELECTOR, "li > a")
        tabUrls = []
        for link in tabLinks:
            tabUrls.append(link.get_attribute('href'))
        return random.choice(tabUrls)

    def __createCollection(self, url):
        logging.info('collection url: {}'.format(url))
        self.__driver.get(url)
        time.sleep(3)
        
        try:
            img = self.__getCollectionImage()
            bannerImg = self.__getBannerImage()
            collectionInfo = self.__getCollectionInfo()

            self.__saveToFile(img, bannerImg, collectionInfo)
            
            maxItemCnt = self.__getMaxItemNum()
            collectionInfo["item_cnt"] = min([self.__maxNumOfAssets, maxItemCnt]) 
            return collectionInfo
        except RuntimeError as err:
            raise err
        
        

    def __saveToFile(self, img: Image, bannerImg: Image, collection):
        
        try:
            collectionPath = 'dist/{}'.format(collection["name"])
            logging.info('collection path: {}'.format(collectionPath))
            createFolder(collectionPath)
            
            img.save("{}/{}.{}".format(collectionPath, collection["name"]+"-thumbnail", img.format.lower()))
            bannerImg.save("{}/{}.{}".format(collectionPath, collection["name"]+"-banner", bannerImg.format.lower()))
            collection_json = json.dumps(collection)
            with open("{}/{}.json".format(collectionPath, collection["name"]), "w") as outfile:
                outfile.write(collection_json)
            
        except:
            raise RuntimeError('fail to create collection folder')


    def __getBannerImage(self):
        try:
            bannerImg = self.__driver.find_elements(By.XPATH, "//main//img")[0]
            imgUrl = bannerImg.get_attribute('src')
            imgRes = requests.get(imgUrl)
            img = Image.open(BytesIO(imgRes.content))
            return img
        except:
            raise RuntimeError('fail to get collection banenr image')

    def __getCollectionImage(self):
        try:
            collectionImg = self.__driver.find_elements(By.XPATH, "//main//img")[1]
            imgUrl = collectionImg.get_attribute('src')
            imgRes = requests.get(imgUrl)
            img = Image.open(BytesIO(imgRes.content))
            return img
        except:
            raise RuntimeError('fail to get collection thumbnail image')

    def __getMaxItemNum(self):
        try:
            itemStatus = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'AssetSearchView--results')]//p")[0].text
            itemCnt = int(str(itemStatus).replace('items', '').replace(',', '').strip())
            logging.info('total items: {}'.format(itemCnt))
            return itemCnt
        except Exception as e:
            logging.error(e)
            return self.__maxNumOfAssets

    def __getCollectionInfo(self):
        try:
            collectionInfo = {}
            collectionName = self.__driver.find_element(By.TAG_NAME, "h1").text
            collectionInfo["name"] = collectionName
            collectionInfo["symbol"] = collectionName[:3].upper()
            try:
                desc = self.__driver.find_element(By.CSS_SELECTOR, "CollectionHeader--description > span")
                collectionInfo["description"] = desc.text
            except:
                collectionInfo["description"] = ""

            return collectionInfo
        except:
            raise RuntimeError('fail to get collection info')