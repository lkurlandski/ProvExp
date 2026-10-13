# Local build of main.tex -> main.pdf.
#   make         build main.pdf
#   make watch   rebuild on every save (latexmk -pvc, no viewer)
#   make check   list undefined references/citations and overfull boxes from the last build
#   make clean   remove the build files (keeps the PDF); make distclean also removes the PDF

TEXBIN := $(lastword $(sort $(wildcard $(HOME)/texlive/*/bin/x86_64-linux)))
export PATH := $(if $(TEXBIN),$(TEXBIN):,)$(PATH)

MAIN    := main
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: pdf watch check clean distclean

pdf:
	$(LATEXMK) $(MAIN).tex

watch:
	$(LATEXMK) -pvc -view=none $(MAIN).tex

check:
	@grep -E "Warning: (Citation|Reference)" $(MAIN).log | sort -u | grep . || echo "No undefined references or citations."
	@grep -A1 "^Overfull" $(MAIN).log || echo "No overfull boxes."

clean:
	latexmk -c $(MAIN).tex

distclean:
	latexmk -C $(MAIN).tex
