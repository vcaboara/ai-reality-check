# AI Reality Check - UI Guide

## Overview

The AI Reality Check UI provides a simple interface for analyzing the technical feasibility of engineering projects using AI.

## How to Use

### 1. Start the Server

**Using Docker:**
```bash
docker-compose up -d
```

**Access:** http://localhost:5000

### 2. Choose Input Method

**Option A: Text Input**
- Click the "Text Input" tab
- Enter your technical project description
- Include details like temperatures, equipment, materials, scale, etc.

**Option B: Upload Files**
- Click the "Upload File" tab
- Upload one or more PDF or TXT files
- Multiple files will be analyzed together

### 3. Provide Context (Optional)

Use the "Additional Context" field to provide:
- Budget constraints
- Timeline requirements
- Location/regulatory requirements
- Specific technical concerns
- Questions you want answered

**Example:**
```
Budget: $500K
Timeline: 18 months
Location: California (must meet CARB standards)
Key question: Can we use stainless steel 316 at 600°C?
```

### 4. Add Project Title (Optional)

Give your analysis a memorable name for easy reference later.

### 5. Submit for Analysis

Click "🚀 Analyze Feasibility" and wait 30-60 seconds while the AI:
- Validates your proposal against domain expertise
- Identifies technical risks and challenges
- Provides specific recommendations
- Highlights potential issues

### 6. Review Results

The analysis includes:
- **Domain Expert Validation**: Checks against engineering best practices
- **Feasibility Analysis**: Detailed technical assessment
- **Metadata**: Model used, analysis timestamp

## Current AI Model

The UI displays the current model in the header:
- **Ollama**: Local model (e.g., llama3.2:3b) - Private, no API costs
- **Google Gemini**: Cloud API - Faster, requires API key

Configure via environment variables (see `.env.example`).

## Multi-File Analysis

Upload multiple files to analyze:
- Multiple technical specifications
- Related documents (requirements + design)
- Supporting research papers

Files are combined and analyzed together for comprehensive insights.

## Tips for Best Results

1. **Be Specific**: Include numbers (temperatures, pressures, flow rates)
2. **Provide Context**: Explain your goals and constraints
3. **Ask Questions**: Include specific technical questions
4. **Use Both Tabs**: Upload specs as files, add context as text
5. **Review Past Results**: Check the "📊 View Results" link for history

## Interactive Chat

Click "💬 Interactive Chat" for conversational analysis where you can:
- Ask follow-up questions
- Refine your design iteratively
- Explore alternatives
- Deep-dive into specific aspects

## Example Workflow

1. **Upload** your technical specification PDF
2. **Add context**: "Budget $300K, must be operational by Q3 2026"
3. **Submit** and review initial analysis
4. **Switch to Chat** to ask follow-up questions about specific concerns
5. **Review Results** page to compare different design iterations

## Troubleshooting

**"No file selected" error**: Make sure to select a file or enter text
**"Invalid file type" error**: Only PDF and TXT files supported
**Analysis takes too long**: Normal for complex documents (30-60s)
**Empty results**: Check Docker logs: `docker logs ai-reality-check-web`

## Data Storage

- **Uploads**: Saved to `data/uploads/` (not analyzed again)
- **Results**: Saved to `data/results/` as JSON files
- **Conversations**: Stored in memory (cleared on restart)

For production use, consider:
- Using Redis for conversation storage
- Adding user authentication
- Implementing result pagination
