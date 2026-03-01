# Получение Speechace API Key

## 1. Регистрация (бесплатно)

Перейди на: **https://www.speechace.com/api/**

**Free Tier:**
- ✅ **1000 запросов/месяц** (бесплатно навсегда)
- ✅ Полный функционал (phoneme scores, fluency, timing)
- ✅ Нет кредитной карты для регистрации

## 2. Шаги регистрации

1. **Sign Up** → Create Free Account
2. Заполни форму:
   - Email
   - Password
   - Company name (можно любое)
3. Подтверди email
4. Войди в dashboard
5. **Copy API Key** (будет видно сразу после входа)

## 3. Добавление в проект

```bash
# В терминале:
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer

# Создай .env файл (если ещё нет):
echo "SPEECHACE_API_KEY=your_key_here" >> .env

# Или руководствуйся .env.example
```

## 4. Проверка установки

```bash
# Тест API:
source venv/bin/activate
python speechace_scorer.py
```

Должно вывести анализ `test_data/russian_accent/russian1.mp3`

## 5. Альтернатива (если нужно больше запросов)

**Платные планы:**
- Starter: $19/mo → 10,000 requests
- Pro: $49/mo → 50,000 requests
- Enterprise: Custom pricing

Но для MVP **1000 бесплатных** хватит!

---

## ⚠️ Важно:

- **НЕ коммить** API key в git
- `.env` уже в `.gitignore`
- Для production используй environment variables
