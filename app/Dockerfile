# 1. Escolha a imagem base do Python (existem várias versões)
FROM python:3.11-slim

# 2. Define onde o código vai morar dentro do container
WORKDIR /app

# 3. Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia o resto do seu código
COPY . .

# 5. O comando que inicia sua aplicação
CMD ["python", "main.py"]