"""
AgriGrantCoach Configuration Module

Centralized configuration management for all environment variables and settings.
This module loads configuration from .env file and provides typed access to settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the parent directory of the AgriGrantCoach folder
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Centralized configuration class with all settings."""

    # ===========================================
    # API Configuration
    # ===========================================
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    OPENALEX_EMAIL: str = os.getenv('OPENALEX_EMAIL', '')

    # ===========================================
    # Model Configuration
    # ===========================================
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    GROQ_MODEL: str = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
    GROQ_ANALYSIS_MODEL: str = os.getenv('GROQ_ANALYSIS_MODEL', 'llama-3.1-70b-versatile')
    GROQ_ANALYSIS_TEMPERATURE: float = float(os.getenv('GROQ_ANALYSIS_TEMPERATURE', '0.2'))
    GROQ_ANALYSIS_MAX_TOKENS: int = int(os.getenv('GROQ_ANALYSIS_MAX_TOKENS', '4000'))

    # ===========================================
    # Path Configuration
    # ===========================================
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = Path(os.getenv('AGRIGRANTCOACH_DATA_DIR', BASE_DIR / 'data'))
    OUTPUT_DIR: Path = Path(os.getenv('AGRIGRANTCOACH_OUTPUT_DIR', BASE_DIR / 'output'))

    # Data subdirectories
    SOLICITATION_DIR: Path = DATA_DIR / 'solicitation'
    NARRATIVE_DIR: Path = DATA_DIR / 'narrative'
    BIOSKETCHES_DIR: Path = DATA_DIR / 'biosketches'
    CPS_DIR: Path = DATA_DIR / 'cps'

    # ===========================================
    # Analysis Parameters
    # ===========================================
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '512'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '50'))
    TOP_K_MATCHES: int = int(os.getenv('TOP_K_MATCHES', '5'))
    CONFIDENCE_THRESHOLD: float = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
    SEMANTIC_SIMILARITY_THRESHOLD: float = float(os.getenv('SEMANTIC_SIMILARITY_THRESHOLD', '0.65'))

    # ===========================================
    # Personnel Identifiers
    # ===========================================
    # Extracted from the uploaded files
    PERSONNEL_NAMES = ['Ekin', 'Dey', 'OChen', 'qasem', 'Pratheesh']

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration is present.

        Returns:
            bool: True if configuration is valid, raises ValueError otherwise.
        """
        errors = []

        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set in .env file")

        if not cls.DATA_DIR.exists():
            errors.append(f"Data directory does not exist: {cls.DATA_DIR}")

        if not cls.OUTPUT_DIR.exists():
            cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def get_solicitation_path(cls) -> Path:
        """Get the path to the solicitation PDF file."""
        solicitation_files = list(cls.SOLICITATION_DIR.glob('*.pdf'))
        if not solicitation_files:
            raise FileNotFoundError(f"No solicitation PDF found in {cls.SOLICITATION_DIR}")
        return solicitation_files[0]

    @classmethod
    def get_narrative_path(cls) -> Path:
        """Get the path to the narrative DOCX file."""
        narrative_files = list(cls.NARRATIVE_DIR.glob('*.docx'))
        if not narrative_files:
            raise FileNotFoundError(f"No narrative DOCX found in {cls.NARRATIVE_DIR}")
        return narrative_files[0]

    @classmethod
    def display_config(cls) -> str:
        """
        Display current configuration (for debugging).

        Returns:
            str: Formatted configuration string.
        """
        return f"""
╔══════════════════════════════════════════════════════════════╗
║           AgriGrantCoach Configuration                       ║
╠══════════════════════════════════════════════════════════════╣
║ API Keys:
║   - Groq API Key: {'✓ Set' if cls.GROQ_API_KEY else '✗ Missing'}
║   - OpenAlex Email: {cls.OPENALEX_EMAIL or '✗ Not set'}
║
║ Models:
║   - Embedding Model: {cls.EMBEDDING_MODEL}
║   - Analysis Model: {cls.GROQ_ANALYSIS_MODEL}
║   - Temperature: {cls.GROQ_ANALYSIS_TEMPERATURE}
║
║ Paths:
║   - Data Directory: {cls.DATA_DIR}
║   - Output Directory: {cls.OUTPUT_DIR}
║
║ Analysis Parameters:
║   - Chunk Size: {cls.CHUNK_SIZE}
║   - Chunk Overlap: {cls.CHUNK_OVERLAP}
║   - Top K Matches: {cls.TOP_K_MATCHES}
║   - Confidence Threshold: {cls.CONFIDENCE_THRESHOLD}
║
║ Personnel: {', '.join(cls.PERSONNEL_NAMES)}
╚══════════════════════════════════════════════════════════════╝
        """.strip()


# Validate configuration on import
if __name__ == "__main__":
    try:
        Config.validate()
        print("✓ Configuration is valid")
        print(Config.display_config())
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
