# AI Ontwikkelhulp (aiontwikkelhulp)

Een gespecialiseerde tool die communicatie tussen gebruikers en AI-modellen (Claude) faciliteert voor code-ontwikkeling en repository-beheer. De applicatie biedt een gestructureerde werkwijze voor AI-gestuurde softwareontwikkeling met integratie van externe tools via het Model Context Protocol (MCP).

## ✨ Kernfunctionaliteiten

### 🤖 AI-Gestuurde Repository Ontwikkeling
- **`ga` commando**: Start automatische repository ontwikkeling volgens voorgedefinieerde werkwijze
- **Project management**: Automatische creatie en beheer van `project_info.txt` en `project_stappen.txt`
- **Issue-driven development**: Automatische GitHub issue creatie en afhandeling
- **Branch management**: Automatische branch creatie en pull request workflow

#### 🏷️ Issue Labels en Workflow Prioritering

De AI-ontwikkelworkflow gebruikt een gestructureerd label systeem voor prioritering:

**Label Types:**
- **`must-have`**: Essentiële functionaliteiten die vereist zijn voor een werkende applicatie
- **`nice-to-have`**: Optionele verbeteringen en extra features
- **`bug`**: Fouten die opgelost moeten worden

**Workflow Prioritering:**
1. **Bugs eerst**: Issues met label `bug` krijgen altijd de hoogste prioriteit
2. **Must-have features**: Daarna worden `must-have` issues opgepakt
3. **Nice-to-have features**: Alleen als alle must-have taken voltooid zijn

**Workflow Stopconditie:**
De automatische ontwikkelworkflow stopt wanneer:
- Alle `must-have` taken zijn uitgevoerd
- Er geen openstaande `bug` issues zijn
- De AI meldt: *"Alle must-have taken zijn uitgevoerd"*

Na deze melding zijn alleen nog `nice-to-have` features beschikbaar, die handmatig kunnen worden opgepakt indien gewenst.

### 🔧 Model Context Protocol (MCP) Integratie
- **GitHub Tools**: Directe integratie met GitHub API voor repository beheer
- **External Tools**: Ondersteuning voor custom MCP servers en tools
- **Real-time Tool Use**: Live feedback over tool gebruik en resultaten

### 💬 Conversation Management
- **Persistent Storage**: Gesprekken worden opgeslagen in database
- **Search & Filter**: Zoek door gesprekgeschiedenis
- **Bulk Operations**: Beheer meerdere gesprekken tegelijk
- **Metadata**: Automatische tracking van model, timestamps, en status

### 🎨 Enhanced User Interface
- **Split View**: Gescheiden weergave van chat en log berichten
- **Log Formatting**: Automatische formattering van JSON, tool gebruik, en errors
- **Dark/Light Theme**: Volledig themable interface
- **Real-time Updates**: Live updates van gespreksstatus

### 🔐 Lynxx Google Authentication
- **Domain Restriction**: Alleen @lynxx.com e-mailadressen toegestaan
- **OAuth 2.0**: Veilige Google OAuth integratie
- **Session Management**: Persistent login sessies
- **User Profiles**: Automatische gebruikersinformatie van Google

## 🚀 Installatie

### Vereisten
- Python 3.8+
- Google Cloud Platform project met OAuth configuratie
- Anthropic API key
- GitHub Personal Access Token (voor MCP integratie)

### Stap 1: Repository Clonen
```bash
git clone https://github.com/Fbeunder/aiontwikkelhulp.git
cd aiontwikkelhulp
```

### Stap 2: Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OF
venv\Scripts\activate     # Windows
```

### Stap 3: Dependencies Installeren
```bash
pip install -r requirements.txt
```

### Stap 4: Google OAuth Configuratie

#### Google Cloud Console Setup:
1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Maak een nieuw project aan of selecteer bestaand project
3. Activeer de "Google+ API" en "Google OAuth2 API"
4. Ga naar "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configureer OAuth consent screen:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5000/auth/login/callback`
   - Voor productie: `https://yourdomain.com/auth/login/callback`

#### OAuth Client Configuratie:
- **Application type**: Web application
- **Name**: AI Ontwikkelhulp (of eigen naam)
- **Authorized JavaScript origins**: 
  - `http://localhost:5000` (development)
  - `https://yourdomain.com` (production)
