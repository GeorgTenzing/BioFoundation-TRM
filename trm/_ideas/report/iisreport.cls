\ProvidesClass{iisreport}

% The 'parskip' option causes paragraphs to start with a vertical space of half a line instead of
% indentation.
\DeclareOption{parskip}{%
 \PassOptionsToClass{parskip=half}{scrbook}
}

% The 'print' option optimizes the page layout for printing and binding the report.
\newif\if@printlayout
\@printlayoutfalse
\DeclareOption{print}{%
 \@printlayouttrue
 \PassOptionsToClass{%
  BCOR=5mm, % Our ring bindings are 5mm wide.
  twoside,
 }{scrbook}
}
\DeclareOption{noprint}{%
 \@printlayoutfalse
 \PassOptionsToClass{oneside}{scrbook}
}

% The 'oldfonts' option brings back the fonts from the legacy IIS report template.
\newif\if@oldfonts
\@oldfontsfalse
\DeclareOption{oldfonts}{%
 \@oldfontstrue
}

% The 'oldsubscript' option disables having a printable underscore in favor of being able to use it
% for subscripts.
\newif\if@oldsubscript
\@oldsubscriptfalse
\DeclareOption{oldsubscript}{%
 \@oldsubscripttrue
}

% Pass unknown options to the base class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{scrbook}}
\ExecuteOptions{noprint}
\ProcessOptions\relax

