# AI Ontwikkelhulp (aiontwikkelhulp)

Een gespecialiseerde tool die communicatie tussen gebruikers en AI-modellen (Claude) faciliteert voor code-ontwikkeling en repository-beheer. De applicatie biedt een gestructureerde werkwijze voor AI-gestuurde softwareontwikkeling met integratie van externe tools via het Model Context Protocol (MCP) en directe API integratie.

## ✨ Kernfunctionaliteiten

### 🤖 AI-Gestuurde Repository Ontwikkeling
- **`ga` commando**: Start automatische repository ontwikkeling volgens voorgedefinieerde werkwijze
- **Multi-platform ondersteuning**: Werkt met zowel GitHub als Bitbucket repositories
- **Project management**: Automatische creatie en beheer van `project_info.txt` en `project_stappen.txt`
- **Issue-driven development**: Automatische issue creatie en afhandeling
- **Branch management**: Automatische branch creatie en pull request workflow

### 🔄 Workflow Automation
De applicatie beschikt over een geavanceerde workflow functionaliteit die automatisch de ontwikkelcyclus beheert door AI-responses te monitoren en nieuwe chat windows te openen op basis van specifieke patterns.

#### Workflow Toggle Functionaliteit
De **Workflow** toggle in de interface activeert een intelligente automatisering die:
- **Automatisch nieuwe chat windows opent** wanneer specifieke AI-responses worden gedetecteerd
- **Automatisch het huidige window sluit** na het starten van een nieuwe taak
- **Configureert nieuwe windows** met Claude 4 Sonnet en developer_agent preset
- **Monitort AI-responses** voor ontwikkelworkflow patterns

#### Samenhang met werkwijze.txt
De workflow automation is direct gekoppeld aan de instructies in `werkwijze/werkwijze.txt`:

**Automatische Pattern Herkenning:**
1. **Issue Creation Pattern**: `"Ik heb issue [nummer] aangemaakt voor Repo [owner]/[repo]"` (GitHub) of `"Ik heb issue [nummer] aangemaakt voor Repo [workspace]/[repo_slug]"` (Bitbucket)
   - **Actie**: Opent nieuw window met prompt: `"Ga naar Repo [owner]/[repo] en pak issue [nummer] op"`
   - **Doel**: Automatisch doorschakelen naar issue uitvoering

2. **PR Creation Pattern**: `"Ik heb Pull Request [nummer] aangemaakt voor Repo [owner]/[repo]"` (GitHub) of `"Ik heb Pull Request [nummer] aangemaakt voor Repo [workspace]/[repo_slug]"` (Bitbucket)
   - **Actie**: Opent nieuw window met prompt: `"Ga naar Repo [owner]/[repo] en merge Pull Request [nummer] en delete de bijbehorende branche"`
   - **Doel**: Automatisch doorschakelen naar PR merge proces

3. **PR Processed Pattern**: `"Ik heb Pull Request [nummer] verwerkt en bijbehorende branche [branche] verwijderd voor Repo [owner]/[repo]"` (GitHub) of `"Ik heb Pull Request [nummer] verwerkt en bijbehorende branche [branche] verwijderd voor Repo [workspace]/[repo_slug]"` (Bitbucket)
   - **Actie**: Opent nieuw window met prompt: `"Ga Repo [owner]/[repo]"`
   - **Doel**: Terugkeren naar algemene repository ontwikkeling

#### Automatische Configuratie
Wanneer workflow mode actief is, worden nieuwe windows automatisch geconfigureerd met:
- **Model**: Claude 4 Sonnet (`claude-sonnet-4-20250514`)
- **Preset**: Developer Agent (`developer_agent`)
- **Timing**: 1 seconde delay voor natuurlijke flow
- **Window Management**: Automatisch sluiten van vorige windows

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

### 🔧 Multi-Platform Repository Integratie

#### GitHub Integratie (via MCP)
- **MCP Protocol**: Directe integratie met GitHub API via Model Context Protocol
- **GitHub Tools**: Volledige GitHub API toegang voor repository beheer
- **Real-time Tool Use**: Live feedback over tool gebruik en resultaten

#### Bitbucket Integratie (via Direct API)
- **Bitbucket API**: Directe integratie met Bitbucket REST API v2.0
- **Workspace Support**: Ondersteuning voor Bitbucket workspaces en repository slugs
- **App Passwords**: Veilige authenticatie via Bitbucket app passwords

#### Platform Detectie
- **Automatische Detectie**: Herkent platform op basis van repository referentie format
- **GitHub Format**: `owner/repo` (bijv. "NoutNouhuys/Noutai")
- **Bitbucket Format**: `workspace/repo_slug` (bijv. "myworkspace/myrepo")
- **Platform Switching**: Handmatige platform selectie via interface

#### Ondersteunde Operaties (Beide Platforms)
- Repository management (create, list, fork)
- Issue management (create, update, list, close)
- Pull request management (create, update, merge, list)
- Branch management (create, list, delete)
- File operations (read, create, update)
- Commit operations

