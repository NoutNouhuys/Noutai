# AI Ontwikkelhulp

Een AI-gestuurde ontwikkelingsassistent die helpt bij het beheren en doorontwikkelen van GitHub repositories. Deze applicatie gebruikt de Anthropic Claude API en Model Context Protocol (MCP) om intelligente ondersteuning te bieden voor softwareontwikkeling.

## 🚀 Hoofdfunctionaliteiten

- **AI-gestuurde Repository Ontwikkeling**: Automatische analyse en doorontwikkeling van GitHub repositories
- **MCP Tool Integratie**: Gebruik van Model Context Protocol voor GitHub operaties
- **Conversation Management**: Persistente chat geschiedenis met database opslag
- **Log Formatting**: Gestructureerde logging voor ontwikkelingsprocessen
- **Project Info Caching**: Intelligente caching van project informatie
- **Werkwijze-gebaseerd**: Volgt gedefinieerde ontwikkelingsworkflows

## 📋 Vereisten

- Python 3.8+
- Anthropic API key
- GitHub Personal Access Token
- SQLite (voor conversation storage)

## 🛠️ Installatie

1. **Clone de repository**
   ```bash
   git clone https://github.com/Fbeunder/aiontwikkelhulp.git
   cd aiontwikkelhulp
   ```

2. **Installeer dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configureer environment variabelen**
   
   Maak een `.env` bestand aan in de root directory:
   ```env
   ANTHROPIC_API_KEY=jouw_anthropic_api_key
   GITHUB_TOKEN=jouw_github_personal_access_token
   ```

4. **Start de applicatie**
   ```bash
   python main.py
   ```

## 🏗️ Projectstructuur

```
aiontwikkelhulp/
├── main.py                    # Hoofdapplicatie entry point
├── anthropic_client.py        # Anthropic API client configuratie
├── anthropic_config.py        # Configuratie voor Anthropic integratie
├── conversation_manager.py    # Chat geschiedenis beheer
├── mcp_integration.py         # Model Context Protocol integratie
├── ui.py                     # Streamlit gebruikersinterface
├── ui_sidebar.py             # Sidebar componenten
├── conversations.db          # SQLite database (automatisch aangemaakt)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variabelen (maak zelf aan)
└── README.md                 # Dit bestand
```

## 💡 Gebruik

### Basis Chat Functionaliteit
- Start een conversatie met de AI assistent
- Stel vragen over software ontwikkeling
- Krijg hulp bij code review en debugging

### Repository Ontwikkeling
- Gebruik het `ga` commando gevolgd door een repository naam
- De AI analyseert de repository structuur
- Volgt automatisch de werkwijze gedefinieerd in `werkwijze.txt`
- Maakt issues, branches en pull requests aan
- Implementeert nieuwe functionaliteiten

### Voorbeeld Commando's
```
ga Fbeunder/mijn-project
```

Dit commando:
1. Analyseert de repository structuur
2. Leest `werkwijze.txt` voor specifieke instructies
3. Creëert of update `project_info.txt`
4. Maakt ontwikkelingsplan in `project_stappen.txt`
5. Implementeert volgende stappen automatisch

## 🔧 Configuratie

### Anthropic API
- Verkrijg een API key van [Anthropic Console](https://console.anthropic.com/)
- Voeg toe aan `.env` bestand als `ANTHROPIC_API_KEY`

### GitHub Integration
- Maak een Personal Access Token in GitHub Settings
- Geef permissies voor repo access, issues, en pull requests
- Voeg toe aan `.env` bestand als `GITHUB_TOKEN`

### MCP Configuration
De applicatie gebruikt MCP (Model Context Protocol) voor GitHub operaties. Dit wordt automatisch geconfigureerd bij opstarten.

## 🔄 Workflow

### Automatische Repository Ontwikkeling
1. **Analyse**: Leest bestaande code en documentatie
2. **Planning**: Maakt ontwikkelingsplan gebaseerd op `werkwijze.txt`
3. **Implementatie**: Voert stappen uit volgens gedefinieerde workflow
4. **Review**: Maakt pull requests voor code review
5. **Iteratie**: Herhaalt proces voor volgende functionaliteiten

### Project Info Management
- `project_info.txt`: Bevat overzicht van modules en architectuur
- `project_stappen.txt`: Definieert volgende ontwikkelstappen
- `werkwijze.txt`: Bevat specifieke ontwikkelingsinstructies

## 🐛 Troubleshooting

### Veelvoorkomende Problemen

**API Errors**
- Controleer of `ANTHROPIC_API_KEY` correct is ingesteld
- Verificeer of je Anthropic account actief is

**GitHub Permissions**
- Zorg dat `GITHUB_TOKEN` alle benodigde permissies heeft
- Test verbinding met een eenvoudige repository operatie

**Database Issues**
- `conversations.db` wordt automatisch aangemaakt
- Bij problemen: verwijder bestand en herstart applicatie

## 📚 Ontwikkeling

### Nieuwe Features Toevoegen
1. Fork de repository
2. Maak een feature branch
3. Implementeer wijzigingen
4. Schrijf tests
5. Maak een pull request

### Code Structuur
- `main.py`: Entry point en applicatie setup
- `anthropic_client.py`: AI model integratie
- `mcp_integration.py`: GitHub API operaties via MCP
- `conversation_manager.py`: Chat persistentie
- `ui.py`: Frontend interface

## 🤝 Contributing

Bijdragen zijn welkom! Zie de development sectie voor instructies over het toevoegen van nieuwe features.

## 📄 Licentie

Dit project is beschikbaar onder MIT licentie.

## 🔗 Links

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [GitHub API](https://docs.github.com/en/rest)

---

Voor vragen of ondersteuning, maak een issue aan in deze repository.