from django import forms

from portal.models import Site
from portal.services import scrape_limits_from_settings

_default_pages, _default_products = scrape_limits_from_settings()


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            "slug",
            "name",
            "enabled",
            "country",
            "scraper",
            "base_url",
            "catalog_urls",
            "product_link_pattern",
            "currency",
            "delay_seconds",
            "notes",
        ]
        widgets = {
            "catalog_urls": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.TextInput(),
        }

    def clean_catalog_urls(self) -> str:
        value = self.cleaned_data["catalog_urls"]
        lines = [ln.strip() for ln in value.splitlines() if ln.strip()]
        if not lines:
            raise forms.ValidationError("Ingresá al menos una URL de catálogo.")
        return "\n".join(lines)

    def clean(self):
        cleaned = super().clean()
        country = cleaned.get("country")
        if country == "CL" and not cleaned.get("currency"):
            cleaned["currency"] = "CLP"
        if country == "AR" and not cleaned.get("currency"):
            cleaned["currency"] = "ARS"
        return cleaned


class RunScrapeForm(forms.Form):
    country = forms.ChoiceField(
        choices=[("all", "Todos"), ("AR", "Argentina"), ("CL", "Chile")],
        initial="all",
    )
    max_products = forms.IntegerField(
        min_value=1, max_value=200, initial=_default_products
    )
    max_pages = forms.IntegerField(min_value=1, max_value=10, initial=_default_pages)
    do_export = forms.BooleanField(initial=False, required=False, label="Exportar al finalizar")
    export_format = forms.ChoiceField(
        choices=[("xlsx", "Excel (.xlsx)"), ("csv", "CSV")],
        initial="xlsx",
    )
