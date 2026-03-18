#!/usr/bin/env python3
"""
Professional HTML Report Generator for SDN Conflict Detection Results
Creates clean, publication-ready visualizations
"""

import json
import sys

def generate_html_report(json_file):
    with open(json_file, 'r') as f:
        results = json.load(f)
    
    algorithms = ['DT', 'SVM', 'EFDT', 'Hybrid_DT_SVM']
    alg_labels = ['Decision Tree', 'SVM', 'EFDT', 'Hybrid DT-SVM']
    
    # Extract data
    accuracy = [results[alg]['accuracy'] for alg in algorithms]
    precision = [results[alg]['precision'] for alg in algorithms]
    recall = [results[alg]['recall'] for alg in algorithms]
    f1_score = [results[alg]['f1_score'] for alg in algorithms]
    exec_time = [results[alg]['execution_time'] * 1000 for alg in algorithms]
    
    best_alg = algorithms[accuracy.index(max(accuracy))]
    best_acc = max(accuracy)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>SDN Conflict Detection - ML Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        .subtitle {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        .best-result {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 30px 0;
        }}
        .best-result h3 {{
            margin: 0;
            font-size: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        tr:hover {{
            background: #e8f4f8;
        }}
        .highlight {{
            background: #d4edda !important;
            font-weight: bold;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SDN Conflict Detection Using Machine Learning</h1>
        <p class="subtitle">Performance Analysis Report | Dataset: {json_file}</p>
        
        <div class="best-result">
            <h3>🏆 Best Performing Algorithm</h3>
            <p style="font-size: 20px; margin: 10px 0;">{best_alg} with {best_acc:.2f}% Accuracy</p>
        </div>
        
        <h2>1. Algorithm Performance Comparison</h2>
        <table>
            <tr>
                <th>Algorithm</th>
                <th>Accuracy (%)</th>
                <th>Precision (%)</th>
                <th>Recall (%)</th>
                <th>F1-Score (%)</th>
                <th>Time (ms)</th>
            </tr>'''
    
    for i, alg in enumerate(algorithms):
        highlight = 'class="highlight"' if accuracy[i] == max(accuracy) else ''
        html += f'''
            <tr {highlight}>
                <td><strong>{alg_labels[i]}</strong></td>
                <td>{accuracy[i]:.2f}</td>
                <td>{precision[i]:.2f}</td>
                <td>{recall[i]:.2f}</td>
                <td>{f1_score[i]:.2f}</td>
                <td>{exec_time[i]:.4f}</td>
            </tr>'''
    
    html += '''
        </table>
        
        <h2>2. Detection Accuracy Comparison</h2>
        <div class="chart-container">
            <canvas id="accuracyChart"></canvas>
        </div>
        
        <h2>3. Complete Metrics Comparison</h2>
        <div class="chart-container">
            <canvas id="metricsChart"></canvas>
        </div>
        
        <div class="grid">
            <div>
                <h2>4. Execution Time</h2>
                <div class="chart-container" style="height: 300px;">
                    <canvas id="timeChart"></canvas>
                </div>
            </div>
            <div>
                <h2>5. F1-Score Comparison</h2>
                <div class="chart-container" style="height: 300px;">
                    <canvas id="f1Chart"></canvas>
                </div>
            </div>
        </div>'''
    
    # Add classification results if available
    if 'classification' in results:
        c = results['classification']
        html += f'''
        <h2>6. Conflict Type Classification (7-Class)</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value (%)</th>
            </tr>
            <tr><td>Accuracy</td><td>{c['accuracy']:.2f}</td></tr>
            <tr><td>Precision</td><td>{c['precision']:.2f}</td></tr>
            <tr><td>Recall</td><td>{c['recall']:.2f}</td></tr>
            <tr><td>F1-Score</td><td>{c['f1_score']:.2f}</td></tr>
        </table>'''
    
    html += f'''
    </div>
    
    <script>
        const labels = {alg_labels};
        const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'];
        
        // Accuracy Chart
        new Chart(document.getElementById('accuracyChart'), {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Accuracy (%)',
                    data: {accuracy},
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: colors.map(c => c)
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: true, text: 'Detection Accuracy by Algorithm', font: {{ size: 16 }} }}
                }},
                scales: {{
                    y: {{ beginAtZero: false, min: 70, max: 105, title: {{ display: true, text: 'Accuracy (%)' }} }}
                }}
            }}
        }});
        
        // Metrics Comparison Chart
        new Chart(document.getElementById('metricsChart'), {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [
                    {{ label: 'Accuracy', data: {accuracy}, backgroundColor: '#3498db' }},
                    {{ label: 'Precision', data: {precision}, backgroundColor: '#2ecc71' }},
                    {{ label: 'Recall', data: {recall}, backgroundColor: '#e74c3c' }},
                    {{ label: 'F1-Score', data: {f1_score}, backgroundColor: '#f39c12' }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'All Metrics Comparison', font: {{ size: 16 }} }}
                }},
                scales: {{
                    y: {{ beginAtZero: false, min: 50, max: 105, title: {{ display: true, text: 'Percentage (%)' }} }}
                }}
            }}
        }});
        
        // Execution Time Chart
        new Chart(document.getElementById('timeChart'), {{
            type: 'doughnut',
            data: {{
                labels: labels,
                datasets: [{{
                    data: {exec_time},
                    backgroundColor: colors
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'Execution Time Distribution', font: {{ size: 14 }} }}
                }}
            }}
        }});
        
        // F1-Score Chart
        new Chart(document.getElementById('f1Chart'), {{
            type: 'polarArea',
            data: {{
                labels: labels,
                datasets: [{{
                    data: {f1_score},
                    backgroundColor: colors.map(c => c + '99')
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'F1-Score Distribution', font: {{ size: 14 }} }}
                }},
                scales: {{
                    r: {{ min: 50, max: 100 }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    # Save HTML file
    output_file = json_file.replace('.json', '_report.html')
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_file}")
    print(f"   Open in browser: firefox {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 html_report.py <results.json>")
        print("Example: python3 html_report.py ml_results_ds1000.json")
    else:
        generate_html_report(sys.argv[1])
