# Aiontwikkelhulp Handleiding

## Inleiding
Aiontwikkelhulp is een geavanceerde webgebaseerde tool die de samenwerking tussen ontwikkelaars en AI-modellen van Anthropic (Claude) stroomlijnt. De applicatie biedt een intuïtieve chatinterface, geautomatiseerde workflow-ondersteuning, uitgebreide analytics en naadloze integratie met GitHub via het Model Context Protocol (MCP).

### Belangrijkste kenmerken
- **AI-gestuurde ontwikkeling**: Werk samen met Claude voor code-ontwikkeling en repository-beheer
- **Workflow automatisering**: Geautomatiseerde issue- en pull request-workflows
- **Token analytics**: Real-time inzicht in tokengebruik en kosten
- **MCP integratie**: Directe toegang tot GitHub-functionaliteiten
- **Configureerbare LLM-instellingen**: Aanpasbare temperature en presets voor verschillende use cases

Deze handleiding bestaat uit vier delen:
1. **Gebruikershandleiding** – praktisch gebruik van de tool
2. **Workflow automatisering** – gedetailleerde uitleg van het `ga` commando
3. **Installatie & configuratie** – opzetten van de applicatie
4. **Technische architectuur** – overzicht van modules en hun samenhang

---

## 1. Gebruikershandleiding

### Toegang en authenticatie
1. **Navigeer** naar de webinterface (standaard `http://localhost:5000`)
2. **Login** met je `@lynxx.com` Google-account via de OAuth-integratie
3. Na succesvolle authenticatie kom je op het **dashboard** met de chatinterface

### Chatten met Claude

#### Basis interactie
1. Open de chatpagina en typ je vraag of opdracht in het invoerveld
2. Selecteer het gewenste **model** (Claude 3.5 Sonnet, Claude 4 Sonnet, etc.)
3. Kies een **preset** voor optimale resultaten:
   - `developer_agent` (temperature 0.2) - Voor code-ontwikkeling
   - `creative_writing` (temperature 0.8) - Voor creatieve taken
   - `analysis` (temperature 0.3) - Voor data-analyse
   - `balanced` (temperature 0.5) - Voor algemeen gebruik

#### Geavanceerde features
- **Split-view**: Links de chat, rechts gedetailleerde logs van alle interacties
- **Tool gebruik**: Claude kan automatisch GitHub-tools gebruiken voor repository-beheer
- **Token tracking**: Real-time weergave van tokengebruik per bericht
- **Enhanced logging**: Visuele indicatoren voor tool-uitvoering (▶ start, ✓ succes, ✗ fout)

### Workflow automatisering met het `ga` commando

Het `ga` commando is een krachtige feature voor geautomatiseerde repository-ontwikkeling:

```
ga [repository-naam]
```

#### Werkwijze van het `ga` commando
1. **Repository identificatie**: Als geen repository wordt opgegeven, vraagt de AI dit eerst
2. **Project analyse**: Leest `project_info.txt` en `project_stappen.txt`
3. **Issue management**: 
   - Controleert openstaande issues (bugs hebben prioriteit)
   - Maakt nieuwe issues aan voor must-have taken
   - Voegt automatisch labels toe (`must-have`, `nice-to-have`, `bug`)
4. **Development workflow**:
   - Maakt feature branches aan
   - Implementeert wijzigingen volgens issue-beschrijving
   - Commit en push automatisch
   - Maakt pull requests aan
   - Update projectdocumentatie

#### Workflow tabs
Schakel de **Workflow toggle** in voor geavanceerde automatisering:
- **3 workflow profielen** met eigen tabs:
  - Issue Creation (Claude Sonnet 4, developer_agent preset)
  - PR Creation (Claude Sonnet 4, developer_agent preset)
  - PR Processed (Claude 3.5 Sonnet, balanced preset)
- **Automatische tab-switching** op basis van AI-responses
- **Activity indicators** tonen welke tab actief is
- **WCAG AA compliant** kleurenschema voor optimale toegankelijkheid

### Gesprekken beheren

#### Overzicht en zoeken
- Navigeer naar **Conversations** in het menu
- **Zoek** gesprekken op titel of inhoud
- **Paginering** voor grote aantallen gesprekken
- **Token usage** weergave per gesprek (input/output tokens, kosten)

