# Research Paper: Transformer-Based Deep Learning Recommender System

This directory contains the complete research paper with properly formatted LaTeX source and generated figures.

## Files

### Main Paper
- `paper.tex` - Main LaTeX source file with proper formatting and figure references
- `paper.pdf` - Compiled PDF (generate using LaTeX compiler)

### Figures
- `architecture_diagram.png/pdf` - System architecture overview
- `performance_metrics.png/pdf` - Comprehensive performance metrics visualization
- `calibration_plot.png/pdf` - Calibration reliability diagrams
- `encoder_quality.png/pdf` - Problem encoder quality analysis
- `training_dynamics.png/pdf` - Training dynamics showing overfitting

### Scripts
- `create_figures.py` - Main script to generate all figures from evaluation data
- `create_training_plot.py` - Script to generate training dynamics plot

## Compilation Instructions

To compile the paper:

```bash
# Install required LaTeX packages (if not already installed)
# On Ubuntu/Debian:
sudo apt-get install texlive-full

# On macOS with MacTeX:
# Download and install MacTeX from https://www.tug.org/mactex/

# On Windows with MiKTeX:
# Download and install MiKTeX from https://miktex.org/

# Compile the paper
pdflatex paper.tex
pdflatex paper.tex  # Run twice for proper cross-references
```

## Figure Generation

To regenerate all figures:

```bash
# Install Python dependencies
pip install matplotlib seaborn numpy

# Generate all figures
python create_figures.py
python create_training_plot.py
```

## Paper Structure

The paper includes:

1. **Title Page** with authors and affiliations
2. **Table of Contents, List of Figures, and List of Tables**
3. **Abstract** - Comprehensive summary of the work
4. **Introduction** - Problem motivation and contributions
5. **Related Work** - Literature review
6. **Methodology** - Detailed system description with architecture diagram
7. **Experimental Setup** - Dataset and training configuration
8. **Results** - Comprehensive evaluation with multiple visualizations
9. **Analysis** - Detailed discussion of findings
10. **Real-World Implications** - Practical deployment considerations
11. **Limitations** - Honest assessment of current limitations
12. **Conclusion** - Summary and future work
13. **Bibliography** - Complete reference list

## Key Visualizations

### Figure 1: System Architecture Overview
- Shows the three-component pipeline: Problem Encoder, User Encoder, and Multi-Task Recommender
- Illustrates data flow and component interactions

### Figure 2: Comprehensive Performance Overview
- Classification accuracy and AUC by task
- Ranking performance metrics (NDCG, MRR)
- Model size distribution across components
- Inference latency and throughput scaling

### Figure 3: Problem Encoder Quality Analysis
- Per-cluster purity showing semantic organization
- Attention entropy across Transformer layers
- Loss component magnitudes
- CLS token attention concentration

### Figure 4: Training Dynamics
- Evidence of overfitting in Stage 2 training
- Validation vs training loss curves
- Best checkpoint selection at epoch 5

### Figure 5: Calibration Reliability Diagrams
- Solve and helpful prediction calibration
- Systematic overconfidence in high-probability predictions
- Expected Calibration Error (ECE) visualization

## Paper Formatting Features

- Professional academic formatting with proper margins and spacing
- Consistent table and figure positioning using `[H]` placement
- Comprehensive cross-referencing between text and figures/tables
- Publication-quality figures with consistent styling
- Proper mathematical notation and equations
- Complete bibliography with standard academic citations

## Data Sources

All figures are generated from the evaluation results in:
- `../../backend/eval_results/evaluation_report.json`

The paper provides a complete empirical account of the Transformer-based recommender system with honest reporting of both strengths and limitations.