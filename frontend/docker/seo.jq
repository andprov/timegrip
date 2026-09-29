# Deployment-specific SEO for the landing page, rendered at container start
# by 40-timegrip-seo.sh. The input is seo.config.json (field reference in
# docs/DEPLOY.md, sample in the repo root); $mode picks the output:
#   html     index.html built from $template (the page as the image ships it)
#   robots   robots.txt
#   sitemap  sitemap.xml

def fail($msg): error("seo.config.json: \($msg)");

def check(cond; $msg): if cond then . else fail($msg) end;

def optional($key; cond; $msg): check((has($key) | not) or (.[$key] | cond); $msg);

def validate:
  if type != "object" then fail("root must be an object") else . end
  | check(
      (.siteUrl | type) == "string"
      and (.siteUrl | test("^[A-Za-z][A-Za-z0-9+.-]*://[^/]"));
      "\"siteUrl\" must be an absolute URL"
    )
  | check((.indexing | type) == "boolean"; "\"indexing\" must be a boolean")
  | check((.title | type) == "string" and .title != ""; "\"title\" is required")
  | reduce ("lang", "locale", "description", "siteName", "image", "imageAlt", "twitterSite") as $key
      (.; optional($key; type == "string"; "\"\($key)\" must be a string"))
  | reduce ("imageWidth", "imageHeight") as $key
      (.; optional($key; type == "number" and . > 0 and . == floor;
        "\"\($key)\" must be a positive integer"))
  | reduce ("keywords", "disallow") as $key
      (.; optional($key; type == "array" and all(type == "string");
        "\"\($key)\" must be an array of strings"))
  | optional("meta"; type == "object" and all(.[]; type == "string");
      "\"meta\" must be an object of strings")
  | .siteUrl |= sub("/+$"; "");

# Drops missing and empty values, like a falsy check in JS.
def present: select(. != null and . != "");

# Resolves a path against siteUrl the way new URL(path, siteUrl + "/") does.
def absolute($site):
  if test("^[A-Za-z][A-Za-z0-9+.-]*:") then .
  elif startswith("//") then ($site | capture("^(?<scheme>[^:]+):").scheme) + ":" + .
  elif startswith("/") then ($site | capture("^(?<origin>[^:]+://[^/]+)").origin) + .
  else "\($site)/\(.)"
  end;

def meta_name($name; $content): @html "<meta name=\"\($name)\" content=\"\($content)\">";

def meta_property($property; $content):
  @html "<meta property=\"\($property)\" content=\"\($content)\">";

def head_tags:
  . as $c
  | "\($c.siteUrl)/" as $page
  | (($c.image | present | absolute($c.siteUrl)) // null) as $image
  | [
      ($c.description | present | meta_name("description"; .)),
      ($c.keywords // [] | select(length > 0) | meta_name("keywords"; join(", "))),
      meta_name("robots"; if $c.indexing then "index, follow" else "noindex, nofollow" end),
      @html "<link rel=\"canonical\" href=\"\($page)\">",
      meta_property("og:type"; "website"),
      meta_property("og:url"; $page),
      meta_property("og:title"; $c.title),
      ($c.description | present | meta_property("og:description"; .)),
      ($c.siteName | present | meta_property("og:site_name"; .)),
      (($c.locale | present) // ($c.lang | present | sub("-"; "_"))
        | meta_property("og:locale"; .)),
      ($image // empty | meta_property("og:image"; .)),
      ($image // empty | $c.imageWidth // empty | meta_property("og:image:width"; tostring)),
      ($image // empty | $c.imageHeight // empty | meta_property("og:image:height"; tostring)),
      ($image // empty | $c.imageAlt | present | meta_property("og:image:alt"; .)),
      meta_name("twitter:card"; if $image then "summary_large_image" else "summary" end),
      ($c.twitterSite | present | meta_name("twitter:site"; .)),
      ($c.meta // {} | to_entries[] | select(.value != "") | meta_name(.key; .value)),
      # "<" is escaped so a string value can never close the <script> early.
      if $c | has("structuredData") then
        "<script type=\"application/ld+json\">"
        + ($c.structuredData | tojson | gsub("<"; "\\u003c"))
        + "</script>"
      else empty end
    ];

def index_html:
  . as $c
  | (head_tags | map("    \(.)\n") | join("")) as $tags
  | $template
  | sub("<title>[^<]*</title>"; "<title>\($c.title | @html)</title>")
  | if ($c.lang // "") != "" then
      sub("<html lang=\"[^\"]*\""; "<html lang=\"\($c.lang | @html)\"")
    else . end
  | sub("\\s*</head>"; "\n\($tags)  </head>");

def robots_txt:
  . as $c
  | if .indexing | not then "User-agent: *\nDisallow: /\n"
    else
      ["User-agent: *"] + (.disallow // [] | map("Disallow: \(.)"))
      | if length == 1 then . + ["Allow: /"] else . end
      | . + ["", "Sitemap: \($c.siteUrl)/sitemap.xml"]
      | join("\n") + "\n"
    end;

def sitemap_xml:
  [
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
    "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    @html "  <url><loc>\(.siteUrl)/</loc></url>",
    "</urlset>",
    ""
  ]
  | join("\n");

validate
| if $mode == "html" then index_html
  elif $mode == "robots" then robots_txt
  elif $mode == "sitemap" then sitemap_xml
  else error("unknown mode \($mode)")
  end
