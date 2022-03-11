from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
from PIL import Image # pillow
import json
import random
from faker import Faker
from datetime import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging
import os

class OpenseaTokenScraper:
    def __init__(self, driver: webdriver, authKey: str) -> None:
        self.__driver = driver
        self.__authKey = authKey
        self.__fake = Faker()

    def scrapeTokens(self, collectionInfo):
        logging.info('token scrape start')
        urlsMoreThanItemCnt = self.__getTokenUrls(collectionInfo["item_cnt"])
        numOfSuccess = 0
        for i in range(collectionInfo["item_cnt"]):
            try:
                self.__createToken(urlsMoreThanItemCnt[i], collectionInfo["collection_id"], collectionInfo["type"])
                numOfSuccess += 1
            except RuntimeError as err:
                logging.warning(err)
                raise RuntimeError('토큰을 원하는만큼 만드는데 실패했습니다. 성공한 개수 : {}'.format(numOfSuccess))
        logging.info('토큰 생성 성공수: {}'.format(numOfSuccess))
            

    def __getTokenUrls(self, itemCnt):
        tokenUrls = []

        viewToggleButton = self.__driver.find_elements(By.CLASS_NAME, "AssetSearchView--toggle-buttons")[1]
        viewToggleButton.find_elements(By.CSS_SELECTOR, '[type="button"]')[1].click()
        assetContainer = self.__driver.find_element(By.CLASS_NAME, "AssetsSearchView--assets")

        while True:
            time.sleep(5)
            moreAsset = assetContainer.find_elements(By.CSS_SELECTOR, "article.Asset--loaded")
            for asset in moreAsset:
                link = asset.find_element(By.CLASS_NAME, "Asset--anchor")
                tokenUrls.append(link.get_attribute('href'))
            self.__driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            if len(tokenUrls) >= itemCnt: break
        
        return tokenUrls

    def __createToken(self, url, collectionId, tokenType):
        self.__driver.get(url)
        time.sleep(3)
        try:
            img = self.__getTokenImage()
            token = self.__getTokenInfo(collectionId, tokenType)
            self.__sendTokenToServer(img, token)
        except:
            raise RuntimeError('토큰 생성 중 실패')

    def __getTokenImage(self):
        imgFound = True
        videoFound = True
        try:
            imgElement = self.__driver.find_element(By.CLASS_NAME, "Image--image")
            imgUrl = imgElement.get_attribute("src")
            imgRes = requests.get(imgUrl)
            return Image.open(BytesIO(imgRes.content))
        except:
            imgFound = False

        try:
            videoElement = self.__driver.find_element(By.CSS_SELECTOR, ".item--media video")
            posterUrl = videoElement.get_attribute("poster")
            imgRes = requests.get(posterUrl)
            return Image.open(BytesIO(imgRes.content))
        except:
            videoFound = False

        if not imgFound and not videoFound:
            raise RuntimeError('토큰 이미지 가져오기 실패')

    def __getTokenInfo(self, collectionId, tokenType):
        token = {}
        token["collection_id"] = collectionId
        token["name"] = self.__driver.find_element(By.CLASS_NAME, "item--title").text
        try:
            token["description"] = self.__driver.find_element(By.CSS_SELECTOR, ".item--description-text>span").text
        except:
            token["description"] = ""
        token["type"] = tokenType
        token["total_count"] = self.__getTotalCount(tokenType)
        token["royalties"] = random.randrange(1, 20)
        token["sale"] = self.__getSale()
        token["traits"] = self.__getTraits()

        return token

    def __sendTokenToServer(self, img: Image, token):
        url = os.getenv('TOKEN_API_URL')
        imgIO = BytesIO()
        img.save(imgIO, img.format)
        img_format = img.format.lower()
        encoded = MultipartEncoder(
            fields={
                'contentImage': ("test.{}".format(img_format), imgIO, 'image/{}'.format(img_format)),
                'json': json.dumps(token)
            }
        )
        headers = {
            'accept': 'application/json',
            'Content-Type': encoded.content_type,
            'Authorization': "Bearer {}".format(self.__authKey)
        }
        res = requests.post(url, headers=headers, data=encoded)
        logging.info('token {} {}'.format(token["name"], res.status_code))

    def __getTotalCount(self, tokenType):
        if tokenType == "erc721":
            return 1
        else:
            return random.randrange(1, 3)

    def __getSale(self):
        sale = {}
        sale["sale_type"] = self.__randomSaleType()
        sale["currency"] = self.__randomCurrency()

        if sale["sale_type"] == "fixed":
            sale["price"] = self.__randomPrice()
        elif sale["sale_type"] == "time":
            sale["start_price"] = self.__randomPrice()
            sale["start_at"] = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
            sale["end_at"] = self.__randomDateWithinMonth().strftime("%Y-%m-%dT%H:%M:%SZ")
        return sale

    def __getTraits(self):
        traits = []
        properties = self.__driver.find_elements(By.CSS_SELECTOR, ".item--properties>a")
        for prop in properties:
            trait = {}
            trait["key"] = prop.find_element(By.CLASS_NAME, "Property--type").get_attribute('innerHTML')
            trait["value"] = prop.find_element(By.CLASS_NAME, "Property--value").get_attribute('innerHTML')
            traits.append(trait)
        return traits

    def __randomSaleType(self):
        return random.choice(["fixed", "auction", "time"])

    def __randomCurrency(self):
        return random.choice(["eth", "mr", "mf"])

    def __randomPrice(self):
        return round(random.uniform(0.01, 100.0), 2)

    def __randomDateWithinMonth(self):
        return self.__fake.date_time_between(start_date='now', end_date="+30d")