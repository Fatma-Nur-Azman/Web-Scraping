import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from selenium.common.exceptions import TimeoutException

def initialize_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.set_window_position(0, 0)
    driver.set_window_size(960, 1080)  # Tarayıcı ekran boyutu
    return driver

# Popup'ları kontrol et ve kapat
def close_popups(driver):
    try:
        popup_close_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'No, thanks')]"))
        )
        popup_close_button.click()
        print("Popup kapatıldı.")
    except TimeoutException:
        print("Popup bulunamadı veya otomatik kapandı.")

# Ürün sayısını al
def get_total_items(driver):
    try:
        items_count_element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.items-count"))
        )
        total_items = int(items_count_element.text.split(" ")[0])
        print(f"Toplam ürün sayısı: {total_items}")
        return total_items
    except Exception as e:
        print(f"Ürün sayısı alınamadı: {e}")
        return None

# Tüm ürün bağlantılarını toplama
def collect_all_product_links(driver, category_url):
    driver.get(category_url)
    time.sleep(3)  # Sayfanın başlangıç yüklenmesini bekle
    close_popups(driver)  # Popup'ları kapat
    total_items = get_total_items(driver)  # Toplam ürün sayısını alın

    all_product_links = set()
    scroll_pause_time = 2
    max_scroll_attempts = 10
    scroll_attempts = 0

    while scroll_attempts < max_scroll_attempts:
        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR, ".pdp-link a")
            current_links = {element.get_attribute("href") for element in product_elements if element.get_attribute("href")}
            print(f"Şu anki sayfada {len(current_links)} ürün linki bulundu.")

            previous_count = len(all_product_links)
            all_product_links.update(current_links)

            # Yeni link eklenmediyse, kaydırmaya devam et
            if len(all_product_links) == previous_count:
                scroll_attempts += 1
                print(f"Yeni ürün linki bulunamadı. Kaydırma denemesi: {scroll_attempts}/{max_scroll_attempts}")
            else:
                scroll_attempts = 0  # Yeni link bulunduysa deneme sayısını sıfırla

            # Sayfayı aşağı kaydır
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            # Eğer toplam ürün linkine ulaşıldıysa, durdur
            if total_items and len(all_product_links) >= total_items:
                print("Tüm ürün bağlantıları toplandı.")
                break

        except Exception as e:
            print(f"Bağlantı toplama sırasında hata: {e}")
            break

    print(f"Toplam {len(all_product_links)} ürün linki bulundu.")
    return list(all_product_links)

# Lengths ve diğer detayları çekme fonksiyonu
def scrape_all_details(driver, product_url, category, sex, index):
    driver.get(product_url)
    time.sleep(1)

    product_details = []
    close_popups(driver)

    # Ürün bilgilerini al
    try:
        product_name = driver.find_element(By.XPATH, "//h1[@class='product-name']").text.strip()
    except Exception:
        product_name = np.nan

    try:
        product_id = driver.find_element(By.XPATH, "//span[@class='product-id']").text.strip()
    except Exception:
        product_id = np.nan

    # Length alanı var mı kontrol et
    try:
        lengths_container = driver.find_element(By.CLASS_NAME, "pdp-length-wrapper")
    except Exception:
        lengths_container = None

    # Eğer Length alanı varsa tüm length'ler için döngü
    if lengths_container:
        length_buttons = lengths_container.find_elements(By.TAG_NAME, "a")
        for i in range(len(length_buttons)):
            try:
                # Her tıklamada listeyi yeniden almak için length_buttons'u tekrar bul
                lengths_container = driver.find_element(By.CLASS_NAME, "pdp-length-wrapper")
                length_buttons = lengths_container.find_elements(By.TAG_NAME, "a")

                length_button = length_buttons[i]
                length_text = length_button.text.strip()
                print(f"Length: {length_text}")

                # Length butonuna tıklama
                driver.execute_script("arguments[0].click();", length_button)
                time.sleep(3)

                # Renkleri ve bedenleri işleme
                scrape_colors_and_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index)
            except Exception as e:
                print(f"Length işlenemedi: {e}")
                continue
    else:
        print("Length alanı bulunamadı, sadece renk ve bedenlerle devam ediyor.")
        scrape_colors_and_sizes(driver, product_url, product_details, product_name, product_id, np.nan, category, sex, index)

    return product_details

