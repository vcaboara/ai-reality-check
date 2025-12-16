# AI Reality Check

**Ground your technical ideas in engineering reality.**

AI-powered feasibility analysis that provides honest, structured assessments of technical projects. Perfect for climate tech, thermal systems, sustainability projects, and any engineering concept that needs a reality check.

## 🎯 What It Does

Performs rigorous 3-part analysis of technical briefs:

1. **FEASIBILITY & RISK** - Technical viability, material constraints, major risks
2. **EFFICIENCY & OPTIMIZATION** - Quantitative performance assessment, optimization pathways  
3. **PROPOSED IMPROVEMENTS** - Actionable steps to enhance design, sustainability, cost-efficiency

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/vcaboara/ai-reality-check.git
cd ai-reality-check

# Install with uv (recommended)
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Add your GEMINI_API_KEY or configure Ollama (see docs)

# Run web interface
python src/ui/server.py
# Visit http://localhost:5000
```

## 🔧 Features

- **Domain-Driven Analysis** - YAML-based domain expertise (temperature ranges, equipment types, process validation)
- **Multi-Provider AI** - Gemini API (fast, cloud) or Ollama (private, local) with automatic fallback
- **PDF Upload Support** - Analyze technical documents directly
- **Structured Output** - Clear, actionable analysis in 3 sections
- **Extensible** - Add new domains (chemical processes, mechanical systems, etc.) via YAML config

## 📋 Example Use Cases

**Climate Tech:**
- Pyrolysis reactor designs (300-900°C thermal decomposition)
- Waste-to-energy systems (mass balance validation)
- Carbon capture projects (net-negative potential)

**Thermal Systems:**
- Gasification processes
- Combustion optimization
- Heat recovery systems

**Sustainability:**
- Circular economy projects
- Resource efficiency improvements
- Lifecycle impact assessments

## 🏗️ Architecture

Built on [ai-search-match-framework](https://github.com/vcaboara/ai-search-match-framework) v0.2.0:

```
ai-reality-check/
├── src/
│   ├── analyzers/
│   │   └── feasibility_analyzer.py  # Core analysis logic
│   ├── config/
│   │   └── domain.yaml              # Thermal systems domain (example)
│   ├── prompts/
│   │   └── reality_check.txt        # System prompt
│   └── ui/
│       └── server.py                # Flask web interface
├── tests/
├── data/
│   ├── uploads/                     # PDF inputs
│   └── results/                     # Analysis outputs
└── docs/
```

**Leverages ASMF:**
- `DomainConfig` - YAML-based technical domain configuration
- `DomainExpert` - Temperature, pressure, mass balance validation
- `AIProviderFactory` - Gemini/Ollama provider management with fallback
- `PDFParser` - Document text extraction
- `ModelSelector` - Task-specific Ollama model selection (VRAM-aware)

## 🔬 Domain Configuration

Define your technical domain in `config/domain.yaml`:

```yaml
domain:
  name: "Thermal Processing Systems"
  description: "Pyrolysis, gasification, and thermal conversion"

temperature_ranges:
  pyrolysis: [300, 900]     # Celsius
  gasification: [700, 1500]
  combustion: [800, 2000]

equipment_types:
  - "Fixed bed reactor"
  - "Fluidized bed reactor"
  - "Rotary kiln"

operating_conditions:
  pressure:
    min: 0.1  # bar
    max: 50.0
  residence_time:
    min: 0.1  # seconds
    max: 3600
```

## 📊 System Prompt

Analysis follows structured template:

```
You are a Senior Project Architect and Climate Engineer. 

Perform rigorous feasibility analysis:

1. FEASIBILITY & RISK
   - Technical viability assessment
   - Material/equipment constraints
   - Major risk identification

2. EFFICIENCY & OPTIMIZATION  
   - Energy balance analysis
   - Mass balance validation
   - Yield optimization opportunities

3. PROPOSED IMPROVEMENTS
   - Concrete, actionable steps
   - Focus: net-negative potential, sustainability, cost-efficiency
   
Be concise, professional, grounded in current engineering knowledge.
```

## 🛠️ Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Check coverage (must be ≥80%)
pytest --cov

# Format code
black src tests
ruff check src tests --fix

# Type checking
mypy src
```

## 🐳 Docker

```bash
# Build image
docker build -t ai-reality-check .

# Run container
docker run -p 5000:5000 \
  -e GEMINI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  ai-reality-check
```

## 📚 Documentation

- [System Prompts](docs/PROMPTS.md) - Analysis templates and reasoning
- [Domain Configuration](docs/DOMAIN_CONFIG.md) - Creating custom domains
- [API Reference](docs/API.md) - Programmatic usage
- [Examples](docs/EXAMPLES.md) - Sample analyses

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow [commit conventions](.github/commit-conventions.md)
4. Ensure tests pass and coverage ≥80%
5. Submit Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Credits

Built with:
- [ai-search-match-framework](https://github.com/vcaboara/ai-search-match-framework) - Domain expertise and AI providers
- [Flask](https://flask.palletsprojects.com/) - Web interface
- [Gemini API](https://ai.google.dev/) - Cloud AI (fast, scalable)
- [Ollama](https://ollama.ai/) - Local AI (private, unlimited)

---

**Reality is not what you want it to be; it is what it is. Let's figure out what that is.** 🔬
