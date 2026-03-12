# LaTeX IIS Report Framework

This is a framework for writing reports in LaTeX according to the rules and
conventions at the Integrated Systems Laboratory (IIS) at ETH Zurich.  It should
work out of the box on any reasonably up-to-date Linux workstation with a
current LaTeX distribution.  The framework consists of the `iisreport` LaTeX
document class, a template of the report with guidelines on what to write where,
and some more specific, topic-related guidelines and a short guide to LaTeX in
the appendix.

## Getting started

To get started, simply run

```sh
make
```

to compile the document, and then open the resulting PDF file.

More detailed instructions on how to work with the `iisreport` document class as
well as the folder structure are described in the LaTeX guide in the appendix.
Even advanced LaTeX users should have a look!  For example, you might want to
know how your vector graphics can get compiled automatically from source files
(i.e., `.svg`, `.obj`, or `.eps` files), dispending you from the need to
manually export and track them in your VCS.

We run pdfLaTeX in *quiet* mode (since it is unreasonably verbose otherwise), so
you have to inspect the log file in this directory to find error messages if
your document does not compile. In pdfLaTeX log files, lines containing error
messages always start with `! `.

This template is readily equipped with `.gitignore` files, so go ahead and track
your changes!

```sh
git init    # skip if you copied this into an existing repository
git add -A
git commit -m "Initial commit"  # or another meaningful message of your choice
```

## Creating an archive

If you want to create an archive from the report including sources in its
current state (e.g., to distribute it afterwards), run

```sh
make report.tar.gz
```

This will ensure that `report.pdf` is up-to-date, then remove all intermediate
LaTeX files (without touching your source files, though), and finally create a
gzipped tar archive from all remaining content except the `.git` directory.
