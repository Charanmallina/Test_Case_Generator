# FILE: web_app/app_with_conversations.py
# Enhanced version of your Flask app with conversational AI endpoints

import os
import json
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
from werkzeug.utils import secure_filename

# Add the parent directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.transcript_parser import TranscriptParser
from src.data_cleaner import DataCleaner
from src.pii_masker import PIIMasker
from src.ai_test_generator import GroqTestCaseGenerator
from src.conversational_ai import ConversationalTestCaseAI  # NEW IMPORT

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global AI components
test_generator = None
conversational_ai = None

def initialize_ai_components():
    """Initialize AI components with error handling"""
    global test_generator, conversational_ai
    
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("⚠️ GROQ_API_KEY not found - AI features will be limited")
            return False
        
        test_generator = GroqTestCaseGenerator(api_key)
        conversational_ai = ConversationalTestCaseAI(api_key)  # NEW COMPONENT
        
        print("✅ Both AI components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing AI: {str(e)}")
        return False

# Initialize AI components at startup
ai_available = initialize_ai_components()

# =================== EXISTING ROUTES (UNCHANGED) ===================

# 
# QUICK FIX: Update the path handling in your app_enhanced.py

# Replace the index() function in your app_enhanced.py with this version:

@app.route('/')
def index():
    """Main dashboard - now with conversational stats"""
    
    # Load existing test cases
    try:
        # Fix path - check if running from web_app directory or root
        if os.path.exists('data/output'):
            output_dir = 'data/output'  # Running from root
        elif os.path.exists('../data/output'):
            output_dir = '../data/output'  # Running from web_app
        else:
            print("❌ No data/output directory found")
            return render_template('index.html', test_cases=[], stats={})
        
        test_case_files = [f for f in os.listdir(output_dir) if f.startswith('test_cases_')]
        
        if test_case_files:
            latest_file = sorted(test_case_files)[-1]
            file_path = os.path.join(output_dir, latest_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_cases = data.get('test_cases', [])
            
            # Calculate enhanced statistics including conversational data
            stats = calculate_enhanced_statistics(test_cases)
            
            return render_template('index.html', test_cases=test_cases, stats=stats)
        
    except Exception as e:
        print(f"Error loading test cases: {str(e)}")
    
    # Fallback for empty state
    return render_template('index.html', test_cases=[], stats={})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            request_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save uploaded file
            upload_path = os.path.join('static', 'uploads', filename)
            file.save(upload_path)
            
            # Process through pipeline
            success = process_transcript_pipeline(upload_path, request_id)
            
            if success:
                # Initialize conversational data for new test cases
                initialize_conversational_data_for_file(request_id)
                flash(f'File processed successfully! Request ID: {request_id}', 'success')
            else:
                flash('Error processing file', 'error')
                
        except Exception as e:
            flash(f'Upload error: {str(e)}', 'error')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('index'))

@app.route('/download/<request_id>')
def download_test_cases(request_id):
    """Download test cases with optional conversational data"""
    
    try:
        current_file = os.path.abspath(__file__)
        web_app_dir = os.path.dirname(current_file)
        project_root = os.path.dirname(web_app_dir)
        file_path = os.path.join(project_root, 'data', 'output', f'test_cases_{request_id}.json')
        
        if os.path.exists(file_path):
            # Check if enhanced download is requested
            include_conversations = request.args.get('conversations', 'false').lower() == 'true'
            
            if include_conversations:
                download_name = f'enhanced_test_cases_{request_id}.json'
            else:
                download_name = f'test_cases_{request_id}.json'
            
            return send_file(file_path, 
                           as_attachment=True,
                           download_name=download_name,
                           mimetype='application/json')
        else:
            return "File not found", 404
            
    except Exception as e:
        return f"Download error: {str(e)}", 500

# =================== NEW CONVERSATIONAL ROUTES ===================

