# Получение Azure Speech Service Key

## 1. Создание аккаунта Azure (бесплатно)

Перейди на: **https://portal.azure.com**

**Free Tier:**
- ✅ **5 часов/месяц** Speech-to-Text (бесплатно навсегда)
- ✅ ~300+ pronunciation assessments (по 15 сек каждый)
- ✅ Не нужна кредитная карта для free tier
- ✅ После free tier: ~$1 за 1000 запросов (pay-as-you-go)

## 2. Шаги регистрации

### 2.1 Создай аккаунт
1. Перейди на https://portal.azure.com
2. **Sign up** → Create Free Account
3. Заполни форму (email, телефон)
4. **НЕ НУЖНА** кредитная карта для free tier

### 2.2 Создай Speech Service ресурс

1. В Azure Portal → **Create a resource**
2. Поиск: **"Speech"**
3. Выбери **"Speech Services"**
4. Нажми **Create**

**Настройки:**
- **Subscription:** Free Trial или Azure for Students
- **Resource group:** Создай новую (например, "pronunciation-app")
- **Region:** **East US** (рекомендую, самый популярный)
- **Name:** Любое имя (например, "my-pronunciation-service")
- **Pricing tier:** **Free F0** (5 часов/месяц)

5. **Review + create** → **Create**
6. Подожди 1-2 минуты (ресурс создаётся)

### 2.3 Получи ключи

1. Перейди в созданный ресурс
2. Слева: **Keys and Endpoint**
3. Скопируй:
   - **KEY 1** (или KEY 2, любой)
   - **Region** (например, `eastus`)

## 3. Добавление в проект

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer

# Добавь в .env:
echo "AZURE_SPEECH_KEY=твой_ключ_сюда" >> .env
echo "AZURE_SPEECH_REGION=eastus" >> .env
```

**Пример .env:**
```bash
AZURE_SPEECH_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
AZURE_SPEECH_REGION=eastus
```

## 4. Проверка установки

```bash
source venv/bin/activate
python azure_scorer.py
```

Должно вывести анализ `test_data/russian_accent/russian1.mp3`

## 5. Лимиты Free Tier

**Бесплатно навсегда:**
- 5 часов Speech-to-Text в месяц
- = 18,000 секунд
- = ~1,200 запросов по 15 сек
- = ~40 запросов в день

**После превышения:**
- $1 за 1000 транзакций (0.001$ каждая)
- 1 транзакция = до 15 секунд аудио
- Можно установить billing alerts (чтобы не потратить лишнего)

## 6. Альтернативные регионы

Если `eastus` не работает, попробуй:
- `westus`
- `westeurope`
- `southeastasia`

Полный список: https://learn.microsoft.com/azure/ai-services/speech-service/regions

---

## ⚠️ Важно:

- **НЕ коммить** ключи в git
- `.env` уже в `.gitignore`
- Для production используй Azure Key Vault
- Можно установить **spending limit** в Azure Portal (защита от случайных трат)

## 🎯 Что дальше?

После получения ключа:
1. Протестируем на 82 русских спикерах
2. Сравним с Gentle
3. Интегрируем в веб-сервер
4. Запустим MVP!
