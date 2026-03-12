tex_target ?= report

LATEXMK := latexmk -quiet -pdf

figs_obj = $(wildcard fig/*.obj)
figs_eps = $(wildcard fig/*.eps)
figs_svg = $(wildcard fig/*.svg)
figs_tex = $(wildcard fig/*.tex)

figs_obj_pdf = $(patsubst %.obj,%.pdf,$(figs_obj))
figs_eps_pdf = $(patsubst %.eps,%.pdf,$(figs_eps))
figs_svg_pdf = $(patsubst %.svg,%.pdf,$(figs_svg))
figs_tex_pdf = $(patsubst %.tex,%.pdf,$(figs_tex))
figs_pdf = $(figs_obj_pdf) $(figs_eps_pdf) $(figs_svg_pdf) $(figs_tex_pdf)

.PHONY: all
all: $(tex_target).pdf

# Declare the PDF output file as phony because we do not want to rely on Make's dependency
# resolution (getting it to work properly with LaTeX is very difficult).  Instead, we always invoke
# `latexmk` and let that tool decide which steps to take (it was designed for this task).
.PHONY: $(tex_target).pdf
$(tex_target).pdf: $(figs_pdf)
	$(LATEXMK) $(tex_target).tex

$(tex_target).tar.gz: $(tex_target).pdf dist-clean
	$(eval tmpdir := $(shell mktemp -d))
	mkdir $(tmpdir)/$(tex_target)
	rsync -a \
		--exclude='.git/' --exclude='.gitlab-ci.yml' --exclude='$@' --exclude='$(tex_target).zip' \
		. $(tmpdir)/$(tex_target)
	tar czf $@ -C $(tmpdir) $(tex_target)
	rm -r $(tmpdir)

$(tex_target).zip: $(tex_target).pdf dist-clean
	$(eval tmpdir := $(shell mktemp -d))
	mkdir $(tmpdir)/$(tex_target)
	rsync -a \
		--exclude='.git/' --exclude='.gitlab-ci.yml' --exclude='$@' --exclude='$(tex_target).tar.gz' \
		. $(tmpdir)/$(tex_target)
	cd $(tmpdir) && zip -r $@ $(tex_target)
	mv $(tmpdir)/$@ .
	rm -r $(tmpdir)

$(figs_obj_pdf): %.pdf : %.obj
	tgif -print -eps -color $*.obj
	epstopdf $*.eps
	rm $*.eps

$(figs_eps_pdf): %.pdf : %.eps
	epstopdf $*.eps

$(figs_svg_pdf): %.pdf : %.svg
	inkscape --without-gui --export-pdf=$*.pdf $*.svg

$(figs_tex_pdf): %.pdf : %.tex
	$(LATEXMK) -cd $*.tex

.PHONY: clean
clean:: clean-figs
	latexmk -C
	rm -f $(tex_target).{tar.gz,zip}

.PHONY: clean-figs
clean-figs:
	rm -f $(figs_pdf)

.PHONY: dist-clean
dist-clean::
	latexmk -c
