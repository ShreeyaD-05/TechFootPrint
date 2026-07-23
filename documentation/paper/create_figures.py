#!/usr/bin/env python3
"""
Script to generate figures for the research paper from evaluation data.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 14,
    'font.family': 'serif'
})

def load_evaluation_data():
    """Load evaluation data from JSON file."""
    with open('../../backend/eval_results/evaluation_report.json', 'r') as f:
        return json.load(f)

def create_architecture_diagram():
    """Create system architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Define colors
    colors = {
        'problem': '#FF6B6B',
        'user': '#4ECDC4', 
        'recommender': '#45B7D1',
        'output': '#96CEB4',
        'flow': '#666666'
    }
    
    # Problem Encoder
    prob_rect = Rectangle((1, 6), 2.5, 1.5, facecolor=colors['problem'], alpha=0.7, edgecolor='black')
    ax.add_patch(prob_rect)
    ax.text(2.25, 6.75, 'Problem Encoder\n(3-layer Transformer)\n64-dim embedding', 
            ha='center', va='center', fontsize=9, weight='bold')
    
    # User Encoder
    user_rect = Rectangle((1, 3.5), 2.5, 1.5, facecolor=colors['user'], alpha=0.7, edgecolor='black')
    ax.add_patch(user_rect)
    ax.text(2.25, 4.25, 'User Encoder\n(Sequential + Skill)\n64-dim embedding', 
            ha='center', va='center', fontsize=9, weight='bold')
    
    # Recommender Model
    rec_rect = Rectangle((5, 4.5), 3, 2, facecolor=colors['recommender'], alpha=0.7, edgecolor='black')
    ax.add_patch(rec_rect)
    ax.text(6.5, 5.5, 'Multi-Task Recommender\n(3 Residual Blocks)\n257-dim interaction', 
            ha='center', va='center', fontsize=9, weight='bold')
    
    # Output heads
    solve_rect = Rectangle((9.5, 6), 2, 0.8, facecolor=colors['output'], alpha=0.7, edgecolor='black')
    ax.add_patch(solve_rect)
    ax.text(10.5, 6.4, 'Solve Probability', ha='center', va='center', fontsize=9, weight='bold')
    
    helpful_rect = Rectangle((9.5, 4.8), 2, 0.8, facecolor=colors['output'], alpha=0.7, edgecolor='black')
    ax.add_patch(helpful_rect)
    ax.text(10.5, 5.2, 'Helpful Probability', ha='center', va='center', fontsize=9, weight='bold')
    
    diff_rect = Rectangle((9.5, 3.6), 2, 0.8, facecolor=colors['output'], alpha=0.7, edgecolor='black')
    ax.add_patch(diff_rect)
    ax.text(10.5, 4.0, 'Difficulty Match', ha='center', va='center', fontsize=9, weight='bold')
    
    # Input labels
    ax.text(2.25, 8, 'Problem Text\nTags, Difficulty', ha='center', va='center', fontsize=9)
    ax.text(2.25, 2, 'User History\nSkill Profile', ha='center', va='center', fontsize=9)
    
    # Arrows
    # Problem encoder to recommender
    ax.arrow(3.5, 6.75, 1.3, -1, head_width=0.1, head_length=0.1, fc=colors['flow'], ec=colors['flow'])
    # User encoder to recommender
    ax.arrow(3.5, 4.25, 1.3, 1, head_width=0.1, head_length=0.1, fc=colors['flow'], ec=colors['flow'])
    # Recommender to outputs
    ax.arrow(8, 5.5, 1.3, 0.7, head_width=0.1, head_length=0.1, fc=colors['flow'], ec=colors['flow'])
    ax.arrow(8, 5.5, 1.3, -0.5, head_width=0.1, head_length=0.1, fc=colors['flow'], ec=colors['flow'])
    ax.arrow(8, 5.5, 1.3, -1.7, head_width=0.1, head_length=0.1, fc=colors['flow'], ec=colors['flow'])
    
    ax.set_xlim(0, 12)
    ax.set_ylim(1, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('System Architecture Overview', fontsize=14, weight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('architecture_diagram.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('architecture_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_metrics_chart(data):
    """Create comprehensive performance metrics visualization."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Classification Performance
    tasks = ['Solve', 'Helpful', 'Difficulty']
    accuracies = [
        data['classification_metrics']['solve_accuracy'] * 100,
        data['classification_metrics']['helpful_accuracy'] * 100,
        data['classification_metrics']['difficulty_accuracy'] * 100
    ]
    aucs = [
        data['classification_metrics']['solve_auc'] * 100,
        data['classification_metrics']['helpful_auc'] * 100,
        50  # No AUC for multiclass difficulty
    ]
    
    x = np.arange(len(tasks))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, accuracies, width, label='Accuracy', alpha=0.8)
    bars2 = ax1.bar(x + width/2, aucs, width, label='AUC', alpha=0.8)
    
    ax1.set_ylabel('Performance (%)')
    ax1.set_title('Classification Performance by Task')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tasks)
    ax1.legend()
    ax1.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # 2. Ranking Performance
    metrics = ['NDCG@5', 'NDCG@10', 'NDCG@20', 'MRR']
    values = [
        data['ranking_metrics']['NDCG@5'] * 100,
        data['ranking_metrics']['NDCG@10'] * 100,
        data['ranking_metrics']['NDCG@20'] * 100,
        data['ranking_metrics']['MRR'] * 100
    ]
    
    bars = ax2.bar(metrics, values, alpha=0.8, color='#45B7D1')
    ax2.set_ylabel('Performance (%)')
    ax2.set_title('Ranking Performance Metrics')
    ax2.set_ylim(0, 100)
    
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # 3. Model Size Breakdown
    components = ['Problem\nEncoder', 'User\nEncoder', 'Recommender']
    sizes_mb = [
        data['model_size']['problem_encoder']['size_mb_fp32'],
        data['model_size']['user_encoder']['size_mb_fp32'],
        data['model_size']['recommender']['size_mb_fp32']
    ]
    params_k = [
        data['model_size']['problem_encoder']['total_params'] / 1000,
        data['model_size']['user_encoder']['total_params'] / 1000,
        data['model_size']['recommender']['total_params'] / 1000
    ]
    
    ax3_twin = ax3.twinx()
    bars1 = ax3.bar(components, sizes_mb, alpha=0.8, color='#FF6B6B', label='Size (MB)')
    bars2 = ax3_twin.bar(components, params_k, alpha=0.6, color='#96CEB4', label='Params (K)')
    
    ax3.set_ylabel('Model Size (MB)', color='#FF6B6B')
    ax3_twin.set_ylabel('Parameters (K)', color='#96CEB4')
    ax3.set_title('Model Size and Parameter Distribution')
    
    # 4. Latency vs Throughput
    batch_sizes = [1, 10, 50, 100, 200]
    latencies = [data['latency'][str(bs)]['total_ms'] for bs in batch_sizes]
    throughputs = [data['latency'][str(bs)]['throughput_per_s'] for bs in batch_sizes]
    
    ax4_twin = ax4.twinx()
    line1 = ax4.plot(batch_sizes, latencies, 'o-', color='#FF6B6B', linewidth=2, label='Latency (ms)')
    line2 = ax4_twin.plot(batch_sizes, throughputs, 's-', color='#45B7D1', linewidth=2, label='Throughput (prob/s)')
    
    ax4.set_xlabel('Batch Size')
    ax4.set_ylabel('Latency (ms)', color='#FF6B6B')
    ax4_twin.set_ylabel('Throughput (problems/s)', color='#45B7D1')
    ax4.set_title('Inference Latency vs Throughput')
    ax4.set_xscale('log')
    ax4_twin.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig('performance_metrics.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('performance_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_calibration_plot(data):
    """Create calibration reliability diagram."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Solve calibration
    solve_bins = data['calibration']['solve_bins']
    confidences = [bin_data['confidence'] for bin_data in solve_bins]
    accuracies = [bin_data['accuracy'] for bin_data in solve_bins]
    bin_counts = [bin_data['n'] for bin_data in solve_bins]
    
    # Create reliability diagram
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect Calibration')
    scatter = ax1.scatter(confidences, accuracies, s=[n*3 for n in bin_counts], 
                         alpha=0.7, c=bin_counts, cmap='viridis')
    
    # Add ECE text
    ece_solve = data['calibration']['solve_ece']
    ax1.text(0.05, 0.95, f'ECE = {ece_solve:.3f}', transform=ax1.transAxes, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax1.set_xlabel('Mean Predicted Probability')
    ax1.set_ylabel('Fraction of Positives')
    ax1.set_title('Solve Prediction Calibration')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Helpful calibration
    helpful_bins = data['calibration']['helpful_bins']
    confidences_h = [bin_data['confidence'] for bin_data in helpful_bins]
    accuracies_h = [bin_data['accuracy'] for bin_data in helpful_bins]
    bin_counts_h = [bin_data['n'] for bin_data in helpful_bins]
    
    ax2.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect Calibration')
    scatter2 = ax2.scatter(confidences_h, accuracies_h, s=[n*3 for n in bin_counts_h], 
                          alpha=0.7, c=bin_counts_h, cmap='viridis')
    
    # Add ECE text
    ece_helpful = data['calibration']['helpful_ece']
    ax2.text(0.05, 0.95, f'ECE = {ece_helpful:.3f}', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2.set_xlabel('Mean Predicted Probability')
    ax2.set_ylabel('Fraction of Positives')
    ax2.set_title('Helpful Prediction Calibration')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter2, ax=[ax1, ax2], shrink=0.6)
    cbar.set_label('Bin Count')
    
    plt.tight_layout()
    plt.savefig('calibration_plot.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('calibration_plot.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_encoder_quality_plot(data):
    """Create encoder quality visualization."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Cluster Purity
    clusters = list(data['encoder_metrics']['per_cluster_purity'].keys())
    purities = list(data['encoder_metrics']['per_cluster_purity'].values())
    
    bars = ax1.bar(range(len(clusters)), [p*100 for p in purities], alpha=0.8, color='#4ECDC4')
    ax1.set_xlabel('Cluster ID')
    ax1.set_ylabel('Purity (%)')
    ax1.set_title('Per-Cluster Purity (Nearest Neighbor)')
    ax1.set_xticks(range(len(clusters)))
    ax1.set_xticklabels([c.split('_')[1] for c in clusters])
    ax1.set_ylim(95, 101)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
    
    # 2. Attention Entropy by Layer
    layers = ['Layer 0', 'Layer 1', 'Layer 2']
    entropies = [
        data['attention_quality']['layer_0_mean_entropy'],
        data['attention_quality']['layer_1_mean_entropy'],
        data['attention_quality']['layer_2_mean_entropy']
    ]
    
    bars = ax2.bar(layers, entropies, alpha=0.8, color='#FF6B6B')
    ax2.set_ylabel('Mean Attention Entropy')
    ax2.set_title('Attention Entropy by Transformer Layer')
    
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 3. Loss Components
    loss_names = ['Alignment', 'Uniformity', 'Contrastive']
    loss_values = [
        data['encoder_metrics']['alignment_loss'],
        abs(data['encoder_metrics']['uniformity_loss']),  # Take absolute for visualization
        data['encoder_metrics']['contrastive_loss']
    ]
    
    bars = ax3.bar(loss_names, loss_values, alpha=0.8, color='#96CEB4')
    ax3.set_ylabel('Loss Value')
    ax3.set_title('Encoder Loss Components')
    ax3.set_yscale('log')
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height * 1.1,
                f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 4. CLS Token Concentration
    cls_conc = data['attention_quality']['cls_concentration_mean'] * 100
    
    # Create a simple gauge-like visualization
    theta = np.linspace(0, np.pi, 100)
    r = 1
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    ax4.plot(x, y, 'k-', linewidth=2)
    ax4.fill_between(x, 0, y, alpha=0.3, color='lightgray')
    
    # Mark the concentration value
    conc_angle = np.pi * (1 - cls_conc/100)
    conc_x = r * np.cos(conc_angle)
    conc_y = r * np.sin(conc_angle)
    
    ax4.plot([0, conc_x], [0, conc_y], 'r-', linewidth=4)
    ax4.plot(conc_x, conc_y, 'ro', markersize=8)
    
    ax4.text(0, -0.3, f'{cls_conc:.1f}%', ha='center', va='center', 
             fontsize=14, weight='bold')
    ax4.text(0, -0.5, 'CLS Concentration', ha='center', va='center', fontsize=10)
    
    ax4.set_xlim(-1.2, 1.2)
    ax4.set_ylim(-0.6, 1.2)
    ax4.set_aspect('equal')
    ax4.axis('off')
    ax4.set_title('CLS Token Attention Concentration')
    
    plt.tight_layout()
    plt.savefig('encoder_quality.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('encoder_quality.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all figures for the research paper."""
    print("Loading evaluation data...")
    data = load_evaluation_data()
    
    print("Creating architecture diagram...")
    create_architecture_diagram()
    
    print("Creating performance metrics chart...")
    create_performance_metrics_chart(data)
    
    print("Creating calibration plot...")
    create_calibration_plot(data)
    
    print("Creating encoder quality plot...")
    create_encoder_quality_plot(data)
    
    print("All figures generated successfully!")
    print("Generated files:")
    print("- architecture_diagram.pdf/png")
    print("- performance_metrics.pdf/png")
    print("- calibration_plot.pdf/png")
    print("- encoder_quality.pdf/png")

if __name__ == "__main__":
    main()