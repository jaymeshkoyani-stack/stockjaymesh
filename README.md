# iCharts Live Strategy 1, Strategy 2 & Master Excel Dashboard (215+ F&O Symbols)

A real-time financial web application and scanner dashboard for tracking **215+ Indian F&O Index and Stock Options** (NIFTY, BANKNIFTY, FINNIFTY, SENSEX, RELIANCE, TCS, INFY, ADANIENT, BAJAJFINSV, etc.).

---

## 🌟 Key Features

1. **Strategy 2 Scanner (QTY OTM & Future OI):**
   - Automatically scans **Future OI** from `SymbolDashboard.php` and compares it with **Total OTM OI Chg (Calls & Puts)** in **Quantity (QTY)** mode.
   - Calculation: $\text{Future OI} \times 15\% < \text{Total OTM OI Chg (Calls)}$ OR $\text{Total OTM OI Chg (Puts)}$.

2. **Strategy 1 Scanner:**
   - Real-time OI concentration check: $\text{Total OI Chg Net} > \text{Total OI (Calls)}$ AND $\text{Total OI (Puts)}$, with negative Calls/Puts OI Chg highlighting.

3. **Master Excel Grid View:**
   - Dense spreadsheet layout with sticky symbol column, sortable headers, red/green cell highlights, symbol search bar, and sentiment filter.

4. **1-Click Export to Excel:**
   - Download Strategy 1, Strategy 2, or Master Excel Grid data into `.csv` spreadsheet files anytime.

5. **Zero Data Loss & Session Auto-Recovery:**
   - Persistent backend data store (`backend_store.json`) guarantees data retention even if iCharts session disconnects.
   - Clicking **Sync Now** automatically re-authenticates login with iCharts.

---

## 🚀 Quick Deployment to GitHub & Online Hosting

### Step 1: Create a GitHub Repository
1. Go to [https://github.com/new](https://github.com/new).
2. Name your repo `icharts-excel-dashboard`.
3. Select **Public** or **Private**, then click **Create Repository**.

### Step 2: Push Code to GitHub
Run the following commands in your terminal:
```bash
cd C:\Users\Manan\.gemini\antigravity\scratch\icharts_dashboard
git init
git add .
git commit -m "Initial commit for iCharts Master Excel & Strategy Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/icharts-excel-dashboard.git
git push -u origin main
```

### Step 3: Enable Free Online Hosting (GitHub Pages / Vercel)
* **GitHub Pages (Free):**
  1. Go to your GitHub repository -> **Settings** -> **Pages**.
  2. Under **Source**, select **`main`** branch and `/ (root)` folder.
  3. Click **Save**. Your dashboard will be live at `https://YOUR_GITHUB_USERNAME.github.io/icharts-excel-dashboard/`!

* **Vercel / Netlify (1-Click Hosting):**
  - Import your GitHub repository to Vercel or Netlify for free SSL and instant web hosting!

---

## 🛠️ Running Locally

1. **Start Dashboard Server:**
   ```bash
   python server.py
   ```
2. Open your web browser at **`http://localhost:8080`**.

3. **Background Updater Daemon:**
   ```bash
   python live_updater_3min.py
   ```

---

## 📁 Repository Project Structure

```
icharts_dashboard/
├── index.html                  # Main Web Dashboard UI Layout
├── styles.css                  # Modern Glassmorphism & Excel Grid CSS
├── app.js                      # Strategy 1 & Strategy 2 Evaluators & Table Logic
├── server.py                   # Custom HTTP Server & Re-Login API Endpoint
├── fetch_all_216_full.py       # Multi-Threaded iCharts Data Extractor & Store
├── live_updater_3min.py        # 3-Minute Background Auto-Updater Daemon
├── data.json                   # Live Web Dataset (215+ Symbols)
├── backend_store.json          # Persistent Data Vault (Prevents Data Loss)
├── requirements.txt            # Python Dependencies
└── README.md                   # Project Documentation & Hosting Guide
```