- **Authorized redirect URIs**:
  - `http://localhost:5000/auth/login/callback` (development)
  - `https://yourdomain.com/auth/login/callback` (production)

### Stap 5: Environment Configuratie
Maak een `.env` bestand aan in de root directory:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here
DEBUG=True

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid_configuration

# Lynxx Domain Restriction
ALLOWED_DOMAINS=lynxx.com

# Anthropic API Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# GitHub Integration (voor MCP tools)
GITHUB_TOKEN=your-github-personal-access-token

# MCP Server Configuration
MCP_SERVER_PATH=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-github

# Database Configuration
DATABASE_URL=sqlite:///instance/aiontwikkelhulp.db

# Application Settings
APP_NAME=AI Ontwikkelhulp
LOG_LEVEL=INFO
```

### Stap 6: Database Initialisatie
```bash
flask db upgrade
```

### Stap 7: Applicatie Starten
```bash
python app.py
```

De applicatie is nu beschikbaar op: `http://localhost:5000`

## 📁 Projectstructuur

```
aiontwikkelhulp/
├── 📄 app.py                          # Flask applicatie entry point
├── 📄 auth.py                         # Google OAuth authenticatie
├── 📄 user.py                         # User model en sessie beheer
├── 📄 config.py                       # Algemene applicatie configuratie
├── 📄 database.py                     # Database configuratie en setup
├── 📄 requirements.txt                # Python dependencies
├── 📄 .env.example                    # Environment variabelen template
├── 📄 README.md                       # Project documentatie
├── 📄 project_info.txt                # AI project informatie cache
├── 📄 project_stappen.txt             # Ontwikkelstappen voor AI
├── 📄 system_prompt.txt               # AI system prompt
│
├── 🔧 Anthropic API Modules
│   ├── 📄 anthropic_api.py            # High-level Anthropic API interface
│   ├── 📄 anthropic_config.py         # Anthropic configuratie beheer
│   ├── 📄 anthropic_client.py         # Pure API communicatie client
│   ├── 📄 conversation_manager.py     # Gesprek state management
│   └── 📄 mcp_integration.py          # MCP server integratie
│
├── 🔌 MCP & External Tools
│   └── 📄 mcp_connector.py            # MCP protocol connector
│
├── 🛣️ routes/
│   └── 📄 api.py                      # REST API endpoints
│
├── 🗄️ repositories/
│   └── 📄 conversation_repository.py   # Database CRUD operaties
│
├── 📊 models/
│   └── 📄 conversation.py             # SQLAlchemy database modellen
│
├── 🎨 templates/
│   ├── 📄 base.html                   # Base template met navigatie
│   ├── 📄 home.html                   # Hoofd chat interface
│   └── 📄 conversations.html          # Gesprekken overzicht
│
├── 🎨 static/
│   ├── css/
│   │   ├── 📄 style.css               # Hoofd styling en thema's
│   │   └── 📄 log-formatter.css       # Log formattering styles
│   └── js/
│       ├── 📄 main.js                 # Hoofd JavaScript functionaliteit
│       └── 📄 log-formatter.js        # Log formattering module
│
├── 🗂️ werkwijze/
│   └── 📄 werkwijze.txt               # AI ontwikkeling instructies
│
├── 🧪 tests/
│   ├── 📄 test_anthropic_config.py    # Anthropic config unit tests
│   ├── 📄 test_anthropic_client.py    # Anthropic client unit tests
│   ├── 📄 test_conversation_manager.py # Conversation manager tests
│   └── 📄 test_api_conversation_persistence.py # API tests
│
├── 🗃️ instance/                       # Flask instance folder (auto-created)
│   ├── 🗄️ aiontwikkelhulp.db          # SQLite database
│   └── 👥 users/                      # User session storage
│
└── 📁 migrations/                     # Database migration bestanden
    └── versions/                      # Alembic version bestanden
```

## 🔧 Configuratie Details

### Google OAuth Setup voor Lynxx
De applicatie is geconfigureerd voor Lynxx medewerkers:

