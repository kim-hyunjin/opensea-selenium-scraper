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

from utils import createFolder

class OpenseaTokenScraper:
    def __init__(self, driver: webdriver) -> None:
        self.__driver = driver
        self.__fake = Faker()

    def scrapeTokens(self, collectionInfo):
        logging.info('token scrape start')
        urlsMoreThanItemCnt = self.__getTokenUrls(collectionInfo["item_cnt"])
        numOfSuccess = 0
        for i in range(collectionInfo["item_cnt"]):
            try:
                self.__createToken(urlsMoreThanItemCnt[i], collectionInfo["name"])
                numOfSuccess += 1
            except RuntimeError as err:
                logging.warning(err)
                raise RuntimeError('fail to create amount of tokens what you want - num of success : {}'.format(numOfSuccess))
        logging.info('num of token created : {}'.format(numOfSuccess))
            

    def __getTokenUrls(self, itemCnt):
        tokenUrls = []

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

    def __createToken(self, url, collectionId):
        self.__driver.get(url)
        time.sleep(3)
        try:
            img = self.__getTokenImage()
            token = self.__getTokenInfo(collectionId)
            self.__saveToFile(img, token)
        except Exception as e:
            logging.error(e)
            raise RuntimeError('fail to create token')

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
            raise RuntimeError('fail to get token image')

    def __getTokenInfo(self, collectionName):
        token = {}
        token["collection"] = collectionName
        token["name"] = self.__driver.find_element(By.CLASS_NAME, "item--title").text
        try:
            token["description"] = self.__driver.find_element(By.CSS_SELECTOR, ".item--description-text>span").text
        except:
            token["description"] = ""
        token["traits"] = self.__getTraits()

        logging.info("token info : {}".format(token))
        return token

    def __saveToFile(self, img: Image, token):

        try:
            tokenPath = 'dist/{}/{}'.format(token["collection"], token["name"])
            createFolder(tokenPath)

            img.save("{}/{}.{}".format(tokenPath, token["name"], img.format.lower()))
            token_json = json.dumps(token)
            with open("{}/{}.json".format(tokenPath, token["name"]), "w") as outfile:
                outfile.write(token_json)
        except:
            raise RuntimeError('fail to create token folder')
        

    def __getTraits(self):
        traits = []
        properties = self.__driver.find_elements(By.CSS_SELECTOR, ".item--property")
        for prop in properties:
            trait = {}
            trait["key"] = prop.find_element(By.CLASS_NAME, "Property--type").text
            trait["value"] = prop.find_element(By.CLASS_NAME, "Property--value").text
            traits.append(trait)
        return traits