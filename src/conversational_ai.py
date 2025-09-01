# FILE: src/conversational_ai.py

import json
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConversationalTestCaseAI:
    """
    Enhanced AI system for conversational interactions with test cases.
    Allows QA teams to ask detailed follow-up questions about generated test cases.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the conversational AI system"""
        
        # Set up API configuration
        raw_key = api_key or os.getenv('GROQ_API_KEY')
        if not raw_key:
            raise ValueError("Groq API key required for conversational AI")
        
        self.api_key = raw_key.strip().strip('"').strip("'")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 2000
        self.temperature = 0.4  # Slightly higher for conversational responses
        
        print("🗣️ Conversational Test Case AI initialized")
    
    def ask_question(self, test_case: Dict[str, Any], question: str, 
                    original_transcript: Dict[str, Any] = None,
                    conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a question about a specific test case
        
        Args:
            test_case: The generated test case data
            question: The question from the QA team
            original_transcript: Original customer transcript for context
            conversation_history: Previous Q&A pairs for context
            
        Returns:
            Dictionary with response and metadata
        """
        
        try:
            # Build conversation context
            context = self._build_conversation_context(
                test_case, original_transcript, conversation_history
            )
            
            # Create the conversational prompt
            prompt = self._create_conversation_prompt(context, question)
            
            # Make API request
            response = self._make_groq_request(prompt)
            
            if response:
                # Parse and structure the response
                conversation_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "question": question,
                    "response": response,
                    "question_type": self._classify_question(question),
                    "confidence_score": 0.85,
                    "context_used": {
                        "has_transcript": original_transcript is not None,
                        "conversation_length": len(conversation_history) if conversation_history else 0
                    }
                }
                
                return conversation_entry
            else:
                return self._create_error_response(question, "API request failed")
                
        except Exception as e:
            print(f"❌ Error processing question: {str(e)}")
            return self._create_error_response(question, str(e))
    
    def get_suggested_questions(self, test_case: Dict[str, Any], 
                              original_transcript: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """
        Generate AI-suggested follow-up questions for a test case
        
        Args:
            test_case: The generated test case
            original_transcript: Original transcript for context
            
        Returns:
            List of suggested questions with categories
        """
        
        try:
            context = self._build_conversation_context(test_case, original_transcript)
            prompt = self._create_suggestions_prompt(context)
            
            response = self._make_groq_request(prompt)
            
            if response:
                # Parse the suggested questions
                suggestions = self._parse_suggestions_response(response)
                return suggestions
            else:
                return self._get_fallback_questions(test_case)
                
        except Exception as e:
            print(f"❌ Error generating suggestions: {str(e)}")
            return self._get_fallback_questions(test_case)
    
    def enhance_test_case_with_conversation(self, test_case: Dict[str, Any], 
                                         conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add conversational data to a test case
        
        Args:
            test_case: Original test case
            conversations: List of conversation entries
            
        Returns:
            Enhanced test case with conversational data
        """
        
        enhanced_case = test_case.copy()
        
        # Add conversational data structure
        conversational_data = {
            "conversation_history": conversations,
            "qa_insights": self._extract_insights_from_conversations(conversations),
            "additional_context": self._generate_additional_context(conversations),
            "conversation_summary": self._summarize_conversations(conversations),
            "last_updated": datetime.now().isoformat()
        }
        
        enhanced_case["conversational_data"] = conversational_data
        
        return enhanced_case
    
    def _build_conversation_context(self, test_case: Dict[str, Any], 
                                  original_transcript: Dict[str, Any] = None,
                                  conversation_history: List[Dict[str, Any]] = None) -> str:
        """Build context string for AI conversations"""
        
        context_parts = []
        
        # Add test case context
        context_parts.append("=== GENERATED TEST CASE ===")
        context_parts.append(f"ID: {test_case.get('test_case_id', 'Unknown')}")
        context_parts.append(f"Domain: {test_case.get('domain', 'Unknown')}")
        context_parts.append(f"Service: {test_case.get('service', 'Unknown')}")
        context_parts.append(f"Priority: {test_case.get('priority', 'Unknown')}")
        context_parts.append(f"Issue: {test_case.get('issue_description', 'Unknown')}")
        context_parts.append(f"Test Scenario: {test_case.get('test_scenario', 'Unknown')}")
        
        if test_case.get('test_steps'):
            context_parts.append("Test Steps:")
            for i, step in enumerate(test_case['test_steps'], 1):
                context_parts.append(f"  {i}. {step}")
        
        # Add original transcript context if available
        if original_transcript:
            context_parts.append("\n=== ORIGINAL CUSTOMER TRANSCRIPT ===")
            context_parts.append(f"Channel: {original_transcript.get('channel', 'Unknown')}")
            context_parts.append(f"Issue Category: {original_transcript.get('category', 'Unknown')}")
            if original_transcript.get('transcript_text'):
                # Truncate long transcripts
                transcript_text = original_transcript['transcript_text']
                if len(transcript_text) > 1000:
                    transcript_text = transcript_text[:1000] + "..."
                context_parts.append(f"Customer Issue: {transcript_text}")
        
        # Add conversation history if available
        if conversation_history:
            context_parts.append("\n=== PREVIOUS CONVERSATION ===")
            for entry in conversation_history[-3:]:  # Last 3 exchanges for context
                context_parts.append(f"Q: {entry.get('question', '')}")
                response_preview = entry.get('response', '')[:200]
                if len(entry.get('response', '')) > 200:
                    response_preview += "..."
                context_parts.append(f"A: {response_preview}")
        
        return "\n".join(context_parts)
    
    def _create_conversation_prompt(self, context: str, question: str) -> str:
        """Create prompt for conversational AI"""
        
        return f"""You are a QA Testing Expert Assistant helping teams understand and enhance test cases.

Context Information:
{context}

QA Team Question: {question}

Instructions:
- Provide helpful, specific, and actionable answers
- Reference details from the test case and transcript when relevant  
- Suggest concrete improvements or additional test scenarios
- Use clear formatting with bullet points or numbered lists when appropriate
- If the question relates to automation, provide specific technical guidance
- If asking about edge cases, suggest realistic scenarios based on the customer issue
- Keep responses practical and focused on QA testing needs
- Use emojis sparingly for better readability

Provide a comprehensive but concise response:"""
    
    def _create_suggestions_prompt(self, context: str) -> str:
        """Create prompt for generating suggested questions"""
        
        return f"""Based on this test case and context, generate 6 helpful follow-up questions that a QA team might want to ask.

Context:
{context}

Generate questions in these categories:
1. Automation (2 questions about test automation specifics)
2. Edge Cases (2 questions about additional scenarios to test)  
3. Clarification (2 questions about test details or requirements)

Format as JSON:
{{
  "suggestions": [
    {{"category": "automation", "question": "What specific UI elements should be automated?"}},
    {{"category": "edge_cases", "question": "What happens in low network conditions?"}},
    {{"category": "clarification", "question": "Which error messages should be validated?"}}
  ]
}}

Return only the JSON, no other text."""
    
    def _make_groq_request(self, prompt: str) -> Optional[str]:
        """Make request to Groq API"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful QA testing expert with deep knowledge of software testing, automation, and quality assurance best practices."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"❌ API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            return None
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question being asked"""
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['automate', 'automation', 'script', 'selenium', 'playwright']):
            return 'automation'
        elif any(word in question_lower for word in ['edge case', 'edge', 'additional', 'what if', 'scenario']):
            return 'edge_case'
        elif any(word in question_lower for word in ['why', 'how', 'explain', 'clarify', 'what does']):
            return 'clarification'
        elif any(word in question_lower for word in ['improve', 'enhance', 'better', 'optimize']):
            return 'enhancement'
        else:
            return 'general'
    
    def _parse_suggestions_response(self, response: str) -> List[Dict[str, str]]:
        """Parse AI response for suggested questions"""
        
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                
                data = json.loads(json_str)
                return data.get('suggestions', [])
            else:
                # Fallback parsing if JSON format is not found
                return []
                
        except json.JSONDecodeError:
            return []
    
    def _get_fallback_questions(self, test_case: Dict[str, Any]) -> List[Dict[str, str]]:
        """Provide fallback questions if AI generation fails"""
        
        domain = test_case.get('domain', '').lower()
        service = test_case.get('service', '').lower()
        
        base_questions = [
            {"category": "automation", "question": "What specific UI elements should be automated for this test?"},
            {"category": "automation", "question": "What test data variations should be included in automation?"},
            {"category": "edge_cases", "question": "What additional scenarios should be tested?"},
            {"category": "edge_cases", "question": "How does this issue vary across different devices or browsers?"},
            {"category": "clarification", "question": "What specific error messages should be validated?"},
            {"category": "clarification", "question": "What are the exact steps to reproduce this issue?"}
        ]
        
        # Customize questions based on domain
        if 'mobile' in domain:
            base_questions.append({"category": "edge_cases", "question": "How does this behave on different mobile OS versions?"})
        
        if 'web' in domain:
            base_questions.append({"category": "edge_cases", "question": "What happens with different browser configurations?"})
        
        return base_questions[:6]  # Return first 6 questions
    
    def _extract_insights_from_conversations(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from conversation history"""
        
        insights = []
        
        for conv in conversations:
            question_type = conv.get('question_type', '')
            if question_type == 'automation':
                insights.append(f"Automation guidance requested: {conv.get('question', '')[:50]}...")
            elif question_type == 'edge_case':
                insights.append(f"Edge case identified: {conv.get('question', '')[:50]}...")
        
        return insights
    
    def _generate_additional_context(self, conversations: List[Dict[str, Any]]) -> str:
        """Generate additional context from conversations"""
        
        if not conversations:
            return ""
        
        context_items = []
        for conv in conversations:
            response = conv.get('response', '').lower()
            if 'specific' in response:
                context_items.append("Requires specific implementation details")
            if 'edge case' in response:
                context_items.append("Multiple edge cases identified")
        
        return "; ".join(context_items)
    
    def _summarize_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        """Create a summary of the conversation"""
        
        if not conversations:
            return "No conversations yet"
        
        total = len(conversations)
        automation_q = len([c for c in conversations if c.get('question_type') == 'automation'])
        edge_case_q = len([c for c in conversations if c.get('question_type') == 'edge_case'])
        
        return f"Total questions: {total} (Automation: {automation_q}, Edge cases: {edge_case_q})"
    
    def _create_error_response(self, question: str, error: str) -> Dict[str, Any]:
        """Create error response structure"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": f"I encountered an error processing your question: {error}. Please try rephrasing or contact support if the issue persists.",
            "question_type": "error",
            "confidence_score": 0.0,
            "error": True
        }