1. **Domain Restrictie**: Alleen `@lynxx.com` e-mailadressen worden geaccepteerd
2. **OAuth Scopes**: `openid`, `email`, `profile`
3. **Redirect Flow**: Automatische redirect naar dashboard na succesvolle login
4. **Session Persistence**: Login sessies blijven actief tussen browser sessies

### Anthropic API Configuratie
- **Model**: Claude 3.5 Sonnet (configureerbaar)
- **Caching**: Ephemeral caching voor system prompt en project info
- **Streaming**: Real-time response streaming voor betere UX

### MCP Tools Configuratie
- **GitHub Integration**: Volledige GitHub API toegang via MCP
- **Custom Tools**: Ondersteuning voor additional MCP servers
- **Tool Results**: Real-time feedback over tool execution

## 🎯 Gebruik

### Voor Gebruikers
1. **Login**: Gebruik je @lynxx.com Google account
2. **Chat Interface**: Stel vragen of geef opdrachten aan Claude
3. **Repository Ontwikkeling**: Gebruik `ga [repository-naam]` voor automatische ontwikkeling
4. **Gesprekken Beheren**: Bekijk, zoek, en beheer je gesprekgeschiedenis

### Voor Ontwikkelaars
1. **Code Development**: Gebruik `ga` commando met repository naam
2. **Issue Tracking**: Automatische GitHub issue creatie en management
3. **Branch Workflow**: Automatische branch creatie en PR workflow
4. **Testing**: Gebruik MCP tools voor code testing en validation

## 🚀 Productie Deployment

### Environment Variables voor Productie
```env
FLASK_ENV=production
DEBUG=False
SECRET_KEY=strong-production-secret-key
GOOGLE_CLIENT_ID=production-client-id
GOOGLE_CLIENT_SECRET=production-client-secret
DATABASE_URL=postgresql://user:pass@localhost/aiontwikkelhulp
SSL_REDIRECT=True
PROXY_COUNT=1
```

### Gunicorn Deployment
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🧪 Testing

### Unit Tests Uitvoeren
```bash
# Alle tests
pytest

# Specifieke test suite
pytest tests/test_anthropic_config.py

# Met coverage
pytest --cov=. --cov-report=html
```

### API Tests
```bash
# API endpoints testen
pytest tests/test_api_conversation_persistence.py -v
```

## 🔍 Troubleshooting

### Veel Voorkomende Problemen

#### Google OAuth Errors
- **Error**: `redirect_uri_mismatch`
  - **Oplossing**: Controleer of redirect URI in Google Console overeenkomt met applicatie URL

#### Anthropic API Issues
- **Error**: `AuthenticationError`
  - **Oplossing**: Verifieer ANTHROPIC_API_KEY in .env bestand

#### MCP Connection Problems
- **Error**: MCP server connection failed
  - **Oplossing**: Controleer of GitHub token juiste permissions heeft

#### Database Errors
- **Error**: `sqlite3.OperationalError`
  - **Oplossing**: Run `flask db upgrade` om database schema bij te werken

### Logging & Debugging
```bash
# Verhoog log level voor debugging
export LOG_LEVEL=DEBUG

# Check logs voor specifieke modules
tail -f logs/app.log | grep "anthropic_api"
```

## 🤝 Contributing

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/nieuwe-functie`)
3. Commit je wijzigingen (`git commit -am 'Voeg nieuwe functie toe'`)
4. Push naar branch (`git push origin feature/nieuwe-functie`)
5. Maak een Pull Request

## 📝 Changelog

### Recent Updates
- **v2.1.0**: Log formatting en UI verbeteringen
- **v2.0.0**: Database persistence voor conversations
- **v1.5.0**: MCP integration en GitHub tools
- **v1.0.0**: Basis applicatie met Google OAuth

## 📄 Licentie

Dit project is eigendom van Lynxx en bedoeld voor intern gebruik.

## 📞 Support

Voor vragen of problemen:
- **Internal Slack**: #ai-ontwikkelhulp
- **Email**: development@lynxx.com
- **GitHub Issues**: [Issue Tracker](https://github.com/Fbeunder/aiontwikkelhulp/issues)

---
*Gebouwd met ❤️ door het Lynxx development team*