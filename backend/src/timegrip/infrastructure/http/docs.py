from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from scalar_fastapi import (
    AgentScalarConfig,
    DocumentDownloadType,
    get_scalar_api_reference,
)

_LOGO_CSS = """
.t-doc__sidebar::before {
    content: "TimeGrip API";
    display: flex;
    align-items: center;
    flex: none;
    height: 32px;
    margin: 14px 12px 4px;
    padding-left: 28px;
    background: url("/favicon-light.ico") no-repeat left center / 24px;
    color: var(--scalar-color-1);
    font-size: 18px;
    font-weight: 600;
}

.dark-mode .t-doc__sidebar::before {
    background-image: url("/favicon-dark.ico");
}
"""

_FAVICON_JS = """
<script>
  (function () {
    try {
      var media = window.matchMedia('(prefers-color-scheme: dark)')
      var favicon = document.querySelector('link[rel~="icon"]')
      function applyFavicon() {
        favicon.href = media.matches
          ? '/favicon-dark.ico'
          : '/favicon-light.ico'
      }
      applyFavicon()
      media.addEventListener('change', applyFavicon)
    } catch (e) {}
  })()
</script>
"""


def setup_docs(app: FastAPI, scalar_url: str, interactive: bool) -> None:
    download_type = (
        DocumentDownloadType.BOTH if interactive else DocumentDownloadType.NONE
    )

    @app.get(scalar_url, include_in_schema=False)
    async def scalar_html() -> HTMLResponse:
        reference = get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=app.title,
            scalar_favicon_url="/favicon-light.ico",
            hide_test_request_button=not interactive,
            hide_models=True,
            hide_client_button=True,
            document_download_type=download_type,
            persist_auth=False,
            custom_css=_LOGO_CSS,
            integration=None,
            show_developer_tools="localhost" if interactive else "never",
            agent=AgentScalarConfig(disabled=True),
            telemetry=False,
            overrides={"mcp": {"disabled": True}},
        )
        html = reference.body.decode()
        return HTMLResponse(
            html.replace("</head>", _FAVICON_JS + "</head>", 1),
        )
