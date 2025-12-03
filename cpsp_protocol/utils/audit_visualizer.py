"""
Audit Visualization utilities for CPSO-Protocol Multi-Agent System
Provides functions to visualize audit reports in a user-friendly manner.
"""

import json
from typing import Dict, Any, List
from ..nodes.advanced_auditor import StructuredAuditReport


def generate_audit_visualization(audit_report_json: str) -> Dict[str, Any]:
    """
    Generate visualization data from a structured audit report.
    
    Args:
        audit_report_json (str): JSON string of the structured audit report
        
    Returns:
        Dict[str, Any]: Visualization data for frontend display
    """
    try:
        # Parse the audit report
        audit_report_dict = json.loads(audit_report_json)
        audit_report = StructuredAuditReport(**audit_report_dict)
        
        # Generate severity distribution
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        for finding in audit_report.findings:
            severity_counts[finding.severity] += 1
            
        # Generate dimension distribution
        dimension_counts = {}
        for finding in audit_report.findings:
            if finding.dimension in dimension_counts:
                dimension_counts[finding.dimension] += 1
            else:
                dimension_counts[finding.dimension] = 1
                
        # Generate severity by dimension
        severity_by_dimension = {}
        for finding in audit_report.findings:
            if finding.dimension not in severity_by_dimension:
                severity_by_dimension[finding.dimension] = {"low": 0, "medium": 0, "high": 0}
            severity_by_dimension[finding.dimension][finding.severity] += 1
            
        # Prepare visualization data
        visualization_data = {
            "summary": {
                "overall_status": audit_report.overall_status,
                "score": audit_report.score,
                "total_findings": len(audit_report.findings),
                "generated_at": audit_report.generated_at.isoformat() if audit_report.generated_at else None
            },
            "charts": {
                "severity_distribution": severity_counts,
                "dimension_distribution": dimension_counts,
                "severity_by_dimension": severity_by_dimension
            },
            "findings": [
                {
                    "dimension": finding.dimension,
                    "severity": finding.severity,
                    "description": finding.description,
                    "recommendation": finding.recommendation,
                    "location": finding.location
                }
                for finding in audit_report.findings
            ]
        }
        
        return visualization_data
    except Exception as e:
        # Return a basic visualization if parsing fails
        return {
            "summary": {
                "overall_status": "unknown",
                "score": 0,
                "total_findings": 0,
                "error": str(e)
            },
            "charts": {
                "severity_distribution": {"low": 0, "medium": 0, "high": 0},
                "dimension_distribution": {},
                "severity_by_dimension": {}
            },
            "findings": []
        }


def generate_html_report(visualization_data: Dict[str, Any]) -> str:
    """
    Generate an HTML report from visualization data.
    
    Args:
        visualization_data (Dict[str, Any]): Visualization data from generate_audit_visualization
        
    Returns:
        str: HTML formatted report
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit Report Visualization</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
            .summary {{ display: flex; justify-content: space-between; margin: 20px 0; }}
            .summary-item {{ text-align: center; padding: 10px; }}
            .score {{ font-size: 24px; font-weight: bold; }}
            .status-pass {{ color: green; }}
            .status-conditional {{ color: orange; }}
            .status-reject {{ color: red; }}
            .chart-container {{ margin: 20px 0; }}
            .findings {{ margin: 20px 0; }}
            .finding {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }}
            .finding.high {{ border-left: 5px solid red; }}
            .finding.medium {{ border-left: 5px solid orange; }}
            .finding.low {{ border-left: 5px solid green; }}
            .severity-high {{ color: red; }}
            .severity-medium {{ color: orange; }}
            .severity-low {{ color: green; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Audit Report Visualization</h1>
        </div>
        
        <div class="summary">
            <div class="summary-item">
                <div>Overall Status</div>
                <div class="status-{status_class}">{overall_status}</div>
            </div>
            <div class="summary-item">
                <div>Score</div>
                <div class="score">{score}</div>
            </div>
            <div class="summary-item">
                <div>Total Findings</div>
                <div>{total_findings}</div>
            </div>
        </div>
        
        <div class="charts">
            <h2>Charts</h2>
            <!-- In a full implementation, charts would be rendered here using a library like Chart.js -->
            <div class="chart-container">
                <h3>Severity Distribution</h3>
                <pre>{severity_dist}</pre>
            </div>
            
            <div class="chart-container">
                <h3>Findings by Dimension</h3>
                <pre>{dimension_dist}</pre>
            </div>
        </div>
        
        <div class="findings">
            <h2>Detailed Findings</h2>
            {findings_html}
        </div>
    </body>
    </html>
    """
    
    # Determine status class for coloring
    status_class = "unknown"
    if visualization_data["summary"]["overall_status"] == "pass":
        status_class = "pass"
    elif visualization_data["summary"]["overall_status"] == "conditional":
        status_class = "conditional"
    elif visualization_data["summary"]["overall_status"] == "reject":
        status_class = "reject"
    
    # Generate findings HTML
    findings_html = ""
    for finding in visualization_data["findings"]:
        findings_html += f"""
        <div class="finding {finding['severity']}">
            <h3>{finding['dimension'].title()} - <span class="severity-{finding['severity']}">{finding['severity'].title()}</span></h3>
            <p><strong>Description:</strong> {finding['description']}</p>
            <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
            {f"<p><strong>Location:</strong> {finding['location']}</p>" if finding['location'] else ""}
        </div>
        """
    
    return html_template.format(
        status_class=status_class,
        overall_status=visualization_data["summary"]["overall_status"].title(),
        score=visualization_data["summary"]["score"],
        total_findings=visualization_data["summary"]["total_findings"],
        severity_dist=json.dumps(visualization_data["charts"]["severity_distribution"], indent=2),
        dimension_dist=json.dumps(visualization_data["charts"]["dimension_distribution"], indent=2),
        findings_html=findings_html
    )