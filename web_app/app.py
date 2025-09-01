# FILE: web_app/app.py

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import io
import sys
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

# Add src directory to path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

from ai_test_generator import GroqTestCaseGenerator
from transcript_parser import TranscriptParser
from data_cleaner import DataCleaner
from pii_masker import PIIMasker


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'web_app/static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data/output', exist_ok=True)

class TestCaseWebApp:
    def __init__(self):
        self.supported_brands = ['Total Wireless', 'TracFone', 'Straight Talk', 'Simple Mobile']
        self.supported_channels = ['TASORA', 'Web Portal', 'Mobile App', 'Target', 'SMS/Bot/IVR']
        self.supported_categories = [
            'Plan Change', 'Device Activation', 'Billing Dispute', 
            'Device Purchase', 'Account Management', 'Promotional Offers',
            'Data Usage Tracking', 'Device Upgrade', 'Auto-Pay Management',
            'SIM Card Activation', 'Network Coverage', 'Service Commands'
        ]
        
    def load_available_transcripts(self):
        """Load all available transcripts with metadata for filtering"""
        transcript_files = [
            'data/processed/parsed_transcripts.json',
            'data/processed/cleaned_transcripts.json', 
            'data/processed/masked_transcripts.json'
        ]
        
        for file_path in transcript_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('transcripts', [])
        
        return []
    
    def filter_transcripts(self, transcripts, filters):
        """Filter transcripts based on user criteria"""
        filtered = transcripts
        
        if filters.get('channel') and filters['channel'] != 'all':
            filtered = [t for t in filtered if t.get('channel') == filters['channel']]
            
        if filters.get('category') and filters['category'] != 'all':
            filtered = [t for t in filtered if t.get('category') == filters['category']]
            
        if filters.get('severity') and filters['severity'] != 'all':
            filtered = [t for t in filtered if t.get('severity') == filters['severity']]
        
        return filtered
    
    def generate_filtered_test_cases(self, filtered_transcripts, request_id):
        """Generate test cases from filtered transcripts"""
        if not filtered_transcripts:
            return None, "No transcripts match your criteria"
            
        try:
            # Save filtered transcripts temporarily
            temp_file = f'data/output/temp_filtered_{request_id}.json'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'filtered_at': datetime.now().isoformat(),
                        'total_transcripts': len(filtered_transcripts)
                    },
                    'transcripts': filtered_transcripts
                }, f, indent=2)
            
            # Generate test cases
            generator = GroqTestCaseGenerator()
            output_file = f'data/output/test_cases_{request_id}.json'
            
            success = generator.generate_test_cases(temp_file, output_file)
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            if success:
                return output_file, None
            else:
                return None, "Failed to generate test cases"
                
        except Exception as e:
            return None, f"Error generating test cases: {str(e)}"

webapp = TestCaseWebApp()

@app.route('/')
def index():
    """Main dashboard page"""
    transcripts = webapp.load_available_transcripts()
    
    # Get summary statistics
    channels = {}
    categories = {}
    severities = {}
    
    for transcript in transcripts:
        channel = transcript.get('channel', 'Unknown')
        category = transcript.get('category', 'Unknown')
        severity = transcript.get('severity', 'Unknown')
        
        channels[channel] = channels.get(channel, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        severities[severity] = severities.get(severity, 0) + 1
    
    stats = {
        'total_transcripts': len(transcripts),
        'channels': channels,
        'categories': categories,
        'severities': severities
    }
    
    return render_template('index.html', 
                         stats=stats,
                         channels=webapp.supported_channels,
                         categories=webapp.supported_categories)

@app.route('/generate', methods=['POST'])
def generate_test_cases():
    """Generate test cases based on filters"""
    try:
        data = request.json
        filters = {
            'channel': data.get('channel', 'all'),
            'category': data.get('category', 'all'), 
            'severity': data.get('severity', 'all'),
            'brand': data.get('brand', 'all')
        }
        
        # Load and filter transcripts
        all_transcripts = webapp.load_available_transcripts()
        filtered_transcripts = webapp.filter_transcripts(all_transcripts, filters)
        
        if not filtered_transcripts:
            return jsonify({
                'success': False,
                'error': 'No transcripts match your filter criteria'
            })
        
        # Generate unique request ID
        request_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate test cases
        output_file, error = webapp.generate_filtered_test_cases(filtered_transcripts, request_id)
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
        
        # Load generated test cases for preview
        with open(output_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'filtered_count': len(filtered_transcripts),
            'generated_count': len(result_data.get('test_cases', [])),
            'download_url': f'/download/{request_id}',
            'preview': result_data.get('test_cases', [])[:3]  # First 3 for preview
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Generation failed: {str(e)}'
        })

# @app.route('/download/<request_id>')
# def download_test_cases(request_id):
#     """Download generated test cases"""
#     try:
#         file_path = f'data/output/test_cases_{request_id}.json'
#         if os.path.exists(file_path):
#             return send_file(file_path, 
#                            as_attachment=True,
#                            download_name=f'test_cases_{request_id}.json',
#                            mimetype='application/json')
#         else:
#             return "File not found", 404
            
#     except Exception as e:
#         return f"Download error: {str(e)}", 500

