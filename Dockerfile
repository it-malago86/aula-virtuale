FROM python:3.10-slim
WORKDIR /app
# Installa Flask e Redis (le dipendenze per il web)
RUN pip install flask redis
COPY . .
# Esponi la porta interna
EXPOSE 5000
CMD ["python", "app.py"]
