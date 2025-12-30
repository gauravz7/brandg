FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (if generic python image was used, but we use playwright image so this might be pre-installed, but 'install' ensures dependencies)
# Actually the image has browsers, but sometimes we need specifically 'chromium'
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
