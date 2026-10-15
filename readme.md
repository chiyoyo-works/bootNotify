# Boot Notify for Raspberry Pi

Raspberry Piの起動時に **Discord** へ自動通知するPythonスクリプト群です。

---

## 特徴
**軽量な通知システム**: 外部の重いフレームワークを使わず、標準ライブラリと `requests` のみで動作します。
**環境変数の分離**: DiscordのWebhook URLは `.env` ファイルで一元管理し、セキュリティに配慮しています。
**systemd連携**: systemdのサービスを利用して、バックグラウンドで確実かつ自動的に実行されます。

---

## フォルダ構成

```text
bootNotify/
├── .env.example          # 環境変数（Webhook URL）のテンプレート
├── .gitignore            # Git除外設定
├── LICENSE               # MITライセンス
├── README.md             # このドキュメント
├── requirements.txt      # 依存Pythonパッケージ一覧
└── boot_notify.py        # 起動時通知スクリプト

