# Mini‑Agent Gmail → Google Calendar

Un mini agent automatizat care monitorizeaza Gmail inbox-ul tau, extrage informatii despre intalniri/meeting-uri/evenimente din email-urile primite folosindu-se de Gmail API,, le interpreteaza folosind **Gemini**, si creeaza automat evenimente in **Google Calendar**.

Acest proiect include:

- citire e‑mailuri din INBOX (Gmail API)
- analiza semantica prin LLM (Gemini 2.5)
- extragerea datelor intr‑o structura mai stricta (Pydantic)
- creare automata a evenimentelor in Google Calendar

---

# 1. Instalare & configurare

## 1.1. Clonare proiect

```bash
git clone
cd <repo>
```

## 1.2. Setari de mediu

Creaza un fisier `.env`:

```env
GEMINI_API_KEY=
```

### Obtine cheia din Google AI Studio (Gemini)

[https://aistudio.google.com/](https://aistudio.google.com/)

---

# 1.3. Instalare dependinte

Eu folosesc **uv** (recomandat) dar merge si cu **pip**.

```bash
uv venv
uv pip install -r requirements.txt
```

```bash
uv pip install google-genai google-api-python-client google-auth-oauthlib python-dotenv bs4 pydantic
```

# 2. Configurare Google OAuth

Acest proiect foloseste OAuth 2.0 pentru acces la Gmail & Calendar.

1. Mergi la [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Creeaza un proiect
3. Enable la APIs:

   - **Gmail API**
   - **Google Calendar API**

4. Mergi la _Credentials_ > _Create Credentials_ > **OAuth client ID**
5. Alege _Desktop App_
6. Descarcă `credentials.json` si pune‑l in root-ul proiectului

La prima rulare, scriptul va deschide un browser pentru autentificare si va genera un `token.json`.

---

# 3. Rulare proiect

Dupa instalare si configurare:

## UV

```bash
uv run app.py
```

## Python normal

```bash
python app.py
```

Scriptul are un while-loop in care face polling INBOX-ului si proceseaza mailurile noi.

---

# 4. Cum funcționează agentul

1. Scriptul interogheaza periodic Gmail folosind un interval setat în `gmail.py` (`POLLING_INTERVAL_SECONDS`). Exista alternative mai bune, pt. a evita polling-ul, dar pt. necesitatea mea/demonstratie, e destul sa fac polling la un interval hard-codat.
2. Cand detecteaza un mesaj nou, extrage:
   - Subject, From, Date, Body (decodat, HTML cleaned)
3. Continutul mailului + instructiunile LLM sunt trimise catre Gemini.
4. Gemini intoarce JSON strict conform `ExtractedCalendarInfo`.
5. Daca exista evenimente, primul este convertit in Google Calendar Event.
6. Evenimentul este inserat automat in calendarul tau primar.
