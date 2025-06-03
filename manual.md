# Aiontwikkelhulp Handleiding

## Inleiding
Aiontwikkelhulp is een webgebaseerde tool om de samenwerking tussen ontwikkelaars en AI-modellen van Anthropic te stroomlijnen. De applicatie biedt een chatinterface, automatische workflowondersteuning en integraties met GitHub via het Model Context Protocol (MCP). Deze handleiding bestaat uit drie delen:

1. **Gebruikershandleiding** – hoe je de tool gebruikt vanuit de browser.
2. **Installatie** – stappen om de applicatie lokaal of in productie te draaien.
3. **Technische achtergrond** – overzicht van de belangrijkste modules en hun samenhang.

---

## 1. Gebruikershandleiding

### Inloggen
1. Navigeer naar de webinterface (`/` of `http://localhost:5000`).
2. Klik op **Login** en meld je aan met je `@lynxx.com` Google-account.
3. Na succesvolle authenticatie kom je op het dashboard terecht.

### Chatten met Claude
1. Open de chatpagina en typ je vraag of opdracht in het invoerveld.
2. Gebruik het `ga <repository>` commando om automatisch aan een repository te werken. De AI creëert issues en pull requests en voert de stappen uit volgens `werkwijze/werkwijze.txt`.
3. De rechterkolom toont gedetailleerde logs van elke interactie, inclusief toolgebruik.

### Workflow mode
- Schakel de **Workflow** toggle in om meerdere chats automatisch te laten openen en sluiten op basis van herkenbare patronen in de AI-responses.
- Er worden tabs aangemaakt voor de verschillende workflowprofielen (Issue Creation, PR Creation en PR Processed). Een draaiende indicator laat zien welke tab actief is.
- Volg de voortgang in de logs; de AI kan zelfstandig issues aanmaken, pull requests openen en mergen.

### Gesprekken beheren
- Via het menu **Conversations** bekijk je eerdere gesprekken. Je kunt zoeken, pagineren en gesprekken in bulk verwijderen.
- In het analytics-scherm zie je per gesprek het tokengebruik en de bijbehorende kosten.

### Tips
- Bij fouten in OAuth of MCP-verbindingen raadpleeg je de sectie *Troubleshooting* in de README.
- Zet bij debugging de omgevingvariabele `LOG_LEVEL` op `DEBUG` om uitgebreide logs te krijgen.

---

## 2. Installatie

### Vereisten
- Python 3.8 of hoger
- Google OAuth-gegevens (client ID en secret)
- Een Anthropic API key
- Optioneel: GitHub Personal Access Token voor MCP-tools

### Stappen
1. **Repository clonen**
   ```bash
   git clone https://github.com/Fbeunder/aiontwikkelhulp.git
   cd aiontwikkelhulp
   ```
2. **Virtuele omgeving maken**
   ```bash
   python -m venv venv
   source venv/bin/activate  # of venv\Scripts\activate op Windows
   ```
3. **Afhankelijkheden installeren**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment instellen** – Maak een `.env` bestand op basis van `.env.example` en vul minimaal de volgende waarden in:
   ```env
   FLASK_ENV=development
   SECRET_KEY=your-secret
   GOOGLE_CLIENT_ID=<client-id>
   GOOGLE_CLIENT_SECRET=<client-secret>
   ANTHROPIC_API_KEY=<anthropic-key>
   ```
   Voor aanvullende variabelen zie de sectie "Stap 5" van de README.
5. **Database initialiseren**
   ```bash
   flask db upgrade
   ```
6. **Applicatie starten**
   ```bash
   python app.py
   ```
   De website draait nu op `http://localhost:5000`.

### Productie
Gebruik bij voorkeur Gunicorn of Docker voor productie. Voorbeeld:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 3. Technische achtergrond

Onderstaand overzicht beschrijft hoe de belangrijkste modules samenwerken.

### Flask applicatie
`app.py` bevat de functie `create_app` die de configuratie laadt, logging instelt, de database initialiseert en alle routes registreert. Zie onder meer regels 13–55 voor deze setup.

### Configuratie
`config.py` definieert de basisinstellingen en leest environment-variabelen. De klasse `BaseConfig` bevat onder andere de OAuth- en databaseconfiguratie (regels 13–38). Anthropic-specifieke instellingen worden beheerd door `anthropic_config.py`.

### Anthropic integratie
`anthropic_api.py` vormt de schakel tussen de applicatie en de Anthropic API. Het houdt runtime-instellingen bij (zoals temperature) en registreert tokengebruik. De methode `update_runtime_settings` op regels 115–152 past waarden aan zonder herstart.
`anthropic_client.py` voert de daadwerkelijke API-calls uit en ondersteunt presets en model-specifieke limieten.

### Conversatiebeheer
`conversation_manager.py` beheert gesprekken in geheugen én (indien ingeschakeld) in de database. De klasse `ConversationManager` start rond regel 36 en slaat berichten op via `ConversationRepository` wanneer `storage_backend=True`.

### Database
Het bestand `database.py` initialiseert SQLAlchemy en maakt de tabellen aan (zie `init_db` op regels 16–32). De datamodellen voor gesprekken en berichten staan in `models/conversation.py`.

### Routes en API
Alle REST-endpoints bevinden zich in `routes/api.py`. Voorbeelden zijn `/api/llm-settings` en conversation-endpoints voor lijst- en zoekfunctionaliteit. Authenticatie wordt geregeld via `auth.py` met Google OAuth.

### MCP-integratie
De module `mcp_integration.py` verbindt met een MCP-server voor GitHub-tools. Bij het verzenden van een prompt worden tools opgehaald en uitgevoerd (zie `AnthropicAPI._send_prompt_async` rond regel 245). Toolresultaten en -fouten worden gelogd en teruggegeven aan de gebruiker.

### Analytics
Tokengebruik en kosten worden bijgehouden in `analytics/token_tracker.py`. De `TokenTracker.record_usage` methode slaat voor ieder bericht het aantal tokens en de kosten op in de database.

### Frontend
De HTML-sjablonen staan in `templates/`, terwijl CSS en JavaScript onder `static/` zijn geplaatst. `home.html` en `static/js/home.js` regelen de chatinterface en workflow tabs.

---

Met deze handleiding heb je als ontwikkelaar een overzicht van het gebruik, de installatie en de technische structuur van Aiontwikkelhulp. Raadpleeg de uitgebreide README voor meer gedetailleerde informatie en troubleshooting.
