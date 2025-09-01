# Automated Test Case Generator

> Transform customer support transcripts into actionable QA test cases using AI

An AI-powered solution that converts customer support call transcripts into structured, executable test cases for QA teams. Built to bridge the gap between expert QA testing and real customer behavior patterns.

## 🎯 Problem Statement

QA teams test from an expert perspective, missing real-world customer behaviors and mistakes. This creates a testing gap where software passes QA but still generates customer support calls due to unintuitive user experiences.

**Business Impact:**
- High volume of preventable customer support calls
- Increased operational costs from support interactions  
- Poor customer experience leading to potential churn
- Development teams unaware of real-world usage patterns

## 🚀 Solution Overview

The Automated Test Case Generator processes customer support transcripts through an AI-powered pipeline to generate structured test cases that reflect actual customer journey failures and pain points.

### Key Features

- **Multi-channel Support**: TASORA, Web Portal, Mobile App, Target, SMS/Bot/IVR
- **AI-Powered Analysis**: Converts natural language issues into structured test scenarios
- **Privacy Compliant**: Automatic PII detection and masking
- **Web Dashboard**: Filter and generate test cases through intuitive interface
- **Multiple Export Formats**: JSON and Excel downloads

## 📋 What We Built

### Phase 1: Project Planning & Data Collection
✅ **Requirements Analysis** - Identified QA testing gaps and customer experience problems  
✅ **Sample Data Creation** - 15 realistic customer support transcripts across 5 channels  

### Phase 2: Project Structure & Setup  
✅ **Project Architecture** - Modular structure with clean separation of concerns  
✅ **Environment Setup** - Python virtual environment with all dependencies  

### Phase 3: Data Processing Pipeline
✅ **PDF Parser** (`src/transcript_parser.py`) - Extract and split individual call transcripts  
✅ **Data Cleaner** (`src/data_cleaner.py`) - Standardize formats and clean artifacts  
✅ **PII Masker** (`src/pii_masker.py`) - Privacy-compliant data sanitization  

### Phase 4: AI Integration
✅ **AI Model Integration** (`src/ai_test_generator.py`) - Groq API for test case generation  
✅ **Structured Output** - JSON schema for QA-actionable test scenarios  

### Phase 5: Web Application
✅ **Flask Web App** (`web_app/app.py`) - Professional interface with filtering  
✅ **Dashboard** - Statistics and transcript analytics  
✅ **Upload & Processing** - End-to-end pipeline integration  

### Phase 6: Testing & Validation
✅ **End-to-End Testing** - Validated with real dataset  
✅ **PII Masking Validation** - Successfully masked 578 PII items  
✅ **Test Case Generation** - Produced actionable QA scenarios  

## 🏗️ Project Structure

```
automated-test-case-generator/
├── README.md
├── requirements.txt
├── .env.example
│
├── src/                          # Core processing modules
│   ├── transcript_parser.py      # PDF parsing and transcript extraction
│   ├── data_cleaner.py          # Data standardization and cleaning
│   ├── pii_masker.py            # Privacy compliance and PII masking
│   └── ai_test_generator.py     # AI-powered test case generation
│
├── web_app/                     # Flask web application
│   ├── app.py                   # Main Flask application
│   ├── templates/
│   │   └── index.html          # Web dashboard interface
│   └── static/
│       └── uploads/            # Uploaded file storage
│
├── data/                        # Data storage
│   ├── input/                   # Raw transcript files
│   ├── processed/              # Cleaned and masked data
│   └── output/                 # Generated test cases
│
└── config/                      # Configuration files
    └── categories.json         # Issue categories and mappings
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Groq API key (free tier available)

### Installation Steps

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd automated-test-case-generator
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key:
   # GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Create Required Directories**
   ```bash
   mkdir -p data/{input,processed,output}
   mkdir -p web_app/static/uploads
   ```

## 🚀 Usage

### Web Application (Recommended)

1. **Start the Flask Application**
   ```bash
   cd web_app
   python app.py
   ```

2. **Access Dashboard**
   Open your browser to `http://localhost:5000`

3. **Upload Transcripts**
   - Use the upload feature to add new PDF transcript files
   - Files are automatically processed through the entire pipeline

