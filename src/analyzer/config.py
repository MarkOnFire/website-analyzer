"""Configuration file support for bug-finder and other tools.

Supports JSON and YAML configuration files with support for:
- Default scan settings (max-pages, max-depth, formats, etc.)
- Output directory preferences
- Pattern configurations
- Site-specific settings
- Command-line overrides
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class ScanSettings(BaseModel):
    """Default scan settings."""
    max_pages: int = Field(1000, description="Maximum pages to scan")
    max_depth: Optional[int] = Field(None, description="Maximum crawl depth")
    format: str = Field("txt", description="Output format: txt, csv, html, json, all")

    class Config:
        extra = "allow"  # Allow additional fields


class OutputSettings(BaseModel):
    """Output directory and format preferences."""
    output_dir: str = Field("projects", description="Base output directory")
    create_scans_subdir: bool = Field(True, description="Create 'scans' subdirectory for results")
    timestamp_results: bool = Field(True, description="Include timestamp in result filenames")

    class Config:
        extra = "allow"


class PatternSettings(BaseModel):
    """Pattern configuration settings."""
    case_sensitive: bool = Field(False, description="Whether pattern matching is case-sensitive")
    use_regex: bool = Field(True, description="Enable regex pattern matching")
    min_pattern_length: int = Field(5, description="Minimum length for generated patterns")

    class Config:
        extra = "allow"


class SiteSettings(BaseModel):
    """Site-specific configuration."""
    url: str = Field(..., description="Site URL")
    max_pages: Optional[int] = Field(None, description="Override default max_pages for this site")
    max_depth: Optional[int] = Field(None, description="Override default max_depth for this site")
    format: Optional[str] = Field(None, description="Override default format for this site")
    custom_patterns: Optional[list] = Field(None, description="Custom patterns to use for this site")
    exclude_patterns: Optional[list] = Field(None, description="URL patterns to exclude from scanning")

    class Config:
        extra = "allow"


class BugFinderConfig(BaseModel):
    """Root configuration for bug-finder tool."""
    scan_settings: ScanSettings = Field(default_factory=ScanSettings)
    output_settings: OutputSettings = Field(default_factory=OutputSettings)
    pattern_settings: PatternSettings = Field(default_factory=PatternSettings)
    site_specific: Dict[str, SiteSettings] = Field(default_factory=dict, description="Site-specific overrides")

    class Config:
        extra = "allow"  # Allow additional root-level fields


class ConfigLoader:
    """Load and manage configuration from files."""

    SUPPORTED_FORMATS = ['.json', '.yaml', '.yml']

    @staticmethod
    def load(config_path: Union[str, Path]) -> BugFinderConfig:
        """Load configuration from file.

        Args:
            config_path: Path to config file (JSON or YAML)

        Returns:
            BugFinderConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is unsupported or invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        suffix = config_path.suffix.lower()

        if suffix == '.json':
            return ConfigLoader._load_json(config_path)
        elif suffix in ['.yaml', '.yml']:
            return ConfigLoader._load_yaml(config_path)
        else:
            raise ValueError(f"Unsupported config format: {suffix}. Supported: {ConfigLoader.SUPPORTED_FORMATS}")

    @staticmethod
    def _load_json(config_path: Path) -> BugFinderConfig:
        """Load JSON configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BugFinderConfig(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    @staticmethod
    def _load_yaml(config_path: Path) -> BugFinderConfig:
        """Load YAML configuration file."""
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "YAML support requires PyYAML. Install with: pip install PyYAML"
            )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data is None:
                data = {}
            return BugFinderConfig(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    @staticmethod
    def save(config: BugFinderConfig, output_path: Union[str, Path], format: str = 'json') -> None:
        """Save configuration to file.

        Args:
            config: BugFinderConfig object to save
            output_path: Path where config will be saved
            format: Output format ('json' or 'yaml')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = config.model_dump(exclude_none=True, exclude_defaults=False)

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format in ['yaml', 'yml']:
            try:
                import yaml
            except ImportError:
                raise ImportError("YAML support requires PyYAML. Install with: pip install PyYAML")

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


class ConfigMerger:
    """Merge configuration from multiple sources with proper precedence."""

    @staticmethod
    def merge(
        config: BugFinderConfig,
        cli_overrides: Dict[str, Any],
        site_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Merge configuration with CLI overrides and site-specific settings.

        Precedence (highest to lowest):
        1. CLI arguments
        2. Site-specific settings
        3. Default settings in config file

        Args:
            config: BugFinderConfig loaded from file
            cli_overrides: Dictionary of CLI-provided overrides
            site_url: Optional site URL to apply site-specific settings

        Returns:
            Dictionary of merged settings
        """
        # Start with default scan settings
        merged = config.scan_settings.model_dump()

        # Apply site-specific overrides if applicable
        if site_url and site_url in config.site_specific:
            site_config = config.site_specific[site_url]
            site_data = site_config.model_dump(exclude_none=True)
            merged.update(site_data)

        # Apply CLI overrides (only for explicitly provided values)
        for key, value in cli_overrides.items():
            if value is not None:
                merged[key] = value

        return merged


def create_example_config(output_path: Union[str, Path], format: str = 'json') -> None:
    """Create an example configuration file.

    Args:
        output_path: Where to save the example config
        format: 'json' or 'yaml'
    """
    config = BugFinderConfig(
        scan_settings=ScanSettings(
            max_pages=1000,
            max_depth=None,
            format="txt"
        ),
        output_settings=OutputSettings(
            output_dir="projects",
            create_scans_subdir=True,
            timestamp_results=True
        ),
        pattern_settings=PatternSettings(
            case_sensitive=False,
            use_regex=True,
            min_pattern_length=5
        ),
        site_specific={
            "https://www.example.com": SiteSettings(
                url="https://www.example.com",
                max_pages=500,
                format="html",
                exclude_patterns=["*/admin/*", "*/api/*"]
            ),
            "https://www.wpr.org": SiteSettings(
                url="https://www.wpr.org",
                max_pages=2000,
                format="all"
            )
        }
    )

    ConfigLoader.save(config, output_path, format=format)