# Renkler ve bedenler için döngü
def scrape_colors_and_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index):
    """Renkler ve bedenler için döngü."""
    
    # Tüm durumları (status) almak için genişletildi
    color_sections = driver.find_elements(By.XPATH, "//span[contains(@class, 'color non-input-label')]")
    swatch_containers = driver.find_elements(By.XPATH, "//div[@class='swatches-container d-flex flex-wrap']")

    if not color_sections or not swatch_containers:
        print("Renk bulunamadı, beden işlemeye geçiliyor...")
        process_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index, "Unknown", "Unknown")
        return

    for section, container in zip(color_sections, swatch_containers):
        # Status bilgisi
        try:
            status_text = section.text.strip().split(":")[0] if section else "Unknown"
            print(f"Status: {status_text}")
        except Exception:
            status_text = "Unknown"

        # Renk butonlarını bulma
        color_buttons = container.find_elements(By.XPATH, "./button")
        if not color_buttons:
            print("Renk butonu bulunamadı, beden işlemeye geçiliyor...")
            process_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index, "Unknown", status_text)
            continue

        for button in color_buttons:
            try:
                color_name = None

                # Renk adına ulaşma denemeleri
                try:
                    color_span = button.find_element(By.XPATH, ".//span[@class='color-value swatch-circle swatch-value selectable']")
                    color_name = color_span.get_attribute("data-original-title")
                    if color_name and "<span>" in color_name:
                        color_name = color_name.split("<span>")[0].strip()
                except Exception:
                    pass

                if not color_name:
                    try:
                        color_name = button.get_attribute("data-original-title")
                    except Exception:
                        pass

                if not color_name:
                    try:
                        color_name = button.get_attribute("data-attr-value")
                    except Exception:
                        pass

                if not color_name:
                    try:
                        color_name = button.get_attribute("aria-label")
                        if color_name:
                            color_name = color_name.split(" ")[-1]
                    except Exception:
                        pass

                if not color_name:
                    color_name = "Unknown"

                print(f"Renk: {color_name}")

                # Renk butonuna tıklama
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1)

                # Bedenleri işle
                process_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index, color_name, status_text)

            except Exception as e:
                print(f"Renk işlenemedi: {e}")
                continue


def process_sizes(driver, product_url, product_details, product_name, product_id, length_text, category, sex, index, color_name, status_text):
    """Bedenleri işleme fonksiyonu."""
    size_buttons = driver.find_elements(By.XPATH, "//div[@class='sizes-container d-flex flex-wrap']/button")

    # Eğer size yoksa fiyatı doğrudan çekmek için boş bir döngüye gir
    if not size_buttons:
        print("Beden bulunamadı, fiyat doğrudan çekiliyor.")
        size_text = "No Size"

        # Fiyat bilgilerini al
        try:
            price_container = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='col mt-2 sku-price-display']//div[@class='price']"))
            )
            try:
                discounted_price = price_container.find_element(By.XPATH, ".//span[@class='sales sale']//span[@class='value']").text.strip()
            except Exception:
                discounted_price = np.nan

            try:
                original_price = price_container.find_element(By.XPATH, ".//span[@class='strike-through list']//span[@class='value']").text.strip()
            except Exception:
                try:
                    original_price = price_container.find_element(By.XPATH, ".//span[@class='list']//span[@class='value']").text.strip()
                except Exception:
                    original_price = np.nan
        except Exception:
            discounted_price = original_price = np.nan

        # Eğer bir tane bile fiyat çekilemezse diğer yöntemlere geç
        if pd.isna(discounted_price) and pd.isna(original_price):
            try:
                alternative_price_container = driver.find_element(By.XPATH, "//div[@class='product-price-ratings']//span[@class='value']")
                discounted_price = alternative_price_container.get_attribute("content").strip()
                original_price = original_price if not pd.isna(original_price) else discounted_price
            except Exception:
                print("Alternatif fiyat bilgisi bulunamadı.")
                discounted_price = original_price = np.nan

        # Eğer hala fiyat bilgileri NaN ise 'Clearance' sınıfını kontrol et
        if pd.isna(discounted_price) and pd.isna(original_price):
            try:
                clearance_container = driver.find_element(By.XPATH, "//span[@class='color non-input-label text-warning']")
                clearance_price = clearance_container.find_element(By.XPATH, ".//span[@class='font-weight-normal text-capitalize group-values']").text.strip()
                clearance_price = clearance_price.split("From")[1].strip() if "From" in clearance_price else clearance_price
                discounted_price = discounted_price if not pd.isna(discounted_price) else clearance_price
                original_price = original_price if not pd.isna(original_price) else clearance_price
            except Exception:
                print("Clearance fiyat bilgisi bulunamadı.")
                discounted_price = original_price = np.nan

        # Ürün detaylarını listeye ekle
        product_details.append({
            "Index": index,
            "Category": category,
            "Product Name": product_name,
            "Product ID": product_id,
            "Product URL": product_url,
            "Length": length_text,
            "Status": status_text,
            "Colors": color_name,
            "Size": size_text,
            "Sex": sex,
            "Original Price": original_price,
            "Discounted Price": discounted_price
        })

        print(f"Index: {index}, Category: {category}, Length: {length_text}, Status: {status_text}, Colors: {color_name}, Size: {size_text}, Original Price: {original_price}, Discounted Price: {discounted_price}")
        return

    # Eğer size varsa, her bir size için döngüye devam et
    for size_button in size_buttons:
        try:
            size_text = size_button.find_element(By.TAG_NAME, "span").text.strip() if size_button else np.nan
            driver.execute_script("arguments[0].click();", size_button)
            time.sleep(1)

            # Fiyat bilgilerini al
            try:
                price_container = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='col mt-2 sku-price-display']//div[@class='price']"))
                )
                try:
                    discounted_price = price_container.find_element(By.XPATH, ".//span[@class='sales sale']//span[@class='value']").text.strip()
                except Exception:
                    discounted_price = np.nan

                try:
                    original_price = price_container.find_element(By.XPATH, ".//span[@class='strike-through list']//span[@class='value']").text.strip()
                except Exception:
                    try:
                        original_price = price_container.find_element(By.XPATH, ".//span[@class='list']//span[@class='value']").text.strip()
                    except Exception:
                        original_price = np.nan
            except Exception:
                discounted_price = original_price = np.nan

            # Eğer bir tane bile fiyat çekilemezse diğer yöntemlere geç
            if pd.isna(discounted_price) and pd.isna(original_price):
                try:
                    alternative_price_container = driver.find_element(By.XPATH, "//div[@class='product-price-ratings']//span[@class='value']")
                    discounted_price = alternative_price_container.get_attribute("content").strip()
                    original_price = original_price if not pd.isna(original_price) else discounted_price
                except Exception:
                    print("Alternatif fiyat bilgisi bulunamadı.")
                    discounted_price = original_price = np.nan

            # Eğer hala fiyat bilgileri NaN ise 'Clearance' sınıfını kontrol et
            if pd.isna(discounted_price) and pd.isna(original_price):
                try:
                    clearance_container = driver.find_element(By.XPATH, "//span[@class='color non-input-label text-warning']")
                    clearance_price = clearance_container.find_element(By.XPATH, ".//span[@class='font-weight-normal text-capitalize group-values']").text.strip()
                    clearance_price = clearance_price.split("From")[1].strip() if "From" in clearance_price else clearance_price
                    discounted_price = discounted_price if not pd.isna(discounted_price) else clearance_price
                    original_price = original_price if not pd.isna(original_price) else clearance_price
                except Exception:
                    print("Clearance fiyat bilgisi bulunamadı.")
                    discounted_price = original_price = np.nan

            # Ürün detaylarını listeye ekle
            product_details.append({
                "Index": index,
                "Category": category,
                "Product Name": product_name,
                "Product ID": product_id,
                "Product URL": product_url,
                "Length": length_text,
                "Status": status_text,
                "Colors": color_name,
                "Size": size_text,
                "Sex": sex,
                "Original Price": original_price,
                "Discounted Price": discounted_price
            })

            print(f"Index: {index}, Category: {category}, Length: {length_text}, Status: {status_text}, Colors: {color_name}, Size: {size_text}, Original Price: {original_price}, Discounted Price: {discounted_price}")

        except Exception as e:
            print(f"Beden veya fiyat bilgisi alınamadı: {e}")
            continue


