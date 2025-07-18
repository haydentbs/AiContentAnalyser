#!/usr/bin/env python3
"""Example script demonstrating how to use the CoordinatorAgent with visualization.

This script loads configuration, creates an LLM client and CoordinatorAgent,
runs an evaluation on a sample piece of content, and visualizes the results
using the same components as the Streamlit UI.
"""

import asyncio
import logging
import sys
import tomli
import argparse
import webbrowser
import os
import tempfile
from pathlib import Path

from config.models import LLMConfig
from agents.llm_client import create_llm_client, LLMClientError
from agents.coordinator_agent import CoordinatorAgent
from storage.guidelines import load_guidelines, get_default_guidelines
from storage.reports import ReportStorage, ReportGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Sample content for evaluation
SAMPLE_CONTENT = """# This is my investment report for this month or maybe even longer. I'm not sure exactly when everything was bought but I know there was some stocks and crypto and maybe also ETF, but I will talk about that later. The market has been going up and down a lot lately, which is very stressful and confusing and hard to keep track of everything at once. But anyway, I think it's important to have some kind of record about my portfolio even if the results are not the best right now. I did not use any kind of plan or strategy really but more went with instincts and things I saw online like Reddit and TikTok or sometimes just vibes.

So in the portfolio there's a mix of stuff like Tesla which I got because Elon Musk is in charge and he does a lot of crazy things so I thought the stock would just keep going up. But it didn't really. It went down a lot actually but I didn't sell because that would feel like giving up and also maybe it will go back up later. I also got Apple because everyone uses iPhones and they always launching new stuff so it felt like a safe one to put some money in. Amazon is another one I added because they have the website and also AWS which I heard is important but I don't really know much about that. All those tech companies were down a bit recently so my portfolio isn't great.

I got some Bitcoin too because people were saying it's like gold but digital and you don't have to trust banks, which I liked the sound of. At first it was going up and I was very excited but then it dropped again and I got nervous. I still didn't sell though because what if it goes back up and I miss it? So now it's just sitting there and I'm checking the price all the time. There's also maybe some Ethereum in there but I can't remember how much. I think I bought it on a weekend after seeing someone tweet about it.

One time I bought an ETF too which is kind of like buying a bunch of stocks at once, I think. I don't remember which one but I think it has the word "growth" in it. I figured if I don't know which company to pick it's better to just buy a basket of them all. The ETF has been a bit boring because the price barely moves but I guess that's better than crashing. I also have some cash in the account but I'm waiting for a dip before using it, unless I forget and spend it on something else.

Right now I think the portfolio is down overall. I didn't write down all the prices I bought stuff at which makes it hard to really calculate. But looking at the numbers now it feels like I lost some money but I'm not panicking. Everyone says you have to zoom out and think long term. So that's what I'm trying to do. Even if it's not looking good today, maybe in like 10 years it will look amazing and I'll be glad I didn't sell everything in a panic.

In conclusion the portfolio is a work in progress and I still believe in some of the stocks and coins I picked. It's not perfect but it's something. Going forward I might do more research or maybe ask someone who knows more, or maybe just keep doing what I'm doing but with a bit more luck. Investing is hard sometimes but I think if I just hang in there it might all work out eventually.
"""


