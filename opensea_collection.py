from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from PIL import Image # pillow
import json
import random
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging
import os
import time

from opensea_tokens import OpenseaTokenScraper

class OpenseaCollectionScraper:
    def __init__(self, driver: webdriver, numOfCollections: int, maxNumOfAssets: int, authKey: str) -> None:
        self.__driver = driver
        self.__numOfCollections = numOfCollections
        self.__maxNumOfAssets = maxNumOfAssets
        self.__authKey = authKey
        self.tokenScraper = OpenseaTokenScraper(driver, authKey)

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

        logging.info('성공: {}'.format(numOfSuccess))

    def __getCollectionUrls(self) -> list:
        self.__driver.get(self.__rancomCategory())
        time.sleep(3)
        for _ in range(random.randrange(0, 10)):
            self.__driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        collectionUrls = []
        while True:
            time.sleep(3)
            collections = self.__driver.find_elements(By.CSS_SELECTOR, "a.CarouselCard--main")
            for collection in collections:
                url = collection.get_attribute('href')
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
            maxItemCnt = self.__getMaxItemNum()
            collectionInfo = self.__getCollectionInfo()
        except RuntimeError as err:
            raise err
    
        res = self.__sendCollectionToServer(img, collectionInfo)
        if res.status_code != 200:
            raise RuntimeError('서버에 컬렉션 생성 실패!')

        resBody = res.json()
        collectionInfo["collection_id"] = resBody["collection"]["id"]
        # collectionInfo["item_cnt"] = random.randrange(1, min([self.__maxNumOfAssets, maxItemCnt]))
        collectionInfo["item_cnt"] = min([self.__maxNumOfAssets, maxItemCnt]) # 원하는 개수로 고정
        return collectionInfo

    def __sendCollectionToServer(self, img: Image, collection):
        url = os.getenv('COLLECTION_API_URL')
        imgIO = BytesIO()
        img.save(imgIO, img.format)
        img_format = img.format.lower()
        encoded = MultipartEncoder(
            fields={
                'thumbnailImage': ("thumbnail.{}".format(img_format), imgIO, 'image/{}'.format(img_format)),
                'json': json.dumps(collection)
            }
        )
        headers = {
            'accept': 'application/json',
            'Content-Type': encoded.content_type,
            'Authorization': "Bearer {}".format(self.__authKey)
        }
        res = requests.post(url, headers=headers, data=encoded)
        logging.info('컬렉션 생성 결과: {} {}'.format(collection["name"], res.status_code))
        return res

    def __getCollectionImage(self):
        try:
            collectionImg = self.__driver.find_element(By.CSS_SELECTOR, ".CollectionHeader--collection-image > img")
            imgUrl = collectionImg.get_attribute('src')
            imgRes = requests.get(imgUrl)
            img = Image.open(BytesIO(imgRes.content))
            return img
        except:
            raise RuntimeError('컬렉션 썸네일 가져오기 실패')

    def __getMaxItemNum(self):
        try:
            itemStatus = self.__driver.find_element(By.CLASS_NAME, 'CollectionStatsBar--bottom-bordered div[tabIndex="-1"]')
            return int(itemStatus.get_attribute('innerHTML'))
        except:
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

            collectionInfo["type"] = random.choice(["erc721", "erc1155"])

            return collectionInfo
        except:
            raise RuntimeError('컬렉션 정보 생성 중 실패!')