# FILE: web_app/app_fixed.py
# Enhanced Flask app that works with your existing HTML template

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
from src.conversational_ai import ConversationalTestCaseAI

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
        conversational_ai = ConversationalTestCaseAI(api_key)
        
        print("✅ Both AI components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing AI: {str(e)}")
        return False

# Initialize AI components at startup
ai_available = initialize_ai_components()

def load_existing_data():
    """Load existing transcripts and test cases for the template"""
    
    try:
        # Try to load existing processed data
        if os.path.exists('../data/processed'):
            processed_dir = '../data/processed'
        elif os.path.exists('data/processed'):
            processed_dir = 'data/processed'
        else:
            return get_default_template_data()
        
        # Look for transcript files
        transcript_files = ['masked_transcripts.json', 'cleaned_transcripts.json', 'parsed_transcripts.json']
        transcripts = []
        
        for filename in transcript_files:
            file_path = os.path.join(processed_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data structures
                if isinstance(data, list):
                    transcripts = data
                elif isinstance(data, dict):
                    transcripts = data.get('transcripts', [])
                
                if transcripts:
                    break
        
        if not transcripts:
            return get_default_template_data()
        
        # Calculate statistics
        stats = calculate_template_stats(transcripts)
        
        # Extract unique values for dropdowns
        channels = list(set(t.get('channel', 'Unknown') for t in transcripts))
        categories = list(set(t.get('category', 'Unknown') for t in transcripts))
        
        return {
            'stats': stats,
            'channels': channels,
            'categories': categories,
            'transcripts': transcripts
        }
        
    except Exception as e:
        print(f"❌ Error loading existing data: {str(e)}")
        return get_default_template_data()

def get_default_template_data():
    """Return default data when no transcripts are available"""
    return {
        'stats': {
            'total_transcripts': 0,
            'channels': {},
            'severities': {}
        },
        'channels': ['Web Portal', 'Mobile App', 'TASORA'],
        'categories': ['Device Activation', 'Plan Management', 'Billing'],
        'transcripts': []
    }

# def calculate_template_stats(transcripts):
#     """Calculate statistics for the template"""
    
#     stats = {
#         'total_transcripts': len(transcripts),
#         'channels': {},
#         'severities': {}
#     }
    
#     # Count by channel
#     for transcript in transcripts:
#         channel = transcript.get('channel', 'Unknown')
#         stats['channels'][channel] = stats['channels'].get(channel, 0) + 1
    
#     # Count by severity
#     for transcript in transcripts:
#         severity = transcript.get('severity', 'Medium')
#         stats['severities'][severity] = stats['severities'].get(severity, 0) + 1
    
#     return stats

# def calculate_template_stats(transcripts):
#     """Calculate statistics for the template"""
    
#     stats = {
#         'total_transcripts': len(transcripts),
#         'channels': {},
#         'severities': {}
#     }
    
#     # Initialize all expected severity levels with 0
#     stats['severities'] = {
#         'High': 0,
#         'Medium': 0,
#         'Low': 0
#     }
    
#     # Count by channel
#     for transcript in transcripts:
#         channel = transcript.get('channel', 'Unknown')
#         stats['channels'][channel] = stats['channels'].get(channel, 0) + 1
    
#     # Count by severity
#     for transcript in transcripts:
#         severity = transcript.get('severity', 'Medium')
#         if severity in stats['severities']:
#             stats['severities'][severity] += 1
#         else:
#             # Handle any unexpected severity values
#             stats['severities'][severity] = stats['severities'].get(severity, 0) + 1
    
#     return stats

def calculate_template_stats(transcripts):
    """Calculate statistics for the template"""
    
    # DEBUG: Let's see all severity values
    all_severities = []
    for transcript in transcripts:
        severity = transcript.get('severity', 'Unknown')
        all_severities.append(f"'{severity}'")
    
    print(f"DEBUG: All severity values found: {set(all_severities)}")
    
    stats = {
        'total_transcripts': len(transcripts),
        'channels': {},
        'severities': {}
    }
    
    # Initialize all expected severity levels with 0
    stats['severities'] = {
        'High': 0,
        'Medium': 0,
        'Low': 0
    }
    
    # Count by channel
    for transcript in transcripts:
        channel = transcript.get('channel', 'Unknown')
        stats['channels'][channel] = stats['channels'].get(channel, 0) + 1
    
    # Count by severity
    for transcript in transcripts:
        severity = transcript.get('severity', 'Medium')
        if severity in stats['severities']:
            stats['severities'][severity] += 1
        else:
            stats['severities'][severity] = stats['severities'].get(severity, 0) + 1
    
    print(f"DEBUG: Final severity counts: {stats['severities']}")
    
    return stats

# =================== ROUTES THAT YOUR HTML EXPECTS ===================

@app.route('/')
def index():
    """Main dashboard - matches your HTML template expectations"""
    
    template_data = load_existing_data()
    
    return render_template('index.html', 
                         stats=template_data['stats'],
                         channels=template_data['channels'],
                         categories=template_data['categories'])

# @app.route('/generate', methods=['POST'])
# def generate():
#     """Generate test cases - matches your HTML form submission"""
    
#     try:
#         data = request.get_json()
        
#         # Get filters from the request
#         channel_filter = data.get('channel', 'all')
#         category_filter = data.get('category', 'all')
#         severity_filter = data.get('severity', 'all')
#         brand_filter = data.get('brand', 'all')
        
#         print(f"🔍 Generating test cases with filters: {data}")
        
#         # Load and filter transcripts
#         template_data = load_existing_data()
#         transcripts = template_data['transcripts']
        
#         if not transcripts:
#             return jsonify({
#                 'success': False,
#                 'error': 'No transcripts available. Please upload some transcript files first.'
#             })
        
#         # Apply filters
#         filtered_transcripts = filter_transcripts(transcripts, data)
        
#         if not filtered_transcripts:
#             return jsonify({
#                 'success': False,
#                 'error': 'No transcripts match your filters. Try different filter criteria.'
#             })
        
#         if not ai_available:
#             return jsonify({
#                 'success': False,
#                 'error': 'AI test generator is not available. Check your GROQ_API_KEY.'
#             })
        
#         # Generate test cases
#         request_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         # Save filtered data to temporary file
#         temp_file = f'../data/processed/filtered_{request_id}.json'
#         os.makedirs('../data/processed', exist_ok=True)
        
#         with open(temp_file, 'w', encoding='utf-8') as f:
#             json.dump(filtered_transcripts, f, indent=2, ensure_ascii=False)
        
#         # Generate test cases
#         output_file = f'../data/output/test_cases_{request_id}.json'
#         os.makedirs('../data/output', exist_ok=True)
        
#         success = test_generator.generate_test_cases(temp_file, output_file)
        
#         if not success:
#             return jsonify({
#                 'success': False,
#                 'error': 'Failed to generate test cases. Please try again.'
#             })
        
#         # Load generated test cases for preview
#         with open(output_file, 'r', encoding='utf-8') as f:
#             results = json.load(f)
        
#         test_cases = results.get('test_cases', [])
        
#         # Initialize conversational data for new test cases
#         initialize_conversational_data_for_file(request_id)
        
#         return jsonify({
#             'success': True,
#             'generated_count': len(test_cases),
#             'filtered_count': len(filtered_transcripts),
#             'download_url': f'/download/{request_id}',
#             'preview': test_cases[:3]  # First 3 test cases for preview
#         })
        
#     except Exception as e:
#         print(f"❌ Generate error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': f'Generation failed: {str(e)}'
#         })

# REPLACE the /generate route in your app_fixed.py with this corrected version:

@app.route('/generate', methods=['POST'])
def generate():
    """Generate test cases - with fixed data format handling"""
    
    try:
        data = request.get_json()
        
        # Get filters from the request
        channel_filter = data.get('channel', 'all')
        category_filter = data.get('category', 'all')
        severity_filter = data.get('severity', 'all')
        brand_filter = data.get('brand', 'all')
        
        print(f"🔍 Generating test cases with filters: {data}")
        
        # Load and filter transcripts
        template_data = load_existing_data()
        transcripts = template_data['transcripts']
        
        if not transcripts:
            return jsonify({
                'success': False,
                'error': 'No transcripts available. Please upload some transcript files first.'
            })
        
        # Apply filters
        filtered_transcripts = filter_transcripts(transcripts, data)
        
        if not filtered_transcripts:
            return jsonify({
                'success': False,
                'error': 'No transcripts match your filters. Try different filter criteria.'
            })
        
        if not ai_available:
            return jsonify({
                'success': False,
                'error': 'AI test generator is not available. Check your GROQ_API_KEY.'
            })
        
        # Generate test cases
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # FIXED: Save filtered data in the correct format that AI generator expects
        temp_file = f'../data/processed/filtered_{request_id}.json'
        os.makedirs('../data/processed', exist_ok=True)
        
        # The AI generator expects the data in this specific format
        filtered_data = {
            "transcripts": filtered_transcripts,
            "metadata": {
                "total_transcripts": len(filtered_transcripts),
                "filter_applied": data,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(filtered_transcripts)} filtered transcripts to: {temp_file}")
        
        # Generate test cases
        output_file = f'../data/output/test_cases_{request_id}.json'
        os.makedirs('../data/output', exist_ok=True)
        
        success = test_generator.generate_test_cases(temp_file, output_file)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to generate test cases. Please try again.'
            })
        
        # Load generated test cases for preview
        with open(output_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        test_cases = results.get('test_cases', [])
        
        if not test_cases:
            return jsonify({
                'success': False,
                'error': 'No test cases were generated from the filtered transcripts.'
            })
        
        # Initialize conversational data for new test cases
        initialize_conversational_data_for_file(request_id)
        
        print(f"✅ Successfully generated {len(test_cases)} test cases")
        
        return jsonify({
            'success': True,
            'generated_count': len(test_cases),
            'filtered_count': len(filtered_transcripts),
            'download_url': f'/download/{request_id}',
            'preview': test_cases[:3]  # First 3 test cases for preview
        })
        
    except Exception as e:
        print(f"❌ Generate error: {str(e)}")
        import traceback
        traceback.print_exc()  # This will help us see the full error
        return jsonify({
            'success': False,
            'error': f'Generation failed: {str(e)}'
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            request_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save uploaded file
            upload_path = os.path.join('static', 'uploads', filename)
            os.makedirs('static/uploads', exist_ok=True)
            file.save(upload_path)
            
            # Process through pipeline
            success = process_transcript_pipeline(upload_path, request_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'File processed successfully. Request ID: {request_id}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to process the uploaded file.'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload PDF, TXT, or JSON files.'
            })
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        })

