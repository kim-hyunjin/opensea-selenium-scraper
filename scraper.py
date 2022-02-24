from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
from PIL import Image # pillow

numOfAssets = int(input("토큰 개수"))

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get('https://opensea.io/collection/mfers')
driver.implicitly_wait(5) # seconds

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

def getTokenInfo(url):
    driver.get(url)
    driver.implicitly_wait(3)
    imgElement = driver.find_element(By.CLASS_NAME, "Image--image")
    imgUrl = imgElement.get_attribute("src")
    imgRes = requests.get(imgUrl)
    img = Image.open(BytesIO(imgRes.content))
    print(img)

try:
    tokenUrlList = getTokenList()
    for i in range(numOfAssets):
        getTokenInfo(tokenUrlList[i])
finally:
    driver.quit()

while(True):
    pass