#### Bulk operaties
- **Selecteer** meerdere gesprekken met checkboxes
- **Bulk delete** met bevestigingsmodal
- **Select all/none** functionaliteit
- Alle operaties zijn **CSRF-beveiligd**

### Analytics dashboard

Het analytics dashboard biedt uitgebreide inzichten:

#### Overzichtskaarten
- **Totaal tokengebruik** (input/output/cache)
- **Totale kosten** met trend-indicatoren
- **Gemiddelde kosten** per gesprek
- **Model gebruik** verdeling

#### Visualisaties
- **Token usage trends** grafiek
- **Kosten per model** breakdown
- **Top gesprekken** op basis van kosten
- **Insights** met automatische aanbevelingen

#### Periode selectie
- Vandaag, Deze week, Deze maand
- Custom datumbereik
- Real-time data updates

### Tips voor effectief gebruik

1. **Voor code-ontwikkeling**: Gebruik altijd de `developer_agent` preset
2. **Bij debugging**: Zet `LOG_LEVEL=DEBUG` in environment variabelen
3. **Voor grote projecten**: Gebruik workflow tabs voor overzicht
4. **Kosten optimalisatie**: Monitor regelmatig het analytics dashboard
5. **Bij OAuth problemen**: Controleer Google OAuth configuratie in `.env`

---

## 2. Workflow automatisering in detail

### Het ontwikkelproces volgens werkwijze.txt

De AI volgt een gestructureerd ontwikkelproces bij het `ga` commando:

#### Stap 1: Project analyse
- Controleert altijd eerst `project_info.txt`
- Bij afwezigheid: maakt deze aan op basis van `start.txt`
- Documenteert: projectdoel, doelgroep, nut, architectuur

#### Stap 2: Issue prioritering
1. **Bugs** hebben altijd voorrang
2. **Must-have** features komen daarna
3. **Nice-to-have** alleen als alle must-haves klaar zijn

#### Stap 3: Issue creatie
Voor nieuwe taken wordt een gedetailleerd issue aangemaakt:
- **Titel**: Duidelijke functionaliteit-omschrijving
- **Beschrijving** bevat:
  - Technische implementatiedetails
  - Doel, nut en noodzaak (niet alleen technisch!)
  - Te wijzigen modules/bestanden
  - Acceptatiecriteria
  - Branch naam (bijv. `feature/nieuwe-functionaliteit`)

#### Stap 4: Implementatie
- Analyseert relevante bestanden grondig
- Werkt in de juiste branch
- Commit met duidelijke berichten
- Houdt documentatie synchroon

#### Stap 5: Pull Request workflow
- Automatische PR creatie met issue-referentie
- Wacht op merge-instructie
- Sluit issue na succesvolle merge
- Verwijdert feature branch

### Best practices voor `ga` commando

1. **Start altijd met een duidelijke `start.txt`** die projectdoel en requirements beschrijft
2. **Gebruik labels consequent** voor prioritering
3. **Houd issues klein en gefocust** (max 400 regels code per PR)
4. **Review de gegenereerde issues** voordat je verder gaat
5. **Monitor de workflow tabs** voor real-time voortgang

---

## 3. Installatie & configuratie

### Systeemvereisten
- Python 3.8 of hoger
- 2GB RAM minimum (4GB aanbevolen)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stabiele internetverbinding

### Installatiestappen

#### 1. Repository setup
```bash
git clone https://github.com/Fbeunder/aiontwikkelhulp.git
cd aiontwikkelhulp
```

#### 2. Python omgeving
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# of
venv\Scripts\activate     # Windows
```

#### 3. Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment configuratie
Maak een `.env` bestand op basis van `.env.example`:

```env
# Flask configuratie
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: MCP GitHub integratie
GITHUB_TOKEN=ghp_your-token-here

# Optional: Custom settings
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///aiontwikkelhulp.db
```

#### 5. Database initialisatie
```bash
flask db upgrade
```

#### 6. Applicatie starten
```bash
python app.py
```

De applicatie draait nu op `http://localhost:5000`

### Productie deployment

#### Met Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Met Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### Configuratie opties

#### LLM Settings
Pas temperature en presets aan via de API:
```bash
PUT /api/llm-settings
{
  "temperature": 0.3,
  "preset": "developer_agent"
}
```

