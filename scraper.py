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
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(
  level = logging.INFO
)

load_dotenv()

fake = Faker()
authKey = input('인증키')
numOfCollections = int(input('컬렉션 수'))
maxNumOfAssets = int(input("최대 토큰 개수"))
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def main():
    try:
        scrapeCollection()
    finally:
        driver.quit()

# 컬렉션 관련
def scrapeCollection():
    collectionUrls = getCollectionUrls()
    for i in range(numOfCollections):
        collectionInfo = createCollection(collectionUrls[i])
        if collectionInfo == None:
            continue
        scrapeTokens(collectionInfo)

def getCollectionUrls():
    driver.get(rancomCategory())
    driver.implicitly_wait(1)
    for _ in range(random.randrange(0, 10)):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    driver.implicitly_wait(5)
    collectionUrls = []
    while True:
        collections = driver.find_elements(By.CSS_SELECTOR, "a.CarouselCard--main")
        for collection in collections:
            collectionUrls.append(collection.get_attribute('href'))
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        if len(collectionUrls) > numOfCollections: break
    return collectionUrls

def rancomCategory():
    driver.get('https://opensea.io/explore-collections')
    driver.implicitly_wait(5)
    category = driver.find_element(By.CSS_SELECTOR, "#main ul")
    tabLinks = category.find_elements(By.CSS_SELECTOR, "li > a")
    tabUrls = []
    for link in tabLinks:
        tabUrls.append(link.get_attribute('href'))
    return random.choice(tabUrls)

def createCollection(url):
    logging.info('collection url: {}'.format(url))
    driver.get(url)
    driver.implicitly_wait(5)
    collectionImg = driver.find_element(By.CSS_SELECTOR, ".CollectionHeader--collection-image > img")
    imgUrl = collectionImg.get_attribute('src')
    img = getImage(imgUrl)

    itemStatus = driver.find_element(By.CLASS_NAME, 'CollectionStatsBar--bottom-bordered div[tabIndex="-1"]')
    try:
        maxItemCnt = int(itemStatus.get_attribute('innerHTML'))
    except:
        maxItemCnt = maxNumOfAssets

    collectionInfo = {}
    collectionName = driver.find_element(By.TAG_NAME, "h1").text
    collectionInfo["name"] = collectionName
    collectionInfo["symbol"] = collectionName[:3].upper()
    try:
        desc = driver.find_element(By.CSS_SELECTOR, "CollectionHeader--description > span")
        collectionInfo["description"] = desc.text
    except:
        collectionInfo["description"] = ""

    collectionInfo["type"] = random.choice(["erc721", "erc1155"])

    res = sendCollectionToServer(img, collectionInfo)
    if res.status_code != 200:
        logging.warning('컬렉션 생성 실패')
        return None

    resBody = res.json()
    collectionInfo["collection_id"] = resBody["collection"]["id"]
    collectionInfo["item_cnt"] = random.randrange(1, min([maxNumOfAssets, maxItemCnt]))
    return collectionInfo

def sendCollectionToServer(img: Image, collection):
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
        'Authorization': "Bearer {}".format(authKey)
    }
    res = requests.post(url, headers=headers, data=encoded)
    logging.info('collection {} {}'.format(collection["name"], res.status_code))
    return res

# 토큰 관련
def scrapeTokens(collectionInfo):
    logging.info('token scrape')
    urlsMoreThanItemCnt = getTokenUrls(collectionInfo["item_cnt"])
    for i in range(collectionInfo["item_cnt"]):
        isMakeToken = createToken(urlsMoreThanItemCnt[i], collectionInfo["collection_id"], collectionInfo["type"])
        if isMakeToken == False:
            logging.warning('token 만들기 실패')
            break

def getTokenUrls(itemCnt):
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
        if len(tokenUrls) > itemCnt: break
    
    return tokenUrls

def createToken(url, collectionId, tokenType):
    driver.get(url)
    driver.implicitly_wait(5)
    img = getTokenImage()
    if img == None:
        logging.warning('토큰 이미지 가져오기 실패')
        return False
    token = getTokenInfo(collectionId, tokenType)
    sendTokenToServer(img, token)

def sendTokenToServer(img: Image, token):
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
        'Authorization': "Bearer {}".format(authKey)
    }
    res = requests.post(url, headers=headers, data=encoded)
    logging.info('token {} {}'.format(token["name"], res.status_code))

def getTokenImage():
    try:
        imgElement = driver.find_element(By.CLASS_NAME, "Image--image")
        imgUrl = imgElement.get_attribute("src")
        return getImage(imgUrl)
    except:
        return None

def getTokenInfo(collectionId, tokenType):
    token = {}
    token["collection_id"] = collectionId
    token["name"] = driver.find_element(By.CLASS_NAME, "item--title").text
    try:
        token["description"] = driver.find_element(By.CSS_SELECTOR, ".item--description-text>span").text
    except:
        token["description"] = ""
    token["type"] = tokenType
    token["total_count"] = getTotalCount(tokenType)
    token["royalties"] = random.randrange(1, 20)
    token["sale"] = getSale()
    token["traits"] = getTraits()

    return token

def getTotalCount(tokenType):
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

def getImage(url):
    imgRes = requests.get(url)
    img = Image.open(BytesIO(imgRes.content))
    return img

def randomSaleType():
    saleType = ["fixed", "auction", "time"]
    return random.choice(saleType)

def randomPrice():
    return round(random.uniform(0.01, 100.0), 2)

def randomDateWithinMonth():
    return fake.date_time_between(start_date='now', end_date="+30d")
    

if __name__ == "__main__":
    main()
