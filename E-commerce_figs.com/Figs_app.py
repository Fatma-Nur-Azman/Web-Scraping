from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Driver initialization function
def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to scrape product details
def scrape_core_colors(driver, base_url, sex, category_name):
    driver.get(base_url)
    time.sleep(3)

    # Find all hrefs on the product list page
    product_links_xpath = "//li[contains(@class, 'Collection__StyledGridItem')]//a[@href]"
    try:
        product_links = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, product_links_xpath))
        )
    except Exception:
        print(f"No product list found in the {category_name} ({sex}) category!")
        return []
    
    print(f"Total number of products in the {category_name} ({sex}) category: {len(product_links)}")

    product_data = []

    # Save product links to a separate list
    product_urls = [link.get_attribute("href") for link in product_links]

    for href in product_urls:
        try:
            # Click each product link
            print(f"Product URL: {href}")
            driver.get(href)
            time.sleep(3)

            # Find product name (h1)
            try:
                product_name = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                ).text
            except Exception:
                product_name = "N/A"

            # Get product category (first text under Shop More)
            product_category_xpath = "//div[contains(@class, 'CollectionLink__Body')]//ul/li[1]//div"
            try:
                product_category = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, product_category_xpath))
                ).text
            except Exception:
                product_category = "N/A"

            # Find discounted price
            discounted_price_xpath = "//span[contains(@class, 'MarkedDownPrice')]"
            try:
                discounted_price = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, discounted_price_xpath))
                ).text
            except Exception:
                discounted_price = "N/A"

            # Find original price
            original_price_xpath = "//span[contains(@class, 'Price-sc') and not(contains(@class, 'MarkedDownPrice'))]"
            try:
                original_price = driver.find_element(By.XPATH, original_price_xpath).text
            except Exception:
                original_price = "N/A"

            # Get Core Colors
            core_colors_xpath = "//div[contains(@class, 'AttributeSection__Body') and .//div[text()='core']]//div[@data-scroll-item-key]"
            try:
                core_color_elements = driver.find_elements(By.XPATH, core_colors_xpath)
                core_colors = [color.get_attribute("data-scroll-item-key") for color in core_color_elements]
                core_colors_list = ", ".join(core_colors)

                # If no Core Colors found, search for all data-scroll-item-key values on the page
                if not core_colors:
                    fallback_colors_xpath = "//div[@data-scroll-item-key]"
                    try:
                        fallback_color_elements = driver.find_elements(By.XPATH, fallback_colors_xpath)
                        fallback_colors = [color.get_attribute("data-scroll-item-key") for color in fallback_color_elements]
                        if fallback_colors:
                            core_colors = fallback_colors
                            core_colors_list = ", ".join(fallback_colors)
                        else:
                            core_colors_list = "N/A"
                    except Exception:
                        core_colors_list = "N/A"
                        core_colors = []
            except Exception:
                core_colors_list = "N/A"
                core_colors = []

            # Get Limited Edition colors
            limited_colors_xpath = "//div[contains(@class, 'AttributeSection__Content-sc-1c7dvy3-4 jqqKJO')]//div[@data-scroll-item-key]"
            try:
                limited_color_elements = driver.find_elements(By.XPATH, limited_colors_xpath)
                limited_colors = [color.get_attribute("data-scroll-item-key") for color in limited_color_elements]
                limited_colors = [color for color in limited_colors if color not in core_colors]
                limited_colors_list = ", ".join(limited_colors)
            except Exception:
                limited_colors_list = "N/A"
                limited_colors = []

            # Get Discounted Limited Edition colors
            discounted_price_divs_xpath = "(//div[contains(@class, 'ColorSection__PriceBucketLabel')])[2]/following-sibling::div[contains(@data-test-id, 'base-attribute-selector')]//div[@data-scroll-item-key]"
            try:
                discounted_limited_color_elements = driver.find_elements(By.XPATH, discounted_price_divs_xpath)
                discounted_limited_colors = [color.get_attribute("data-scroll-item-key") for color in discounted_limited_color_elements]
                discounted_limited_colors = [color for color in discounted_limited_colors if color not in core_colors]
                discounted_limited_colors_list = ", ".join(discounted_limited_colors)
            except Exception:
                discounted_limited_colors_list = "N/A"
                discounted_limited_colors = []

            # Remove Discounted Limited Colors from Limited Colors
            limited_colors = [color for color in limited_colors if color not in discounted_limited_colors]
            limited_colors_list = ", ".join(limited_colors)

            # Get Size information
            size_buttons_xpath = "//section[contains(@class, 'DetailsSection__SectionWrapper')]//button[contains(@class, 'SelectorButton__Body-sc-fcv82-0')]"
            try:
                size_buttons = driver.find_elements(By.XPATH, size_buttons_xpath)
                sizes = [button.text for button in size_buttons]
                
                # Remove specified words
                exclude_sizes = {"Regular", "Short", "Tall", "Petite"}
                filtered_sizes = [size for size in sizes if size not in exclude_sizes]
                sizes_list = ", ".join(filtered_sizes)
            except Exception:
                sizes_list = "N/A"

            print(f"Product Name: {product_name}, Gender: {sex}, Category: {category_name}, Discounted Price: {discounted_price}, Original Price: {original_price}, Core Colors: {core_colors_list}, Limited Edition Colors: {limited_colors_list}, Discounted Limited Edition Colors: {discounted_limited_colors_list}, Sizes: {sizes_list}")

            # Save data
            product_data.append({
                "Product Name": product_name,
                "Gender": sex,
                "Category": category_name,
                "Product URL": href,
                "Product Category": product_category,
                "Discounted Price": discounted_price,
                "Original Price": original_price,
                "Core Colors": core_colors_list,
                "Limited Edition Colors": limited_colors_list,
                "Discounted Limited Edition Colors": discounted_limited_colors_list,
                "Sizes": sizes_list
            })

        except Exception as e:
            print(f"Error occurred: {e}")
            continue

    return product_data

