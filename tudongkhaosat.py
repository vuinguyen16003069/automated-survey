from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login(driver, wait, username, password):
    driver.get("https://sinhvien.donga.edu.vn")
    user_el = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "#idsv, [name='idsv'], #UserName, [name='UserName']")
    ))
    pass_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    driver.execute_script("""
        const [u, p, userVal, passVal] = arguments;
        for (const [el, val] of [[u, userVal], [p, passVal]]) {
            el.value = val;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        (document.querySelector("button[type='submit'], input[type='submit']") || p.form)?.click?.() ?? p.form?.submit();
    """, user_el, pass_el, username, password)
    try:
        wait.until(lambda d: "/Home" in d.current_url or not d.find_elements(By.CSS_SELECTOR, "input[type='password']"))
    except TimeoutException:
        raise RuntimeError("Đăng nhập thất bại, kiểm tra lại tài khoản/mật khẩu.")


def do_surveys(driver, wait):
    tried, done = [], 0
    while True:
        driver.get(f"{"https://sinhvien.donga.edu.vn"}/Khaosat/DanhSachKhaoSat")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

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

        res = driver.execute_script("""
            const groups = {};
            document.querySelectorAll("input[type='radio']").forEach(r => (groups[r.name] ??= []).push(r));
            Object.values(groups).forEach(list => {
                const best = list.reduce((a, b) => (Number(b.value) || 0) > (Number(a.value) || 0) ? b : a);
                best.click();
                best.dispatchEvent(new Event('change', { bubbles: true }));
            });

            const submit = [...document.querySelectorAll("button, input[type='submit'], .btn")]
                .find(b => /lưu|gửi|hoàn thành|xác nhận|submit/i.test(b.innerText || b.value || ''))
                ?? document.querySelector('#button, #btnSave');
            submit?.click();
            return { radios: Object.keys(groups).length, submitted: !!submit };
        """)

        if not res["submitted"]:
            print(f"⚠️ Không tìm thấy nút gửi: {url}")
            continue

        done += 1
        print(f"✔️ Xong khảo sát {done} ({res['radios']} câu)")
        try:
            ok = wait.until(lambda d: d.current_url != url or next(
                (b for b in d.find_elements(By.CSS_SELECTOR, ".swal2-confirm") if b.is_displayed()), None
            ))
            if ok is not True:
                driver.execute_script("arguments[0].click();", ok)
        except TimeoutException:
            pass


def main():
    username = input("Mã sinh viên: ").strip()
    password = input("Mật khẩu: ").strip()

    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    options.set_capability("unhandledPromptBehavior", "accept")
    options.add_argument("--start-maximized")
    options.add_argument("--blink-settings=imagesEnabled=false")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15, poll_frequency=0.1)

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
