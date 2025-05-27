"""
Issue Manager Agent voor multi-agent systeem.

Deze agent is verantwoordelijk voor het analyseren van project staat,
beheren van GitHub issues en plannen van ontwikkel stappen.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class IssueManagerAgent(BaseAgent):
    """
    Agent voor issue management en project planning.
    
    Analyseert project staat, creëert en beheert GitHub issues,
    en plant ontwikkel stappen.
    """
    
    def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Voer issue management taak uit.
        
        Args:
            task_input: Input data met actie en parameters
            
        Returns:
            Resultaat van de uitgevoerde actie
        """
        action = task_input.get('action', 'analyze_project_state')
        
        logger.info(f"IssueManagerAgent executing action: {action}")
        
        try:
            if action == 'analyze_project_state':
                return self._analyze_project_state(task_input)
            elif action == 'create_or_update_issue':
                return self._create_or_update_issue(task_input)
            elif action == 'analyze_issue':
                return self._analyze_issue(task_input)
            elif action == 'prioritize_issues':
                return self._prioritize_issues(task_input)
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Error in IssueManagerAgent.execute: {e}")
            raise
    
    def _analyze_project_state(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyseer de huidige project staat.
        
        Args:
            task_input: Input data
            
        Returns:
            Analyse resultaten
        """
        # Bouw prompt voor project analyse
        prompt = self._build_project_analysis_prompt(task_input)
        
        # Stuur naar AI voor analyse
        response = self.send_message(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info("Project state analysis completed")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Fallback: return raw response
            return {
                "action": "analyze_project",
                "analysis": {
                    "current_state": response,
                    "next_priority": "Manual review needed",
                    "dependencies": []
                },
                "raw_response": response
            }
    
    def _create_or_update_issue(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creëer of update een GitHub issue.
        
        Args:
            task_input: Input data met issue informatie
            
        Returns:
            Issue creatie/update resultaat
        """
        # Bouw prompt voor issue creatie
        prompt = self._build_issue_creation_prompt(task_input)
        
        # Stuur naar AI voor issue specificatie
        response = self.send_message(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info("Issue creation/update specification completed")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Fallback: return structured response
            return {
                "action": "create_issue",
                "issue": {
                    "title": "Manual Review Required",
                    "description": f"AI response needs manual review:\n\n{response}",
                    "labels": ["manual-review"],
                    "branch_name": "feature/manual-review"
                },
                "raw_response": response
            }
    
    def _analyze_issue(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyseer een bestaand issue.
        
        Args:
            task_input: Input data met issue ID
            
        Returns:
            Issue analyse resultaat
        """
        issue_id = task_input.get('issue_id')
        if not issue_id:
            raise ValueError("issue_id is required for issue analysis")
        
        # Bouw prompt voor issue analyse
        prompt = self._build_issue_analysis_prompt(task_input)
        
        # Stuur naar AI voor analyse
        response = self.send_message(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info(f"Issue {issue_id} analysis completed")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "action": "analyze_issue",
                "issue_id": issue_id,
                "implementation_plan": response,
                "raw_response": response
            }
    
    def _prioritize_issues(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prioriteer een lijst van issues.
        
        Args:
            task_input: Input data met issue lijst
            
        Returns:
            Geprioriteerde issue lijst
        """
        issues = task_input.get('issues', [])
        if not issues:
            raise ValueError("issues list is required for prioritization")
        
        # Bouw prompt voor issue prioritering
        prompt = self._build_prioritization_prompt(task_input)
        
        # Stuur naar AI voor prioritering
        response = self.send_message(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info(f"Prioritized {len(issues)} issues")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "action": "prioritize_issues",
                "prioritized_issues": issues,  # Return original order as fallback
                "raw_response": response
            }
    
    def _build_project_analysis_prompt(self, task_input: Dict[str, Any]) -> str:
        """
        Bouw prompt voor project staat analyse.
        
        Args:
            task_input: Input data
            
        Returns:
            Geformatteerde prompt
        """
        project_info = task_input.get('project_info', '')
        project_stappen = task_input.get('project_stappen', '')
        open_issues = task_input.get('open_issues', [])
        
        prompt = f"""
Analyseer de huidige project staat en bepaal de volgende stap.

## Project Info
{project_info}

## Project Stappen
{project_stappen}

## Openstaande Issues
{json.dumps(open_issues, indent=2) if open_issues else 'Geen openstaande issues'}

Analyseer deze informatie en bepaal:
1. Wat is de huidige staat van het project?
2. Wat is de volgende logische stap?
3. Zijn er bugs die voorrang hebben?
4. Welke afhankelijkheden zijn er?

Geef je antwoord in het JSON formaat zoals gespecificeerd in je system prompt.
"""
        return prompt.strip()
    
    def _build_issue_creation_prompt(self, task_input: Dict[str, Any]) -> str:
        """
        Bouw prompt voor issue creatie.
        
        Args:
            task_input: Input data
            
        Returns:
            Geformatteerde prompt
        """
        next_step = task_input.get('next_issue', '')
        priority = task_input.get('priority', 'medium')
        project_context = task_input.get('project_context', '')
        
        prompt = f"""
Creëer een GitHub issue voor de volgende ontwikkel stap.

## Te Implementeren Stap
{next_step}

## Prioriteit
{priority}

## Project Context
{project_context}

Creëer een gedetailleerde issue met:
1. Duidelijke titel
2. Uitgebreide beschrijving met acceptatiecriteria
3. Specificatie van welke bestanden gewijzigd moeten worden
4. Welke tests geschreven moeten worden
5. Juiste labels (must-have, nice-to-have, bug)
6. Branch naam voor implementatie

Geef je antwoord in het JSON formaat zoals gespecificeerd in je system prompt.
"""
        return prompt.strip()
    
    def _build_issue_analysis_prompt(self, task_input: Dict[str, Any]) -> str:
        """
        Bouw prompt voor issue analyse.
        
        Args:
            task_input: Input data
            
        Returns:
            Geformatteerde prompt
        """
        issue_id = task_input.get('issue_id')
        issue_content = task_input.get('issue_content', '')
        project_context = task_input.get('project_context', '')
        
        prompt = f"""
Analyseer het volgende GitHub issue en maak een implementatie plan.

## Issue #{issue_id}
{issue_content}

## Project Context
{project_context}

Analyseer dit issue en creëer:
1. Gedetailleerd implementatie plan
2. Lijst van benodigde wijzigingen
3. Identificatie van afhankelijkheden
4. Schatting van complexiteit
5. Mogelijke risico's

Geef je antwoord in het JSON formaat zoals gespecificeerd in je system prompt.
"""
        return prompt.strip()
    
    def _build_prioritization_prompt(self, task_input: Dict[str, Any]) -> str:
        """
        Bouw prompt voor issue prioritering.
        
        Args:
            task_input: Input data
            
        Returns:
            Geformatteerde prompt
        """
        issues = task_input.get('issues', [])
        criteria = task_input.get('criteria', 'impact and urgency')
        
        prompt = f"""
Prioriteer de volgende GitHub issues op basis van {criteria}.

## Issues
{json.dumps(issues, indent=2)}

Prioriteer deze issues en geef voor elk issue:
1. Prioriteit score (1-10, waarbij 10 hoogste prioriteit is)
2. Reden voor prioriteit
3. Afhankelijkheden
4. Geschatte impact

Geef bugs altijd de hoogste prioriteit.

Geef je antwoord in het JSON formaat zoals gespecificeerd in je system prompt.
"""
        return prompt.strip()
    
    def get_project_state(self) -> Dict[str, Any]:
        """
        Krijg huidige project staat informatie.
        
        Returns:
            Project staat informatie
        """
        try:
            # Lees project bestanden
            project_info = self._read_project_file('project_info.txt')
            project_stappen = self._read_project_file('project_stappen.txt')
            
            return {
                'project_info': project_info,
                'project_stappen': project_stappen,
                'last_updated': self.get_context_data('last_analysis_time')
            }
        except Exception as e:
            logger.error(f"Error reading project state: {e}")
            return {}
    
    def _read_project_file(self, filename: str) -> str:
        """
        Lees een project bestand.
        
        Args:
            filename: Naam van het bestand
            
        Returns:
            Inhoud van het bestand
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Project file {filename} not found")
            return ""
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return ""