def test_conversational_ai():
    """Test the conversational AI system"""
    
    # Sample test case for testing
    sample_test_case = {
        "test_case_id": "TC_WEB_001",
        "domain": "Web Portal",
        "service": "Device Activation",
        "priority": "High",
        "issue_description": "Device activation delayed due to incomplete name field",
        "test_scenario": "Test form validation for complete name fields",
        "test_steps": [
            "Step 1: Navigate to activation form",
            "Step 2: Enter name with middle initial",
            "Step 3: Submit form and verify success"
        ]
    }
    
    # Initialize conversational AI
    try:
        conv_ai = ConversationalTestCaseAI()
        
        # Test suggested questions
        print("🤖 Testing suggested questions generation...")
        suggestions = conv_ai.get_suggested_questions(sample_test_case)
        
        print(f"Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. [{suggestion['category']}] {suggestion['question']}")
        
        # Test asking a question
        print("\n💬 Testing question answering...")
        test_question = "What specific form fields should be tested for this issue?"
        response = conv_ai.ask_question(sample_test_case, test_question)
        
        print(f"Question: {response['question']}")
        print(f"Response: {response['response'][:200]}...")
        print(f"Type: {response['question_type']}")
        
        print("✅ Conversational AI test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Make sure GROQ_API_KEY is set in your environment variables")


if __name__ == "__main__":
    test_conversational_ai()