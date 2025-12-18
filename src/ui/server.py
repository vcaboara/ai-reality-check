"""Flask web interface for AI Reality Check."""

import json
import logging
import os
import shutil
import yaml
from datetime import datetime
from pathlib import Path

import markdown
from asmf.llm import ModelSelector, TaskType
from asmf.parsers import PDFParser
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from src.analyzers.feasibility_analyzer import FeasibilityAnalyzer
from src.utils.archive_handler import (
    ArchiveExtractionError,
    SecurityValidationError,
    is_archive_file,
    process_archive,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * \
    1024  # 50MB max file size (for archives)
app.config["UPLOAD_FOLDER"] = Path(
    __file__).parent.parent.parent / "data" / "uploads"
app.config["RESULTS_FOLDER"] = Path(
    __file__).parent.parent.parent / "data" / "results"

# Create directories
app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
app.config["RESULTS_FOLDER"].mkdir(parents=True, exist_ok=True)

# Metadata file for fast result listings
METADATA_FILE = app.config["RESULTS_FOLDER"] / "_metadata.json"

# Initialize analyzer
DOMAIN_CONFIG = Path(__file__).parent.parent.parent / "config" / "domain.yaml"
analyzer = FeasibilityAnalyzer(domain_config_path=DOMAIN_CONFIG)

# Load user preferences
USER_PREFS_CONFIG = Path(__file__).parent.parent.parent / \
    "config" / "user_preferences.yaml"
user_preferences = {}
if USER_PREFS_CONFIG.exists():
    with open(USER_PREFS_CONFIG, encoding="utf-8") as f:
        user_preferences = yaml.safe_load(f) or {}
    logger.info(f"Loaded user preferences from {USER_PREFS_CONFIG}")
else:
    logger.info("No user preferences file found, using defaults")

# Detect if running in container (skip GPU auto-detection if so)
in_container = os.path.exists(
    "/.dockerenv") or os.path.exists("/run/.containerenv")

# Load GPU config from user_preferences.yaml (required for containers)
try:
    hardware_config = user_preferences.get("hardware", {}).get("gpu", {})
    config_vram = hardware_config.get("vram_gb")

    if config_vram:
        # Use manual config from user_preferences.yaml
        selector = ModelSelector(vram_gb=config_vram)
        logger.info(
            f"Using GPU config from user_preferences.yaml: {config_vram}GB VRAM")

        recommended_model = selector.select_model(
            TaskType.DOCUMENT_ANALYSIS, check_availability=False
        )
        logger.info(
            f"Recommended model for {config_vram}GB VRAM: {recommended_model}")

        # Don't show warnings - user knows their hardware best
        # The config file documents available models for their VRAM tier
    elif in_container:
        # In container but no GPU config - skip detection
        logger.warning(
            "Running in container without GPU config in user_preferences.yaml - skipping GPU detection"
        )
        selector = None
        recommended_model = None
    else:
        # Not in container - auto-detect from system
        selector = ModelSelector()
        logger.info(
            f"Auto-detected: {selector.vram_gb}GB VRAM ({selector.gpu_vendor})")

        recommended_model = selector.select_model(
            TaskType.DOCUMENT_ANALYSIS, check_availability=False
        )
        logger.info(
            f"Recommended model for {selector.vram_gb}GB VRAM: {recommended_model}")
except Exception as e:
    logger.warning(f"Could not load GPU config: {e}")
    selector = None
    recommended_model = None

# In-memory conversation storage (for demo - use Redis/DB for production)
conversations: dict[str, list[dict]] = {}

# Note: .tar.gz handled specially
ALLOWED_EXTENSIONS = {"pdf", "txt", "zip", "tar", "tgz"}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    # Handle .tar.gz specially
    if filename.lower().endswith(".tar.gz"):
        return True
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(filepath: Path) -> str:
    """Extract text from a single file.

    Args:
        filepath: Path to file

    Returns:
        Extracted text content

    Raises:
        Exception: If file cannot be read
    """
    filename = filepath.name.lower()

    if filename.endswith(".pdf"):
        # PDFParser requires path at init, unavoidable per-file instantiation
        parser = PDFParser(str(filepath))
        return parser.extract_text()
    elif filename.endswith(".txt"):
        # Read text files directly
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def process_archive_files(archive_path: Path) -> str:
    """Process archive file and extract combined text from all supported files.

    Args:
        archive_path: Path to archive file

    Returns:
        Combined text from all supported files in archive

    Raises:
        ArchiveExtractionError: If extraction fails
        SecurityValidationError: If security checks fail
    """
    temp_dir = None
    try:
        # Extract archive and get supported files
        supported_files, temp_dir = process_archive(archive_path)

        if not supported_files:
            raise ValueError("No supported files (PDF, TXT) found in archive")

        # Extract text from each file
        combined_text = []
        for file_path in supported_files:
            try:
                text = extract_text_from_file(file_path)
                combined_text.append(
                    f"\n--- File: {file_path.name} ---\n{text}")
                logger.info(f"Extracted text from {file_path.name}")
            except Exception as e:
                logger.warning(
                    f"Failed to extract text from {file_path.name}: {e}")
                continue

        if not combined_text:
            raise ValueError(
                "Could not extract text from any files in archive")

        return "\n".join(combined_text)

    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp directory: {temp_dir}")


def load_metadata() -> list[dict]:
    """Load metadata from cached file."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                f"Could not load metadata: {e}, rebuilding from files")

    # Rebuild metadata from existing files
    return rebuild_metadata()


def rebuild_metadata() -> list[dict]:
    """Rebuild metadata by scanning all result files."""
    metadata = []
    for result_file in app.config["RESULTS_FOLDER"].glob("*.json"):
        if result_file.name == "_metadata.json":
            continue
        try:
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)
            metadata.append(
                {
                    "filename": result_file.name,
                    "title": data.get("title", "Untitled"),
                    # Handle missing timestamp
                    "timestamp": data.get("timestamp", ""),
                }
            )
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                f"Skipping invalid result file {result_file.name}: {e}")

    save_metadata(metadata)
    return metadata


def save_metadata(metadata: list[dict]) -> None:
    """Save metadata to cached file."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    except OSError as e:
        logger.error(f"Could not save metadata: {e}")


def add_result_metadata(filename: str, title: str, timestamp: str) -> None:
    """Add new result to metadata cache."""
    metadata = load_metadata()
    metadata.append(
        {"filename": filename, "title": title, "timestamp": timestamp})
    save_metadata(metadata)


def render_markdown_to_html(markdown_text: str) -> str:
    """Convert markdown text to sanitized HTML.
    
    Args:
        markdown_text: Raw markdown content
        
    Returns:
        HTML string with proper formatting
    """
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'nl2br',
        ],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'linenums': False,
            }
        }
    )
    return md.convert(markdown_text)


