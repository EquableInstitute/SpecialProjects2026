# NVIDIA Holdings of Large State and Local Pension Funds: Daily Value Tracker

A static page (`index.html`) that charts the daily market value of the NVDA shares that 25 large U.S. public pension funds report holding. It reads `data.json`, which a GitHub Action rebuilds each weekday from the Google Sheet "NVIDIA Tracking (live)".

## How the daily update works

1. **5:41 PM ET, weekdays:** a Claude scheduled task adds the day's NVDA close to column B of 'Daily Values' in the Google Sheet (cross-checked between StockAnalysis.com and Yahoo Finance).
2. **6:47 PM EST / 7:47 PM EDT, weekdays:** the GitHub Action (`.github/workflows/nvda-update-data.yml` at the repository root) downloads the 'Daily Values' and 'Holdings' tabs as CSV, rebuilds `data.json`, and commits it if anything changed.
3. GitHub Pages republishes the site within a minute or two of the commit.

Edits made by hand in the sheet (a corrected close, new 13F holdings in slot 4) reach the site at the next run. Click **Actions → Update NVDA tracker data from Google Sheet → Run workflow** to sync right away.

## One-time setup

### 1. Let the Action read the sheet (pick one)

**Option A: publish only the two tabs (recommended).** Only those two tabs become public.
1. In the sheet: **File → Share → Publish to web**.
2. Choose the **Daily Values** tab and **Comma-separated values (.csv)**, click **Publish**, and copy the link.
3. Repeat for the **Holdings** tab.
4. In GitHub: **Settings → Secrets and variables → Actions → Variables → New repository variable**:
   - `DAILY_CSV_URL` = the Daily Values link
   - `HOLDINGS_CSV_URL` = the Holdings link

**Option B: link sharing.** Set the sheet to **Share → General access → Anyone with the link → Viewer**. No variables are needed. The whole workbook can then be opened by anyone who has the link.

### 2. Create the repository
1. On GitHub, click **New repository** (for example `nvda-pension-tracker`). Public, unless your plan allows Pages on private repositories.
2. Upload every file in this folder, keeping the folder structure: `index.html`, `data.json`, `.nojekyll`, `README.md`, `scripts/update_data.py`, `.github/workflows/update-data.yml`.
   - Using the web uploader: drag the whole unzipped folder onto **Add file → Upload files**. Check that `.github/workflows/update-data.yml` is there; hidden folders are sometimes skipped. If so, use **Add file → Create new file**, type `.github/workflows/update-data.yml` as the name, and paste the contents.
   - Using git: `git init`, `git add .`, `git commit -m "Initial tracker"`, `git branch -M main`, `git remote add origin <repo URL>`, `git push -u origin main`.

### 3. Turn on GitHub Pages
**Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main, folder: / (root) → Save.** The site appears at `https://<your-account>.github.io/<repo-name>/`. For a custom subdomain (for example `data.equable.org`), enter it under **Custom domain** and add the CNAME record GitHub shows to your DNS.

### 4. Allow the Action to commit
**Settings → Actions → General → Workflow permissions → Read and write permissions → Save.** Then open **Actions**, enable workflows if prompted, and click **Run workflow** once to test. A green check with "No change" or "data.json updated" means it worked.

## Putting it on a WordPress page

Add a **Custom HTML** block:

```html
<iframe src="https://<your-account>.github.io/<repo-name>/"
        title="NVIDIA holdings of large public pension funds: daily value tracker"
        style="width:100%;height:2600px;border:0" loading="lazy"></iframe>
```

Adjust the height to fit your layout, or link to the page directly.

## Files

| File | What it is |
|---|---|
| `index.html` | The page. Calculates every figure in the browser from `data.json`. |
| `data.json` | Closing prices (`daily`) and holdings (`holdings`) copied from the sheet. Rebuilt by the Action. |
| `scripts/update_data.py` | Downloads the two tabs, checks them (200+ closes, prices in a sane range, 20+ fund rows), and writes `data.json`. Exits without writing if a check fails. |
| `.github/workflows/update-data.yml` | Weekday schedule plus a manual "Run workflow" button. |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is. |

## If the sheet's layout changes
The script reads 'Daily Values' from row 8 down (columns A–B), so date rows added below row 258 are picked up. It reads Holdings rows 9–34 (columns A–P); if you add funds, update `HOLD_LAST` at the top of `scripts/update_data.py` (and the Holdings range in the Claude scheduled task).