### 💬 Conversation Management
- **Persistent Storage**: Gesprekken worden opgeslagen in database
- **Search & Filter**: Zoek door gesprekgeschiedenis
- **Bulk Operations**: Beheer meerdere gesprekken tegelijk
- **Metadata**: Automatische tracking van model, timestamps, en status

### 🎨 Enhanced User Interface
- **Platform Selector**: Kies tussen GitHub en Bitbucket in de interface
- **Connection Status**: Real-time status van platform verbindingen
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
- **Voor GitHub**: GitHub Personal Access Token (voor MCP integratie)
- **Voor Bitbucket**: Bitbucket App Password en workspace toegang

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

### Stap 5: Platform Configuratie

#### GitHub Setup (Optioneel)
1. Ga naar GitHub Settings → Developer settings → Personal access tokens
2. Genereer een nieuwe token met de volgende scopes:
   - `repo` (volledige repository toegang)
   - `workflow` (GitHub Actions toegang)
   - `admin:org` (organisatie toegang indien nodig)

#### Bitbucket Setup (Optioneel)
1. Ga naar Bitbucket Settings → App passwords
2. Maak een nieuwe app password aan met de volgende permissions:
   - **Repositories**: Read, Write, Admin
   - **Pull requests**: Read, Write
   - **Issues**: Read, Write
   - **Webhooks**: Read, Write (optioneel)

### Stap 6: Environment Configuratie
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

# Platform Configuration
DEFAULT_PLATFORM=github

# GitHub MCP Configuration (Optioneel)
MCP_SERVER_SCRIPT=npx
MCP_SERVER_VENV_PATH=path/to/mcp/venv
GITHUB_TOKEN=your-github-personal-access-token

# Bitbucket API Configuration (Optioneel)
BITBUCKET_WORKSPACE=your-workspace-name
BITBUCKET_USERNAME=your-bitbucket-username
BITBUCKET_APP_PASSWORD=your-bitbucket-app-password

# Database Configuration
DATABASE_URL=sqlite:///instance/aiontwikkelhulp.db

# Application Settings
APP_NAME=AI Ontwikkelhulp
LOG_LEVEL=INFO
```

### Stap 7: Database Initialisatie
```bash
flask db upgrade
```

### Stap 8: Applicatie Starten
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
├── 📄 platform_api.py                 # Platform management API endpoints
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
│   └── 📄 mcp_integration.py          # Multi-platform MCP integratie
│
├── 🔌 Platform Connectors
│   ├── 📄 mcp_connector.py            # GitHub MCP protocol connector
│   └── 📄 mcp_bitbucket_connector.py  # Bitbucket API connector
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
│   ├── 📄 home.html                   # Hoofd chat interface met platform selector
│   └── 📄 conversations.html          # Gesprekken overzicht
│
├── 🎨 static/
│   ├── css/
│   │   ├── 📄 style.css               # Hoofd styling en thema's
│   │   ├── 📄 log-formatter.css       # Log formattering styles
│   │   └── 📄 platform-selector.css   # Platform selector styling
│   └── js/
│       ├── 📄 home.js                 # Hoofd JavaScript met platform switching
│       └── 📄 log-formatter.js        # Log formattering module
│
├── 🗂️ werkwijze/
│   └── 📄 werkwijze.txt               # Multi-platform AI ontwikkeling instructies
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

## 🔧 Platform Configuratie Details

### GitHub Configuratie
Voor GitHub integratie via MCP:

```env
# GitHub MCP Server
MCP_SERVER_SCRIPT=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-github
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optioneel: MCP server virtual environment
MCP_SERVER_VENV_PATH=/path/to/mcp/venv
```

**GitHub Token Permissions:**
- `repo`: Volledige repository toegang
- `workflow`: GitHub Actions toegang
- `admin:org`: Organisatie toegang (indien nodig)

### Bitbucket Configuratie
Voor Bitbucket integratie via directe API:

```env
# Bitbucket API Credentials
BITBUCKET_WORKSPACE=my-workspace
BITBUCKET_USERNAME=my-username
BITBUCKET_APP_PASSWORD=ATBBxxxxxxxxxxxxxxxxxx
```

**Bitbucket App Password Permissions:**
- **Repositories**: Read, Write, Admin
- **Pull requests**: Read, Write
- **Issues**: Read, Write
- **Webhooks**: Read, Write (optioneel)

**App Password Aanmaken:**
1. Ga naar Bitbucket Settings → App passwords
2. Klik "Create app password"
3. Geef een naam (bijv. "AI Ontwikkelhulp")
4. Selecteer de benodigde permissions
5. Kopieer het gegenereerde password (eenmalig zichtbaar)

### Platform Switching
De applicatie ondersteunt dynamische platform switching:

1. **Interface**: Platform selector in de hoofdinterface
2. **Automatische Detectie**: Op basis van repository referentie format
3. **API Endpoints**: `/api/platform/connect`, `/api/platform/disconnect`, `/api/platform/switch`
4. **Session Storage**: Actieve platform wordt opgeslagen in gebruikerssessie

## 🎯 Gebruik

### Voor Gebruikers
1. **Login**: Gebruik je @lynxx.com Google account
2. **Platform Selectie**: Kies GitHub of Bitbucket in de interface
3. **Verbinding**: Klik "Verbinden" om verbinding te maken met het gekozen platform
4. **Chat Interface**: Stel vragen of geef opdrachten aan Claude
5. **Repository Ontwikkeling**: Gebruik `ga [repository-naam]` voor automatische ontwikkeling
6. **Workflow Mode**: Activeer de workflow toggle voor geautomatiseerde development cycles

### Voor Ontwikkelaars

#### GitHub Repositories
```bash
# GitHub repository format: owner/repo
ga NoutNouhuys/Noutai
ga myorganization/myproject
```

#### Bitbucket Repositories
```bash
# Bitbucket repository format: workspace/repo_slug
ga myworkspace/myproject
ga company-workspace/application-name
```

#### Multi-Platform Development
1. **Platform Detection**: De AI detecteert automatisch het platform op basis van repository format
2. **Cross-Platform**: Wissel tussen GitHub en Bitbucket projecten binnen dezelfde sessie
3. **Unified Workflow**: Dezelfde workflow instructies werken voor beide platforms
4. **Tool Translation**: GitHub tools worden automatisch vertaald naar Bitbucket equivalenten

### Workflow Mode Gebruiken
1. **Activeer Workflow**: Zet de "Workflow" toggle aan in de interface
2. **Selecteer Platform**: Kies GitHub of Bitbucket en maak verbinding
3. **Start Development**: Gebruik `ga [repository-naam]` commando
4. **Automatische Flow**: De AI zal automatisch:
   - Issues aanmaken en oppakken
   - Pull requests creëren en mergen
   - Nieuwe chat windows openen met juiste configuratie
   - Platform-specifieke API calls gebruiken
   - Vorige windows sluiten voor clean workflow

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

# Platform Configuration
DEFAULT_PLATFORM=github
BITBUCKET_WORKSPACE=production-workspace
BITBUCKET_USERNAME=production-user
BITBUCKET_APP_PASSWORD=production-app-password
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

### Platform Integration Tests
```bash
# Test GitHub integratie
pytest tests/test_github_integration.py -v

