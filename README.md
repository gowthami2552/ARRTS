# ARRTS — Advanced Railway Routing & Travel System

An advanced railway routing, journey planning, and timetable search engine with an interactive frontend, live journey diagnosis, connecting route discovery, and an intelligent railway assistant.

---

## 🌟 Features

- **Direct & Connecting Journey Search**: Finds optimal direct trains as well as intelligent multi-leg connecting routes with realistic layover times.
- **Interactive Route Visualization**: Visual journey maps showing station hops, coordinates, and intermediate stops.
- **Railway Chatbot Assistant**: Embedded AI/knowledge assistant for handling railway timetable and station queries.
- **Live Timetable & Station Index**: Powered by indexed timetable datasets (`trains.csv`, `stops.csv`, `stations.csv`, `schedules.jsonl`).
- **Full REST API**: Clean endpoints for station autocomplete, direct routes, connecting routes, timetable lookups, and diagnostic information.

---

## 📂 Project Structure

```text
ARRTS/
├── app.py                      # Main Flask application and REST API
├── engine/
│   ├── chatbot.py              # Railway chatbot and knowledge base
│   └── search.py               # Direct and connecting search engine
├── data/
│   ├── out/                    # Processed CSVs and JSONL timetable data
│   └── railwaystationlist.json # Station master dataset
├── templates/
│   ├── index.html              # Main web portal interface
│   └── journey.html            # Detailed journey visualization
├── static/                     # Assets, scripts, and styling
├── start_arrts.bat             # Quick launch script for Windows
└── requirements.txt            # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Installation
```bash
git clone https://github.com/gowthami2552/ARRTS.git
cd ARRTS
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```
Or simply double-click `start_arrts.bat` on Windows.

Open your browser at `http://127.0.0.1:5000` to access the ARRTS portal.

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