# Ürünleri sırayla işleme
def scrape_products(driver, category_url, category_name):
    product_links = collect_all_product_links(driver, category_url)  # Tüm ürün bağlantılarını toplama
    all_details = []

    for index, product_url in enumerate(product_links, start=1):  # Her ürün linkini sırayla işle
        try:
            print(f"Ürün {index} işleniyor: {product_url}")
            
            # Ürün detayları için cinsiyet sütununu belirle
            if "women" in product_url.lower():
                sex = "Women"
            elif "men" in product_url.lower():
                sex = "Men"
            else:
                sex = "Unisex"
            
            details = scrape_all_details(driver, product_url, category_name, sex, index)  # Ürün detaylarını çek
            
            all_details.extend(details)  # Detayları genel listeye ekle
        except Exception as e:
            print(f"Ürün işlenemedi: {e}")
            continue

    return all_details

# Ana fonksiyon
def main():
    driver = initialize_driver()  # WebDriver'ı başlat

    categories = {
        
        "Women": "https://www.uniformadvantage.com/ladies-uniforms/womens-special-sizes/"
    }

    all_data = []

    for category_name, category_url in categories.items():
        print(f"{category_name} kategorisi işleniyor...")
        category = category_url.rstrip("/").split("/")[-1]  # Kategoriyi URL'den çıkart
        category_data = scrape_products(driver, category_url, category)  # Her kategori için ürün detaylarını al
        all_data.extend(category_data)  # Tüm kategori verilerini genel listeye ekle

    # Verileri Excel dosyasına kaydet
    df = pd.DataFrame(all_data)
    output_path = "womens-special-sizes.xlsx"
    df.to_excel(output_path, index=False)
    print(f"Tüm ürün bilgileri Excel dosyasına kaydedildi: {output_path}")

    driver.quit()  # WebDriver'ı kapat

if __name__ == "__main__":
    main()
