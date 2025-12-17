"""Feasibility analysis using ASMF domain expertise.

Performs rigorous 3-part technical assessment:
1. FEASIBILITY & RISK - Viability, constraints, risks
2. EFFICIENCY & OPTIMIZATION - Performance metrics, optimization paths
3. PROPOSED IMPROVEMENTS - Actionable enhancement recommendations
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from asmf.domain import DomainExpert, get_domain_config
from asmf.providers import AIProviderFactory

logger = logging.getLogger(__name__)

# Load system prompt
PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "reality_check.txt"


class FeasibilityAnalyzer:
    """Analyze technical feasibility using domain expertise and AI."""

    def __init__(self, domain_config_path: Optional[str] = None):
        """Initialize analyzer with domain configuration.

        Args:
            domain_config_path: Optional path to domain YAML config.
                               If None, uses default from ASMF.
        """
        # Load domain configuration
        if domain_config_path:
            from asmf.domain.config import DomainConfig
            self.domain_config = DomainConfig(domain_config_path)
        else:
            self.domain_config = get_domain_config()

        # Initialize domain expert (uses global config)
        self.expert = DomainExpert()

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        logger.info(
            f"FeasibilityAnalyzer initialized with domain: "
            f"{self.domain_config.domain_name}"
        )

    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        if PROMPT_FILE.exists():
            return PROMPT_FILE.read_text(encoding="utf-8")

        # Fallback prompt if file doesn't exist
        return """You are a Senior Project Architect and Climate Engineer.

Your task is to perform a rigorous feasibility analysis of the user-provided technical brief.

Your response MUST be structured into three sections:

1. FEASIBILITY & RISK
   Assessment of technical viability, material constraints, and major risks.

2. EFFICIENCY & OPTIMIZATION
   Quantitative assessment of energy, material, or process efficiency.
   Identification of optimization pathways.

3. PROPOSED IMPROVEMENTS
   Concrete, actionable steps to enhance the design.
   Focus on net-negative potential, sustainability, or cost-efficiency.

Be concise, professional, and grounded in current engineering knowledge.
"""

    def analyze(self, text: str, context: Optional[Dict] = None) -> Dict[str, any]:
        """Analyze technical description for feasibility.

        Args:
            text: Technical description or proposal to analyze
            context: Optional additional context (title, metadata, etc.)

        Returns:
            Dictionary with analysis results:
            {
                "analysis": str,  # Main AI analysis (3 sections)
                "domain_validation": dict,  # Technical validation results
                "metadata": dict  # Analysis metadata
            }
        """
        logger.info("Starting feasibility analysis")

        # Run domain expert validation
        validation = self._validate_technical_details(text)

        # Build full prompt with context
        full_prompt = self._build_prompt(text, validation, context)

        # Get AI analysis using provider factory (Gemini with Ollama fallback)
        provider = AIProviderFactory.create_provider()
        analysis_context = {"system_prompt": self.system_prompt}
        if context:
            analysis_context.update(context)
        analysis = provider.analyze_text(full_prompt, analysis_context)

        from datetime import datetime

        result = {
            "analysis": analysis,
            "domain_validation": validation,
            "metadata": {
                "domain": self.domain_config.domain_name,
                "provider": provider.__class__.__name__,
                "model": getattr(provider, 'model', 'unknown'),
                "timestamp": datetime.now().isoformat(),
            },
        }

        logger.info("Feasibility analysis complete")
        return result

    def _validate_technical_details(self, text: str) -> Dict[str, any]:
        """Validate technical details using domain expert.

        Args:
            text: Technical description

        Returns:
            Dictionary with validation results
        """
        validation = {}

        # Temperature validation
        temp_result = self.expert.validate_temperature_claim(text)
        if temp_result.get("temperatures_found"):
            validation["temperature"] = temp_result

        # Equipment design validation
        equip_result = self.expert.validate_equipment_design(text)
        if equip_result.get("equipment_mentioned"):
            validation["equipment"] = equip_result

        # Process type identification
        process_type = self.expert.identify_process_type(text)
        if process_type:
            validation["process_type"] = process_type
            # Get typical products for this process
            validation["expected_products"] = self.expert.get_typical_products_for_process(
                process_type
            )

        # Mass balance check
        mass_result = self.expert.check_mass_balance(text)
        if mass_result.get("yields_found"):
            validation["mass_balance"] = mass_result

        return validation

    def _build_prompt(
        self, text: str, validation: Dict, context: Optional[Dict] = None
    ) -> str:
        """Build full analysis prompt with validation context.

        Args:
            text: Technical description
            validation: Domain validation results
            context: Optional additional context

        Returns:
            Complete prompt string
        """
        prompt_parts = []

        # Add context if provided
        if context:
            if context.get("title"):
                prompt_parts.append(f"Project Title: {context['title']}\n")

        # Add main text
        prompt_parts.append(f"Technical Description:\n{text}\n")

        # Add domain validation insights
        if validation:
            prompt_parts.append("\n--- Domain Expert Validation ---")

            if "temperature" in validation:
                temp = validation["temperature"]
                if temp.get("all_valid"):
                    prompt_parts.append(
                        "✓ Temperature ranges are technically valid")
                else:
                    issues = temp.get("issues", [])
                    prompt_parts.append(
                        f"⚠ Temperature concerns: {'; '.join(issues)}")

            if "equipment" in validation:
                equip = validation["equipment"]
                if equip.get("recognized"):
                    prompt_parts.append(
                        f"✓ Equipment recognized: {', '.join(equip['recognized'])}")
                if equip.get("unrecognized"):
                    prompt_parts.append(
                        f"? Unknown equipment: {', '.join(equip['unrecognized'])}")

            if "process_type" in validation:
                process = validation["process_type"]
                prompt_parts.append(f"✓ Process identified: {process}")

            if "mass_balance" in validation:
                mass = validation["mass_balance"]
                if not mass.get("valid"):
                    prompt_parts.append(
                        f"⚠ Mass balance issue: {mass.get('message')}")
                else:
                    prompt_parts.append("✓ Mass balance appears valid")

        return "\n".join(prompt_parts)

    def analyze_pdf(self, pdf_path: str, context: Optional[Dict] = None) -> Dict[str, any]:
        """Analyze PDF document for feasibility.

        Args:
            pdf_path: Path to PDF file
            context: Optional additional context

        Returns:
            Analysis results dictionary
        """
        import pypdf
        
        logger.info(f"Parsing PDF: {pdf_path}")
        
        # Extract text from PDF using pypdf
        text_parts = []
        try:
            with open(pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text())
            text = '\n\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise ValueError(f"Could not extract text from PDF: {e}")

        return self.analyze(text, context)
