# FILE: src/pii_masker.py

import json
import re
from typing import List, Dict, Any, Tuple

class PIIMasker:
    """Remove or mask personally identifiable information from transcripts"""
    
    def __init__(self):
        print("🔒 PII Masker initialized")
        
        # Define PII patterns to detect and mask
        self.pii_patterns = {
            'phone_numbers': [
                r'\b\d{3}-\d{3}-\d{4}\b',           # 555-123-4567
                r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',     # (555) 123-4567
                r'\b\d{3}\.\d{3}\.\d{4}\b',         # 555.123.4567
                r'\b\d{10}\b',                      # 5551234567
            ],
            'emails': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'account_numbers': [
                r'\b\d{10,15}\b',                   # 10-15 digit account numbers
                r'\b[A-Z0-9]{8,12}\b',              # Alphanumeric account IDs
            ],
            'imei_numbers': [
                r'\b\d{15}\b',                      # 15-digit IMEI
            ],
            'credit_cards': [
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Credit card patterns
            ],
            'ssn': [
                r'\b\d{3}-\d{2}-\d{4}\b',           # SSN format
            ],
            'names': [
                # Common name patterns in agent/customer context
                r'\b(?:Agent|Customer):\s*[A-Z][a-z]+\s+[A-Z][a-z]+\b',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?=\s+(?:said|called|from))\b',
            ],
            'addresses': [
                r'\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b',
                r'\b\d{5}(?:-\d{4})?\b',           # ZIP codes
            ]
        }
        
        # Define replacement patterns
        self.replacements = {
            'phone_numbers': '[PHONE_NUMBER]',
            'emails': '[EMAIL_ADDRESS]',
            'account_numbers': '[ACCOUNT_NUMBER]',
            'imei_numbers': '[DEVICE_ID]',
            'credit_cards': '[CREDIT_CARD]',
            'ssn': '[SSN]',
            'names': '[CUSTOMER_NAME]',
            'addresses': '[ADDRESS]'
        }
    
    def mask_data(self, input_file: str, output_file: str) -> bool:
        """
        Mask PII in cleaned transcript data
        
        Args:
            input_file: Path to cleaned_transcripts.json
            output_file: Path to save masked data
        """
        try:
            # Load cleaned data
            with open(input_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📖 Loading data from: {input_file}")
            transcripts = data.get('transcripts', [])
            print(f"🔍 Found {len(transcripts)} transcripts to mask")
            
            # Track PII found
            pii_stats = {pii_type: 0 for pii_type in self.pii_patterns.keys()}
            
            # Mask each transcript
            masked_transcripts = []
            for i, transcript in enumerate(transcripts, 1):
                masked, found_pii = self._mask_single_transcript(transcript)
                masked_transcripts.append(masked)
                
                # Update stats
                for pii_type, count in found_pii.items():
                    pii_stats[pii_type] += count
                
                if any(found_pii.values()):
                    print(f"🔒 Masked transcript {i}: {transcript['call_id']} - Found {sum(found_pii.values())} PII items")
                else:
                    print(f"✅ Clean transcript {i}: {transcript['call_id']} - No PII found")
            
            # Save masked data
            masked_data = {
                'metadata': {
                    'total_transcripts': len(masked_transcripts),
                    'masked_at': data.get('metadata', {}).get('cleaned_at', ''),
                    'channels': list(set(call.get('channel', 'Unknown') for call in masked_transcripts)),
                    'categories': list(set(call.get('category', '') for call in masked_transcripts if call.get('category'))),
                    'pii_removed': pii_stats
                },
                'transcripts': masked_transcripts
            }
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(masked_data, file, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved masked data to: {output_file}")
            self._print_pii_stats(pii_stats)
            return True
            
        except Exception as e:
            print(f"❌ Error masking data: {str(e)}")
            return False
    
    def _mask_single_transcript(self, transcript: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Mask PII in a single transcript"""
        
        masked = transcript.copy()
        pii_found = {pii_type: 0 for pii_type in self.pii_patterns.keys()}
        
        # Fields to check for PII
        fields_to_mask = ['transcript', 'resolution', 'impact', 'root_cause']
        
        for field in fields_to_mask:
            if field in masked and masked[field]:
                original_text = masked[field]
                masked_text, field_pii = self._mask_text(original_text)
                masked[field] = masked_text
                
                # Update PII counts
                for pii_type, count in field_pii.items():
                    pii_found[pii_type] += count
        
        # Also mask call_id if it contains sensitive info (but keep format)
        if 'call_id' in masked:
            call_id = masked['call_id']
            # Keep the structure but mask any embedded sensitive data
            masked_call_id, _ = self._mask_text(call_id)
            masked['call_id'] = masked_call_id
        
        return masked, pii_found
    
    def _mask_text(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Mask PII in a single text field"""
        
        if not text:
            return text, {pii_type: 0 for pii_type in self.pii_patterns.keys()}
        
        masked_text = text
        pii_counts = {pii_type: 0 for pii_type in self.pii_patterns.keys()}
        
        # Apply each PII pattern
        for pii_type, patterns in self.pii_patterns.items():
            replacement = self.replacements[pii_type]
            
            for pattern in patterns:
                # Find and count matches
                matches = re.findall(pattern, masked_text, re.IGNORECASE)
                pii_counts[pii_type] += len(matches)
                
                # Replace matches
                masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
        
        # Additional specific masking for common telecommunications data
        masked_text = self._mask_telecom_specific(masked_text)
        
        return masked_text, pii_counts
    
    def _mask_telecom_specific(self, text: str) -> str:
        """Mask telecom-specific sensitive information"""
        
        # Mask common telecom patterns
        telecom_patterns = {
            r'\b(SIM|sim)\s*(card\s*)?number[:\s]+[\w\d]+': '[SIM_NUMBER]',
            r'\bactivation\s*code[:\s]+[\w\d]+': '[ACTIVATION_CODE]',
            r'\bport\s*request[:\s]+[\w\d-]+': '[PORT_REQUEST_ID]',
            r'\btrade-in\s*reference[:\s]+[\w\d-]+': '[TRADE_IN_ID]',
            r'\border\s*confirmation[:\s]+[\w\d-]+': '[ORDER_ID]',
            r'\bbilling\s*address[:\s]+[^.]+\.': '[BILLING_ADDRESS].',
            r'\bZIP\s*code[:\s]+\d{5}': '[ZIP_CODE]',
        }
        
        masked_text = text
        for pattern, replacement in telecom_patterns.items():
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
        
        return masked_text
    
    def _print_pii_stats(self, pii_stats: Dict[str, int]):
        """Print PII masking statistics"""
        
        print(f"\n🔒 PII MASKING SUMMARY")
        print("=" * 40)
        
        total_pii = sum(pii_stats.values())
        print(f"Total PII items masked: {total_pii}")
        
        if total_pii > 0:
            print(f"\n📊 PII types found:")
            for pii_type, count in pii_stats.items():
                if count > 0:
                    print(f"  • {pii_type.replace('_', ' ').title()}: {count}")
        else:
            print("✅ No PII found in transcripts")
        
        print(f"\n🛡️ Data is now safe to send to AI models")
    
    def verify_masking(self, masked_file: str):
        """Verify that PII masking was successful"""
        
        try:
            with open(masked_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"\n🔍 VERIFYING MASKED DATA")
            print("=" * 40)
            
            transcripts = data.get('transcripts', [])
            issues_found = []
            
            # Check for common PII patterns that might have been missed
            verification_patterns = [
                (r'\b\d{3}-\d{3}-\d{4}\b', 'Phone numbers'),
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email addresses'),
                (r'\b\d{10,15}\b', 'Long number sequences'),
            ]
            
            for transcript in transcripts:
                call_id = transcript.get('call_id', 'Unknown')
                
                for field in ['transcript', 'resolution', 'impact']:
                    text = transcript.get(field, '')
                    if text:
                        for pattern, pii_type in verification_patterns:
                            matches = re.findall(pattern, text)
                            if matches:
                                issues_found.append(f"{call_id} - {pii_type}: {len(matches)} items")
            
            if issues_found:
                print("⚠️ Potential PII still found:")
                for issue in issues_found[:5]:  # Show first 5
                    print(f"  • {issue}")
                if len(issues_found) > 5:
                    print(f"  ... and {len(issues_found) - 5} more")
            else:
                print("✅ No obvious PII patterns found")
                print("🛡️ Data appears properly masked")
            
        except Exception as e:
            print(f"❌ Error verifying masked data: {str(e)}")


def test_pii_masker():
    """Test the PII masker"""
    masker = PIIMasker()
    
    input_file = 'data/processed/cleaned_transcripts.json'
    output_file = 'data/processed/masked_transcripts.json'
    
    print("🔒 Starting PII masking process...")
    
    success = masker.mask_data(input_file, output_file)
    
    if success:
        masker.verify_masking(output_file)
        print(f"\n✅ PII masking completed!")
        print(f"📁 Check '{output_file}' for masked data")
        print(f"🚀 Ready for AI processing!")
    else:
        print("❌ PII masking failed")


if __name__ == "__main__":
    test_pii_masker()