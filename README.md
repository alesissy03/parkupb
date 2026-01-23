# ParkUPB - Smart Parking Management System

Aplicație pentru monitorizarea și gestionarea locurilor de parcare din cadrul campusului UPB.

# Reservations for statistics
To add reservations:
```bash
python seed_fake_reservations.py <parking_lot name>
```
To delete reservations:
```bash
python delete_fake_reservations.py
```

## Prerequisites

- Python 3.8 or higher
- Git

## Setup Instructions

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd parkupb
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 4. Install Dependencies

**Windows:**
```bash
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

## Running the Application

### Start the Server

**Windows:**
```bash
python run.py
```

**Mac/Linux:**
```bash
python3 run.py
```

### Access the Application

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Stop the Server

Press `Ctrl+C` in the terminal

## Common Issues

### Virtual Environment Not Activating

**Windows:**
If you get an execution policy error:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Mac/Linux:**
Make sure you have Python 3 installed:
```bash
python3 --version
```

### Port Already in Use

Run on a different port:
```bash
python run.py --port 5001
```

Or in your code, modify `run.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

### Module Not Found Error

Make sure virtual environment is activated and dependencies are installed:
```bash
# Activate venv first
pip install -r requirements.txt
```

## Team Members

- Mocanu Alexia
- Olteanu Andreea-Denisa
- Rusen Paula

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Frontend:** HTML, CSS, JavaScript
- **Maps:** Leaflet.js, OpenStreetMap
- **Database:** SQLite

## API Documentation

See `/docs/api/endpoints.md` for detailed API documentation.

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is for educational purposes at Universitatea Politehnica București.
