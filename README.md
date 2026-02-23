# 📈 React Asset Dashboard

A modern, high-performance, and privacy-focused asset management dashboard built with React and Tailwind CSS. It visualizes personal finance data exported from Google Sheets, providing a sleek interface for tracking net worth, asset allocation, and historical performance.

## ✨ Features

- **Realistic Linear Charting:** Uses `recharts` to render a highly accurate, un-smoothed historical Net Asset Value (NAV) curve, complete with an interactive X-axis timeline.
- **Dynamic Time Ranges:** Zero-latency toggles to slice data across multiple horizons (**7D**, **30D**, and **ALL**) without reloading.
- **Bone-Screen Privacy Mode:** A hardware-level secure UI toggle that masks all sensitive numerical data with an elegant `••••••` string replacement (avoiding readable CSS blur hacks), perfect for public viewing or screen sharing.
- **Data Anonymization Engine:** Includes a Python secure-scalar script (`generate_demo_data.py`) that extracts real Google Sheets data and multiplies it by a random scalar. This generates a safe, realistic demo `.json` payload that preserves 100% accurate performance curves and percentages while completely obfuscating the underlying absolute wealth.

## 🛠️ Tech Stack

- **Frontend Framework:** React 18, Vite
- **Styling:** Tailwind CSS (utility-first, responsive design)
- **Data Visualization:** Recharts (SVG-based reactive chart components)
- **Animations:** Framer Motion (smooth entry transitions and micro-interactions)
- **Icons:** Lucide-React
- **Data Processing:** Python (Pandas) for data extraction and formatting from raw `.xlsx` exports.

## 🚀 Getting Started

### Prerequisites

- Node.js (v18+)
- Python 3.9+ (if you wish to extract your own raw Excel data)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/zcxixixi/Asset-Management.git
   cd Asset-Management
   ```

2. Install JavaScript dependencies:

   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Navigate to `http://localhost:5173` to see the dashboard running locally over the anonymized mock data.

### 📊 Injecting Your Own Data

The dashboard consumes data from `src/data.json`. To use your own real-time Google Sheets tracking:

1. Export your tracking sheet as `assets.xlsx` and place it in the `public/` directory.
2. Run the extraction script (make sure `pandas` and `openpyxl` are installed):
   ```bash
   python3 src/extract_data.py
   ```
3. To generate highly secure demo data (scaled values but true trends) for safe sharing, run instead:
   ```bash
   python3 src/generate_demo_data.py
   ```

## 🔒 Security

The project strictly `.gitignore`s the `public/assets.xlsx` file. Real asset data is never committed to version control. The included `data.json` provides a pre-scaled demo sample.

---

_Designed for precision, built for privacy._