@app.route('/download/<request_id>')
def download_test_cases(request_id):
    """Download generated test cases"""
    
    try:
        # Build correct path
        if os.path.exists('../data/output'):
            output_dir = '../data/output'
        elif os.path.exists('data/output'):
            output_dir = 'data/output'
        else:
            return "Output directory not found", 404
        
        file_path = os.path.join(output_dir, f'test_cases_{request_id}.json')
        
        if os.path.exists(file_path):
            return send_file(file_path, 
                           as_attachment=True,
                           download_name=f'test_cases_{request_id}.json',
                           mimetype='application/json')
        else:
            return "File not found", 404
            
    except Exception as e:
        return f"Download error: {str(e)}", 500

# =================== NEW CONVERSATIONAL AI ENDPOINTS ===================

@app.route('/api/ask_question', methods=['POST'])
def ask_question():
    """Handle conversational questions about test cases"""
    
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
    """Get AI-suggested questions for a test case"""
    
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

@app.route('/export_conversations/<test_case_id>')
def export_conversations(test_case_id):
    """Export conversations for a specific test case"""
    
    try:
        test_case, _ = load_test_case_with_context(test_case_id)
        
        if not test_case:
            return "Test case not found", 404
        
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
        temp_dir = 'static/temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f'conversations_{test_case_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"❌ Error exporting conversations: {str(e)}")
        return "Export failed", 500

