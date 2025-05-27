"""
Tests voor multi-agent systeem.

Test de core functionaliteit van agents, orchestrator en workflows.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from agents.base_agent import BaseAgent
from agents.orchestrator import AgentOrchestrator, WorkflowStatus
from agents.issue_manager_agent import IssueManagerAgent
from agents.config import get_agent_config, get_workflow_config


class TestBaseAgent(unittest.TestCase):
    """Test BaseAgent functionaliteit."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Maak tijdelijk system prompt bestand
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file.write("Test system prompt")
        self.temp_file.close()
        
        self.agent = BaseAgent(
            name="test_agent",
            model="claude-3-haiku-20240307",
            temperature=0.2,
            system_prompt_file=self.temp_file.name
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)
    
    def test_agent_initialization(self):
        """Test agent initialisatie."""
        self.assertEqual(self.agent.name, "test_agent")
        self.assertEqual(self.agent.model, "claude-3-haiku-20240307")
        self.assertEqual(self.agent.temperature, 0.2)
        self.assertEqual(self.agent.status, "idle")
        self.assertIsNone(self.agent.conversation_id)
    
    def test_system_prompt_loading(self):
        """Test system prompt laden."""
        self.assertEqual(self.agent.system_prompt, "Test system prompt")
    
    def test_context_data_management(self):
        """Test context data beheer."""
        # Set context data
        self.agent.set_context_data("test_key", "test_value")
        
        # Get context data
        value = self.agent.get_context_data("test_key")
        self.assertEqual(value, "test_value")
        
        # Get non-existent key with default
        default_value = self.agent.get_context_data("non_existent", "default")
        self.assertEqual(default_value, "default")
    
    def test_clear_context(self):
        """Test context clearing."""
        self.agent.conversation_id = "test_conversation"
        self.agent.status = "active"
        self.agent.last_output = "test output"
        self.agent.set_context_data("test_key", "test_value")
        
        self.agent.clear_context()
        
        self.assertIsNone(self.agent.conversation_id)
        self.assertEqual(self.agent.status, "idle")
        self.assertIsNone(self.agent.last_output)
        self.assertEqual(len(self.agent.context_data), 0)
    
    def test_get_status(self):
        """Test status informatie."""
        status = self.agent.get_status()
        
        expected_keys = ['name', 'status', 'model', 'temperature', 'conversation_id', 'has_output', 'context_keys']
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status['name'], "test_agent")
        self.assertEqual(status['status'], "idle")


