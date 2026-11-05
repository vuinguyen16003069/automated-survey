from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def ask_credentials():
    username = input("Mã sinh viên: ").strip()
    password = input("Mật khẩu: ").strip()
    return username, password


def login(driver, wait, username, password):
    driver.get("https://sinhvien.donga.edu.vn")
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#idsv, [name='idsv'], #UserName, [name='UserName']")
    )).send_keys(username)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password + "\n")
    try:
        wait.until(lambda d: not d.find_elements(By.CSS_SELECTOR, "input[type='password']"))
    except TimeoutException:
        raise RuntimeError("Đăng nhập thất bại, kiểm tra lại tài khoản/mật khẩu.")


def do_surveys(driver, wait):
    tried, done = [], 0
    while True:
        driver.get("https://sinhvien.donga.edu.vn/Khaosat/DanhSachKhaoSat")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

        # Tìm link khảo sát chưa làm và chưa thử
        url = driver.execute_script("""
            const skip = new Set(arguments[0]);
            const link = [...document.querySelectorAll("table tr a[href]")].find(a =>
                /thuchien|khaosat/i.test(a.href) && !/danhsachkhaosat/i.test(a.href) &&
                !/đã khảo sát|✓/i.test(a.innerText) && !skip.has(a.href));
            return link ? link.href : null;
        """, tried)
        if not url:
            return done
        tried.append(url)

        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='radio'], textarea")))

        # Chọn mức cao nhất, bấm gửi
        res = driver.execute_script("""
            const fire = (el, ...types) => types.forEach(t => el.dispatchEvent(new Event(t, { bubbles: true })));
            const groups = {};
            document.querySelectorAll("input[type='radio']").forEach(r => (groups[r.name] ??= []).push(r));

            Object.values(groups).forEach(list => {
                const best = list.reduce((a, b) => (Number(b.value) || 0) > (Number(a.value) || 0) ? b : a);
                best.click();
                fire(best, 'change');
            });

            const submit = [...document.querySelectorAll("button, input[type='submit'], .btn")]
                .find(b => /lưu|gửi|hoàn thành|xác nhận|submit/i.test(b.innerText || b.value || ''))
                ?? document.querySelector('#button, #btnSave');
            submit?.click();

            return { radios: Object.keys(groups).length, submitted: !!submit };
        """)

        if res["submitted"]:
            done += 1
            print(f"✔️ Xong khảo sát {done} ({res['radios']} câu)")
            try:
                wait.until(lambda d: d.current_url != url)
            except TimeoutException:
                pass
        else:
            print(f"⚠️ Không tìm thấy nút gửi: {url}")


def main():
    username, password = ask_credentials()

    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    options.set_capability("unhandledPromptBehavior", "accept")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        login(driver, wait, username, password)
        print("✅ Đăng nhập thành công!")
        print(f"🎉 Hoàn tất! Đã làm {do_surveys(driver, wait)} khảo sát.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
