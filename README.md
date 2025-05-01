# Geocoding API

A FastAPI-based reverse geocoding service integrating multiple geolocation providers such as **Geoapify**, **HERE**, and **Nominatim**. This API enables dynamic location lookups with flexible provider selection and automated environment-based configuration.

## Features
- **Multi-provider support**: Query different geocoding providers dynamically.
- **Automated configuration**: Detects and registers geocoders based on environment variables.
- **Flexible provider selection**: Use any available provider or fall back to defaults.
- **FastAPI integration**: Built with FastAPI for high performance and scalability.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/xeland314/geocoders_api.git
   cd geocoders_api
