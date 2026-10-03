import datetime
import logging
import os
import socket
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("boot_notify")

REQUEST_TIMEOUT = 10        # HTTPリクエストのタイムアウト（秒）
NETWORK_WAIT_MAX = 300      # ネットワーク接続を待つ最大時間（秒）
NETWORK_WAIT_INTERVAL = 5   # ネットワーク確認の間隔（秒）
SEND_RETRIES = 5            # Webhook送信の最大試行回数
SEND_RETRY_INTERVAL = 30    # 送信リトライの間隔（秒）


def wait_for_network(max_wait, interval):
    """外部へ接続できるようになるまで待つ。接続できればTrue、時間切れならFalse"""
    deadline = time.monotonic() + max_wait
    while True:
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=3):
                return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(interval)


def get_wan_ip():
    """外部サービスを利用してWAN IP（グローバルIP）を取得する"""
    services = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    for service in services:
        try:
            response = requests.get(service, timeout=3)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            continue
    return "取得失敗"


def get_local_ip(hostname):
    """外部接続に使われるローカルIPアドレスを取得する"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(hostname)
        except Exception:
            return "取得失敗"


def post_webhook(webhook_url, content, retries, interval):
    """Discordへ送信する。失敗時はリトライし、成功したらTrueを返す"""
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                webhook_url, json={"content": content}, timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 204:
                log.info("Discordへの通知に成功しました。")
                return True
            log.warning(
                "通知に失敗しました (%d/%d): %s - %s",
                attempt, retries, response.status_code, response.text,
            )
        except Exception as e:
            log.warning("エラーが発生しました (%d/%d): %s", attempt, retries, e)
        if attempt < retries:
            time.sleep(interval)
    return False


def send_startup_notification(webhook_url):
    # 起動直後はWi-Fi未接続のことがあるため、接続を待つ
    if not wait_for_network(NETWORK_WAIT_MAX, NETWORK_WAIT_INTERVAL):
        log.warning("ネットワーク接続を確認できませんでしたが、送信を試みます。")

    hostname = socket.gethostname()
    local_ip = get_local_ip(hostname)
    wan_ip = get_wan_ip()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"### Boot Notification ###\n"
        f"- HOST NAME: `{hostname}`\n"
        f"- WAN IP: `{wan_ip}`\n"
        f"- LOCAL IP: `{local_ip}`\n"
        f"- BOOT TIME: `{now}`"
    )
    return post_webhook(webhook_url, message, SEND_RETRIES, SEND_RETRY_INTERVAL)


def main():
    # スクリプトと同じ階層の .env（シンボリックリンク可）を読み込む
    load_dotenv(Path(os.path.abspath(__file__)).parent / ".env")

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        log.error("DISCORD_WEBHOOK_URL が設定されていません。")
        return 1

    return 0 if send_startup_notification(webhook_url) else 1


if __name__ == "__main__":
    sys.exit(main())