# FILE: test_conversational_integration.py

import json
import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.append('src')

from src.conversational_ai import ConversationalTestCaseAI

def test_with_existing_test_cases():
    """Test conversational AI with your existing generated test cases"""
    
    print("🧪 Testing Conversational AI with Existing Test Cases")
    print("=" * 60)
    
    # Load existing test cases
    test_cases_data = load_existing_test_cases()
    if not test_cases_data:
        print("❌ No existing test cases found")
        return False
    
    test_cases = test_cases_data.get('test_cases', [])
    if not test_cases:
        print("❌ No test cases in data")
        return False
    
    print(f"✅ Found {len(test_cases)} existing test cases")
    
    # Initialize conversational AI
    try:
        conv_ai = ConversationalTestCaseAI()
        print("✅ Conversational AI initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize conversational AI: {str(e)}")
        return False
    
    # Test with first test case
    test_case = test_cases[0]
    print(f"\n🔍 Testing with test case: {test_case.get('test_case_id', 'Unknown')}")
    print(f"Domain: {test_case.get('domain', 'Unknown')}")
    print(f"Issue: {test_case.get('issue_description', 'Unknown')[:100]}...")
    
    # Test 1: Generate suggested questions
    print("\n1️⃣ Testing suggested questions generation...")
    try:
        suggestions = conv_ai.get_suggested_questions(test_case)
        print(f"✅ Generated {len(suggestions)} suggestions:")
        
        for i, suggestion in enumerate(suggestions[:3], 1):  # Show first 3
            category = suggestion.get('category', 'unknown')
            question = suggestion.get('question', '')
            print(f"   {i}. [{category.upper()}] {question}")
        
        if len(suggestions) > 3:
            print(f"   ... and {len(suggestions) - 3} more")
            
    except Exception as e:
        print(f"❌ Error generating suggestions: {str(e)}")
        return False
    
    # Test 2: Ask specific questions
    print("\n2️⃣ Testing question answering...")
    
    test_questions = [
        "What specific UI elements should be automated for this test case?",
        "What additional edge cases should be considered?",
        "How can we improve the test coverage for this scenario?"
    ]
    
    conversation_history = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   Question {i}: {question}")
        
        try:
            response = conv_ai.ask_question(
                test_case=test_case,
                question=question,
                conversation_history=conversation_history
            )
            
            print(f"   ✅ Response type: {response.get('question_type', 'unknown')}")
            print(f"   📝 Response preview: {response.get('response', '')[:150]}...")
            
            conversation_history.append(response)
            
        except Exception as e:
            print(f"   ❌ Error processing question: {str(e)}")
            continue
    
    # Test 3: Enhanced test case creation
    print("\n3️⃣ Testing test case enhancement...")
    try:
        enhanced_case = conv_ai.enhance_test_case_with_conversation(test_case, conversation_history)
        
        conv_data = enhanced_case.get('conversational_data', {})
        print(f"✅ Enhanced test case created:")
        print(f"   - Conversations: {len(conv_data.get('conversation_history', []))}")
        print(f"   - Summary: {conv_data.get('conversation_summary', 'None')}")
        print(f"   - Insights: {len(conv_data.get('qa_insights', []))}")
        
        # Save enhanced test case for inspection
        save_enhanced_test_case(enhanced_case)
        
    except Exception as e:
        print(f"❌ Error enhancing test case: {str(e)}")
        return False
    
    print(f"\n🎉 All tests completed successfully!")
    return True

def load_existing_test_cases():
    """Load existing test cases from output directory"""
    
    try:
        output_dir = 'data/output'
        if not os.path.exists(output_dir):
            print(f"❌ Output directory not found: {output_dir}")
            return None
        
        # Find test case files
        test_case_files = [f for f in os.listdir(output_dir) 
                          if f.startswith('test_cases_') and f.endswith('.json')]
        
        if not test_case_files:
            print(f"❌ No test case files found in {output_dir}")
            return None
        
        # Load most recent file
        latest_file = sorted(test_case_files)[-1]
        file_path = os.path.join(output_dir, latest_file)
        
        print(f"📂 Loading test cases from: {latest_file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
        
    except Exception as e:
        print(f"❌ Error loading test cases: {str(e)}")
        return None

def save_enhanced_test_case(enhanced_case):
    """Save enhanced test case for inspection"""
    
    try:
        output_dir = 'data/output'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'enhanced_test_case_sample_{timestamp}.json'
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(enhanced_case, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced test case saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving enhanced test case: {str(e)}")

def test_fallback_functionality():
    """Test fallback functionality when API is not available"""
    
    print("\n🔧 Testing Fallback Functionality")
    print("=" * 40)
    
    # Create a mock test case
    mock_test_case = {
        "test_case_id": "TC_MOCK_001",
        "domain": "Web Portal",
        "service": "User Authentication",
        "priority": "High",
        "issue_description": "Users unable to login with special characters in password",
        "test_scenario": "Test login functionality with various password formats"
    }
    
    try:
        # Test with invalid API key to trigger fallback
        conv_ai = ConversationalTestCaseAI("invalid_key")
        
        # This should use fallback questions
        suggestions = conv_ai.get_suggested_questions(mock_test_case)
        
        print(f"✅ Fallback generated {len(suggestions)} questions:")
        for suggestion in suggestions:
            print(f"   - [{suggestion['category']}] {suggestion['question']}")
            
    except Exception as e:
        print(f"❌ Fallback test error: {str(e)}")

def check_environment():
    """Check if environment is properly set up"""
    
    print("🔍 Environment Check")
    print("=" * 30)
    
    # Check API key
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        print(f"✅ GROQ_API_KEY found: {api_key[:10]}...{api_key[-5:]}")
    else:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("   Please set it in your .env file or environment")
        return False
    
    # Check directories
    directories = ['data/output', 'data/processed', 'src']
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
    
    # Check for existing test cases
    output_dir = 'data/output'
    if os.path.exists(output_dir):
        test_files = [f for f in os.listdir(output_dir) 
                     if f.startswith('test_cases_') and f.endswith('.json')]
        print(f"📊 Found {len(test_files)} existing test case files")
        
        if test_files:
            latest = sorted(test_files)[-1]
            print(f"   Latest: {latest}")
    
    return True

def main():
    """Main test execution"""
    
    print("🚀 Conversational AI Integration Test")
    print("=" * 50)
    
    # Environment check
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues above.")
        return
    
    # Test with existing data
    success = test_with_existing_test_cases()
    
    if success:
        print(f"\n✅ Integration test PASSED!")
        print("🎯 Ready to integrate with web application!")
    else:
        print(f"\n❌ Integration test FAILED!")
        print("🔧 Please check the errors above and fix before proceeding.")
    
    # Test fallback
    test_fallback_functionality()

if __name__ == "__main__":
    main()