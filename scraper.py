from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get('https://opensea.io/collection/mfers')
driver.implicitly_wait(5) # seconds
def getCollectionInfo():
    pass

def getTokenList():
    tokenUrls = []

    assetContainer = driver.find_element(By.CLASS_NAME, "AssetsSearchView--assets")
    assets = assetContainer.find_elements(By.CSS_SELECTOR, "article.Asset--loaded")
    print(len(assets))
    for asset in assets:
        link = asset.find_element(By.CLASS_NAME, "Asset--anchor")
        tokenUrls.append(link.get_attribute('href'))
    
    return tokenUrls

def getTokenInfo(url):
    pass

def findByClassName(className):
    return driver.find_element_by_class_name(className)

def findById(id):
    return driver.find_element_by_id(id)

def findByCssSelector(selector):
    return driver.find_element_by_css_selector(selector)

print(getTokenList())

while(True):
    pass
