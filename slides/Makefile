# Local build of slides.tex -> slides.pdf (same toolchain as manuscript/).
#   make         build slides.pdf
#   make check   list overfull boxes from the last build
#   make clean   remove the build files (keeps the PDF)

TEXBIN := $(lastword $(sort $(wildcard $(HOME)/texlive/*/bin/x86_64-linux)))
export PATH := $(if $(TEXBIN),$(TEXBIN):,)$(PATH)

MAIN    := slides
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: pdf check clean

pdf:
	$(LATEXMK) $(MAIN).tex

check:
	@grep -A1 "^Overfull" $(MAIN).log || echo "No overfull boxes."

clean:
	latexmk -c $(MAIN).tex