#### MCP Server configuratie
Voor GitHub-integratie, configureer in `.env`:
```env
MCP_SERVER_GITHUB=npx -y @modelcontextprotocol/server-github
```

---

## 4. Technische architectuur

### Overzicht architectuur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Flask Backend   │────▶│  Anthropic API  │
│  (HTML/JS/CSS)  │     │   (app.py)       │     │   (Claude)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   MCP Integration    │
                    │  (GitHub Tools)      │
                    └──────────────────────┘
```

### Core modules

#### Flask applicatie (`app.py`)
- **Functie**: Hoofdapplicatie met route-registratie
- **Features**: CSRF protection, session management, error handling
- **Dependencies**: Flask, Flask-WTF, authlib

#### Anthropic integratie
- **`anthropic_api.py`**: High-level API coordinator
- **`anthropic_client.py`**: Low-level API communicatie
- **`anthropic_config.py`**: Configuratie en presets
- **Features**: Ephemeral caching, token tracking, runtime settings

#### Conversation management
- **`conversation_manager.py`**: In-memory + database storage
- **`repositories/conversation_repository.py`**: Database CRUD
- **`models/conversation.py`**: SQLAlchemy modellen
- **Features**: Soft delete, bulk operations, search

#### MCP Integration
- **`mcp_integration.py`**: Tool orchestration
- **`mcp_connector.py`**: Server communication
- **Features**: Enhanced logging, async execution, error recovery

#### Analytics systeem
- **`analytics/token_tracker.py`**: Usage recording
- **`analytics/cost_calculator.py`**: Pricing calculations
- **`analytics/analytics_service.py`**: Data aggregation
- **Features**: Real-time tracking, cost projections, insights

### Frontend architectuur

#### Templates structuur
```
templates/
├── base.html              # Base template met navigatie
├── home.html              # Chat interface met workflow tabs
├── conversations.html     # Gesprekken beheer
├── analytics.html         # Analytics dashboard
└── components/
    └── chat_window.html   # Herbruikbare chat component
```

#### JavaScript modules
- **`home.js`** (59KB): Chat functionaliteit, workflow automation
- **`analytics.js`**: Dashboard visualisaties met Chart.js
- **`log-formatter.js`**: Enhanced log formatting

#### CSS organisatie
- **`style.css`**: Algemene applicatie styling
- **`home.css`**: Chat interface en workflow tabs
- **`analytics.css`**: Dashboard styling
- **`log-formatter.css`**: Log visualisatie

### Database schema

#### Conversations tabel
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSON
);
```

#### Messages tabel
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    role VARCHAR(50),
    content TEXT,
    created_at TIMESTAMP,
    metadata JSON
);
```

#### Token Usage tabel
```sql
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER,
    message_id INTEGER,
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_write_tokens INTEGER,
    total_cost DECIMAL(10,6),
    created_at TIMESTAMP
);
```

### API endpoints

#### Conversation endpoints
- `GET /api/conversations` - Lijst met paginering en search
- `POST /api/conversations` - Nieuwe conversatie
- `PUT /api/conversations/<id>` - Update conversatie
- `DELETE /api/conversations/<id>` - Soft delete
- `POST /api/conversations/bulk-delete` - Bulk verwijderen

#### LLM endpoints
- `GET /api/llm-settings` - Huidige settings
- `PUT /api/llm-settings` - Update settings
- `POST /api/send-prompt` - Stream prompt naar Claude

#### Analytics endpoints
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/conversations/<id>/usage` - Usage per gesprek
- `GET /api/analytics/users/<id>/usage` - User summary

### Security features

1. **OAuth 2.0** authenticatie via Google
2. **CSRF protection** op alle state-changing endpoints
3. **Session management** met secure cookies
4. **Input validation** en sanitization
5. **Rate limiting** mogelijkheden

---

## Conclusie

Aiontwikkelhulp is een krachtige tool voor AI-gestuurde ontwikkeling die het beste van moderne AI-technologie combineert met praktische ontwikkeltools. Door het gebruik van het `ga` commando en workflow automatisering kunnen ontwikkelaars efficiënter werken en zich focussen op creatieve oplossingen terwijl de AI de repetitieve taken overneemt.

Voor vragen of problemen, raadpleeg de uitgebreide README of open een issue op GitHub.