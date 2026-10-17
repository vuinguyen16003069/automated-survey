from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

USERNAME = ""
PASSWORD = ""

BASE_URL = "https://sinhvien.donga.edu.vn"
LOGIN_URL = f"{BASE_URL}/Sinh-vien/dang-nhap?ReturnUrl=%2f"
SURVEY_LIST_URL = f"{BASE_URL}/khaosat/index"

SURVEY_BUTTON = "a.btn.btn-primary[href*='/khaosat/thuchien']"
RATING_RADIO = "input[type='radio'][value='5']"
WAIT_TIMEOUT = 20


def login(driver, wait, username, password):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys(username)
    driver.find_element(By.ID, "Password").send_keys(password, Keys.ENTER)
    wait.until(lambda d: "dang-nhap" not in d.current_url.lower())


def complete_surveys(driver, wait):
    done = 0

    while True:
        driver.get(SURVEY_LIST_URL)

        # Lấy toàn bộ danh sách URL khảo sát trong 1 lệnh JS duy nhất
        urls = driver.execute_script("""
            return Array.from(document.querySelectorAll("a.btn.btn-primary[href*='/khaosat/thuchien']"))
                        .map(a => a.href);
        """)

        if not urls:
            return done

        print(f"📋 Tìm thấy {len(urls)} môn cần khảo sát...")

        for url in urls:
            driver.get(url)
            try:
                # Đợi form load sẵn sàng
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RATING_RADIO)))

                # Chọn toàn bộ radio 5 sao và bấm Lưu trong 1 lệnh JS duy nhất (siêu tốc, 0ms delay)
                save_btn = driver.execute_script("""
                    document.querySelectorAll("input[type='radio'][value='5']").forEach(r => r.click());
                    const btn = document.querySelector("#button");
                    if (btn) {
                        btn.click();
                        return btn;
                    }
                    return null;
                """)

                # Chờ gửi request hoàn tất
                if save_btn:
                    try:
                        WebDriverWait(driver, 2).until(EC.staleness_of(save_btn))
                    except TimeoutException:
                        pass

                done += 1
                print(f"✔️ Đã hoàn thành {done} môn")
            except Exception as e:
                print(f"⚠️ Môn tại {url} gặp lỗi: {e}")

        # Kiểm tra lại xem còn môn nào chưa hoàn tất không
        driver.get(SURVEY_LIST_URL)
        remaining = driver.execute_script("""
            return document.querySelectorAll("a.btn.btn-primary[href*='/khaosat/thuchien']").length;
        """)
        if remaining == 0:
            break

    return done


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    # Tối ưu tốc độ tối đa: không tải ảnh, eager loading (chỉ chờ DOM, không chờ tài nguyên rác)
    options.page_load_strategy = "eager"
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("unhandledPromptBehavior", "accept")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        login(driver, wait, USERNAME, PASSWORD)
        total = complete_surveys(driver, wait)
        print(f"🎉 Xong! Tổng cộng đã hoàn thành {total} môn.")
    except TimeoutException:
        print("❌ Hết thời gian chờ (kiểm tra lại kết nối mạng hoặc tài khoản).")
    except Exception as e:
        print("❌ Lỗi:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