# Main function
def main():
    # Categories and their links
    categories = [
        {"name": "Loungewear", "men": "https://www.wearfigs.com/collections/loungewear-mens", "women": "https://www.wearfigs.com/collections/loungewear-womens"},
        {"name": "Accessories", "men": "https://www.wearfigs.com/collections/accessories-mens", "women": "https://www.wearfigs.com/collections/accessories-womens"},
        {"name": "Lab Coats", "men": "https://www.wearfigs.com/collections/lab-coats-mens", "women": "https://www.wearfigs.com/collections/lab-coats-womens"},
        {"name": "Jackets and Vests", "men": "https://www.wearfigs.com/collections/jackets-and-vests-mens", "women": "https://www.wearfigs.com/collections/jackets-and-vests-womens"},
        {"name": "Underscrubs", "men": "https://www.wearfigs.com/collections/underscrubs-mens", "women": "https://www.wearfigs.com/collections/underscrubs-womens"},
        {"name": "All Scrubs", "men": "https://www.wearfigs.com/collections/all-scrubs-mens", "women": "https://www.wearfigs.com/collections/all-scrubs-womens"}
    ]

    # Unisex kategorisi
    unisex_category = {"name": "Figs New Balance", "url": "https://www.wearfigs.com/collections/figs-new-balance"}

    driver = initialize_driver()

    all_data = []

    try:
        # Loop through men's and women's categories
        for category in categories:
            # Fetch men's data
            print(f"Kategori: {category['name']} (Men)")
            men_data = scrape_core_colors(driver, category["men"], "Men", category["name"])
            all_data.extend(men_data)

            # Fetch women's data
            print(f"Kategori: {category['name']} (Women)")
            women_data = scrape_core_colors(driver, category["women"], "Women", category["name"])
            all_data.extend(women_data)

        # Fetch data from unisex category
        print(f"Kategori: {unisex_category['name']} (Unisex)")
        unisex_data = scrape_core_colors(driver, unisex_category["url"], "Unisex", unisex_category["name"])
        all_data.extend(unisex_data)

        # Convert data to Pandas DataFrame
        df = pd.DataFrame(all_data)

        # Display the DataFrame
        print(df)

        # Save to an Excel file
        output_path = r"C:\Users\ASUS\Desktop\Web-Scraping\E-commerce_figs.com\scraped_data.xlsx"
        df.to_excel(output_path, index=False)
        print(f"Data has been saved to the Excel file: {output_path}")
    finally:
        driver.quit()

# Run Main
if __name__ == "__main__":
    main()
