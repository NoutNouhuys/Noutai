# Bijdragen aan de Lynxx Anthropic Console

Bedankt voor je interesse in het bijdragen aan de Lynxx Anthropic Console! Dit document bevat richtlijnen voor het bijdragen aan de doorontwikkeling en verbetering van de applicatie.

## Inhoudsopgave

- [Code of Conduct](#code-of-conduct)
- [Ontwikkelproces](#ontwikkelproces)
- [Pull Request Process](#pull-request-process)
- [Code Styleguide](#code-styleguide)
- [Testen](#testen)
- [Branchingstrategie](#branchingstrategie)

## Code of Conduct

Bij het bijdragen aan dit project wordt van deelnemers verwacht dat ze respect tonen voor andere bijdragers en gebruikers en dat ze een positieve ontwikkelomgeving helpen creëren. Ongewenst gedrag zoals intimidatie, ongepast taalgebruik of discriminatie wordt niet getolereerd.

## Ontwikkelproces

1. **Issues**: Nieuwe functionaliteit, bugfixes en verbeteringen moeten worden bijgehouden als issues in GitHub.
2. **Planning**: Issues worden besproken en geprioriteerd door het ontwikkelteam.
3. **Implementatie**: Zorg ervoor dat je werkt op basis van de laatste versie van de main branch.
4. **Review**: Alle code wordt gereviewd door middel van pull requests.
5. **Release**: Regelmatige releases worden gepland door het ontwikkelteam.

## Pull Request Process

1. **Branch**: Maak een nieuwe branch vanaf de main branch voor elke feature of bugfix.
   ```
   git checkout -b feature/feature-naam
   git checkout -b bugfix/bug-beschrijving
   ```

2. **Commit**: Maak kleinere, logische commits met duidelijke commit berichten.
   ```
   git commit -m "Functionaliteit X toegevoegd aan module Y"
   ```

3. **Push**: Push je branch naar de remote repository.
   ```
   git push origin feature/feature-naam
   ```

4. **Pull Request**: Maak een pull request naar de main branch.
   - Voeg een duidelijke titel toe
   - Beschrijf de wijzigingen in detail
   - Vermeld het issue nummer (bijv. "Fixes #123")
   - Voeg screenshots toe indien relevant

5. **Review**: Zorg dat je code voldoet aan de styleguide, alle tests slagen, en wacht op code review.

6. **Merge**: Na goedkeuring kan de branch worden gemerged in main.

7. **Opruimen**: Verwijder de branch na het mergen.

## Code Styleguide

### Python

- Volg PEP 8 richtlijnen voor Python code
- Gebruik betekenisvolle variabele- en functienamen in het Engels
- Voeg docstrings toe aan modules, klassen en functies volgens de Google Python Style Guide
- Gebruik type hints waar mogelijk
- Houd functies kort en specifiek (één verantwoordelijkheid per functie)
- Maximale regel lengte: 100 karakters

### HTML/CSS/JavaScript

- Volg consistente indentatie (2 spaties)
- Gebruik betekenisvolle id's en class namen
- Houd JavaScript-bestanden modulair
- Commentaar in het Engels

## Testen

- Nieuwe functionaliteiten moeten worden gedekt door tests
- Voer alle tests uit voordat je een pull request maakt:
  ```
  pytest
  ```
- Zorg voor minimaal 80% test coverage voor nieuwe code

## Branchingstrategie

We volgen een vereenvoudigde Gitflow workflow:

- **main**: Representeert de officiële release history
- **feature/\***: Voor nieuwe functionaliteiten
- **bugfix/\***: Voor bug fixes
- **hotfix/\***: Voor kritieke fixes die direct naar productie moeten

## Documentatie

- Update de `README.md` indien nodig
- Documenteer nieuwe features in de code en in de gebruikersdocumentatie
- Houd documentatie up-to-date bij API-wijzigingen

## Versionering

We volgen [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (bijvoorbeeld 1.2.3)
- **MAJOR**: Incompatibele API wijzigingen
- **MINOR**: Nieuwe functionaliteit (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Vragen?

Als je vragen hebt over het bijdrageproces, open dan een issue op GitHub of neem contact op met een van de hoofdontwikkelaars.

Bedankt voor je bijdragen aan de Lynxx Anthropic Console!
