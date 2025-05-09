# Lynxx Anthropic Console

Een custom webapplicatie die Lynxx medewerkers toegang geeft tot Anthropic's Claude AI-modellen via een gebruiksvriendelijke interface, met organisatie-specifieke authenticatie en functionaliteit.

## Overzicht

De Lynxx Anthropic Console stelt medewerkers in staat om:

- Vragen te stellen aan Claude AI via een gebruiksvriendelijke webinterface
- Te kiezen uit verschillende Claude modellen (Haiku, Sonnet, Opus)
- Conversatiegeschiedenis op te slaan en te beheren
- Veilig in te loggen via Google OAuth met @lynxx.com domeinverificatie

## Systeemvereisten

- Python 3.9 of hoger
- Pip (Python pakketbeheerder)
- Een Google OAuth configuratie voor authenticatie
- Een Anthropic API sleutel

## Installatie

### 1. Clone de repository

```bash
git clone https://github.com/AliceLynxx/AnthropicMCP.git
cd AnthropicMCP
```

### 2. Maak een virtuele omgeving aan

```bash
python -m venv venv
```

Activeer de virtuele omgeving:

- Op Windows:
  ```bash
  venv\Scripts\activate
  ```

- Op macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 3. Installeer de vereiste pakketten

```bash
pip install -r requirements.txt
```

### 4. Configureer de omgevingsvariabelen

Maak een `.env` bestand aan in de hoofdmap van het project op basis van het `.env.example` bestand:

```bash
cp .env.example .env
```

Open het `.env` bestand en vul de vereiste variabelen in:

```
# Google OAuth Configuration
GOOGLE_CLIENT_ID=ABC
GOOGLE_CLIENT_SECRET=ABC

# Anthropic API Configuration
ANTHROPIC_API_KEY=ABC

MCP_SERVER_SCRIPT = ABC
MCP_SERVER_VENV_PATH = ABC
```

De Google Client ID en secret kan je maken op https://console.cloud.google.com/apis/credentials . Vraag hier een project aan en daarbinnen een OAuth 2.0 Client IDs. 

Maak of vraag een key voor de Anthropic API.

MCP_SERVER_SCRIPT en MCP_SERVER_VENV_PATH zijn nodig om een de code een MCP server op te laten starten. Dit hangt dus af welke MCP server je wil gebruiken. Bijvoorbeeld:
MCP_SERVER_SCRIPT = "C:/Users/user/Github-MCP-server/app.py"
MCP_SERVER_VENV_PATH = "C:/Users/annel/Github-MCP-server/venv"

Je kunt toegang vragen tot de Github-MCP-server repo.

## Starten van de applicatie

### Lokale ontwikkelomgeving

```bash
python app.py
```

Doe dit met je venv. De applicatie zal standaard starten op `http://127.0.0.1:5000`.

### Belangrijk voor gebruik

Voor goede resultaten, kies een groter model. Kleinere modellen hebben soms moeite met tools op een MCP server goed te gebruiken.

#### OAuth in ontwikkelomgeving

Wanneer je de applicatie in een ontwikkelomgeving draait (met `FLASK_ENV=development`), zal de applicatie automatisch OAuth over HTTP toestaan, wat nodig is voor lokale ontwikkeling. In een productieomgeving wordt altijd HTTPS vereist voor OAuth.

Als je toch problemen ondervindt met OAuth-authenticatie, kun je handmatig de volgende omgevingsvariabele instellen:

```bash
# Voor Windows (PowerShell)
$env:OAUTHLIB_INSECURE_TRANSPORT=1

# Voor Windows (Command Prompt)
set OAUTHLIB_INSECURE_TRANSPORT=1

# Voor macOS/Linux
export OAUTHLIB_INSECURE_TRANSPORT=1
```

Voeg deze variabele toe voordat je de applicatie start. Dit staat OAuth-authenticatie toe over HTTP, wat nodig is voor lokale ontwikkeling.

**Opmerking**: Gebruik deze instelling nooit in een productieomgeving, waar altijd HTTPS moet worden gebruikt voor veilige authenticatie.

### Productieomgeving

Voor productie gebruik je best een WSGI server zoals Gunicorn:

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

## Gebruik

### Authenticatie

1. Navigeer naar de applicatie in je browser
2. Klik op de "Inloggen met Google" knop
3. Meld je aan met je @lynxx.com Google account

### Een vraag stellen aan Claude

1. Na het inloggen kom je op de hoofdpagina
2. Selecteer het gewenste Claude model uit het dropdown menu
3. Typ je vraag in het tekstveld
4. Klik op "Versturen" om de vraag naar Claude te sturen
5. Het antwoord verschijnt in het gesprekvenster

### Conversaties beheren

1. Ga naar de "Gesprekken" pagina
2. Hier kun je eerdere conversaties bekijken, hernoemen of verwijderen
3. Klik op een conversatie om deze te openen en voort te zetten

## Projectstructuur

```
AnthropicConsole/
├── app.py                  # Hoofdapplicatie bestand
├── config.py               # Configuratie instellingen
├── auth.py                 # Authenticatie module
├── anthropic_api.py        # Anthropic API integratie
├── database.py             # Database module
├── models/                 # Database modellen
│   ├── __init__.py
│   └── conversation.py     # Conversatiemodel
├── repositories/           # Data repository laag
│   ├── __init__.py
│   └── conversation_repository.py
├── routes/                 # API routes
│   ├── __init__.py
│   └── api.py              # API endpoints
├── templates/              # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   └── conversations.html
├── static/                 # Statische bestanden (CSS, JS, afbeeldingen)
│   ├── css/
│   ├── js/
│   └── img/
├── tests/                  # Unit tests
├── requirements.txt        # Projectafhankelijkheden
├── .env.example            # Voorbeeld omgevingsvariabelen
└── README.md               # Projectdocumentatie
```

## Configuratie

De applicatie ondersteunt verschillende omgevingsconfiguraties:

- **Development**: Voor lokale ontwikkeling met debug modus aan
- **Testing**: Voor het uitvoeren van tests, gebruikt in-memory database
- **Production**: Voor productieomgeving met strikte beveiligingsinstellingen
- **Docker**: Voor containerized deployment

Je kunt de omgeving instellen met de `FLASK_ENV` omgevingsvariabele.

## Modellen

De volgende Claude modellen zijn beschikbaar:

- **Claude 3 Haiku**: Snel model voor eenvoudige taken
- **Claude 3 Sonnet**: Gebalanceerd model (snelheid/kwaliteit)
- **Claude 3 Opus**: Hoogste kwaliteit voor complexe taken

## Tests uitvoeren

```bash
pytest
```

Voor specifieke testmodules:

```bash
pytest tests/test_auth.py
pytest tests/test_config.py
pytest tests/test_anthropic_api.py
```

## Bijdragen aan het project

Zie [CONTRIBUTING.md](CONTRIBUTING.md) voor richtlijnen over het bijdragen aan dit project.

## Licentie

Dit project is eigendom van Lynxx en uitsluitend bedoeld voor intern gebruik.