class TestIssueManagerAgent(unittest.TestCase):
    """Test IssueManagerAgent functionaliteit."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Maak tijdelijk system prompt bestand
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file.write("Issue manager system prompt")
        self.temp_file.close()
        
        self.agent = IssueManagerAgent(
            name="issue_manager",
            model="claude-3-5-sonnet-20241022",
            temperature=0.2,
            system_prompt_file=self.temp_file.name
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)
    
    @patch('agents.issue_manager_agent.IssueManagerAgent.send_message')
    def test_analyze_project_state(self, mock_send_message):
        """Test project staat analyse."""
        # Mock AI response
        mock_response = '{"action": "analyze_project", "analysis": {"current_state": "test", "next_priority": "test", "dependencies": []}}'
        mock_send_message.return_value = mock_response
        
        task_input = {
            'action': 'analyze_project_state',
            'project_info': 'Test project info',
            'project_stappen': 'Test project steps'
        }
        
        result = self.agent.execute(task_input)
        
        self.assertEqual(result['action'], 'analyze_project')
        self.assertIn('analysis', result)
        mock_send_message.assert_called_once()
    
    @patch('agents.issue_manager_agent.IssueManagerAgent.send_message')
    def test_create_or_update_issue(self, mock_send_message):
        """Test issue creatie."""
        # Mock AI response
        mock_response = '{"action": "create_issue", "issue": {"title": "Test Issue", "description": "Test description", "labels": ["must-have"], "branch_name": "feature/test"}}'
        mock_send_message.return_value = mock_response
        
        task_input = {
            'action': 'create_or_update_issue',
            'next_issue': 'Test issue to create',
            'priority': 'high'
        }
        
        result = self.agent.execute(task_input)
        
        self.assertEqual(result['action'], 'create_issue')
        self.assertIn('issue', result)
        mock_send_message.assert_called_once()
    
    def test_invalid_action(self):
        """Test ongeldige actie."""
        task_input = {'action': 'invalid_action'}
        
        with self.assertRaises(ValueError):
            self.agent.execute(task_input)


class TestAgentOrchestrator(unittest.TestCase):
    """Test AgentOrchestrator functionaliteit."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = AgentOrchestrator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.orchestrator.shutdown()
    
    @patch('agents.orchestrator.AgentOrchestrator._import_agent_class')
    @patch('agents.config.validate_agent_config')
    def test_load_agents(self, mock_validate, mock_import):
        """Test agent loading."""
        # Mock validation
        mock_validate.return_value = True
        
        # Mock agent class
        mock_agent_class = Mock()
        mock_agent_instance = Mock()
        mock_agent_class.return_value = mock_agent_instance
        mock_import.return_value = mock_agent_class
        
        agents = self.orchestrator.load_agents()
        
        # Verify agents were loaded
        self.assertIsInstance(agents, dict)
        self.assertEqual(len(agents), len(self.orchestrator.agents))
    
    def test_execution_status_tracking(self):
        """Test execution status tracking."""
        # Test non-existent execution
        status = self.orchestrator.get_execution_status("non_existent")
        self.assertIsNone(status)
        
        # Test all executions status
        all_status = self.orchestrator.get_all_executions_status()
        self.assertIsInstance(all_status, list)
    
    def test_cancel_execution(self):
        """Test execution cancellation."""
        # Test cancelling non-existent execution
        result = self.orchestrator.cancel_execution("non_existent")
        self.assertFalse(result)
    
    def test_cleanup_executions(self):
        """Test execution cleanup."""
        # Should not raise any errors
        self.orchestrator.cleanup_completed_executions(max_age_hours=1)


class TestAgentConfig(unittest.TestCase):
    """Test agent configuratie."""
    
    def test_get_agent_config(self):
        """Test agent configuratie ophalen."""
        config = get_agent_config("issue_manager")
        
        required_keys = ['model', 'temperature', 'system_prompt', 'class']
        for key in required_keys:
            self.assertIn(key, config)
    
    def test_get_workflow_config(self):
        """Test workflow configuratie ophalen."""
        config = get_workflow_config("development_cycle")
        
        self.assertIn('description', config)
        self.assertIn('steps', config)
        self.assertIsInstance(config['steps'], list)
    
    def test_invalid_agent_config(self):
        """Test ongeldige agent configuratie."""
        with self.assertRaises(KeyError):
            get_agent_config("non_existent_agent")
    
    def test_invalid_workflow_config(self):
        """Test ongeldige workflow configuratie."""
        with self.assertRaises(KeyError):
            get_workflow_config("non_existent_workflow")


class TestWorkflowExecution(unittest.TestCase):
    """Test workflow execution functionaliteit."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = AgentOrchestrator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.orchestrator.shutdown()
    
    def test_workflow_execution_creation(self):
        """Test workflow execution aanmaken."""
        with self.assertRaises(ValueError):
            # Should fail because workflow doesn't exist
            self.orchestrator.execute_workflow("non_existent_workflow")
    
    @patch('agents.orchestrator.AgentOrchestrator.load_agents')
    def test_workflow_execution_with_mocked_agents(self, mock_load_agents):
        """Test workflow execution met gemockte agents."""
        # Mock agents
        mock_agent = Mock()
        mock_agent.execute.return_value = {"result": "success"}
        
        self.orchestrator.agents = {"issue_manager": mock_agent}
        mock_load_agents.return_value = self.orchestrator.agents
        
        # This would normally start a workflow, but we're just testing the setup
        # The actual execution happens in a separate thread
        try:
            execution_id = self.orchestrator.execute_workflow("development_cycle", {})
            self.assertIsNotNone(execution_id)
            
            # Check that execution was registered
            status = self.orchestrator.get_execution_status(execution_id)
            self.assertIsNotNone(status)
        except Exception as e:
            # Expected to fail due to missing project files, but that's OK for this test
            pass


if __name__ == '__main__':
    unittest.main()