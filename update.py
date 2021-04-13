import functools
import io
import operator
from collections import defaultdict

from scholarly import scholarly, ProxyGenerator
from tqdm import tqdm
from yattag import Doc, indent

# Settings
PEOPLE = ["James O'Shea",
          "Alex Saywell",
          "Philip Moriarty",
          "Peter Beton"]
OUTPUT_DIR = "D:/Nano Group Page/all_pubs"
MIN_YEAR = 2016

# Setup proxy to avoid ignored requests
pg = ProxyGenerator()
scholarly.use_proxy(pg.FreeProxies())

# Preallocate
pubs_by_year = defaultdict(list)
pubs = []

# Get all publications in an unordered list
for p in PEOPLE:
    search_query = scholarly.search_author(f'{p}, Nottingham')
    author = next(search_query)
    info = scholarly.fill(author, sections=['publications'])
    pubs.append(info["publications"])
pubs = functools.reduce(operator.iconcat, pubs, [])

# For every publication
for pub in tqdm(pubs):
    # Skip if year is outside search range (or not available)
    if "pub_year" not in pub["bib"]:
        continue
    year = int(pub["bib"]["pub_year"])
    if year <= MIN_YEAR:
        continue
    else:
        # Fill in details into year based dict
        pub = scholarly.fill(pub, sections=["bib", "pub_url"])

        authors = pub["bib"]["author"]
        authors = authors.replace(" and", ",", (authors.count(" and") - 1))

        for key in ["journal", "number", "volume", "pages"]:
            if key not in pub["bib"].keys():
                pub["bib"][key] = ""

        # Fill in what we can
        pubs_by_year[year].append({"pub_year": year,
                                   "title": pub["bib"]["title"],
                                   "authors": authors,
                                   "journal": pub["bib"]["journal"],
                                   "volume": pub["bib"]["volume"],
                                   "number": pub["bib"]["number"],
                                   "pages": pub["bib"]["pages"],
                                   "url": pub["pub_url"]})

# Now that we have everything separated by year, start building the html strings
for year, pub_details_by_year in pubs_by_year.items():
    doc, tag, text = Doc().tagtext()
    with tag("ul"):
        for parsed in pub_details_by_year:
            with tag("li"):
                with tag("p"):
                    with tag("a",
                             ("href", parsed["url"]),
                             ("target", "_blank")
                             ):
                        text(parsed["title"])
                    doc.stag('br')
                    text(parsed["authors"])
                    doc.stag('br')
                    text(parsed["journal"], " ", parsed["volume"], ", ", parsed["number"], " ", parsed["pages"], " (",
                         year, ")")

    result = indent(doc.getvalue())

    # Write html strings to file
    with io.open(f"{OUTPUT_DIR}/pubs_{year}.html", "w+", encoding="utf-8") as file:
        file.write(result)