def create_html_visualization(result, output_path=None):
    """
    Create an HTML visualization of the evaluation results.
    
    Args:
        result: The evaluation result
        output_path: Path to save the HTML file (if None, uses a temporary file)
        
    Returns:
        Path to the HTML file
    """
    try:
        import plotly.io as pio
        from main import create_gauge_chart, create_radar_chart
        
        # Create gauge chart
        gauge_fig = create_gauge_chart(result.overall_score)
        gauge_html = pio.to_html(gauge_fig, include_plotlyjs='cdn', full_html=False)
        
        # Create radar chart
        radar_fig = create_radar_chart(result.category_scores)
        radar_html = pio.to_html(radar_fig, include_plotlyjs='cdn', full_html=False)
        
        # Generate markdown report
        md_report = ReportGenerator.to_markdown(result)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Content Scorecard - Evaluation Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .chart-container {{ margin: 20px 0; }}
                .metric {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .metric-header {{ display: flex; justify-content: space-between; align-items: center; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .score-1 {{ color: red; }}
                .score-2 {{ color: orange; }}
                .score-3 {{ color: #cccc00; }}
                .score-4 {{ color: lightgreen; }}
                .score-5 {{ color: green; }}
                .section {{ margin: 10px 0; }}
                .positive {{ background-color: #e6ffe6; padding: 10px; border-left: 4px solid green; margin: 5px 0; }}
                .improvement {{ background-color: #fff2e6; padding: 10px; border-left: 4px solid orange; margin: 5px 0; }}
                h1, h2, h3 {{ color: #333; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>Content Scorecard - Evaluation Results</h1>
            <p>Generated: {result.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Overall Score: {result.overall_score:.2f}/5.00</h2>
            <div class="chart-container">
                {gauge_html}
            </div>
            
            <h2>Category Scores</h2>
            <div class="chart-container">
                {radar_html}
            </div>
            
            <h2>Detailed Metric Results</h2>
        """
        
        # Group metrics by category
        metrics_by_category = {}
        for metric_result in result.metric_results:
            category = metric_result.metric.category
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(metric_result)
        
        # Add metrics by category
        for category, metrics in metrics_by_category.items():
            html_content += f"<h3>{category.capitalize()}</h3>"
            
            for metric_result in metrics:
                score_class = f"score-{metric_result.score}"
                html_content += f"""
                <div class="metric">
                    <div class="metric-header">
                        <h4>{metric_result.metric.name.capitalize()}</h4>
                        <span class="score {score_class}">{metric_result.score}/5</span>
                    </div>
                    <p><em>{metric_result.metric.description}</em></p>
                    
                    <div class="section">
                        <h5>Reasoning</h5>
                        <p>{metric_result.reasoning}</p>
                    </div>
                    
                    <div class="section">
                        <h5>Improvement Advice</h5>
                        <p>{metric_result.improvement_advice}</p>
                    </div>
                """
                
                # Add positive examples
                if metric_result.positive_examples:
                    html_content += "<div class='section'><h5>Positive Examples</h5>"
                    for example in metric_result.positive_examples:
                        html_content += f"<div class='positive'>\"{example}\"</div>"
                    html_content += "</div>"
                
                # Add improvement examples
                if metric_result.improvement_examples:
                    html_content += "<div class='section'><h5>Areas for Improvement</h5>"
                    for example in metric_result.improvement_examples:
                        html_content += f"<div class='improvement'>\"{example}\"</div>"
                    html_content += "</div>"
                
                html_content += "</div>"
        
        # Add metadata
        if result.metadata:
            html_content += "<h2>Metadata</h2><ul>"
            for key, value in result.metadata.items():
                html_content += f"<li><strong>{key}:</strong> {value}</li>"
            html_content += "</ul>"
        
        # Close HTML
        html_content += """
        </body>
        </html>
        """
        
        # Save to file
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".html", prefix="scorecard_")
            os.close(fd)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return output_path
    except ImportError as e:
        logger.error(f"Error importing visualization dependencies: {e}")
        logger.error("Make sure plotly is installed: pip install plotly")
        return None
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        return None


async def main():
    """Run the example evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate content using the Content Scorecard")
    parser.add_argument("--file", "-f", help="Path to a file containing content to evaluate")
    parser.add_argument("--config", "-c", default="config.toml", help="Path to configuration file")
    parser.add_argument("--visualize", "-v", action="store_true", help="Open visualization in browser")
    parser.add_argument("--output", "-o", help="Path to save visualization HTML (only with --visualize)")
    args = parser.parse_args()
    
    try:
        # Load content from file if specified
        content = SAMPLE_CONTENT
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(f"Loaded content from {args.file}")
            except Exception as e:
                logger.error(f"Error loading file: {e}")
                return
        
        # Load configuration from config.toml
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config file not found: {args.config}")
            return
        
        logger.info(f"Loading configuration from {config_path}")
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        # Create LLM configuration
        llm_config = LLMConfig(**config_data["llm"])
        
        # If API key is not in the config, try to get it from the openai section
        if not llm_config.api_key and llm_config.provider == "openai" and "openai" in config_data:
            llm_config.api_key = config_data["openai"].get("api_key")
        
        logger.info(f"Using LLM provider: {llm_config.provider}, model: {llm_config.model_name}")
        
        # Create LLM client
        llm_client = create_llm_client(llm_config)
        
        # Test LLM connection
        logger.info("Testing LLM connection...")
        connection_test = await llm_client.test_connection()
        if not connection_test.success:
            logger.error(f"LLM connection failed: {connection_test.error}")
            return
        
        logger.info(f"LLM connection successful: {connection_test.message}")
        
        # Load guidelines (or use defaults)
        guidelines_path = config_data.get("app", {}).get("guidelines_path", "guidelines.yaml")
        logger.info(f"Loading guidelines from {guidelines_path}")
        guidelines = load_guidelines(guidelines_path)
        
        # Create CoordinatorAgent
        coordinator = CoordinatorAgent(llm_client, max_concurrent_evaluations=2)
        
        # Run the evaluation
        logger.info("Starting content evaluation")
        result = await coordinator.evaluate_content(content, guidelines)
        
        # Display the results
        print("\n" + "="*50)
        print("Content Evaluation Results")
        print("="*50)
        print(f"Overall Score: {result.overall_score:.2f}/5.00")
        print("\nCategory Scores:")
        for category, score in result.category_scores.items():
            print(f"  {category.capitalize()}: {score:.2f}/5.00")
        
        print("\nIndividual Metric Results:")
        for metric_result in result.metric_results:
            print(f"\n{'-'*40}")
            print(f"Metric: {metric_result.metric.name} ({metric_result.metric.category})")
            print(f"Score: {metric_result.score}/5")
            print(f"Reasoning: {metric_result.reasoning[:100]}...")
            print(f"Improvement Advice: {metric_result.improvement_advice[:100]}...")
            print("Positive Examples:")
            for i, example in enumerate(metric_result.positive_examples[:2], 1):
                print(f"  {i}. {example[:50]}...")
            print("Improvement Examples:")
            for i, example in enumerate(metric_result.improvement_examples[:2], 1):
                print(f"  {i}. {example[:50]}...")
        
        print("="*50)
        
        # Save reports
        reports_dir = config_data.get("app", {}).get("reports_dir", "reports")
        logger.info(f"Saving reports to {reports_dir} directory")
        
        report_storage = ReportStorage(reports_dir=reports_dir)
        
        # Save in both JSON and Markdown formats
        report_paths = report_storage.save_all_formats(result)
        
        print("\nReports saved:")
        print(f"JSON Report: {report_paths['json']}")
        print(f"Markdown Report: {report_paths['markdown']}")
        
        # Create visualization if requested
        if args.visualize:
            html_path = create_html_visualization(result, args.output)
            if html_path:
                logger.info(f"Opening visualization in browser: {html_path}")
                webbrowser.open(f"file://{os.path.abspath(html_path)}")
        
    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())