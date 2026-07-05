# 台灣公開 API 接入清單 — 旅行目的地評估系統

> 國泰金控雲端開發工程師實習生 — 程式碼筆試
> 繳交期限：7/6（一）中午 12:00
> 本文件整理三個台灣政府公開 API 的申請方式、端點與回傳格式，供開發時對照。

---

## 系統定位

系統要回答一個問題：**「這個目的地、未來這週，適不適合去、怎麼安排？」**

三個資料源各補一塊，全部是台灣政府官方公開資料、免費，命中題目「公開資訊類 API」的精神：

| 資料源 | 角色 | 回答的問題 |
|---|---|---|
| 中央氣象署 | 一週天氣 | 去不去、帶什麼 |
| 環境部環境資料開放平臺 | 空氣品質 AQI | 健康考量 |
| TDX 運輸資料流通服務 | 景點 + 交通 | 玩什麼、怎麼去 |

---

## ① 中央氣象署 開放資料平臺

| 項目 | 內容 |
|---|---|
| 平台網址 | `https://opendata.cwa.gov.tw` |
| 申請方式 | 免費註冊會員（只需 email），登入後在會員專區取得「API 授權碼」 |
| 認證方式 | **最簡單**：授權碼直接帶在 URL query string 的 `Authorization` 參數 |
| 資料格式 | JSON（也支援 XML） |
| 介接方式 | RESTful API（也有 GraphQL，用 REST 即可） |
| 線上文件 | `https://opendata.cwa.gov.tw/dist/opendata-swagger.html`（Swagger，可線上產 URL） |
| 費用 | 免費 |

### 申請機制

需先註冊氣象會員（只需有效郵件帳號即可免費線上申請），登入平臺後即可發展程式介接進行資料擷取。

### 你要的資料集（預報類）

- **一般天氣預報-今明 36 小時**：資料代碼 `F-C0032-001`
- **鄉鎮天氣預報-未來一週**：這類才是「一週天氣概況」，可依縣市查詢

### 端點格式（RESTful）

```
https://opendata.cwa.gov.tw/api/v1/rest/datastore/{資料代碼}?Authorization={你的授權碼}&locationName={縣市名}
```

### Python 範例

```python
import requests

API_KEY = "CWA-XXXXXXXX-XXXX-XXXX"  # 你的授權碼
url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
params = {
    "Authorization": API_KEY,
    "locationName": "臺北市"
}
r = requests.get(url, params=params, timeout=10)
data = r.json()
# 天氣要素在 data['records']['location'][0]['weatherElement']
```

### ⚠️ 重要：7/6 格式異動（交件日當天）

氣象署官網公告：**7/6（一）預報類 API 格式即將異動**。這天正好是繳交日，而一週預報屬於「預報類」。

**應對**：程式對回傳欄位做容錯解析——用 `.get()` 安全取值、加 `try/except`、不要把欄位路徑寫死。這本來就是好習慣，在文件裡寫一句「已預留 API schema 變動容錯」反而是加分點，展示考慮到外部依賴的不穩定性。

---

## ② 環境部 環境資料開放平臺（空氣品質 AQI）

| 項目 | 內容 |
|---|---|
| 平台網址 | `https://data.moenv.gov.tw` |
| 申請方式 | 會員註冊後，平台**寄送 API 金鑰到你的信箱** |
| 申請頁面 | `https://data.moenv.gov.tw/api_term` |
| 認證方式 | API 金鑰帶在 URL 的 `api_key` 參數 |
| 資料格式 | JSON（也支援 CSV、XML） |
| 線上文件 | `https://data.moenv.gov.tw/swagger/` |
| 費用 | 免費 |

### 申請機制

平臺採會員服務機制，需帶入會員之 API 金鑰方可取得資料；於會員註冊後，平臺將寄出 API 金鑰信件，請妥善保存。

### 你要的資料集

- **空氣品質指標 (AQI)**：資料代碼 `aqx_p_432`（即時，每小時更新）
- **空氣品質預報資料**：若想要「未來幾天空品預報」配合一週天氣，這個更適合（每 30 分更新，免費）

### 端點格式

```
https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key={你的金鑰}&limit=1000&format=JSON
```

### Python 範例

```python
import requests

API_KEY = "your-api-key"
url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
params = {"api_key": API_KEY, "limit": 1000, "format": "JSON"}
r = requests.get(url, params=params, timeout=10)
records = r.json()["records"]
# 每筆有 county, sitename, aqi, status, pm2.5, longitude, latitude...
```

### 即時 AQI 回傳欄位（完整）

`SiteName`（測站名稱）、`County`（縣市）、`AQI`（空氣品質指標）、`Pollutant`（污染指標物）、`Status`（狀態）、`SO2`、`CO`、`O3`、`PM10`、`PM2.5`、`NO2`、`WIND_SPEED`、`WIND_DIREC`、`publishtime`（發布時間）、`Longitude`（經度）、`Latitude`（緯度）、`SiteId`（測站編號）等。

**有經緯度**，方便和地圖、景點做地理對應。

### ⚠️ 注意事項

- 舊網址 `data.epa.gov.tw` 已改版為 `data.moenv.gov.tw`（環保署升格環境部）
- 2022/12 曾把部分欄位大小寫統一改成小寫，欄位名請以 Swagger 文件當下顯示為準，一樣做容錯解析

---

