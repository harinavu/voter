# Sakhavaram Voter Search 🗳️

> **Search voter details for Sakhavaram Gram Panchayat — General Elections 2026**

A beautiful, fast, offline-capable voter search website built from the official 2026 voter roll.

## 🌐 Live Website
**[Open Voter Search →](https://navulurineelima.github.io/search_voter/)**

## ✨ Features
- 🔍 **Instant search** by voter name (Telugu), Voter ID, or house number
- 👨👩 **Filter** by gender (Male / Female)
- 📅 **Age range filter**
- 📋 **Browse all 2,187 voters** with pagination
- 🖥️ **Voter detail modal** with full information
- 🖨️ **Print** voter details
- ⬇️ **Export** search results as CSV
- 📊 **Download** full voter list as Excel

## 📊 Data
- **Total Voters**: 2,187
- **Source**: Sakhavaram Gram Panchayat Official Voter Roll 2026
- **District**: Prakasam, Andhra Pradesh

## 📁 Files
| File | Description |
|------|-------------|
| `index.html` | Main website |
| `style.css` | Styling |
| `app.js` | Search & filter logic |
| `voters.json` | Voter data (all 2,187 voters) |
| `voters.xlsx` | Excel file with voter data |
| `extract_voters.py` | Script used to extract data from PDF |

## 🚀 Run Locally
Just open `index.html` in a browser — no server needed for browsing!

For local development with live reload:
```bash
npx serve .
```

## 📜 Data Fields
Each voter record contains:
- Voter Name (Telugu)
- Voter ID Card Number
- Father's / Husband's Name
- Age
- Gender
- House Number
- Part Serial Number / Full Serial Number
