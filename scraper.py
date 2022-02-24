from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
from PIL import Image # pillow
import json
import random
from faker import Faker
from datetime import datetime

fake = Faker()
numOfAssets = int(input("토큰 개수"))
collectionId = input("컬렉션 ID")
tokenType = input("토큰type(erc721, erc1155)")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def main():
    driver.get('https://opensea.io/collection/mfers')
    driver.implicitly_wait(5) # seconds
    try:
        tokenUrlList = getTokenList()
        for i in range(numOfAssets):
            makeToken(tokenUrlList[i])
    finally:
        driver.quit()
    
    while(True):
        pass

def getCollectionInfo():
    pass

def getTokenList():
    tokenUrls = []

    viewToggleButton = driver.find_elements(By.CLASS_NAME, "AssetSearchView--toggle-buttons")[1]
    viewToggleButton.find_elements(By.CSS_SELECTOR, '[type="button"]')[1].click()
    assetContainer = driver.find_element(By.CLASS_NAME, "AssetsSearchView--assets")

    while True:
        time.sleep(5)
        moreAsset = assetContainer.find_elements(By.CSS_SELECTOR, "article.Asset--loaded")
        for asset in moreAsset:
            link = asset.find_element(By.CLASS_NAME, "Asset--anchor")
            tokenUrls.append(link.get_attribute('href'))
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        print(len(tokenUrls))
        if len(tokenUrls) > numOfAssets: break
    
    return tokenUrls

def makeToken(url):
    driver.get(url)
    driver.implicitly_wait(3)
    img = getImage()
    print(img)
    token = getTokenInfo()
    print(json.dumps(token))


def getImage():
    imgElement = driver.find_element(By.CLASS_NAME, "Image--image")
    imgUrl = imgElement.get_attribute("src")
    imgRes = requests.get(imgUrl)
    return Image.open(BytesIO(imgRes.content))

def getTokenInfo():
    token = {}
    token["collection_id"] = collectionId
    token["name"] = driver.find_element(By.CLASS_NAME, "item--title").text
    token["description"] = driver.find_element(By.CSS_SELECTOR, ".item--description-text>span").text
    token["type"] = tokenType
    token["total_count"] = getTotalCount()
    token["royalties"] = random.randrange(1, 20)
    token["sale"] = getSale()
    token["traits"] = getTraits()

    return token


def getTotalCount():
    if tokenType == "erc721":
        return 1
    else:
        return random.randrange(1, 5)

def getSale():
    saleType = randomSaleType()
    sale = {}
    sale["sale_type"] = saleType
    sale["currency"] = "eth"
    if saleType == "fixed":
        sale["price"] = randomPrice()
    elif saleType == "time":
        sale["start_price"] = randomPrice()
        sale["start_at"] = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
        sale["end_at"] = randomDateWithinMonth().strftime("%Y-%m-%dT%H:%M:%SZ")
    return sale

def getTraits():
    traits = []
    properties = driver.find_elements(By.CSS_SELECTOR, ".item--properties>a")
    for prop in properties:
        trait = {}
        trait["key"] = prop.find_element(By.CLASS_NAME, "Property--type").get_attribute('innerHTML')
        trait["value"] = prop.find_element(By.CLASS_NAME, "Property--value").get_attribute('innerHTML')
        traits.append(trait)
    return traits

def randomSaleType():
    saleType = ["fixed", "auction", "time"]
    return random.choice(saleType)

def randomPrice():
    return round(random.uniform(0.01, 100.0), 2)

def randomDateWithinMonth():
    return fake.date_time_between(start_date='now', end_date="+30d")
    

if __name__ == "__main__":
    main()
