# Project Instructions: 上網卡銷售報價查詢

## Project Context
- 本專案主要處理上網卡、eSIM、SIM 卡銷售與報價查詢。
- 核心範圍包含 Excel 商品資料、Python 查詢工具、客服支援系統、知識庫、部署設定與旅遊卡社群內容資料。
- 回覆預設使用繁體中文，重點放在報價準確、查詢效率與可維護性。

## Project Components
- `card.xlsx`、`eSim.xlsx`：實體卡與 eSIM 商品來源資料。
- `quote_lookup.py`、`run_quote_lookup.sh`：商品查詢與報價候選工具。
- `support_server.py`、`run_support_system.sh`：客服支援系統後端與啟動腳本。
- `CUSTOMER_SUPPORT_KNOWLEDGE.md`、`CUSTOMER_SUPPORT_SYSTEM.md`：客服知識與系統說明。
- `DATA_DICTIONARY.md`：商品欄位、查詢邏輯與報價注意事項。
- `DEPLOYMENT.md`、`Procfile`、`requirements.txt`：部署與執行環境設定。
- `k-sim-support-system/`：獨立 Git repository，不要由父層 repository 納入追蹤或改寫其 Git 歷史。

## Data Handling
- Excel 內的價格、天數、流量、國家/地區、方案名稱是關鍵資料，不能任意猜測或改寫。
- 修改報價邏輯前，先理解資料欄位與現有查詢流程。
- 若資料缺漏或格式不一致，先列出問題，不要自行補不存在的價格。
- 需要產出報價時，清楚列出方案、價格、限制、適用地區與備註。

## Coding Style
- 優先維持 `quote_lookup.py` 既有架構與操作方式。
- 修改程式時，避免無關重構。
- 對報價計算、篩選條件、欄位解析等邏輯要特別保守。
- 可以加入簡短註解解釋非直覺的報價或資料清理邏輯。
- 修改客服系統時，先閱讀 `CUSTOMER_SUPPORT_SYSTEM.md`、`CUSTOMER_SUPPORT_KNOWLEDGE.md` 與 `DEPLOYMENT.md`。
- 不要在程式、文件或 commit 中加入密碼、API key、客戶個資或客服工單內容。

## Commands
- 查詢商品使用 `./run_quote_lookup.sh <國家或關鍵字> [天數]`。
- 啟動客服系統使用 `./run_support_system.sh`。
- 若啟動腳本失敗，先檢查腳本指定的 Python runtime 與 `requirements.txt`，不要直接改動商品資料繞過問題。

## Content and Repository Boundaries
- 每週排程表、貼文成稿與產生圖片屬於可再生成的營運輸出，預設不納入本 repository 的版本控制。
- 社群題材是否重複，應參考 `K大叔FB社群經營/CONTENT_HISTORY.md`。
- 需要保留的重要商品規則、客服知識或流程，應整理進專案文件，不要只留在單次產出檔。
- 不要刪除或清理現有圖片、排程表與成稿，除非使用者明確要求。

## Verification
- 修改 Python 工具後，盡量用實際查詢案例測試。
- 修改 Excel 相關邏輯後，確認欄位名稱、資料列數與輸出結果是否合理。
- 修改客服系統後，至少確認程式可啟動、主要頁面或 API 可回應，且沒有洩漏敏感資料。
- 完成時簡短說明改了什麼、如何測試、是否有資料需人工確認。

## Output Preferences
- 報價結果適合整理成表格。
- 若有多個方案，優先依價格、天數、流量或推薦程度排序。
- 對客戶溝通版本要清楚、直接、避免內部術語。
