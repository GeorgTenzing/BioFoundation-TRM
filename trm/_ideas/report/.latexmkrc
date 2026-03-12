# Configure Latexmk to properly build glossaries.
# Source: https://tex.stackexchange.com/a/44316/92384
add_cus_dep('glo', 'gls', 0, 'run_makeglossaries');
add_cus_dep('acn', 'acr', 0, 'run_makeglossaries');
sub run_makeglossaries {
  if ( $silent ) {
    system "makeglossaries -q '$_[0]'";
  }
  else {
    system "makeglossaries '$_[0]'";
  };
}
push @generated_exts, 'glo', 'gls', 'glsdefs', 'glg';
push @generated_exts, 'acn', 'acr', 'alg';
push @generated_exts, 'mtc', 'mtc0';
$clean_ext .= ' %R.ist %R.xdy';
$clean_ext .= ' %R.bbl';
