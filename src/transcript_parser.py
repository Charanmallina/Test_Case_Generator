# FILE: src/transcript_parser.py

import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any
import PyPDF2

class TranscriptParser:
    """Parse customer support transcripts from PDF files"""
    
    def __init__(self):
        print("📋 Transcript Parser initialized")
        
    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse transcript data from PDF file
        
        Args:
            file_path: Path to PDF file (e.g., 'data/data.pdf')
            
        Returns:
            List of parsed transcript dictionaries
        """
        print(f"📖 Reading PDF: {file_path}")
        
        try:
            # Extract text from PDF
            pdf_text = self._extract_pdf_text(file_path)
            
            if not pdf_text:
                print("❌ No text extracted from PDF")
                return []
                
            print(f"📝 Extracted {len(pdf_text)} characters from PDF")
            
            # Parse the extracted text
            parsed_calls = self._parse_text_content(pdf_text)
            
            return parsed_calls
            
        except Exception as e:
            print(f"❌ Error parsing PDF: {str(e)}")
            return []
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract all text from PDF"""
        try:
            pdf_text = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print(f"📄 PDF has {total_pages} pages")
                
                for page_num in range(total_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        pdf_text += page_text + "\n"
                        print(f"✅ Extracted page {page_num + 1}/{total_pages}")
                    except Exception as e:
                        print(f"⚠️ Error on page {page_num + 1}: {str(e)}")
                        
            return pdf_text
            
        except Exception as e:
            print(f"❌ PDF extraction error: {str(e)}")
            return ""
    
    def _parse_text_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse extracted text into individual call records"""
        
        # First, let's see what patterns we can find
        print("🔍 Analyzing text patterns...")
        
        # Look for different ways calls might be separated
        potential_separators = [
            r'(?i)call\s+tw_\w+_\d+',      # Call TW_TASORA_001
            r'tw_\w+_\d+',                  # TW_TASORA_001  
            r'(?i)section\s+\d+',           # Section 1
            r'={3,}',                       # ===
            r'-{10,}',                      # ----------
            r'(?i)transcript\s+\d+',        # Transcript 1
            r'\d+\.\s+\w+\s+channel',       # 1. TASORA Channel
        ]
        
        calls = []
        best_split = None
        
        # Try each separator pattern
        for i, pattern in enumerate(potential_separators):
            test_splits = re.split(pattern, content, flags=re.IGNORECASE)
            
            # Filter out very short sections (likely headers/footers)
            valid_splits = [s.strip() for s in test_splits if len(s.strip()) > 300]
            
            if len(valid_splits) > len(calls):
                calls = valid_splits
                best_split = pattern
                print(f"✅ Found {len(valid_splits)} sections using pattern: {pattern}")
        
        if not calls:
            print("⚠️ No clear separators found, treating as single document")
            calls = [content]
        
        # Parse each call section
        parsed_calls = []
        for i, call_text in enumerate(calls):
            if len(call_text.strip()) < 100:  # Skip very short sections
                continue
                
            parsed_call = self._parse_single_call(call_text, i + 1)
            if parsed_call:
                parsed_calls.append(parsed_call)
        
        print(f"🎉 Successfully parsed {len(parsed_calls)} transcripts")
        return parsed_calls
    
    def _parse_single_call(self, text: str, call_number: int) -> Dict[str, Any]:
        """Parse individual call from text"""
        
        # Extract call ID
        call_id = self._extract_call_id(text, call_number)
        
        # Extract metadata
        channel = self._extract_channel(text, call_id)
        date = self._extract_field(text, ['date:', 'timestamp:', 'time:'])
        category = self._extract_field(text, ['category:', 'issue type:', 'type:', 'problem:'])
        severity = self._extract_field(text, ['severity:', 'priority:', 'level:'])
        journey_type = self._extract_field(text, ['journey type:', 'journey:', 'type:'])
        
        # Extract conversation
        conversation = self._extract_conversation(text)
        
        # Extract resolution info
        resolution = self._extract_field(text, ['resolution:', 'solution:', 'fix:', 'resolved:'])
        impact = self._extract_field(text, ['impact:', 'effect:', 'consequence:'])
        root_cause = self._extract_field(text, ['root cause:', 'cause:', 'reason:'])
        
        return {
            'call_id': call_id,
            'channel': channel,
            'date': date,
            'category': category,
            'severity': severity,
            'journey_type': journey_type,
            'transcript': conversation,
            'resolution': resolution,
            'impact': impact,
            'root_cause': root_cause,
            'raw_text_length': len(text)
        }
    
    def _extract_call_id(self, text: str, call_number: int) -> str:
        """Extract or generate call ID"""
        # Look for existing call IDs
        patterns = [
            r'TW_\w+_\d+',
            r'Call\s+(\w+_\w+_\d+)',
            r'ID[:\s]+([A-Z0-9_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0) if 'TW_' in match.group(0).upper() else f"TW_{match.group(1)}"
        
        # Generate ID based on content
        if 'tasora' in text.lower():
            return f"TW_TASORA_{call_number:03d}"
        elif 'web' in text.lower() or 'portal' in text.lower():
            return f"TW_WEB_{call_number:03d}"
        elif 'app' in text.lower() or 'mobile' in text.lower():
            return f"TW_APP_{call_number:03d}"
        elif 'target' in text.lower():
            return f"TW_TARGET_{call_number:03d}"
        elif 'sms' in text.lower() or 'bot' in text.lower():
            return f"TW_SMS_{call_number:03d}"
        else:
            return f"TW_UNKNOWN_{call_number:03d}"
    
    def _extract_channel(self, text: str, call_id: str) -> str:
        """Determine channel from text or call ID"""
        text_lower = text.lower()
        call_id_upper = call_id.upper()
        
        if 'TASORA' in call_id_upper or 'tasora' in text_lower:
            return 'TASORA'
        elif 'WEB' in call_id_upper or 'web portal' in text_lower or 'website' in text_lower:
            return 'Web Portal'
        elif 'APP' in call_id_upper or 'mobile app' in text_lower or 'application' in text_lower:
            return 'Mobile App'
        elif 'TARGET' in call_id_upper or 'target' in text_lower:
            return 'Target'
        elif 'SMS' in call_id_upper or 'sms' in text_lower or 'bot' in text_lower or 'ivr' in text_lower:
            return 'SMS/Bot/IVR'
        else:
            return 'Unknown'
    
    def _extract_field(self, text: str, field_patterns: List[str]) -> str:
        """Extract field value using multiple possible patterns"""
        for pattern in field_patterns:
            regex = rf'{pattern}\s*([^\n]+)'
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_conversation(self, text: str) -> str:
        """Extract the main conversation from the text"""
        # Look for conversation patterns
        conversation_patterns = [
            r'(?i)transcript:(.+?)(?=resolution:|impact:|root cause:|$)',
            r'(?i)conversation:(.+?)(?=resolution:|impact:|root cause:|$)',
            r'(agent:.+?)(?=resolution:|impact:|root cause:|$)',
        ]
        
        for pattern in conversation_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                conversation = match.group(1).strip()
                # Clean up the conversation text
                conversation = re.sub(r'^(transcript|conversation):\s*', '', conversation, flags=re.IGNORECASE)
                return conversation
        
        # If no clear conversation pattern, look for Agent/Customer exchanges
        agent_customer_pattern = r'(agent:.*?customer:.*?)(?=\n\s*[A-Z][A-Z]:|$)'
        matches = re.findall(agent_customer_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return '\n\n'.join(matches)
        
        # Last resort - return first 1000 characters
        return text[:1000] + "..." if len(text) > 1000 else text
    
    def save_parsed_data(self, parsed_data: List[Dict[str, Any]], output_path: str) -> bool:
        """Save parsed data to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            output_data = {
                'metadata': {
                    'total_transcripts': len(parsed_data),
                    'parsed_at': datetime.now().isoformat(),
                    'channels': list(set(call.get('channel', 'Unknown') for call in parsed_data)),
                    'categories': list(set(call.get('category', '') for call in parsed_data if call.get('category')))
                },
                'transcripts': parsed_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(output_data, file, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved parsed data to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving data: {str(e)}")
            return False
    
    def print_summary(self, parsed_data: List[Dict[str, Any]]):
        """Print summary of parsed data"""
        if not parsed_data:
            print("📋 No data to summarize")
            return
        
        print(f"\n📊 PARSING SUMMARY")
        print("=" * 40)
        print(f"Total Transcripts: {len(parsed_data)}")
        
        # Count by channel
        channels = {}
        categories = {}
        severities = {}
        
        for call in parsed_data:
            channel = call.get('channel', 'Unknown')
            category = call.get('category', 'Unknown')
            severity = call.get('severity', 'Unknown')
            
            channels[channel] = channels.get(channel, 0) + 1
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        print(f"\n📱 Channels:")
        for channel, count in channels.items():
            print(f"  • {channel}: {count}")
        
        if any(categories.keys()):
            print(f"\n📋 Categories:")
            for category, count in categories.items():
                if category:  # Only show non-empty categories
                    print(f"  • {category}: {count}")
        
        if any(severities.keys()):
            print(f"\n⚠️ Severities:")
            for severity, count in severities.items():
                if severity:  # Only show non-empty severities
                    print(f"  • {severity}: {count}")


def test_pdf_parser():
    """Test the PDF parser with your data"""
    parser = TranscriptParser()
    
    # Look for PDF files in data/raw/
    data_dir = 'data/raw'
    pdf_files = []
    
    try:
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            pdf_files = [f for f in files if f.endswith('.pdf')]
        
        if not pdf_files:
            print("❌ No PDF files found in data/raw/")
            print("📁 Please add your PDF file to data/raw/ folder")
            if os.path.exists(data_dir):
                print(f"Files in data/raw/: {os.listdir(data_dir)}")
            return
        
        # Use the first PDF file found
        pdf_file = os.path.join(data_dir, pdf_files[0])
        print(f"🔍 Processing PDF: {pdf_file}")
        
    except Exception as e:
        print(f"❌ Error accessing data directory: {str(e)}")
        return
    
    # Parse the PDF
    parsed_data = parser.parse_pdf(pdf_file)
    
    if parsed_data:
        # Show summary
        parser.print_summary(parsed_data)
        
        # Show first transcript example
        print(f"\n📋 FIRST TRANSCRIPT EXAMPLE:")
        print("=" * 50)
        first_call = parsed_data[0]
        for key, value in first_call.items():
            if key == 'transcript' and len(str(value)) > 300:
                print(f"{key}: {str(value)[:300]}...")
            else:
                print(f"{key}: {value}")
        
        # Save results
        output_path = 'data/processed/parsed_transcripts.json'
        success = parser.save_parsed_data(parsed_data, output_path)
        
        if success:
            print(f"\n✅ Success! Check '{output_path}' for full results")
        
    else:
        print("❌ No transcripts were parsed")
        print("💡 Make sure your PDF contains readable text with call transcripts")


if __name__ == "__main__":
    test_pdf_parser()