# =================== HELPER FUNCTIONS ===================

def filter_transcripts(transcripts, filters):
    """Filter transcripts based on the provided criteria"""
    
    filtered = transcripts
    
    # Apply channel filter
    if filters.get('channel') != 'all':
        filtered = [t for t in filtered if t.get('channel') == filters['channel']]
    
    # Apply category filter
    if filters.get('category') != 'all':
        filtered = [t for t in filtered if t.get('category') == filters['category']]
    
    # Apply severity filter
    if filters.get('severity') != 'all':
        filtered = [t for t in filtered if t.get('severity') == filters['severity']]
    
    # Apply brand filter (if available in data)
    if filters.get('brand') != 'all':
        filtered = [t for t in filtered if t.get('brand') == filters['brand']]
    
    return filtered

def load_test_case_with_context(test_case_id):
    """Load a specific test case with its original transcript context"""
    
    try:
        # Load latest test cases
        if os.path.exists('../data/output'):
            output_dir = '../data/output'
        elif os.path.exists('data/output'):
            output_dir = 'data/output'
        else:
            return None, None
        
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
        if os.path.exists('../data/processed'):
            processed_dir = '../data/processed'
        elif os.path.exists('data/processed'):
            processed_dir = 'data/processed'
        else:
            return None
            
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
        if os.path.exists('../data/output'):
            output_dir = '../data/output'
        elif os.path.exists('data/output'):
            output_dir = 'data/output'
        else:
            return False
            
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
        if os.path.exists('../data/output'):
            output_dir = '../data/output'
        elif os.path.exists('data/output'):
            output_dir = 'data/output'
        else:
            return False
            
        file_path = os.path.join(output_dir, f'test_cases_{request_id}.json')
        
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
        
        # Ensure directories exist
        os.makedirs('../data/processed', exist_ok=True)
        os.makedirs('../data/output', exist_ok=True)
        
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
        
        print("✅ File processing completed successfully")
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