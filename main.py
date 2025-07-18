"""
Content Scorecard - Streamlit UI

This is the main entry point for the Content Scorecard application.
It provides a Streamlit-based user interface for evaluating content
against configurable guidelines.
"""

import os
import asyncio
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config.settings import load_app_config, validate_config
from config.models import AppConfig, EvaluationResult, MetricResult
from storage.guidelines import load_guidelines
from storage.reports import ReportStorage
from agents.llm_client import create_llm_client, LLMClientError, ConnectionTestResult
from agents.coordinator_agent import CoordinatorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = "config.toml"
MAX_CONTENT_LENGTH = 20000  # Maximum content length in characters
MAX_UPLOAD_SIZE = 1 * 1024 * 1024  # 1MB max file size
ALLOWED_EXTENSIONS = [".md", ".txt"]


def load_configuration() -> AppConfig:
    """Load application configuration."""
    try:
        config = load_app_config(CONFIG_PATH)
        return config
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        st.stop()


def validate_content(content: str) -> Tuple[bool, str]:
    """
    Validate the input content.
    
    Args:
        content: The content to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Content cannot be empty"
    
    if len(content) > MAX_CONTENT_LENGTH:
        return False, f"Content exceeds maximum length of {MAX_CONTENT_LENGTH} characters"
    
    return True, ""


def read_file_content(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Read content from an uploaded file.
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        Tuple of (success, content_or_error_message, file_name)
    """
    if uploaded_file is None:
        return False, "No file uploaded", None
    
    # Check file size
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return False, f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE/1024/1024:.1f}MB", None
    
    # Check file extension
    file_name = uploaded_file.name
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}", None
    
    try:
        # Read file content
        content = uploaded_file.read().decode("utf-8")
        return True, content, file_name
    except UnicodeDecodeError:
        return False, "File encoding not supported. Please upload a UTF-8 encoded text file.", None
    except Exception as e:
        return False, f"Error reading file: {e}", None


async def test_llm_connection(config: AppConfig) -> ConnectionTestResult:
    """
    Test the connection to the LLM provider.
    
    Args:
        config: Application configuration
        
    Returns:
        ConnectionTestResult with test results
    """
    try:
        llm_client = create_llm_client(config.llm)
        result = await llm_client.test_connection()
        return result
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Failed to connect to LLM provider",
            error=str(e),
            response_time=None
        )


def create_gauge_chart(score: float, title: str = "Overall Score") -> go.Figure:
    """
    Create a gauge chart for displaying the overall score.
    
    Args:
        score: The score to display (1-5)
        title: Title for the gauge
        
    Returns:
        Plotly figure object
    """
    # Define colors for different score ranges
    colors = {
        "poor": "red",
        "below_average": "orange",
        "average": "yellow",
        "good": "lightgreen",
        "excellent": "green"
    }
    
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 24}},
        gauge={
            "axis": {"range": [1, 5], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": "royalblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [1, 2], "color": colors["poor"]},
                {"range": [2, 3], "color": colors["below_average"]},
                {"range": [3, 4], "color": colors["average"]},
                {"range": [4, 4.5], "color": colors["good"]},
                {"range": [4.5, 5], "color": colors["excellent"]}
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": score
            }
        },
        number={"font": {"size": 36}, "suffix": "/5"}
    ))
    
    # Update layout
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={"color": "darkblue", "family": "Arial"}
    )
    
    return fig


def create_radar_chart(category_scores: Dict[str, float]) -> go.Figure:
    """
    Create a radar chart for displaying category scores.
    
    Args:
        category_scores: Dictionary mapping category names to scores
        
    Returns:
        Plotly figure object
    """
    # Prepare data
    categories = list(category_scores.keys())
    scores = list(category_scores.values())
    
    # Add the first category again to close the polygon
    categories.append(categories[0])
    scores.append(scores[0])
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        fillcolor='rgba(65, 105, 225, 0.5)',
        line=dict(color='royalblue', width=2),
        name="Category Scores"
    ))
    
    # Add reference line for maximum score
    fig.add_trace(go.Scatterpolar(
        r=[5] * len(categories),
        theta=categories,
        fill=None,
        line=dict(color='gray', width=1, dash='dash'),
        name="Maximum Score"
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["1", "2", "3", "4", "5"]
            )
        ),
        showlegend=False,
        height=400,
        margin=dict(l=80, r=80, t=20, b=20)
    )
    
    return fig


def display_metric_result(metric_result: MetricResult) -> None:
    """
    Display a single metric result in an expandable section.
    
    Args:
        metric_result: The metric result to display
    """
    # Create a color based on the score
    score_colors = {
        1: "red",
        2: "orange",
        3: "yellow",
        4: "lightgreen",
        5: "green"
    }
    score_color = score_colors.get(metric_result.score, "gray")
    
    # Display metric name and score
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {metric_result.metric.name.capitalize()}")
        st.markdown(f"*{metric_result.metric.description}*")
    with col2:
        st.markdown(
            f"<h2 style='text-align: center; color: {score_color};'>{metric_result.score}/5</h2>",
            unsafe_allow_html=True
        )
    
    # Display reasoning
    st.markdown("#### Reasoning")
    st.write(metric_result.reasoning)
    
    # Display improvement advice
    st.markdown("#### Improvement Advice")
    st.write(metric_result.improvement_advice)
    
    # Display positive examples
    if metric_result.positive_examples:
        st.markdown("#### Positive Examples")
        for example in metric_result.positive_examples:
            st.success(f'"{example}"')
    
    # Display improvement examples
    if metric_result.improvement_examples:
        st.markdown("#### Areas for Improvement")
        for example in metric_result.improvement_examples:
            st.warning(f'"{example}"')
    
    st.markdown("---")


