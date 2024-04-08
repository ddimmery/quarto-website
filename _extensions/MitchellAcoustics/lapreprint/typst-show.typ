// Typst custom formats typically consist of a 'typst-template.typ' (which is
// the source code for a typst template) and a 'typst-show.typ' which calls the
// template's function (forwarding Pandoc metadata values as required)
//
// This is an example 'typst-show.typ' file (based on the default template  
// that ships with Quarto). It calls the typst function named 'article' which 
// is defined in the 'typst-template.typ' file. 
//
// If you are creating or packaging a custom typst template you will likely
// want to replace this file and 'typst-template.typ' entirely. You can find
// documentation on creating typst templates here and some examples here:
//   - https://typst.app/docs/tutorial/making-a-template/
//   - https://github.com/typst/templates

#show: doc => template(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: "$subtitle$",
$endif$
$if(shorttitle)$
  short-title: "$shorttitle$",
$endif$
$if(venue)$
  venue: [$venue$],
$endif$

$if(by-author)$
  authors: (
$for(by-author)$
$if(it.name.literal)$
    ( name: "$it.name.literal$",
      $if(it.affiliations)$
      affiliations: "$for(it.affiliations)$$it.name$$sep$, $endfor$",
      $endif$
      $if(it.email)$
      email: [$it.email$],
      $endif$
      $if(it.orcid)$
      orcid: "$it.orcid$",
      $endif$
       ),
$endif$
$endfor$
    ),
$endif$

$if(affils)$
  affiliations: (
$for(affils)$
    ( $if(it.name)$name: "$it.name$", $endif$
      $if(it.id)$id: "$it.id$", $endif$
      ),
$endfor$
    ),
$endif$

$if(logo)$
  logo: "$logo$",
$endif$
$if(doi)$
  doi: "$doi$",
$endif$
$if(theme)$
  theme: $theme$,
$endif$
$if(kind)$
  kind: "$kind$",
$endif$
// $if(date)$
//   date: [$date$],
// $endif$

$if(dates)$
  date: (
    $for(dates)$
    ( title: "$it.title$",
      date: datetime(year: $it.year$, month: $it.month$, day: $it.day$)),
    $endfor$
  ),
$endif$

$if(lang)$
  lang: "$lang$",
$endif$
$if(region)$
  region: "$region$",
$endif$
$if(abstract)$
  abstract: [$abstract$],
$endif$
$if(keywords)$
  keywords: ($for(keywords)$"$it$", $endfor$),
$endif$

$if(margins)$
  margin: (
$for(margins)$ (
    title: "$it.title$",
    content: [$it.content$],
  ),
$endfor$
  ),
$endif$

$if(open-access)$
  open-access: $open-access$,
$endif$
$if(margin)$
  margin: ($for(margin/pairs)$$margin.key$: $margin.value$,$endfor$),
$endif$
$if(papersize)$
  paper: "$papersize$",
$endif$
$if(mainfont)$
  font: ("$mainfont$",),
$endif$
$if(fontsize)$
  fontsize: $fontsize$,
$endif$
$if(section-numbering)$
  sectionnumbering: "$section-numbering$",
$endif$
$if(toc)$
  toc: $toc$,
$endif$
$if(bibliography-file)$
  bibliography-file: "$bibliography-file$",
$endif$
$if(bibliography-style)$
  bibliography-style: "$bibliography-style$",
$endif$
  doc,
)
