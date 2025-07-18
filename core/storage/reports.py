"""Report generation and storage system.

This module provides functionality for generating and storing evaluation reports
in both JSON and Markdown formats. It handles file naming with timestamps and content
hashes, and implements local file system storage in the reports directory.
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

from ..config.models import EvaluationResult


# Set up logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generator for evaluation reports in different formats."""
    
    @staticmethod
    def to_json(result: EvaluationResult, pretty: bool = True) -> str:
        """Convert an EvaluationResult to a JSON string.
        
        Args:
            result: The evaluation result to convert
            pretty: Whether to format the JSON with indentation
            
        Returns:
            JSON string representation of the evaluation result
        """
        # Convert to dict using Pydantic's model_dump method
        result_dict = result.model_dump()
        
        # Format the timestamp as ISO format string for better JSON compatibility
        if isinstance(result_dict.get("timestamp"), datetime):
            result_dict["timestamp"] = result_dict["timestamp"].isoformat()
        
        # Convert to JSON
        indent = 2 if pretty else None
        return json.dumps(result_dict, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def to_markdown(result: EvaluationResult) -> str:
        """Convert an EvaluationResult to a Markdown string.
        
        Args:
            result: The evaluation result to convert
            
        Returns:
            Markdown string representation of the evaluation result
        """
        # Format timestamp
        timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Start building the markdown content
        md_lines = [
            "# Content Evaluation Report",
            f"Generated: {timestamp_str}",
            f"Content Hash: {result.content_hash}",
            "",
            f"## Overall Score: {result.overall_score:.2f}/5.00",
            "",
            "## Category Scores",
            ""
        ]
        
        # Add category scores
        for category, score in result.category_scores.items():
            md_lines.append(f"- **{category.capitalize()}**: {score:.2f}/5.00")
        
        md_lines.append("\n## Metric Results\n")
        
        # Group metrics by category
        metrics_by_category: Dict[str, list] = {}
        for metric_result in result.metric_results:
            category = metric_result.metric.category
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(metric_result)
        
        # Add metrics by category
        for category, metrics in metrics_by_category.items():
            md_lines.append(f"### {category.capitalize()}\n")
            
            for metric_result in metrics:
                md_lines.append(f"#### {metric_result.metric.name.capitalize()}")
                md_lines.append(f"*{metric_result.metric.description}*\n")
                md_lines.append(f"**Score**: {metric_result.score}/5")
                md_lines.append(f"**Reasoning**: {metric_result.reasoning}")
                md_lines.append(f"**Improvement Advice**: {metric_result.improvement_advice}\n")
                
                # Add positive examples
                if metric_result.positive_examples:
                    md_lines.append("**Positive Examples**:")
                    for example in metric_result.positive_examples:
                        md_lines.append(f"- \"{example}\"")
                    md_lines.append("")
                
                # Add improvement examples
                if metric_result.improvement_examples:
                    md_lines.append("**Improvement Examples**:")
                    for example in metric_result.improvement_examples:
                        md_lines.append(f"- \"{example}\"")
                    md_lines.append("")
        
        # Add metadata
        if result.metadata:
            md_lines.append("## Metadata\n")
            for key, value in result.metadata.items():
                md_lines.append(f"- **{key}**: {value}")
        
        return "\n".join(md_lines)


class ReportStorage:
    """Storage system for evaluation reports."""
    
    def __init__(self, reports_dir: str = "reports"):
        """Initialize the report storage.
        
        Args:
            reports_dir: Directory path for storing reports
        """
        self.reports_dir = reports_dir
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def ensure_reports_directory(self) -> None:
        """Ensure the reports directory exists.
        
        Creates the reports directory if it doesn't exist.
        
        Raises:
            OSError: If the directory cannot be created
        """
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
            self.logger.debug(f"Ensured reports directory exists: {self.reports_dir}")
        except OSError as e:
            self.logger.error(f"Failed to create reports directory: {e}")
            raise
    
    def generate_filename(self, result: EvaluationResult, extension: str) -> str:
        """Generate a filename for a report.
        
        Args:
            result: The evaluation result
            extension: File extension (e.g., 'json', 'md')
            
        Returns:
            Filename with timestamp and content hash
        """
        # Format timestamp for filename (without special characters)
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Use the first 8 characters of the content hash
        short_hash = result.content_hash[:8]
        
        # Generate filename
        return f"report_{timestamp}_{short_hash}.{extension}"
    
    def save_report(
        self, 
        result: EvaluationResult, 
        format_type: str = "json",
        custom_filename: Optional[str] = None
    ) -> str:
        """Save an evaluation report to the file system.
        
        Args:
            result: The evaluation result to save
            format_type: Report format ('json' or 'md')
            custom_filename: Optional custom filename
            
        Returns:
            Path to the saved report file
            
        Raises:
            ValueError: If the format type is invalid
            OSError: If the file cannot be written
        """
        # Validate format type
        if format_type.lower() not in ["json", "md", "markdown"]:
            raise ValueError(f"Invalid format type: {format_type}. Must be 'json' or 'md'/'markdown'")
        
        # Ensure reports directory exists
        self.ensure_reports_directory()
        
        # Generate filename if not provided
        extension = "json" if format_type.lower() == "json" else "md"
        filename = custom_filename or self.generate_filename(result, extension)
        
        # Create full file path
        file_path = os.path.join(self.reports_dir, filename)
        
        try:
            # Generate report content
            if format_type.lower() == "json":
                content = ReportGenerator.to_json(result)
            else:  # md or markdown
                content = ReportGenerator.to_markdown(result)
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.logger.info(f"Saved {format_type} report to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            raise
    
    def save_all_formats(
        self, 
        result: EvaluationResult,
        custom_prefix: Optional[str] = None
    ) -> Dict[str, str]:
        """Save an evaluation report in all supported formats.
        
        Args:
            result: The evaluation result to save
            custom_prefix: Optional custom filename prefix
            
        Returns:
            Dictionary mapping format types to file paths
            
        Raises:
            OSError: If any file cannot be written
        """
        # Generate a common prefix if provided
        prefix = custom_prefix or f"report_{result.timestamp.strftime('%Y%m%d_%H%M%S')}_{result.content_hash[:8]}"
        
        # Save in each format
        paths = {}
        try:
            # Save JSON
            json_filename = f"{prefix}.json"
            json_path = self.save_report(result, "json", json_filename)
            paths["json"] = json_path
            
            # Save Markdown
            md_filename = f"{prefix}.md"
            md_path = self.save_report(result, "md", md_filename)
            paths["markdown"] = md_path
            
            return paths
            
        except Exception as e:
            self.logger.error(f"Failed to save reports in all formats: {e}")
            raise
    
    def load_report(self, file_path: Union[str, Path]) -> EvaluationResult:
        """Load an evaluation report from a file.
        
        Args:
            file_path: Path to the report file (JSON format)
            
        Returns:
            Loaded EvaluationResult
            
        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Report file not found: {file_path}")
        
        if path.suffix.lower() != ".json":
            raise ValueError(f"Unsupported file format: {path.suffix}. Only JSON files can be loaded.")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert the loaded data back to an EvaluationResult
            return EvaluationResult.model_validate(data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load report from {file_path}: {e}")
            raise
    
    def load_report_by_content_hash(self, content_hash: str) -> Optional[EvaluationResult]:
        """Load a report by its content hash.
        
        Args:
            content_hash: The content hash to search for
            
        Returns:
            The loaded EvaluationResult, or None if not found
            
        Raises:
            FileNotFoundError: If no report file is found with the given content hash
        """
        # Ensure reports directory exists
        if not os.path.exists(self.reports_dir):
            raise FileNotFoundError(f"Reports directory not found: {self.reports_dir}")
        
        # Look for files that contain this content hash
        # Files are named like: report_20250718_155620_9de7d1fd.json
        # where 9de7d1fd is the first 8 chars of the content hash
        short_hash = content_hash[:8] if len(content_hash) >= 8 else content_hash
        
        # Search for files with this hash pattern
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.json') and short_hash in filename:
                file_path = os.path.join(self.reports_dir, filename)
                try:
                    # Load the report and check if the content hash matches
                    report = self.load_report(file_path)
                    if report.content_hash == content_hash:
                        return report
                except Exception as e:
                    self.logger.warning(f"Failed to load report from {filename}: {e}")
                    continue
        
        # If not found by short hash, try searching all JSON files
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.reports_dir, filename)
                try:
                    report = self.load_report(file_path)
                    if report.content_hash == content_hash:
                        return report
                except Exception as e:
                    self.logger.warning(f"Failed to load report from {filename}: {e}")
                    continue
        
        # Not found
        return None
    
    def get_report_path(self, content_hash: str, format_type: str) -> Optional[str]:
        """Get the file path for a report by content hash and format.
        
        Args:
            content_hash: The content hash to search for
            format_type: The format type ('json' or 'md')
            
        Returns:
            The file path if found, None otherwise
        """
        if not os.path.exists(self.reports_dir):
            return None
            
        extension = "json" if format_type.lower() == "json" else "md"
        short_hash = content_hash[:8] if len(content_hash) >= 8 else content_hash
        
        # Search for files with this hash pattern and extension
        for filename in os.listdir(self.reports_dir):
            if filename.endswith(f'.{extension}') and short_hash in filename:
                file_path = os.path.join(self.reports_dir, filename)
                # For JSON files, verify the content hash matches
                if extension == "json":
                    try:
                        report = self.load_report(file_path)
                        if report.content_hash == content_hash:
                            return file_path
                    except Exception:
                        continue
                else:
                    # For markdown files, assume it matches if the hash is in the filename
                    return file_path
        
        return None