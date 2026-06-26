# K大叔上網卡客服系統部署說明

## 先講結論

目前這套客服系統可以放到網路上使用，但不建議直接把本機服務裸露到公開網路。建議用雲端平台部署，並設定登入帳密。

最簡單的部署方式：

1. 將專案放到 GitHub。
2. 到 Render、Railway、Fly.io 或類似 Python Web App 平台建立服務。
3. 指定啟動指令：

```bash
python support_server.py --host 0.0.0.0
```

4. 設定環境變數：

```text
SUPPORT_USERNAME=你的客服帳號
SUPPORT_PASSWORD=你的客服密碼
```

平台通常會自動提供 `PORT`，系統已支援讀取 `PORT` 環境變數。

## 用 Render 建立網站

專案已包含 `render.yaml`，可用 Render Blueprint 建立服務：

1. 登入 Render 並連接 GitHub。
2. 選擇 `New` → `Blueprint`。
3. 選擇 GitHub repo `afkevinfan-code/e-SIM_service`。
4. Render 會讀取 `render.yaml`，建立名稱為 `e-sim-service` 的 Web Service。
5. 在 Render 的 Environment 設定 `SUPPORT_USERNAME` 與 `SUPPORT_PASSWORD`。
6. 按部署後，Render 會提供一個 HTTPS 網址，可給手機與外部客服使用。

服務會用 `/healthz` 作為健康檢查。GitHub `main` 有新的 commit 時，Render 會自動重新部署。

## 需要一起上傳的檔案

部署客服系統至少需要：

| 檔案 | 用途 |
|---|---|
| `support_server.py` | 客服系統網頁服務 |
| `quote_lookup.py` | 查詢商品資料 |
| `card.xlsx` | 實體 SIM 商品資料 |
| `eSim.xlsx` | eSIM 商品資料 |
| `requirements.txt` | Python 套件需求 |
| `Procfile` | 雲端平台啟動指令 |
| `CUSTOMER_SUPPORT_KNOWLEDGE.md` | 客服知識文件 |
| `CUSTOMER_SUPPORT_SYSTEM.md` | 系統使用說明 |

## 本機與網路版差異

| 使用方式 | 網址範例 | 適合情境 |
|---|---|---|
| 本機使用 | `http://127.0.0.1:8766` | 只有自己的 Mac 使用 |
| 同 Wi-Fi 手機使用 | `http://192.168.x.x:8766` | 手機和 Mac 在同一個 Wi-Fi |
| 雲端部署 | `https://你的服務網址` | 外部客服、手機、不同地點都要使用 |

## 安全注意事項

這套系統會處理客戶問題與可能的訂單資訊，上線前請注意：

- 一定要設定 `SUPPORT_USERNAME` 和 `SUPPORT_PASSWORD`。
- 不要把 `support_tickets.jsonl` 公開上傳到 GitHub。
- `card.xlsx`、`eSim.xlsx` 若包含成本或內部資料，請確認是否能放到雲端。
- 免費雲端平台可能會休眠，第一次開啟可能較慢。
- 目前工單寫入本機檔案 `support_tickets.jsonl`；若部署平台重啟或使用臨時檔案系統，工單可能遺失。

## 建議部署階段

### 階段 1：內部試用

- 用雲端平台部署。
- 設定帳密。
- 只給自己或內部客服使用。
- 工單暫時用 `support_tickets.jsonl`。

### 階段 2：正式使用

正式使用時建議再升級：

- 工單改存資料庫，例如 SQLite、PostgreSQL 或 Google Sheets。
- 增加工單查詢與狀態管理。
- 增加登入角色，例如管理者、客服。
- 將 Excel 更新流程標準化，避免雲端資料與本機資料不同步。

## Render 類平台常見設定

| 設定項目 | 建議值 |
|---|---|
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python support_server.py --host 0.0.0.0` |
| Environment Variables | `SUPPORT_USERNAME`、`SUPPORT_PASSWORD` |

## Railway 類平台常見設定

Railway 通常會偵測 `Procfile` 或 Python 專案。若需手動指定：

```bash
python support_server.py --host 0.0.0.0
```

並設定：

```text
SUPPORT_USERNAME=你的客服帳號
SUPPORT_PASSWORD=你的客服密碼
```

## 不建議的做法

不建議直接在家用 Mac 上開 port 給外網連線，原因：

- 需要處理路由器 port forwarding。
- 需要固定 IP 或 DDNS。
- 家用網路與電腦安全風險較高。
- Mac 關機、睡眠或網路斷線，客服系統就不能用。

雲端部署會比較穩定，也比較容易管理網址與 HTTPS。