## ③ TDX 運輸資料流通服務（景點 + 交通）

三個裡認證最複雜，但也最強大——交通部把全台運輸和觀光資料整合在一個平台。

| 項目 | 內容 |
|---|---|
| 平台網址 | `https://tdx.transportdata.tw` |
| 申請方式 | 註冊會員 → email 驗證 → **管理員審核**（約需幾天）→ 取得金鑰 |
| 學生優惠 | 有學生信箱可申請「**學研單位**」會員 |
| 認證方式 | **OAuth2（OIDC Client Credentials）**——先用金鑰換 Access Token，再帶 token 打 API |
| 金鑰 | Client Id + Client Secret（會員中心可建最多 3 組） |
| 資料格式 | JSON（OData 標準介面） |
| 速率限制 | 會員模式：每來源 IP **50 次/秒**，無每日上限 |
| 範例程式 | 官方 GitHub：`https://github.com/tdxmotc/SampleCode` |
| 費用 | 免費 |

### ⚠️ 關鍵：先申請！審核要時間

TDX 不像前兩個註冊完即用。註冊個人帳號後，帳號審核需要約三天，會由信箱通知審核結果。**所以 TDX 今天就該去申請**，不然審核還沒過就沒法開發。氣象署和環境部是即時的，可以晚點再弄。

### 認證流程（兩步驟）

TDX 和前兩個「key 直接帶 URL」不同，要**先換 token**。

**第一步：用金鑰換 Access Token**

取得 Access Token 的 API 為 `https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token`，使用 HTTP POST 方法，帶入 Client Id 和 Client Secret 進行驗證。

**第二步：帶 token 打 API**

呼叫 API 時在 header 帶入 `authorization: Bearer ACCESS_TOKEN`。

Access Token 有效期限預設為一天，到期後需重新取得。程式要做「token 過期自動重取」的邏輯。

### Python 範例

```python
import requests

# 第一步:換 token
auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
auth_data = {
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
}
token = requests.post(auth_url, data=auth_data, timeout=10).json()["access_token"]

# 第二步:帶 token 打觀光景點 API
headers = {"authorization": f"Bearer {token}"}
api_url = "https://tdx.transportdata.tw/api/basic/v2/Tourism/ScenicSpot/Taipei"
params = {"$top": 30, "$format": "JSON"}
spots = requests.get(api_url, headers=headers, params=params, timeout=10).json()
```

### 你要的資料集

**觀光（景點規劃用）**——觀光資訊資料庫 V2：交通部觀光署蒐集各政府機關發布的空間化觀光資訊，內容包含旅遊景點、活動訊息、餐飲美食及旅館民宿、旅遊服務站點、步道、自行車道等。

- 景點：`Tourism/ScenicSpot/{City}`
- 美食：`Tourism/Restaurant/{City}`
- 活動：`Tourism/Activity/{City}`

**交通（第二階段「怎麼去」用）**——TDX 涵蓋公共運輸（臺鐵、高鐵、捷運、輕軌、公車、公共自行車）、路況資訊、停車資訊等。第一階段先不碰，留給路線規劃那階段。

### OData 查詢語法（很好用）

- `$top`：取幾筆
- `$filter`：篩選
- `$select`：選欄位
- `$spatialFilter`：地理範圍篩選——能做「某座標附近的景點」，對旅行情境很實用

---

## 三個資料源對照總表

| | 氣象署 | 環境部 AQI | TDX |
|---|---|---|---|
| 申請難度 | ★ 即時 | ★ 即時（信箱收 key） | ★★★ 需審核約 3 天 |
| 認證方式 | URL 帶授權碼 | URL 帶 api_key | **OAuth2 換 token** |
| 資料格式 | JSON | JSON | JSON (OData) |
| 速率限制 | 寬鬆 | 寬鬆 | 50 次/秒 |
| 費用 | 免費 | 免費 | 免費 |
| 用途 | 一週天氣 | 空氣品質 | 景點/交通 |
| **何時申請** | 可晚 | 可晚 | **今天就申請** |

---

## 立即行動

### 1. 今天先去申請 TDX

用學生信箱選「學研單位」會員，因為要審核約 3 天，卡在這會拖到開發。氣象署和環境部即時就能用，不急。

### 2. 三個 API 的共同工程設計

- **金鑰安全三防線**：
  - key 只存在後端，前端只跟自己的後端講話（前端絕不放任何 key）
  - 本地開發用 `.env` + `.gitignore` 排除（key 絕不進 Git，交的是公開 Git 連結，這條死守）
  - 部署到 Azure 用 Key Vault 存 key（本身也是架構資安亮點）
- **容錯解析**：三個都做（特別是氣象署 7/6 改版、環境部欄位大小寫前科）
- **TDX 額外**：token 快取 + 過期自動重取

---

## 官方文件連結彙整

| 資料源 | 連結 |
|---|---|
| 氣象署平台 | https://opendata.cwa.gov.tw |
| 氣象署 Swagger | https://opendata.cwa.gov.tw/dist/opendata-swagger.html |
| 環境部平台 | https://data.moenv.gov.tw |
| 環境部申請頁 | https://data.moenv.gov.tw/api_term |
| 環境部 Swagger | https://data.moenv.gov.tw/swagger/ |
| TDX 平台 | https://tdx.transportdata.tw |
| TDX 官方範例 | https://github.com/tdxmotc/SampleCode |
