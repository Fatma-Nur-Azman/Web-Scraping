from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Function to initialize the browser
def initialize_driver():
    """Starts the driver in a set window size"""
    options = webdriver.ChromeOptions()
    # options.add_argument("--start-maximized")  # full screen
    driver = Chrome(options=options)
    # Set the browser window size (e.g., width 960px, height 1080px)
    driver.set_window_size(960, 1080)
    return driver

# Function to get music category URLs
def get_music_category_urls(driver, base_url):
    """Retrieves specific music category URLs from the main page"""
    driver.get(base_url)
    time.sleep(2)
    
    # Locate elements containing music categories
    category_elements_xpath = "//a[contains(text(),'Genre')]"
    category_elements = driver.find_elements(By.XPATH, category_elements_xpath)
    category_urls = [element.get_attribute("href") for element in category_elements]
    
    return category_urls

# Function to get album links
def get_album_links(driver):
    """Retrieves album links from the genre page"""
    time.sleep(2)  # Wait for the page to load

    # Locate elements containing album links
    album_elements_xpath = "//ul[@class='items']/li//div[@class='meta']/p/a"
    album_elements = driver.find_elements(By.XPATH, album_elements_xpath)
    album_links = [elem.get_attribute('href') for elem in album_elements]

    return album_links

# Function to get album details
def get_album_titles(driver, album_url):
    """Retrieves album titles from the album page"""
    driver.get(album_url)
    time.sleep(2)  # Wait for the page to load

    try:
        # Retrieve the album title from an element with the class 'trackTitle'
        title_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'trackTitle'))
        )
        title = title_element.text

        # Retrieve the artist name from 'h3 > span > a'
        artist_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3/span/a"))
        )
        artist = artist_element.text

        # Retrieve the price information from 'span.nobreak .base-text-color'
        price_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.nobreak .base-text-color'))
        )
        price = price_element.text

        print(f"Title: {title}, Artist: {artist}, Price: {price}")
        return {'title': title, 'artist': artist, 'price': price, 'url': album_url}
    except Exception as e:
        print(f"An error occurred while retrieving album details: {e}")
        return None

# Main function
def main():
    base_url = "https://bandcamp.com/"
    driver = initialize_driver()
    
    # Go to the genre page and get the URLs
    category_urls = get_music_category_urls(driver, base_url)
    if category_urls:
        driver.get(category_urls[0])  # Navigate to the first genre page
        time.sleep(2)
    
        # Retrieve album links
        album_links = get_album_links(driver)
        data = []

        # Extract album details from album links
        for link in album_links:
            album_data = get_album_titles(driver, link)
            if album_data:
                data.append(album_data)

        # Convert the data to a DataFrame
        df = pd.DataFrame(data)

        # Save the DataFrame to a CSV file
        csv_path = "C:/Users/ASUS/Desktop/bandcamp_album_details.csv"
        df.to_csv(csv_path, index=False)
        print(f"Data saved to '{csv_path}'.")

        driver.quit()
        return df

# Run the code
if __name__ == "__main__":
    df = main()
    if df is not None:
        print(df.head())
        print(df.shape)
