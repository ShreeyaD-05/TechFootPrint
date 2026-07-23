# Makefile for research paper compilation

# Main target
all: paper.pdf

# Generate figures
figures:
	python create_figures.py
	python create_training_plot.py

# Compile paper
paper.pdf: paper.tex figures
	pdflatex paper.tex
	pdflatex paper.tex

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.toc *.lof *.lot *.out *.bbl *.blg

# Clean everything including PDF and figures
distclean: clean
	rm -f paper.pdf *.png *.pdf

# Install Python dependencies
deps:
	pip install matplotlib seaborn numpy

.PHONY: all figures clean distclean deps