4. **Generate Test Cases**
   - Filter transcripts by channel, category, or severity
   - Click "Generate Test Cases" to create structured test scenarios
   - Download results as JSON or Excel format

### Command Line Usage

Process transcripts through individual pipeline stages:

```bash
# Parse PDF transcripts
python src/transcript_parser.py data/input/transcripts.pdf

# Clean parsed data
python src/data_cleaner.py data/processed/parsed_transcripts.json

# Mask PII information
python src/pii_masker.py data/processed/cleaned_transcripts.json

# Generate test cases
python src/ai_test_generator.py data/processed/masked_transcripts.json
```

## 📊 Features

### Data Processing Pipeline
- **PDF Parsing**: Extract individual call transcripts from multi-page documents
- **Data Cleaning**: Standardize categories, severities, and remove artifacts
- **PII Masking**: GDPR/CCPA compliant privacy protection
- **AI Generation**: Convert natural language issues to structured test cases

### Web Dashboard
- **Statistics Overview**: Transcript counts by channel, category, and severity
- **Advanced Filtering**: Target specific issue types or channels
- **Real-time Processing**: Upload and process new transcripts instantly
- **Multiple Export Formats**: JSON for automation, Excel for manual review

### Supported Channels
- TASORA (Agent Oriented Journeys)
- Web Portal
- Mobile App  
- Target (retail channel)
- SMS, Bot, IVR

### Supported Brands
- Total Wireless
- TracFone
- Straight Talk
- Simple Mobile

## 🔧 Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key        # Required for AI generation
MAX_FILE_SIZE=16777216                # 16MB upload limit
DEBUG=True                            # Enable debug mode
```

### Customization
- **Categories**: Edit `config/categories.json` to modify issue classifications
- **PII Patterns**: Update `src/pii_masker.py` to add new PII detection patterns
- **AI Prompts**: Modify prompts in `src/ai_test_generator.py` for different output formats

## 📈 Results & Impact

### Processing Stats
- **15 Sample Transcripts** processed successfully
- **578 PII Items** automatically detected and masked
- **9 Test Cases** generated (limited by API rate limits)
- **100% Pipeline Success Rate** in validation testing

### Generated Test Case Structure
```json
{
  "test_case_id": "TC_001",
  "domain": "Device Activation",
  "priority": "High",
  "test_steps": [...],
  "expected_results": "...",
  "severity": "Critical",
  "channel": "Mobile App"
}
```

## 🐛 Troubleshooting

### Common Issues

**"Not Found" Error**
- Ensure Flask app is running on correct port (5000)
- Check that download routes are uncommented in `app.py`

**Excel File Won't Open**
- Verify `ExcelFormatter` class is properly implemented
- Check file permissions in `data/output/` directory
- Try downloading JSON format first to verify data generation

**Upload Failures**
- Confirm file size is under 16MB limit
- Ensure uploaded files are PDF, TXT, or JSON format
- Check upload directory permissions

**API Rate Limits**
- Groq free tier has usage limits
- Consider upgrading API plan for production use
- Implement retry logic with exponential backoff

## 🔄 Pipeline Flow

```
📄 PDF Upload → 🔍 Parse Transcripts → 🧹 Clean Data → 🔒 Mask PII → 🤖 AI Generation → 📋 Test Cases
```

1. **Input**: Customer support transcript PDFs
2. **Parsing**: Extract individual call records with metadata
3. **Cleaning**: Standardize formats and remove processing artifacts  
4. **Masking**: Replace PII with privacy-safe placeholders
5. **AI Processing**: Convert issues to structured test scenarios
6. **Output**: Downloadable test cases in JSON/Excel format

## 🚀 Future Enhancements

- **Integration with JIRA/TestRail** for direct test case import
- **Automated Test Execution** through Selenium/Playwright
- **Real-time Processing** with live call transcript feeds
- **Advanced Analytics** with trend analysis and issue prediction
- **Multi-language Support** for international customer bases


---

**Built with:** Python, Flask, Groq AI, Google Cloud Platform  
**Team:** Sai Charan Mallina
**Status:** Prototype Complete - Ready for Pilot Testing