def display_evaluation_results(result: EvaluationResult) -> None:
    """
    Display the complete evaluation results with visualizations.
    
    Args:
        result: The evaluation result to display
    """
    st.header("Evaluation Results")
    
    # Display overall score with gauge chart
    st.subheader("Overall Score")
    gauge_fig = create_gauge_chart(result.overall_score)
    st.plotly_chart(gauge_fig, use_container_width=True)
    
    # Display category scores with radar chart
    st.subheader("Category Scores")
    radar_fig = create_radar_chart(result.category_scores)
    st.plotly_chart(radar_fig, use_container_width=True)
    
    # Group metrics by category
    metrics_by_category: Dict[str, List[MetricResult]] = {}
    for metric_result in result.metric_results:
        category = metric_result.metric.category
        if category not in metrics_by_category:
            metrics_by_category[category] = []
        metrics_by_category[category].append(metric_result)
    
    # Display metrics by category in expandable sections
    st.subheader("Detailed Metric Results")
    
    for category, metrics in metrics_by_category.items():
        with st.expander(f"{category.capitalize()} - {len(metrics)} metrics"):
            for metric_result in metrics:
                display_metric_result(metric_result)


def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title="Content Scorecard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load configuration
    config = load_configuration()
    
    # Initialize session state
    if "content" not in st.session_state:
        st.session_state.content = ""
    if "evaluation_result" not in st.session_state:
        st.session_state.evaluation_result = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    
    # Application header
    st.title("Content Scorecard")
    st.markdown(
        "Evaluate your content against configurable guidelines using AI-powered analysis."
    )
    
    # Sidebar for configuration and actions
    with st.sidebar:
        st.header("Configuration")
        
        # LLM provider information
        st.subheader("LLM Provider")
        st.info(f"Provider: {config.llm.provider.upper()}\nModel: {config.llm.model_name}")
        
        # Test connection button
        if st.button("Test LLM Connection"):
            with st.spinner("Testing connection..."):
                result = asyncio.run(test_llm_connection(config))
                
                if result.success:
                    st.success(f"Connection successful! Response time: {result.response_time:.2f}s")
                else:
                    st.error(f"Connection failed: {result.message}")
                    if result.error:
                        st.error(f"Error: {result.error}")
        
        # Validation errors
        errors = validate_config(config)
        if errors:
            st.error("Configuration Errors:")
            for error in errors:
                st.error(f"- {error}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Content Input")
        
        # Tabs for different input methods
        tab1, tab2 = st.tabs(["Text Input", "File Upload"])
        
        with tab1:
            # Text input area
            content = st.text_area(
                "Enter your content here",
                value=st.session_state.content,
                height=300,
                max_chars=MAX_CONTENT_LENGTH,
                help="Enter the content you want to evaluate"
            )
            
            if content != st.session_state.content:
                st.session_state.content = content
                st.session_state.evaluation_result = None
        
        with tab2:
            # File upload
            uploaded_file = st.file_uploader(
                "Upload a file",
                type=ALLOWED_EXTENSIONS,
                help=f"Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )
            
            if uploaded_file is not None:
                success, result, file_name = read_file_content(uploaded_file)
                if success:
                    st.success(f"File '{file_name}' loaded successfully")
                    if result != st.session_state.content:
                        st.session_state.content = result
                        st.session_state.evaluation_result = None
                else:
                    st.error(result)
        
        # Evaluate button
        if st.button("Evaluate Content", type="primary", disabled=not st.session_state.content):
            # Validate content
            is_valid, error_message = validate_content(st.session_state.content)
            if not is_valid:
                st.error(error_message)
            else:
                # Clear previous results
                st.session_state.evaluation_result = None
                st.session_state.error_message = None
                
                with st.spinner("Evaluating content..."):
                    try:
                        # Create LLM client
                        llm_client = create_llm_client(config.llm)
                        
                        # Load guidelines
                        guidelines = load_guidelines(config.guidelines_path)
                        
                        # Create coordinator agent
                        coordinator = CoordinatorAgent(llm_client)
                        
                        # Evaluate content
                        result = asyncio.run(coordinator.evaluate_content(st.session_state.content, guidelines))
                        
                        # Store result in session state
                        st.session_state.evaluation_result = result
                        
                        # Save report to file system
                        report_storage = ReportStorage(config.reports_dir)
                        report_paths = report_storage.save_all_formats(result)
                        
                        # Show success message with report paths
                        st.success(f"Evaluation complete! Reports saved to: {', '.join(report_paths.values())}")
                        
                        st.session_state.error_message = None
                    except Exception as e:
                        st.session_state.error_message = str(e)
                        logger.exception("Error during evaluation")
        
        # Display error message if any
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
    
    with col2:
        st.subheader("Guidelines")
        
        # Load and display guidelines summary
        try:
            guidelines = load_guidelines(config.guidelines_path)
            
            # Display categories
            for category_name, category in guidelines.categories.items():
                with st.expander(f"{category_name.capitalize()} ({len(category.metrics)} metrics)"):
                    st.write(category.description)
                    
                    # List metrics in this category
                    for metric_name, metric in category.metrics.items():
                        st.markdown(f"**{metric_name.capitalize()}** (weight: {metric.weight})")
                        st.markdown(f"_{metric.description}_")
        except Exception as e:
            st.error(f"Error loading guidelines: {e}")
    
    # Results section
    if st.session_state.evaluation_result:
        display_evaluation_results(st.session_state.evaluation_result)


if __name__ == "__main__":
    main()