% Make underscore a printable character.  Use `\sb{}` for subscripts.  (For reasons of symmetry,
% you should use `\sp{}` for superscripts.)
\if@oldsubscript
\else
 \catcode`_=12
\fi

% The underlying base class is `scrbook`.
\LoadClass[%
 a4paper,
 listof=totoc,       % Add "List of .." entries to the Table of Contents.
 bibliography=totoc, % Add Bibliography entry to the Table of Contents.
]{scrbook}

% Workaround to LaTeX complaining about the use of deprecated `\rm`.
\DeclareOldFontCommand{\rm}{\normalfont\rmfamily}{\mathrm}

% Use UTF-8 to encode input and Type 1 font encoding.
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}

% Font packages
\if@oldfonts
 % Latin modern (a Computer Modern derivative with extended glyphs) for all mathematics and text.
 \RequirePackage{lmodern}
 \RequirePackage{amssymb}
\else
 % Kepler fonts for mathematics, Pazo (a Palatino derivative) for text, and Bera Mono for monospace.
 % In contrast to the default (La)TeX fonts, these fonts were designed by experienced typographers.
 \RequirePackage[notext,intlimits]{kpfonts}
 \RequirePackage{mathpazo}
 \RequirePackage[scaled=.85]{beramono}
\fi

% Use American English spelling and hyphenation.
\RequirePackage[english]{babel}

% `graphicx` enables including all kinds of images (including single-page PDFs).  The default search
% path is set to the `fig/` directory.
\RequirePackage{graphicx}
\graphicspath{{fig/}}

% `xcolor` adds rich color support.
\RequirePackage[usenames, dvipsnames, svgnames, table]{xcolor}

% Customize chapter headings.
\RequirePackage[Lenny]{fncychap}

% Packages for typesetting tables.
\RequirePackage{tabularx}
\RequirePackage{booktabs}

% Easily customize the three basic list environments: enumerate, itemize, and description.
\RequirePackage{enumitem}

% Extra symbols through the Text Companion fonts
\RequirePackage{textcomp}

% Easier mathematical operators
\RequirePackage{commath}

% Slightly advanced mathematical utilities, includes the fundamental `amsmath` package.
\RequirePackage{mathtools}

% Theorems, lemmas, corollaries, proofs, and definitions
\RequirePackage{amsthm}
%
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}[chapter]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corrolary}[theorem]{Corollary}
%
\theoremstyle{definition}
\newtheorem{definition}{Definition}[chapter]

% The `IEEEeqnarray` environment allows to properly typeset complex multi-line equations.
\RequirePackage[retainorgcmds]{IEEEtrantools}
% Fix an incompatibility with `cleveref`.  Source: https://tex.stackexchange.com/a/132848/92384.
\let\if@IEEEissubequation\iffalse

% Properly typeset quantities with SI units.
\RequirePackage{siunitx}
\sisetup{%
 binary-units,
 per-mode=symbol-or-fraction  % symbol for inline math, fraction for displayed math
}

% Enable micro-typographic enhancements such as character protrusion and font expansion.
\RequirePackage{microtype}

% `pdfpages` allows to include multi-page PDFs.
\RequirePackage{pdfpages}

% `multicol` defines the `multicols` environment, which typesets text in multiple columns.
\RequirePackage{multicol}

% `etoolbox` provides some programming tools used in this class.
\RequirePackage{etoolbox}

% `algorithm2e` provides the `algorithm` environment for typesetting algorithms.
\RequirePackage[ruled, linesnumbered]{algorithm2e}

% `listings` provides environments and commands for typesetting source code listings.
% `lstautogobble` enables automatic removal of white spaces due to indentation in the LaTeX source
% code.
\RequirePackage{listings}
\RequirePackage{lstautogobble}
% Let sequential `literate` assignments append to the literate list instead of replacing it.
% Source: https://tex.stackexchange.com/a/202340/92384
\def\lst@Literatekey#1\@nil@{\let\lst@ifxliterate\lst@if
    \expandafter\def\expandafter\lst@literate\expandafter{\lst@literate#1}}
% Define default listing settings.
\newcommand{\@linewrapchar}{\textbackslash}
\lstset{
 basicstyle        = \ttfamily,
 frame             = single,
 framexleftmargin  = 0.5em,
 captionpos        = t,
 breaklines        = true,
 breakatwhitespace = false,
 rulesepcolor      = \color{black},
 linewidth         = \linewidth,
 prebreak          = {\@linewrapchar},
 numbers           = none,
 numberstyle       = \ttfamily,
 xleftmargin       = 0.9em,
 xrightmargin      = 0.5em,
 literate          = {~}{\texttildelow}{1},
 % Allow line breaks after underscores.  Source: https://stackoverflow.com/a/1524421/5578775.
 literate          = {\_}{}{0\discretionary{\@linewrapchar}{\_}{\_}},
 autogobble        = true,
}

% Add support for glossaries.
\RequirePackage[%
 toc,              % Add the glossaries to the table of contents.
 acronym,          % Add a list of acronyms.
 section=chapter,  % Show glossary headers as chapters.
 nonumberlist,     % Do not print the page numbers next to glossary entries.
]{glossaries}
\makeglossaries

% `hyperref` inserts hyperlinks into your document.  This package should always be loaded last.
% The `pdfusetitle` option causes `hyperref` to infer PDF metadata such as title and authors.
\RequirePackage[pdfusetitle]{hyperref}
% Do not put a frame around links or highlight them with colored text.
% Only URLs are highlighted by printing their text in blue.
\hypersetup{colorlinks=true, allcolors=., urlcolor=blue}
\if@printlayout
 % Display the PDF document in two columns with odd-numbered pages on the right.
 \hypersetup{pdfpagelayout=TwoColumnRight}
\else
 \hypersetup{pdfpagelayout=OneColumn}
\fi

% `cleveref` provides clever cross-referencing.  It breaks `hyperref`'s last-loading rule and must
% be loaded afterwards.
\RequirePackage[capitalize]{cleveref}

% Custom layout settings:
% - Use the normal serif font for all dispositions (e.g., chapters, sections, ..).
\setkomafont{disposition}{\normalfont\bfseries}

% Define macros for setting document metadata.
\newcommand{\misspar}[1]{\textcolor{red}{\bfseries $<$#1$>$}}
%
\title{\misspar{Specify title}}
%
\author{\misspar{Specify author name}}
%
\def\@email{\misspar{Specify e-mail address}}
\newcommand{\email}[1]{\def\@email{#1}}
%
\date{\misspar{Specify date}}
%
\def\@reporttype{\misspar{Specify report type}}
\newcommand{\reporttype}[1]{\def\@reporttype{#1}}
%
\def\@semester{\misspar{Specify semester and year}}
\newcommand{\semester}[1]{\def\@semester{#1}}
%
\def\@professor{\misspar{Specify professor}}
\newcommand{\professor}[1]{\def\@professor{#1}}
%
\def\@titlelogo{}
\newcommand{\titlelogo}[1]{\def\@titlelogo{#1}}
\def\@titlelogoheight{7cm}
\newcommand{\titlelogoheight}[1]{\def\@titlelogoheight{#1}}
%
\def\@advisors{}
\newcommand{\advisor}[1]{\listadd{\@advisors}{#1}}

% Define shortcut for printing the list of acronyms.
\newcommand{\listofacronyms}{%
 \setlength{\glslistdottedwidth}{.2\linewidth}
 \printglossary[type=\acronymtype,style=listdotted,title=List of Acronyms]
}

%% Mathematical operators and symbols

% Add proper spacing after `\forall`, `\exists`, etc.
\let\@forall\forall
\renewcommand{\forall}{\@forall\;}
\let\@exists\exists
\renewcommand{\exists}{\@exists\;}
\let\@nexists\nexists
\renewcommand{\nexists}{\@nexists\;}

% Multi-letter variables
\newcommand{\var}[1]{\mathit{#1}}

%% Other custom commands

% `\centerfloat` centers all floats (even overly wide ones) without adding space.
% Source: https://tex.stackexchange.com/a/27099/92384
\newcommand{\centerfloat}{%
 \parindent \z@
 \leftskip \z@ \@plus 1fil \@minus \textwidth
 \rightskip\leftskip
 \parfillskip \z@skip
}

% Customize title page.
\newcommand{\@printadvisor}[1]{%
 {} & #1 \\%
}%
%
\renewcommand{\maketitle}{%
 \KOMAoption{twoside}{false}
 \begin{titlepage}
  %
  \thispagestyle{empty}
  %
  \begin{center}
   %
   \begin{minipage}[b]{.45\linewidth}
    \vspace{0pt}\includegraphics[width=.8\linewidth]{eth_logo.pdf}
   \end{minipage}
   \hfill
   \begin{minipage}[b]{.45\textwidth}
    \flushright{%
     \footnotesize\fontfamily{phv}\selectfont%
     Institut f\"ur Integrierte Systeme\\[-.25\baselineskip]%
     Integrated Systems Laboratory%
     \vspace*{-.05\baselineskip}%
    }
   \end{minipage}\\[-.2cm]
   %
   \rule{\textwidth}{.4pt}

   \vspace{.3cm}

   {%
    \Large%
    \textsc{Department of\\Information Technology and Electrical Engineering}
   }

   \vspace{.2cm}

   \@semester

   \vfill

   {%
    \fontfamily{ppl}\fontsize{28}{40}\selectfont%
    \@title\\[.75\baselineskip]%
   }

   \@reporttype

   \vfill

   \ifx\@titlelogo\@empty
    \relax
   \else
    \includegraphics[height=\@titlelogoheight]{\@titlelogo}
   \fi

   \vfill

   {%
    \Large%
    \@author%
   }\\
   \@email

   \vfill

   \@date

   \vfill

   \ifx\@advisors\@empty
    \def\@advisors{\misspar{Specify advisors}}
   \fi
   \begin{tabular}{ll}
    Advisors:
     \forlistloop{\@printadvisor}{\@advisors}
    \rule{0pt}{3ex}%
    Professor: & \@professor \\
   \end{tabular}

  \end{center}
 \end{titlepage}
 \if@printlayout
  \KOMAoption{twoside}{true}
 \fi
}

\AtBeginDocument{%
 \maketitle
 \bibliographystyle{IEEEtran}
}

\AtEndDocument{%
 \nocite*{}         % Also print non-cited references.
 \glsaddallunused{} % Also print unused glossary entries.
}