# Test Bitbucket integratie
pytest tests/test_bitbucket_integration.py -v

# Test platform switching
pytest tests/test_platform_switching.py -v
```

## 🔍 Troubleshooting

### Veel Voorkomende Problemen

#### Platform Connection Issues
- **Error**: `Platform not configured`
  - **Oplossing**: Controleer environment variabelen voor het gekozen platform
- **Error**: `Bitbucket authentication failed`
  - **Oplossing**: Verifieer app password en workspace naam
- **Error**: `GitHub MCP server connection failed`
  - **Oplossing**: Controleer GitHub token permissions en MCP server configuratie

#### Repository Format Issues
- **Error**: `Repository format not recognized`
  - **Oplossing**: Gebruik correct format (`owner/repo` voor GitHub, `workspace/repo_slug` voor Bitbucket)
- **Error**: `Platform detection failed`
  - **Oplossing**: Specificeer platform expliciet in de interface

#### Workflow Pattern Issues
- **Error**: `Workflow patterns not recognized`
  - **Oplossing**: Controleer of AI responses exact overeenkomen met patterns in `werkwijze.txt`
- **Error**: `Cross-platform workflow confusion`
  - **Oplossing**: Zorg dat repository referenties consistent zijn binnen een workflow

### Platform-Specifieke Debugging

#### GitHub Debugging
```bash
# Check GitHub MCP connection
export LOG_LEVEL=DEBUG
tail -f logs/app.log | grep "github"

# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### Bitbucket Debugging
```bash
# Check Bitbucket API connection
export LOG_LEVEL=DEBUG
tail -f logs/app.log | grep "bitbucket"

# Test Bitbucket credentials
curl -u "$BITBUCKET_USERNAME:$BITBUCKET_APP_PASSWORD" \
     https://api.bitbucket.org/2.0/user
```

## 🤝 Contributing

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/nieuwe-functie`)
3. Test op beide platforms (GitHub en Bitbucket)
4. Commit je wijzigingen (`git commit -am 'Voeg nieuwe functie toe'`)
5. Push naar branch (`git push origin feature/nieuwe-functie`)
6. Maak een Pull Request

### Development Guidelines
- Test nieuwe features op beide platforms
- Update werkwijze.txt voor platform-specifieke instructies
- Voeg platform-agnostische error handling toe
- Documenteer platform-specifieke configuratie

## 📝 Changelog

### Recent Updates
- **v3.0.0**: Multi-platform ondersteuning (GitHub + Bitbucket)
- **v2.2.0**: Workflow automation en pattern matching
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