@app.route('/download/<request_id>')
def download_test_cases(request_id):
    """Download generated test cases"""
    try:
        # Build correct path
        current_file = os.path.abspath(__file__)
        web_app_dir = os.path.dirname(current_file)
        project_root = os.path.dirname(web_app_dir)
        file_path = os.path.join(project_root, 'data', 'output', f'test_cases_{request_id}.json')
        
        if os.path.exists(file_path):
            return send_file(file_path, 
                           as_attachment=True,
                           download_name=f'test_cases_{request_id}.txt',
                           mimetype='text/plain')

        else:
            return "File not found", 404
            
    except Exception as e:
        return f"Download error: {str(e)}", 500


# @app.route('/download/<request_id>')
# def download_test_cases(request_id):
#     """Download generated test cases as a real .xlsx workbook"""
#     try:
#         current_file = os.path.abspath(__file__)
#         web_app_dir = os.path.dirname(current_file)
#         project_root = os.path.dirname(web_app_dir)
#         json_path = os.path.join(project_root, 'data', 'output', f'test_cases_{request_id}.json')

#         if not os.path.exists(json_path):
#             return "File not found", 404

#         # Load JSON
#         with open(json_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)

#         test_cases = data.get('test_cases', [])
#         if not isinstance(test_cases, list):
#             test_cases = []

#         # Flatten rows for Excel. Adjust keys to match your schema.
#         rows = []
#         for tc in test_cases:
#             rows.append({
#                 'id': tc.get('id'),
#                 'title': tc.get('title'),
#                 'brand': tc.get('brand'),
#                 'category': tc.get('category'),
#                 'channel': tc.get('channel'),
#                 'severity': tc.get('severity'),
#                 'preconditions': '\n'.join(tc.get('preconditions', [])) if isinstance(tc.get('preconditions'), list) else tc.get('preconditions'),
#                 'steps': '\n'.join([s.get('step', str(s)) for s in tc.get('steps', [])]) if isinstance(tc.get('steps'), list) else tc.get('steps'),
#                 'expected_result': tc.get('expected_result'),
#                 'notes': tc.get('notes'),
#             })

#         df = pd.DataFrame(rows)

#         # Write to an in-memory .xlsx
#         output = io.BytesIO()
#         with pd.ExcelWriter(output, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False, sheet_name='TestCases')
#         output.seek(0)

#         return send_file(
#             output,
#             as_attachment=True,
#             download_name=f'test_cases_{request_id}.xlsx',
#             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#         )

#     except Exception as e:
#         return f"Download error: {str(e)}", 500



# @app.route('/download/<request_id>')
# def download_test_cases(request_id):
#     """Download generated test cases"""
#     try:
#         # Build correct path relative to the app.py file
#         current_file = os.path.abspath(__file__)
#         web_app_dir = os.path.dirname(current_file)
#         project_root = os.path.dirname(web_app_dir)
#         file_path = os.path.join(project_root, 'data', 'output', f'test_cases_{request_id}.json')
        
#         print(f"Looking for file at: {file_path}")  # Debug logging
        
#         if os.path.exists(file_path):
#             return send_file(
#                 file_path, 
#                 as_attachment=True,
#                 download_name=f'test_cases_{request_id}.json',
#                 mimetype='application/json'
#             )
#         else:
#             print(f"File not found: {file_path}")
#             # List files in output directory for debugging
#             output_dir = os.path.join(project_root, 'data', 'output')
#             if os.path.exists(output_dir):
#                 files = os.listdir(output_dir)
#                 print(f"Available files: {files}")
#             return f"File not found: test_cases_{request_id}.json", 404
            
#     except Exception as e:
#         print(f"Download error: {str(e)}")
#         return f"Download error: {str(e)}", 500

@app.route('/upload', methods=['POST'])
def upload_transcripts():
    """Upload new transcript files for processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and file.filename.lower().endswith(('.pdf', '.txt', '.json')):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the uploaded file
            parser = TranscriptParser()
            
            if filename.lower().endswith('.pdf'):
                parsed_data = parser.parse_pdf(file_path)
            else:
                parsed_data = parser.parse_text_file(file_path)
            
            if parsed_data:
                # Clean and mask the data
                temp_parsed = f'data/processed/temp_parsed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                parser.save_parsed_data(parsed_data, temp_parsed)
                
                cleaner = DataCleaner()
                temp_cleaned = temp_parsed.replace('parsed', 'cleaned')
                cleaner.clean_parsed_data(temp_parsed, temp_cleaned)
                
                masker = PIIMasker()
                temp_masked = temp_parsed.replace('parsed', 'masked')
                masker.mask_data(temp_cleaned, temp_masked)
                
                # Clean up temp files
                for temp_file in [temp_parsed, temp_cleaned]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                return jsonify({
                    'success': True,
                    'message': f'Processed {len(parsed_data)} transcripts',
                    'transcripts': len(parsed_data)
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to parse file'})
        else:
            return jsonify({'success': False, 'error': 'Invalid file type. Use PDF, TXT, or JSON'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    transcripts = webapp.load_available_transcripts()
    
    return jsonify({
        'total_transcripts': len(transcripts),
        'channels': list(set(t.get('channel', 'Unknown') for t in transcripts)),
        'categories': list(set(t.get('category', 'Unknown') for t in transcripts if t.get('category'))),
        'recent_uploads': []  # Could track recent uploads here
    })

if __name__ == '__main__':
    print("Starting QA Test Case Generator Web App...")
    print("Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)