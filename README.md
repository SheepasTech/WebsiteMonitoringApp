# Tinklalapių Stebėjimo Sistema

## 🗄️ DUOMENŲ BAZĖS SĄRANKA

### MySQL/MariaDB Diegimas
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mariadb-server mariadb-client

# Paleisti ir įjungti servisą
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Saugos sąranka
sudo mysql_secure_installation
```

### Duomenų bazės ir vartotojo sukūrimas
```bash
# Prisijungti kaip root
sudo mysql -u root -p
```

**Įklijuoti MySQL konsolėje:**
```sql
CREATE DATABASE website_monitor;
CREATE USER 'monitor_user'@'localhost' IDENTIFIED BY 'jusu_slaptazodis';
GRANT ALL PRIVILEGES ON website_monitor.* TO 'monitor_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 🚀 PROGRAMOS SĄRANKA

1. Redaguoti .env failą:
```bash
# Duomenų bazės nustatymai
DB_USER=monitor_user
DB_PASSWORD=jusu_slaptazodis
DB_HOST=localhost
DB_DATABASE=website_monitor

# Stebėjimo nustatymai
JITTER_REQUESTS_COUNT=3
JITTER_REQUEST_DELAY=1
REQUEST_TIMEOUT=30
AUTO_REFRESH_INTERVAL=10000

# Flask nustatymai
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

2. Sukurti Python aplinką:
```bash
python3 -m venv ~/monitor_env
source ~/monitor_env/bin/activate
pip install -r Requirements.txt
```

3. Sukurti duomenų bazės struktūrą:
```bash
python db_setup.py
```

## 🚀 GREITAS PALEIDIMAS

```bash
# 1. Aktyvuoti Python aplinką
source ~/monitor_env/bin/activate

# 2. Paleisti stebėjimą
python improve_monitor.py

# 3. Paleisti web sąsają
python flask_monitor_app.py

# 4. Atidaryti naršyklėje: http://127.0.0.1:5000
```

## 📖 NAUDOJIMAS

### Duomenų rinkimas:
```bash
python improve_monitor.py              # Vienas stebėjimo ciklas
python improve_monitor.py --url <URL>  # Stebėti konkretų URL
python improve_monitor.py --schedule   # Automatinis stebėjimas
```

### Web sąsaja:
```bash
python flask_monitor_app.py            # Paleisti web panelę
```

## 📊 JITTER SKAIČIAVIMAS

**Jitter** - tinklo vėlavimo svyravimas tarp iš eilės einančių užklausų:

- **Formulė**: `jitter = |dabartinis_velavimas - ankstesnis_velavimas|`
- **Vienetai**: Milisekundės (ms)
- **Interpretacija**:
  - **Žemas jitter (0-5ms)**: Stabilus tinklas
  - **Vidutinis jitter (5-20ms)**: Priimtinas
  - **Aukštas jitter (>20ms)**: Galimos tinklo problemos

## 🗃️ DUOMENŲ BAZĖS VALDYMAS

### Prisijungimas:
```bash
mysql -u monitor_user -p website_monitor
```

### Naudingos komandos:
```sql
SHOW TABLES;                     -- Rodyti lenteles
DESCRIBE website_metrics;        -- Lentelės struktūra
SELECT * FROM website_metrics ORDER BY timestamp DESC LIMIT 10;  -- Paskutiniai duomenys
TRUNCATE TABLE website_metrics;  -- Išvalyti duomenis
```



