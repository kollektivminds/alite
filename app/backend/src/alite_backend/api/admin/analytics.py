"""
Custom administrative views for analytical products and dashboards.
Integrates custom Jinja2 templates into the SQLAdmin layout.
"""

from alite_backend.config import settings
from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import Response


class AnalyticsDashboardView(BaseView):
    """
    Administrative view for linguistic and pedagogical analytics dashboards.
    Mounts a custom page in the SQLAdmin navigation tree.
    """

    name = "Analytics & Lab"
    icon = "fa-solid fa-chart-line"

    @expose("/analytics", methods=["GET"])
    async def analytics_page(self, request: Request) -> Response:
        """
        Renders the analytics container page embedding the Streamlit engine.
        Passes authentication state and target host configuration to the template.
        """
        # Streamlit URL (in production, routed through reverse proxy or internal host)
        streamlit_url = getattr(
            settings, "STREAMLIT_HOST_URL", "http://localhost:8501/analytics"
        )

        return await self.templates.TemplateResponse(
            request,
            "admin/analytics.html",
            context={
                "streamlit_url": streamlit_url,
                "page_title": "ALITE Analytics Laboratory",
            },
        )
