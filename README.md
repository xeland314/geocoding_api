# Geocoding API

A **FastAPI-based reverse geocoding service** that integrates multiple geolocation providers, including **Geoapify**, **HERE**, and **Nominatim**. This API enables dynamic and flexible geolocation queries while ensuring automated environment-based configuration.

## 🔥 Key Features

- **Multi-provider support** – Query different geocoding services dynamically.
- **Automated configuration** – Detects and registers geocoders using environment variables.
- **Flexible provider selection** – Choose any available provider or fall back to defaults.
- **High-performance FastAPI** – Built with FastAPI for scalability and speed.

---

## ⚙️ Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/xeland314/geocoding_api.git
   cd geocoding_api
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r pyproject.toml
   ```

---

## 🌍 Environment Configuration

Set up API keys using environment variables:

```bash
export GEOAPIFY_API_KEY="your_api_key"
export HERE_API_KEY="your_api_key"
export NOMINATIM_USER_AGENT="MyGeocoderApp/1.0"
export NOMINATIM_REVERSER_REPLICA_URL_1="http://127.0.0.1:8088/reverse"
export NOMINATIM_REVERSER_REPLICA_URL_2="http://127.0.0.1:8089/reverse"
```

Alternatively, use the provided `set_env.sh` script:

```bash
source ./scripts/set_env.sh
```

---

## 🚀 Running the API

Start the FastAPI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation available at:
🔗 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Endpoints

### 🔎 Reverse Geocode

Perform reverse geocoding by specifying latitude, longitude, and an optional provider:

```bash
curl -X GET "http://127.0.0.1:8000/reverse-geocode?latitude=40.748817&longitude=-73.985428&platform=geoapify"
```

**Example Response**:

```json
{
  "success": true,
  "data": [
    {
      "formatted_address": "Empire State Building, 350 5th Ave, New York, NY, USA",
      "postcode": "10118",
      "country": "US",
      "state": "New York",
      "district": "Manhattan",
      "settlement": "New York",
      "street": "5th Ave",
      "house": "350"
    }
  ],
  "error": null
}
```

### 📜 List Available Providers

Retrieve the list of dynamically registered geocoders:

```bash
curl -X GET "http://127.0.0.1:8000/geocoders"
```

**Example Response**:

```json
{
  "geocoders": [
    {
      "name": "GEOAPIFY",
      "url": "https://api.geoapify.com/v1/geocode/reverse"
    },
    {
      "name": "HERE",
      "url": "https://revgeocode.search.hereapi.com/v1/revgeocode"
    },
    {
      "name": "NOMINATIM",
      "url": "https://nominatim.openstreetmap.org/reverse"
    },
    {
      "name": "NOMINATIM_REPLICA_1",
      "url": "http://127.0.0.1:8088/reverse"
    }
  ]
}
```

---

## 🧪 Running Tests

Execute unit tests using:

```bash
python -m unittest discover -s tests -p "*.py"
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3 (GPLv3)**.  
You are free to **use, modify, and distribute** this project under the terms of the GPLv3 license.

See the [`LICENSE`](LICENSE) file for full details.

---

## ⚠️ Disclaimer

> **This project integrates third-party geocoding services** (**HERE**, **Geoapify**, **Nominatim**).  
> Users must comply with each provider's **terms of service** and **usage limits**.  
> The author of this project **does not endorse or facilitate** any violations of external API agreements.

---

### 🔥 Improvements:

✔ **Enhanced clarity and structure** – Readability improved with better formatting.  
✔ **Clear API usage examples** – Now includes requests and responses for easier understanding.  
✔ **Emphasized key sections** – Features, installation, API endpoints, and environment setup are highlighted.  
✔ **Interactive & user-friendly formatting** – Icons and spacing improve readability.
Absolutely! Here’s the **updated license section** to reflect **GNU GPL v3**, including a clarification about compliance with third-party geolocation services:
