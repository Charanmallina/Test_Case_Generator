# FILE: src/data_cleaner.py

import json
import re
from typing import List, Dict, Any

class DataCleaner:
    """Clean and standardize parsed transcript data"""
    
    def __init__(self):
        print("🧹 Data Cleaner initialized")
    
    def clean_parsed_data(self, input_file: str, output_file: str) -> bool:
        """
        Clean the parsed transcript data
        
        Args:
            input_file: Path to parsed_transcripts.json
            output_file: Path to save cleaned data
        """
        try:
            # Load parsed data
            with open(input_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📖 Loading data from: {input_file}")
            transcripts = data.get('transcripts', [])
            print(f"🔍 Found {len(transcripts)} transcripts to clean")
            
            # Clean each transcript
            cleaned_transcripts = []
            for i, transcript in enumerate(transcripts, 1):
                cleaned = self._clean_single_transcript(transcript)
                cleaned_transcripts.append(cleaned)
                print(f"✅ Cleaned transcript {i}: {cleaned['call_id']}")
            
            # Save cleaned data
            cleaned_data = {
                'metadata': {
                    'total_transcripts': len(cleaned_transcripts),
                    'cleaned_at': data.get('metadata', {}).get('parsed_at', ''),
                    'channels': list(set(call.get('channel', 'Unknown') for call in cleaned_transcripts)),
                    'categories': list(set(call.get('category', '') for call in cleaned_transcripts if call.get('category')))
                },
                'transcripts': cleaned_transcripts
            }
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(cleaned_data, file, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved cleaned data to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning data: {str(e)}")
            return False
    
    def _clean_single_transcript(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Clean individual transcript fields"""
        
        cleaned = transcript.copy()
        
        # Clean category field
        category = transcript.get('category', '')
        cleaned['category'] = self._clean_category(category)
        
        # Clean severity field  
        severity = transcript.get('severity', '')
        cleaned['severity'] = self._clean_severity(severity)
        
        # Clean journey type
        journey_type = transcript.get('journey_type', '')
        cleaned['journey_type'] = self._clean_journey_type(journey_type)
        
        # Clean date field
        date = transcript.get('date', '')
        cleaned['date'] = self._clean_date(date)
        
        # Clean transcript conversation
        conversation = transcript.get('transcript', '')
        cleaned['transcript'] = self._clean_conversation(conversation)
        
        # Clean resolution
        resolution = transcript.get('resolution', '')
        cleaned['resolution'] = self._clean_resolution(resolution)
        
        # Clean impact
        impact = transcript.get('impact', '')
        cleaned['impact'] = self._clean_impact(impact)
        
        return cleaned
    
    def _clean_category(self, category: str) -> str:
        """Clean category field"""
        if not category:
            return ""
        
        # Remove common contamination patterns
        category = re.sub(r'\s*Severity:.*$', '', category, flags=re.IGNORECASE)
        category = re.sub(r'\s*TRANSCRIPT:.*$', '', category, flags=re.IGNORECASE)
        category = re.sub(r'\s*Agent:.*$', '', category, flags=re.IGNORECASE)
        category = re.sub(r'\s*High\s*$', '', category, flags=re.IGNORECASE)
        category = re.sub(r'\s*Medium\s*$', '', category, flags=re.IGNORECASE)
        category = re.sub(r'\s*Low\s*$', '', category, flags=re.IGNORECASE)
        
        # Standardize common categories
        category_mapping = {
            'plan change': 'Plan Change',
            'device activation': 'Device Activation', 
            'billing dispute': 'Billing Dispute',
            'device purchase': 'Device Purchase',
            'account management': 'Account Management',
            'promotional offers': 'Promotional Offers',
            'data usage tracking': 'Data Usage Tracking',
            'device upgrade': 'Device Upgrade',
            'auto-pay management': 'Auto-Pay Management',
            'auto pay management': 'Auto-Pay Management',
            'sim card activation': 'SIM Card Activation',
            'promotional pricing': 'Promotional Pricing',
            'device return': 'Device Return',
            'data usage alerts': 'Data Usage Alerts',
            'service commands': 'Service Commands',
            'balance inquiry': 'Balance Inquiry'
        }
        
        category_clean = category.strip()
        category_lower = category_clean.lower()
        
        for key, value in category_mapping.items():
            if key in category_lower:
                return value
        
        # Return cleaned version if no mapping found
        return category_clean if category_clean else "Unknown"
    
    def _clean_severity(self, severity: str) -> str:
        """Clean severity field"""
        if not severity:
            return ""
        
        # Remove contamination
        severity = re.sub(r'\s*TRANSCRIPT:.*$', '', severity, flags=re.IGNORECASE)
        severity = re.sub(r'\s*Agent:.*$', '', severity, flags=re.IGNORECASE)
        severity = re.sub(r'\s*Category:.*$', '', severity, flags=re.IGNORECASE)
        
        severity_clean = severity.strip().title()
        
        # Standardize severity levels
        if 'high' in severity_clean.lower():
            return 'High'
        elif 'medium' in severity_clean.lower():
            return 'Medium'
        elif 'low' in severity_clean.lower():
            return 'Low'
        elif 'critical' in severity_clean.lower():
            return 'Critical'
        else:
            return severity_clean if severity_clean else "Medium"
    
    def _clean_journey_type(self, journey_type: str) -> str:
        """Clean journey type field"""
        if not journey_type:
            return ""
        
        journey_clean = journey_type.strip().title()
        
        if 'tangible' in journey_clean.lower():
            return 'Tangible'
        elif 'non-tangible' in journey_clean.lower():
            return 'Non-tangible'
        else:
            return journey_clean if journey_clean else "Non-tangible"
    
    def _clean_date(self, date: str) -> str:
        """Clean date field"""
        if not date:
            return ""
        
        # Extract date patterns
        date_patterns = [
            r'(\w+\s+\d+,\s+\d{4})',  # August 1, 2024
            r'(\d{4}-\d{2}-\d{2})',   # 2024-08-01
            r'(\d{1,2}/\d{1,2}/\d{4})'  # 8/1/2024
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date)
            if match:
                return match.group(1)
        
        return date.strip()
    
    def _clean_conversation(self, conversation: str) -> str:
        """Clean conversation transcript"""
        if not conversation:
            return ""
        
        # Remove document headers/footers that got mixed in
        conversation = re.sub(r'^.*?TOTAL WIRELESS.*?Customer Support.*?$', '', conversation, flags=re.MULTILINE | re.IGNORECASE)
        conversation = re.sub(r'^.*?Dataset.*?$', '', conversation, flags=re.MULTILINE | re.IGNORECASE)
        conversation = re.sub(r'^.*?===+.*?$', '', conversation, flags=re.MULTILINE)
        conversation = re.sub(r'^.*?Channels:.*?$', '', conversation, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        conversation = re.sub(r'\n\s*\n\s*\n+', '\n\n', conversation)
        conversation = conversation.strip()
        
        return conversation
    
    def _clean_resolution(self, resolution: str) -> str:
        """Clean resolution field"""
        if not resolution:
            return ""
        
        # Remove contamination
        resolution = re.sub(r'\s*Impact:.*$', '', resolution, flags=re.IGNORECASE)
        resolution = re.sub(r'\s*Root Cause:.*$', '', resolution, flags=re.IGNORECASE)
        
        return resolution.strip()
    
    def _clean_impact(self, impact: str) -> str:
        """Clean impact field"""
        if not impact:
            return ""
        
        # Remove contamination
        impact = re.sub(r'\s*Root Cause:.*$', '', impact, flags=re.IGNORECASE)
        impact = re.sub(r'\s*Resolution:.*$', '', impact, flags=re.IGNORECASE)
        
        return impact.strip()
    
    def print_cleaning_summary(self, input_file: str, output_file: str):
        """Print before/after comparison"""
        try:
            # Load both files
            with open(input_file, 'r', encoding='utf-8') as file:
                original_data = json.load(file)
            
            with open(output_file, 'r', encoding='utf-8') as file:
                cleaned_data = json.load(file)
            
            print(f"\n📊 CLEANING SUMMARY")
            print("=" * 40)
            
            original_transcripts = original_data.get('transcripts', [])
            cleaned_transcripts = cleaned_data.get('transcripts', [])
            
            print(f"Processed: {len(cleaned_transcripts)} transcripts")
            
            # Show categories before/after
            print(f"\n📋 Categories cleaned:")
            original_categories = set(t.get('category', '') for t in original_transcripts if t.get('category'))
            cleaned_categories = set(t.get('category', '') for t in cleaned_transcripts if t.get('category'))
            
            print(f"  Original: {len(original_categories)} unique categories")
            print(f"  Cleaned:  {len(cleaned_categories)} unique categories")
            
            print(f"\n✅ Cleaned categories:")
            for category in sorted(cleaned_categories):
                if category:
                    count = sum(1 for t in cleaned_transcripts if t.get('category') == category)
                    print(f"  • {category}: {count}")
            
            # Show severities
            cleaned_severities = set(t.get('severity', '') for t in cleaned_transcripts if t.get('severity'))
            print(f"\n⚠️ Severities:")
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                count = sum(1 for t in cleaned_transcripts if t.get('severity') == severity)
                if count > 0:
                    print(f"  • {severity}: {count}")
            
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")


def test_data_cleaner():
    """Test the data cleaner"""
    cleaner = DataCleaner()
    
    input_file = 'data/processed/parsed_transcripts.json'
    output_file = 'data/processed/cleaned_transcripts.json'
    
    print("🧹 Starting data cleaning process...")
    
    success = cleaner.clean_parsed_data(input_file, output_file)
    
    if success:
        cleaner.print_cleaning_summary(input_file, output_file)
        print(f"\n✅ Data cleaning completed!")
        print(f"📁 Check '{output_file}' for cleaned data")
    else:
        print("❌ Data cleaning failed")


if __name__ == "__main__":
    test_data_cleaner()