@app.route('/api/ask_question', methods=['POST'])
def ask_question():
    """NEW ENDPOINT: Handle conversational questions about test cases"""
    
    if not ai_available or not conversational_ai:
        return jsonify({'error': 'Conversational AI not available'}), 503
    
    try:
        data = request.get_json()
        test_case_id = data.get('test_case_id')
        question = data.get('question')
        
        if not test_case_id or not question:
            return jsonify({'error': 'Missing test_case_id or question'}), 400
        
        # Load test case and context
        test_case, original_transcript = load_test_case_with_context(test_case_id)
        
        if not test_case:
            return jsonify({'error': 'Test case not found'}), 404
        
        # Get conversation history
        conversation_history = test_case.get('conversational_data', {}).get('conversation_history', [])
        
        # Process the question
        response = conversational_ai.ask_question(
            test_case=test_case,
            question=question,
            original_transcript=original_transcript,
            conversation_history=conversation_history
        )
        
        # Save conversation to test case
        if save_conversation_to_test_case(test_case_id, response):
            return jsonify({
                'success': True, 
                'response': response,
                'conversation_count': len(conversation_history) + 1
            })
        else:
            return jsonify({'error': 'Failed to save conversation'}), 500
        
    except Exception as e:
        print(f"❌ Error processing question: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/suggestions/<test_case_id>')
def get_suggested_questions(test_case_id):
    """NEW ENDPOINT: Get AI-suggested questions for a test case"""
    
    if not ai_available or not conversational_ai:
        return jsonify({'error': 'Conversational AI not available'}), 503
    
    try:
        # Load test case data
        test_case, original_transcript = load_test_case_with_context(test_case_id)
        
        if not test_case:
            return jsonify({'error': 'Test case not found'}), 404
        
        # Generate suggestions
        suggestions = conversational_ai.get_suggested_questions(test_case, original_transcript)
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        print(f"❌ Error getting suggestions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation_history/<test_case_id>')
def get_conversation_history(test_case_id):
    """NEW ENDPOINT: Get conversation history for a test case"""
    
    try:
        test_case, _ = load_test_case_with_context(test_case_id)
        
        if not test_case:
            return jsonify({'error': 'Test case not found'}), 404
        
        conv_data = test_case.get('conversational_data', {})
        
        return jsonify({
            'conversation_history': conv_data.get('conversation_history', []),
            'conversation_summary': conv_data.get('conversation_summary', ''),
            'qa_insights': conv_data.get('qa_insights', []),
            'last_updated': conv_data.get('last_updated', '')
        })
        
    except Exception as e:
        print(f"❌ Error getting conversation history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch_questions', methods=['POST'])
def batch_questions():
    """NEW ENDPOINT: Process multiple questions at once"""
    
    if not ai_available or not conversational_ai:
        return jsonify({'error': 'Conversational AI not available'}), 503
    
    try:
        data = request.get_json()
        test_case_id = data.get('test_case_id')
        questions = data.get('questions', [])
        
        if not test_case_id or not questions:
            return jsonify({'error': 'Missing test_case_id or questions'}), 400
        
        # Load test case data
        test_case, original_transcript = load_test_case_with_context(test_case_id)
        
        if not test_case:
            return jsonify({'error': 'Test case not found'}), 404
        
        responses = []
        conversation_history = test_case.get('conversational_data', {}).get('conversation_history', [])
        
        # Process each question
        for question in questions:
            response = conversational_ai.ask_question(
                test_case=test_case,
                question=question,
                original_transcript=original_transcript,
                conversation_history=conversation_history
            )
            
            responses.append(response)
            conversation_history.append(response)
            
            # Save each conversation entry
            save_conversation_to_test_case(test_case_id, response)
        
        return jsonify({
            'success': True, 
            'responses': responses,
            'total_conversations': len(conversation_history)
        })
        
    except Exception as e:
        print(f"❌ Error processing batch questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/export_conversations/<test_case_id>')
def export_conversations(test_case_id):
    """NEW ENDPOINT: Export conversations for a specific test case"""
    
    try:
        test_case, _ = load_test_case_with_context(test_case_id)
        
        if not test_case:
            flash('Test case not found', 'error')
            return redirect(url_for('index'))
        
        # Extract conversational data
        conv_data = test_case.get('conversational_data', {})
        
        # Create export data
        export_data = {
            'test_case_summary': {
                'test_case_id': test_case_id,
                'domain': test_case.get('domain', 'Unknown'),
                'service': test_case.get('service', 'Unknown'),
                'priority': test_case.get('priority', 'Unknown'),
                'issue_description': test_case.get('issue_description', 'Unknown')
            },
            'export_metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_questions': len(conv_data.get('conversation_history', [])),
                'conversation_summary': conv_data.get('conversation_summary', '')
            },
            'conversations': conv_data.get('conversation_history', []),
            'qa_insights': conv_data.get('qa_insights', [])
        }
        
        # Save to temporary file
        temp_dir = os.path.join('static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f'conversations_{test_case_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ Error exporting conversations: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('index'))

# =================== NEW HELPER FUNCTIONS ===================

# def calculate_enhanced_statistics(test_cases):
#     """Calculate statistics including conversational data"""
    
#     basic_stats = {
#         'total_test_cases': len(test_cases),
#         'high_priority': len([tc for tc in test_cases if tc.get('priority') == 'High']),
#         'critical_priority': len([tc for tc in test_cases if tc.get('priority') == 'Critical']),
#         'channels': len(set(tc.get('source_channel', 'Unknown') for tc in test_cases))
#     }
    
#     # Enhanced conversational statistics
#     cases_with_conv = 0
#     total_questions = 0
#     automation_qs = 0
#     edge_case_qs = 0
    
#     for tc in test_cases:
#         conv_data = tc.get('conversational_data', {})
#         conversations = conv_data.get('conversation_history', [])
        
#         if conversations:
#             cases_with_conv += 1
#             total_questions += len(conversations)
            
#             for conv in conversations:
#                 q_type = conv.get('question_type', '')
#                 if q_type == 'automation':
#                     automation_qs += 1
#                 elif q_type == 'edge_case':
#                     edge_case_qs += 1
    
#     conv_stats = {
#         'cases_with_conversations': cases_with_conv,
#         'total_questions': total_questions,
#         'automation_questions': automation_qs,
#         'edge_case_questions': edge_case_qs,
#         'avg_questions_per_case': round(total_questions / len(test_cases), 1) if test_cases else 0,
#         'conversation_coverage': round((cases_with_conv / len(test_cases)) * 100, 1) if test_cases else 0
#     }
    
#     return {**basic_stats, **conv_stats}

# QUICK FIX: Replace the calculate_enhanced_statistics function in your app_enhanced.py

def calculate_enhanced_statistics(test_cases):
    """Calculate statistics including conversational data - FIXED VERSION"""
    
    # Handle empty case
    if not test_cases:
        return {
            'total_test_cases': 0,
            'high_priority': 0,
            'critical_priority': 0,
            'channels': 0,
            'cases_with_conversations': 0,
            'total_questions': 0,
            'automation_questions': 0,
            'edge_case_questions': 0,
            'avg_questions_per_case': 0,
            'conversation_coverage': 0
        }
    
    # Basic statistics
    basic_stats = {
        'total_test_cases': len(test_cases),
        'high_priority': len([tc for tc in test_cases if tc.get('priority') == 'High']),
        'critical_priority': len([tc for tc in test_cases if tc.get('priority') == 'Critical']),
        'channels': len(set(tc.get('source_channel', 'Unknown') for tc in test_cases))
    }
    
    # Enhanced conversational statistics
    cases_with_conv = 0
    total_questions = 0
    automation_qs = 0
    edge_case_qs = 0
    
    for tc in test_cases:
        conv_data = tc.get('conversational_data', {})
        conversations = conv_data.get('conversation_history', [])
        
        if conversations:
            cases_with_conv += 1
            total_questions += len(conversations)
            
            for conv in conversations:
                q_type = conv.get('question_type', '')
                if q_type == 'automation':
                    automation_qs += 1
                elif q_type == 'edge_case':
                    edge_case_qs += 1
    
    conv_stats = {
        'cases_with_conversations': cases_with_conv,
        'total_questions': total_questions,
        'automation_questions': automation_qs,
        'edge_case_questions': edge_case_qs,
        'avg_questions_per_case': round(total_questions / len(test_cases), 1) if test_cases else 0,
        'conversation_coverage': round((cases_with_conv / len(test_cases)) * 100, 1) if test_cases else 0
    }
    
    return {**basic_stats, **conv_stats}

def load_test_case_with_context(test_case_id):
    """Load a specific test case with its original transcript context"""
    
    try:
        # Load latest test cases
        output_dir = os.path.join('..', 'data', 'output')
        test_case_files = [f for f in os.listdir(output_dir) if f.startswith('test_cases_')]
        
        if not test_case_files:
            return None, None
        
        latest_file = sorted(test_case_files)[-1]
        file_path = os.path.join(output_dir, latest_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = data.get('test_cases', [])
        
        # Find the specific test case
        test_case = None
        for tc in test_cases:
            if tc.get('test_case_id') == test_case_id:
                test_case = tc
                break
        
        if not test_case:
            return None, None
        
        # Load original transcript if available
        source_call_id = test_case.get('source_call_id')
        original_transcript = None
        
        if source_call_id:
            original_transcript = load_original_transcript(source_call_id)
        
        return test_case, original_transcript
        
    except Exception as e:
        print(f"❌ Error loading test case: {str(e)}")
        return None, None

def load_original_transcript(call_id):
    """Load original transcript for context"""
    
    try:
        processed_dir = os.path.join('..', 'data', 'processed')
        transcript_files = ['masked_transcripts.json', 'cleaned_transcripts.json']
        
        for filename in transcript_files:
            file_path = os.path.join(processed_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                transcripts = data if isinstance(data, list) else data.get('transcripts', [])
                
                for transcript in transcripts:
                    if transcript.get('call_id') == call_id:
                        return transcript
        
        return None
        
    except Exception as e:
        print(f"❌ Error loading transcript: {str(e)}")
        return None

def save_conversation_to_test_case(test_case_id, conversation_entry):
    """Save a conversation entry to the test case data"""
    
    try:
        # Load existing test cases
        output_dir = os.path.join('..', 'data', 'output')
        test_case_files = [f for f in os.listdir(output_dir) if f.startswith('test_cases_')]
        
        if not test_case_files:
            return False
        
        latest_file = sorted(test_case_files)[-1]
        file_path = os.path.join(output_dir, latest_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = data.get('test_cases', [])
        
        # Find and update the test case
        for tc in test_cases:
            if tc.get('test_case_id') == test_case_id:
                # Initialize conversational data if not exists
                if 'conversational_data' not in tc:
                    tc['conversational_data'] = {
                        'conversation_history': [],
                        'qa_insights': [],
                        'additional_context': '',
                        'conversation_summary': ''
                    }
                
                # Add new conversation entry
                tc['conversational_data']['conversation_history'].append(conversation_entry)
                
                # Update summary
                conv_history = tc['conversational_data']['conversation_history']
                automation_count = len([c for c in conv_history if c.get('question_type') == 'automation'])
                edge_case_count = len([c for c in conv_history if c.get('question_type') == 'edge_case'])
                
                tc['conversational_data']['conversation_summary'] = f"Total questions: {len(conv_history)} (Automation: {automation_count}, Edge cases: {edge_case_count})"
                tc['conversational_data']['last_updated'] = datetime.now().isoformat()
                
                break
        
        # Save updated data back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving conversation: {str(e)}")
        return False

def initialize_conversational_data_for_file(request_id):
    """Initialize conversational data structure for newly generated test cases"""
    
    try:
        file_path = os.path.join('..', 'data', 'output', f'test_cases_{request_id}.json')
        
        if not os.path.exists(file_path):
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add conversational data structure to each test case
        test_cases = data.get('test_cases', [])
        for tc in test_cases:
            if 'conversational_data' not in tc:
                tc['conversational_data'] = {
                    'conversation_history': [],
                    'qa_insights': [],
                    'additional_context': '',
                    'conversation_summary': 'No conversations yet',
                    'created_at': datetime.now().isoformat()
                }
        
        # Save enhanced data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing conversational data: {str(e)}")
        return False

# =================== EXISTING HELPER FUNCTIONS (UNCHANGED) ===================

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'json'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_transcript_pipeline(file_path, request_id):
    """Process uploaded file through the pipeline"""
    
    if not ai_available or not test_generator:
        print("❌ Test generator not available")
        return False
    
    try:
        # Initialize processors
        parser = TranscriptParser()
        cleaner = DataCleaner()
        masker = PIIMasker()
        
        # Process through pipeline
        print("🔍 Parsing transcripts...")
        parsed_file = f'../data/processed/parsed_{request_id}.json'
        if not parser.process_pdf(file_path, parsed_file):
            return False
        
        print("🧹 Cleaning data...")
        cleaned_file = f'../data/processed/cleaned_{request_id}.json'
        if not cleaner.process_transcripts(parsed_file, cleaned_file):
            return False
        
        print("🔒 Masking PII...")
        masked_file = f'../data/processed/masked_{request_id}.json'
        if not masker.mask_transcripts(cleaned_file, masked_file):
            return False
        
        print("🤖 Generating test cases...")
        output_file = f'../data/output/test_cases_{request_id}.json'
        if not test_generator.generate_test_cases(masked_file, output_file):
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline error: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Starting Enhanced Test Case Generator with Conversational AI...")
    
    # Check for required directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/temp', exist_ok=True)
    
    if ai_available:
        print("✅ All AI components ready - conversational features enabled")
    else:
        print("⚠️ Limited AI functionality - check GROQ_API_KEY")
    
    app.run(debug=True, host='0.0.0.0', port=5000)