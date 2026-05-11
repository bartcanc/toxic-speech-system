# pobranie lekkiego obrazu pythona
FROM python:3.10-slim
# ustawienie katalogu roboczego
WORKDIR /app
# skopiowanie wymagań do kontenera
COPY requirements .
# instalacja bibliotek
RUN pip install --no-cache-dir -r requirements
# kopia całego projektu
COPY . .
# ustawienie ścieżki do projektu
ENV PYTHONPATH="/app/backend_api"
EXPOSE 8000
# uruchomienie aplikacji
CMD ["uvicorn", "backend_api.main:app", "--host", "0.0.0.0", "--port", "8000"]