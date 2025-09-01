# FILE: src/ai_test_generator.py

import json
import os
import requests
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GroqTestCaseGenerator:
    """Generate test cases using Groq API (free alternative to OpenAI)"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY environment variable)
        """
        print("🚀 Groq AI Test Case Generator initialized")
        
        # Set API key and clean it
        raw_key = api_key or os.getenv('GROQ_API_KEY')
        if not raw_key:
            print("❌ Groq API key not found!")
            print("📝 Get your free API key:")
            print("1. Go to https://console.groq.com/")
            print("2. Sign up (free)")
            print("3. Get API key from dashboard")
            print("4. Set GROQ_API_KEY environment variable or pass to constructor")
            raise ValueError("Groq API key required")
        
        # Clean the API key (remove quotes, spaces, newlines)
        self.api_key = raw_key.strip().strip('"').strip("'")
        print(f"🔑 API key loaded: {self.api_key[:10]}...{self.api_key[-5:]}")
        
        # Groq API settings
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Free model with good performance
        self.max_tokens = 1500
        self.temperature = 0.3
        
        print(f"✅ Using model: {self.model}")
        
        # Test API connection
        if self._test_connection():
            print("✅ Groq API connection successful")
        else:
            print("❌ Failed to connect to Groq API")
    
    def _test_connection(self) -> bool:
        """Test if Groq API is accessible"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 10
            }
            
            response = requests.post(self.api_url, headers=headers, json=test_payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
    
    def generate_test_cases(self, input_file: str, output_file: str) -> bool:
        """
        Generate test cases from masked transcript data
        
        Args:
            input_file: Path to masked_transcripts.json
            output_file: Path to save generated test cases
        """
        try:
            # Load masked data
            with open(input_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📖 Loading transcripts from: {input_file}")
            transcripts = data.get('transcripts', [])
            print(f"🔍 Found {len(transcripts)} transcripts to process")
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Generate test cases
            generated_test_cases = []
            successful_generations = 0
            
            for i, transcript in enumerate(transcripts, 1):
                call_id = transcript.get('call_id', f'Unknown_{i}')
                print(f"🤖 Processing {i}/{len(transcripts)}: {call_id}")
                
                try:
                    test_case = self._generate_single_test_case(transcript, i)
                    if test_case:
                        generated_test_cases.append(test_case)
                        successful_generations += 1
                        print(f"✅ Generated: {test_case.get('test_case_id', 'Unknown')}")
                    else:
                        print(f"⚠️ Failed to generate test case for transcript {i}")
                        
                except Exception as e:
                    print(f"❌ Error processing transcript {i}: {str(e)}")
                    continue
            
            # Save generated test cases
            if generated_test_cases:
                output_data = {
                    'metadata': {
                        'total_test_cases': len(generated_test_cases),
                        'generated_at': datetime.now().isoformat(),
                        'success_rate': f"{successful_generations}/{len(transcripts)} ({successful_generations/len(transcripts)*100:.1f}%)",
                        'model_used': self.model,
                        'source_file': input_file
                    },
                    'test_cases': generated_test_cases
                }
                
                with open(output_file, 'w', encoding='utf-8') as file:
                    json.dump(output_data, file, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved {len(generated_test_cases)} test cases to: {output_file}")
                return True
            else:
                print("❌ No test cases were generated")
                return False
                
        except Exception as e:
            print(f"❌ Error generating test cases: {str(e)}")
            return False
    
    def _generate_single_test_case(self, transcript: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate a test case for a single transcript using Groq API"""
        
        try:
            # Create prompt
            prompt = self._create_test_case_prompt(transcript)
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json()
                content = ai_response['choices'][0]['message']['content']
                test_case = self._parse_ai_response(content, transcript, index)
                return test_case
            else:
                print(f"❌ API error: {response.status_code} - {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"❌ Groq API error: {str(e)}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the AI's role"""
        
        return """You are a QA Test Case Generator for telecommunications customer support scenarios.

Analyze customer support transcripts and generate detailed test cases that QA teams can execute.

Generate test cases in this EXACT JSON format:
{
    "test_case_id": "TC_[CHANNEL]_[NUMBER]",
    "domain": "Customer Portal/Mobile App/Target Store/etc",
    "service": "Plan Management/Device Support/Billing/etc", 
    "test_type": "User Experience/Functional/Integration/etc",
    "priority": "Critical/High/Medium/Low",
    "severity": "High/Medium/Low",
    "issue_description": "Clear description of customer issue",
    "test_scenario": "What should be tested to prevent this issue",
    "preconditions": ["Setup requirement 1", "Setup requirement 2"],
    "test_steps": ["Step 1: Action", "Step 2: Action", "Step 3: Verify result"],
    "expected_result": "What should happen when system works correctly",
    "actual_issue": "Current problem that needs fixing",
    "environmental_dependencies": ["Browser type", "Device", "Network"],
    "edge_cases": ["Additional scenarios to test"],
    "automation_feasibility": "High/Medium/Low",
    "customer_impact": "How this affects customer experience"
}

Focus on preventing the specific customer problem identified in the transcript. Return ONLY the JSON, no extra text."""
    
    def _create_test_case_prompt(self, transcript: Dict[str, Any]) -> str:
        """Create the prompt for generating a test case"""
        
        # Extract key information
        call_id = transcript.get('call_id', 'Unknown')
        channel = transcript.get('channel', 'Unknown')
        category = transcript.get('category', 'Unknown')
        severity = transcript.get('severity', 'Medium')
        conversation = transcript.get('transcript', '')
        resolution = transcript.get('resolution', '')
        impact = transcript.get('impact', '')
        
        # Truncate conversation if too long for API limits
        max_conversation_length = 800
        if len(conversation) > max_conversation_length:
            conversation = conversation[:max_conversation_length] + "...[truncated]"
        
        prompt = f"""Analyze this customer support case and create a test case:

CASE DETAILS:
Call ID: {call_id}
Channel: {channel}
Issue Category: {category}
Severity: {severity}

CUSTOMER CONVERSATION:
{conversation}

RESOLUTION: {resolution}
CUSTOMER IMPACT: {impact}

Create a detailed test case that would help QA catch this problem before customers experience it. Focus on the specific steps needed to reproduce and test for this issue.

Return only the JSON test case."""
        
        return prompt.strip()
    
    def _parse_ai_response(self, ai_response: str, original_transcript: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Parse and validate AI response"""
        
        try:
            # Clean up the response - sometimes AI includes markdown or extra text
            response = ai_response.strip()
            
            # Find JSON content
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                
                # Parse JSON
                test_case = json.loads(json_str)
                
                # Add source information
                test_case['source_call_id'] = original_transcript.get('call_id', 'Unknown')
                test_case['source_channel'] = original_transcript.get('channel', 'Unknown')
                test_case['generated_at'] = datetime.now().isoformat()
                
                # Ensure test_case_id exists
                if not test_case.get('test_case_id'):
                    channel_short = original_transcript.get('channel', 'UNK')[:3].upper()
                    test_case['test_case_id'] = f"TC_{channel_short}_{index:03d}"
                
                return test_case
            else:
                print("❌ No valid JSON found in AI response")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"Response preview: {ai_response[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Error parsing AI response: {str(e)}")
            return None
    
    def print_generation_summary(self, output_file: str):
        """Print summary of generated test cases"""
        
        try:
            with open(output_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            test_cases = data.get('test_cases', [])
            metadata = data.get('metadata', {})
            
            print(f"\n🎯 TEST CASE GENERATION SUMMARY")
            print("=" * 50)
            print(f"📊 Total Generated: {len(test_cases)}")
            print(f"✅ Success Rate: {metadata.get('success_rate', 'Unknown')}")
            print(f"🤖 Model Used: {metadata.get('model_used', 'Unknown')}")
            
            if test_cases:
                # Show example
                print(f"\n📋 EXAMPLE TEST CASE:")
                print("-" * 40)
                example = test_cases[0]
                print(f"🆔 ID: {example.get('test_case_id', 'Unknown')}")
                print(f"🏢 Domain: {example.get('domain', 'Unknown')}")
                print(f"⚠️ Priority: {example.get('priority', 'Unknown')}")
                print(f"🔍 Issue: {example.get('issue_description', 'Unknown')[:100]}...")
                print(f"🧪 Test: {example.get('test_scenario', 'Unknown')[:100]}...")
                
                # Count priorities
                priorities = {}
                for tc in test_cases:
                    priority = tc.get('priority', 'Unknown')
                    priorities[priority] = priorities.get(priority, 0) + 1
                
                print(f"\n📈 Priority Breakdown:")
                for priority in ['Critical', 'High', 'Medium', 'Low']:
                    count = priorities.get(priority, 0)
                    if count > 0:
                        print(f"  • {priority}: {count}")
                
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")


def test_groq_generator():
    """Test the Groq AI generator"""
    
    # Check for API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ Groq API key not found!")
        print("\n🔑 Get your FREE Groq API key:")
        print("1. Go to: https://console.groq.com/")
        print("2. Sign up (completely free)")
        print("3. Go to API Keys section")
        print("4. Create new API key")
        print("5. Set environment variable: set GROQ_API_KEY=your_api_key_here")
        print("6. Or create .env file with: GROQ_API_KEY=your_api_key_here")
        return
    
    try:
        generator = GroqTestCaseGenerator(api_key)
        
        input_file = 'data/processed/masked_transcripts.json'
        output_file = 'data/output/generated_test_cases.json'
        
        print("🚀 Starting Groq AI test case generation...")
        print("⚡ Groq is much faster than OpenAI!")
        
        success = generator.generate_test_cases(input_file, output_file)
        
        if success:
            generator.print_generation_summary(output_file)
            print(f"\n🎉 SUCCESS! Test cases generated!")
            print(f"📁 Results saved to: {output_file}")
            print(f"🎯 Ready for your QA team!")
        else:
            print("❌ Generation failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_groq_generator()