@app.route("/")
def index():
    """Render main page with model info."""
    # Model VRAM requirements
    model_vram = {
        "llama3.2:3b": "4GB",
        "phi3:mini": "2GB",
        "llama3.1:8b": "8GB",
        "qwen2.5-coder:7b": "8GB",
        "qwen2.5-coder:14b": "16GB",
        "qwen2.5-coder:32b": "32GB+",
    }

    # Get current model/provider info
    provider_name = (
        os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        if not os.getenv("GEMINI_API_KEY")
        else "Gemini"
    )
    provider_type = "Ollama" if not os.getenv(
        "GEMINI_API_KEY") else "Google Gemini"
    vram_required = model_vram.get(provider_name, "Unknown")

    # Add GPU detection info
    gpu_info = None
    if selector:
        gpu_info = {
            "vram_gb": selector.vram_gb,
            "vendor": selector.gpu_vendor,
            "recommended_model": recommended_model,
        }

    # Get user preference defaults
    project_prefs = user_preferences.get("project", {})
    default_title = project_prefs.get("default_title", "")
    default_context = project_prefs.get("default_context", "")

    return render_template(
        "index.html",
        current_model=provider_name,
        provider_type=provider_type,
        vram_required=vram_required,
        gpu_info=gpu_info,
        default_title=default_title,
        default_context=default_context,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze text or PDF for feasibility."""
    try:
        # Check if text input provided
        text_input = request.form.get("text")
        title = request.form.get("title", "Untitled Project")
        user_context = request.form.get("context", "")

        # Build context dict
        context = {"title": title}
        if user_context:
            context["additional_context"] = user_context

        result = None

        if text_input:
            # Analyze text directly
            logger.info(f"Analyzing text input: {title}")
            result = analyzer.analyze(text_input, context=context)

        elif "file" in request.files:
            # Analyze uploaded file(s)
            files = request.files.getlist("file")

            if not files or all(f.filename == "" for f in files):
                return jsonify({"error": "No file selected"}), 400

            # Process all files and combine text
            combined_text = []
            temp_archives = []  # Track archives for cleanup

            for file in files:
                if file.filename == "":
                    continue

                if not allowed_file(file.filename):
                    return (
                        jsonify(
                            {
                                "error": f"Invalid file type: {file.filename}. "
                                "Allowed: PDF, TXT, ZIP, TAR, TAR.GZ"
                            }
                        ),
                        400,
                    )

                # Save file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                filepath = app.config["UPLOAD_FOLDER"] / unique_filename

                file.save(filepath)
                logger.info(f"Saved upload: {filepath}")

                try:
                    # Check if it's an archive file
                    if is_archive_file(filename):
                        logger.info(f"Processing archive: {filename}")
                        # Extract and process archive
                        archive_text = process_archive_files(filepath)
                        combined_text.append(archive_text)
                        # Mark for later deletion
                        temp_archives.append(filepath)
                    elif filename.endswith(".pdf"):
                        # For PDFs, use the analyzer's PDF parsing
                        if len(files) == 1:
                            # Single PDF - use direct analysis
                            result = analyzer.analyze_pdf(
                                str(filepath), context=context)
                        else:
                            # Multiple files - extract text for combining
                            text = extract_text_from_file(filepath)
                            combined_text.append(
                                f"\n--- File: {filename} ---\n{text}")
                    else:
                        # Read text file
                        text = extract_text_from_file(filepath)
                        combined_text.append(
                            f"\n--- File: {filename} ---\n{text}")

                except (ArchiveExtractionError, SecurityValidationError, ValueError) as e:
                    logger.error(f"Error processing {filename}: {e}")
                    return jsonify({"error": str(e)}), 400

            # If multiple files or archives processed, analyze combined text
            if len(combined_text) > 0 and not result:
                result = analyzer.analyze(
                    "\n".join(combined_text), context=context)
            elif not result and len(files) == 1:
                # Single file case should have been handled above
                return jsonify({"error": "Failed to process file"}), 500

        else:
            return jsonify({"error": "No text or file provided"}), 400

        # Save result
        result_filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_path = app.config["RESULTS_FOLDER"] / result_filename
        timestamp = datetime.now().isoformat()

        # Convert markdown analysis to HTML for display
        if "analysis" in result and isinstance(result["analysis"], str):
            result["analysis_html"] = render_markdown_to_html(result["analysis"])

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"title": title, "timestamp": timestamp,
                      "result": result}, f, indent=2)

        logger.info(f"Saved result: {result_path}")

        # Update metadata cache
        add_result_metadata(result_filename, title, timestamp)

        return jsonify({"success": True, "result": result, "result_file": result_filename})

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/results")
def list_results():
    """Display results page."""
    return render_template("results.html")


@app.route("/api/results")
def api_list_results():
    """API endpoint to list all saved analysis results."""
    try:
        # Load from metadata cache (fast - single file read)
        metadata = load_metadata()

        # Sort by timestamp (newest first), handle None timestamps
        metadata.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

        return jsonify({"results": metadata})

    except Exception as e:
        logger.error(f"Error listing results: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/results/<filename>")
def get_result(filename):
    """Retrieve a specific analysis result."""
    try:
        result_path = app.config["RESULTS_FOLDER"] / secure_filename(filename)

        if not result_path.exists():
            return jsonify({"error": "Result not found"}), 404

        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        logger.error(f"Error retrieving result: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "domain": analyzer.domain_config.domain_name,
            "provider": analyzer.expert.__class__.__name__,
        }
    )


@app.route("/chat")
def chat_page():
    """Render interactive chat interface."""
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handle interactive chat messages with conversation context."""
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        session_id = data.get("session_id")
        # Get analysis context from frontend
        analysis_context = data.get("analysis_context")

        if not message:
            return jsonify({"error": "No message provided"}), 400

        if not session_id:
            return jsonify({"error": "No session ID provided"}), 400

        # Initialize conversation history for this session
        if session_id not in conversations:
            conversations[session_id] = []

        conversation = conversations[session_id]

        # Add user message to history
        conversation.append(
            {"role": "user", "content": message,
                "timestamp": datetime.now().isoformat()}
        )

        # Build context from conversation history
        context_text = "\n\n".join(
            [
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in conversation[-5:]  # Last 5 exchanges for context
            ]
        )

        # Get AI response with conversation context
        from asmf.providers import AIProviderFactory

        provider = AIProviderFactory.create_provider()

        # Build prompt with conversation context and analysis if available
        system_context = "You are a helpful technical expert providing interactive feasibility analysis. Be conversational, clear, and willing to clarify or expand on any point."

        if analysis_context and len(conversation) == 1:
            # First message with existing analysis - make AI aware of it
            prompt = f"""The user has a recent feasibility analysis. Here's the context:

PREVIOUS ANALYSIS:
{analysis_context.get('analysis', '')}

DOMAIN VALIDATION:
{json.dumps(analysis_context.get('domain_validation', {}), indent=2)}

The user is now asking: {message}

Please respond to their question with awareness of the previous analysis."""
        elif len(conversation) == 1:
            # First message - full feasibility analysis
            prompt = f"""Perform a feasibility analysis on the following project/idea:

{message}

Provide a structured response with:
1. FEASIBILITY & RISK - Technical viability and constraints
2. EFFICIENCY & OPTIMIZATION - Performance assessment
3. PROPOSED IMPROVEMENTS - Actionable recommendations

Be conversational and ready to answer follow-up questions."""
        else:
            # Follow-up question - use conversation context
            prompt = f"""Previous conversation:
{context_text}

New question: {message}

Provide a helpful, conversational response that builds on the previous discussion. Reference earlier points when relevant."""

        # Combine system context with user prompt for Ollama
        full_prompt = f"{system_context}\n\n{prompt}"

        response_text = provider.analyze_text(full_prompt)

        # Add assistant response to history
        conversation.append(
            {"role": "assistant", "content": response_text,
                "timestamp": datetime.now().isoformat()}
        )

        # Limit conversation history to prevent memory issues
        if len(conversation) > 20:
            conversation = conversation[-20:]
            conversations[session_id] = conversation

        logger.info(
            f"Chat response for session {session_id}: {len(response_text)} chars")

        return jsonify(
            {
                "success": True,
                "response": response_text,
                "message_count": len([m for m in conversation if m["role"] == "user"]),
            }
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"

    logger.info(f"Starting AI Reality Check server on port {port}")
    logger.info(f"Domain: {analyzer.domain_config.domain_name}")

    app.run(host="0.0.0.0", port=port, debug=debug)
