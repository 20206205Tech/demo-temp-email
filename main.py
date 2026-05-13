import random
import string
import time

import requests
from loguru import logger


def generate_random_string(length=10):
    # Tạo chuỗi ngẫu nhiên cho tên email và mật khẩu
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def get_temp_email_mailtm():
    logger.info("Đang kết nối đến Mail.tm...")

    # 1. Lấy danh sách tên miền (domain) hiện có của hệ thống
    domain_req = requests.get("https://api.mail.tm/domains")
    if domain_req.status_code != 200:
        logger.error("Không thể lấy domain từ Mail.tm")
        return

    # Lấy domain đầu tiên trong danh sách
    domain = domain_req.json().get("hydra:member", [])[0]["domain"]

    # 2. Tạo một tài khoản email ngẫu nhiên
    address = f"{generate_random_string()}@{domain}"
    password = generate_random_string()

    account_data = {"address": address, "password": password}

    logger.info(f"Đang đăng ký hòm thư: {address}")
    create_acc_req = requests.post("https://api.mail.tm/accounts", json=account_data)

    if create_acc_req.status_code != 201:
        logger.error(f"Lỗi tạo tài khoản! Chi tiết: {create_acc_req.text}")
        return

    # 3. Đăng nhập để lấy Token xác thực (JWT)
    auth_req = requests.post("https://api.mail.tm/token", json=account_data)
    token = auth_req.json().get("token")

    headers = {"Authorization": f"Bearer {token}"}

    logger.success(f"Đăng ký thành công! Email của bạn là: {address}")
    logger.info("Đang chờ tin nhắn mới (kiểm tra mỗi 5 giây)...")
    logger.warning("Script sẽ tự động dừng nếu không có thư mới trong 10 phút.")

    # 4. Vòng lặp kiểm tra hộp thư đến
    seen_messages = set()  # Lưu các mail đã đọc để không in lại

    timeout_seconds = 600  # 10 phút = 600 giây
    last_email_time = time.time()  # Đánh dấu thời gian bắt đầu

    while True:
        # Kiểm tra điều kiện dừng: Nếu quá 10 phút không có thư mới
        if time.time() - last_email_time > timeout_seconds:
            logger.warning("Đã 10 phút không có thư mới. Script tự động dừng lại.")
            break

        mail_req = requests.get("https://api.mail.tm/messages", headers=headers)

        if mail_req.status_code == 200:
            messages = mail_req.json().get("hydra:member", [])

            for msg in messages:
                msg_id = msg["id"]

                # Nếu có thư mới chưa đọc
                if msg_id not in seen_messages:
                    seen_messages.add(msg_id)

                    # Reset lại thời gian đếm ngược khi có thư mới
                    last_email_time = time.time()

                    logger.success("BẠN CÓ TIN NHẮN MỚI!")
                    logger.info(
                        f"Từ: {msg['from']['address']} | Tiêu đề: {msg['subject']}"
                    )

                    # 5. Lấy nội dung chi tiết của bức thư
                    content_req = requests.get(
                        f"https://api.mail.tm/messages/{msg_id}", headers=headers
                    )
                    body = content_req.json().get(
                        "text", "Không có nội dung dạng text."
                    )

                    logger.info(f"Nội dung:\n{body}")

                    # Trả về luôn (thoát vòng lặp) sau khi nhận được thư đầu tiên
                    # Nếu bạn muốn treo script để nhận nhiều thư, hãy xóa chữ 'return' đi
                    return

        time.sleep(5)


if __name__ == "__main__":
    get_temp_email_mailtm()
