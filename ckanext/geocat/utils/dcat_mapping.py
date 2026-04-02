"""
Mapping from DCAT-AP-CH XML (as returned by the geocat.ch CSW endpoint with
OUTPUTSCHEMA=http://dcat-ap.ch/schema/dcat-ap-ch/2.0) to a CKAN dataset dict.

Replaces the old ISO 19139.che (CHE schema) mapping in csw_mapping.py.
"""

import json
import logging

from lxml import etree

from ckanext.geocat.utils.mapping_utils import MetadataFormatError
from ckanext.geocat.utils.ogdch_map_utils import (
    get_legal_basis_link,
    map_geocat_to_ogdch_identifier,
)

log = logging.getLogger(__name__)

DCAT_AP_CH_SCHEMA = "http://dcat-ap.ch/schema/dcat-ap-ch/2.0"

# XML namespaces present in DCAT-AP-CH responses from geocat.ch
DCAT_NS = {
    "csw": "http://www.opengis.net/cat/csw/2.0.2",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
RDF_RESOURCE_ATTR = f"{{{DCAT_NS['rdf']}}}resource"
RDF_ABOUT_ATTR = f"{{{DCAT_NS['rdf']}}}about"

# Languages supported by opendata.swiss / CKAN
CKAN_LANGS = ["de", "fr", "it", "en"]

# EU authority language code → ISO 639-1 two-letter code
EU_LANG_MAP = {
    "DEU": "de",
    "FRA": "fr",
    "ITA": "it",
    "ENG": "en",
    "ROH": "rm",
}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _rdf_resource(elem):
    """Return rdf:resource or rdf:about attribute value of *elem*, or ''."""
    return elem.get(RDF_RESOURCE_ATTR) or elem.get(RDF_ABOUT_ATTR) or ""


def _uri_last_segment(uri):
    """Extract the last path segment of a URI, e.g. '.../REGI' → 'REGI'."""
    return uri.rstrip("/").rsplit("/", 1)[-1] if uri else ""


def _xml_lang_dict(node, xpath_expr, namespaces=None):
    """
    Return a {lang: text} dict from all elements matched by *xpath_expr*
    that carry an xml:lang attribute.
    """
    ns = namespaces or DCAT_NS
    result = {}
    for elem in node.xpath(xpath_expr, namespaces=ns):
        lang = elem.get(XML_LANG)
        if lang and elem.text:
            result[lang] = elem.text.strip()
    return result


def _filter_ckan_langs(lang_dict):
    """Project a language dict down to the four CKAN languages."""
    return {lang: lang_dict.get(lang, "") for lang in CKAN_LANGS}


def _eu_lang_to_short(uri):
    """http://..../language/DEU → 'de'."""
    code = _uri_last_segment(uri)
    return EU_LANG_MAP.get(code, "")


def _normalize_datetime(value):
    """
    Strip timezone offset / 'Z' so that we always return a bare
    'YYYY-MM-DDTHH:MM:SS' string, consistent with what the old mapping produced.
    """
    if not value:
        return ""
    return value.split("+")[0].split("Z")[0].strip()


# ---------------------------------------------------------------------------
# Main mapping class
# ---------------------------------------------------------------------------


class DcatMetadataMapping:
    """
    Maps a single DCAT-AP-CH ``dcat:Dataset`` element (as returned by
    the geocat.ch CSW ``GetRecordById`` endpoint) to a CKAN dataset dict.

    The constructor parameters mirror those of the old ``GeoMetadataMapping``
    so that the harvester code requires only a name change.
    """

    def __init__(
        self,
        organization_slug,
        geocat_perma_link,
        geocat_perma_label,
        legal_basis_url,
        default_rights,
        valid_identifiers,
    ):
        self.organization_slug = organization_slug
        self.geocat_perma_link = geocat_perma_link
        self.geocat_perma_label = geocat_perma_label
        self.legal_basis_url = legal_basis_url
        self.default_rights = default_rights
        self.valid_identifiers = valid_identifiers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_metadata(self, csw_record_as_string, geocat_id):
        """
        Parse the raw XML string returned by ``GetRecordById`` (DCAT schema)
        and return a CKAN-compatible dataset dict.
        """
        log.debug("Processing geocat_id %s", geocat_id)

        if isinstance(csw_record_as_string, str):
            csw_record_as_string = csw_record_as_string.encode("utf-8")

        try:
            root = etree.fromstring(csw_record_as_string)
        except etree.XMLSyntaxError as exc:
            raise MetadataFormatError(f"Could not parse XML: {exc!r}")

        dataset_nodes = root.xpath("//dcat:Dataset", namespaces=DCAT_NS)
        if not dataset_nodes:
            raise MetadataFormatError(
                f"No dcat:Dataset element found for geocat_id {geocat_id}"
            )
        node = dataset_nodes[0]

        # --- dataset-level fields ---
        raw_identifier = self._text(node, "dct:identifier")
        dataset_dict = {
            "identifier": map_geocat_to_ogdch_identifier(
                raw_identifier, self.organization_slug
            ),
            "title": _filter_ckan_langs(_xml_lang_dict(node, "dct:title")),
            "description": _filter_ckan_langs(_xml_lang_dict(node, "dct:description")),
            "publisher": self._map_publisher(node),
            "contact_points": self._map_contact_points(node),
            "issued": self._map_datetime(node, "dct:issued"),
            "modified": self._map_datetime(node, "dct:modified"),
            "keywords": self._map_keywords(node),
            "groups": self._map_groups(node),
            "language": self._map_dataset_languages(node),
            "accrual_periodicity": self._map_accrual_periodicity(node),
            "coverage": "",
            "spatial": self._text(node, "dct:spatial") or "",
            "temporals": self._map_temporals(node),
            "qualified_relations": self._map_qualified_relations(node),
            "owner_org": self.organization_slug,
            "conforms_to": self._map_conforms_to(node),
            "url": self._map_landing_page(node),
            "relations": self._map_relations(node),
            "resources": self._map_distributions(node),
        }

        # Optionally append legal-basis relation from harvester config
        if self.legal_basis_url:
            dataset_dict["relations"].append(get_legal_basis_link(self.legal_basis_url))

        return dataset_dict

    # ------------------------------------------------------------------
    # Private helpers – dataset level
    # ------------------------------------------------------------------

    def _text(self, node, xpath_expr):
        """Return the stripped text content of the first matching element."""
        values = node.xpath(f"{xpath_expr}/text()", namespaces=DCAT_NS)
        return values[0].strip() if values else ""

    def _map_datetime(self, node, xpath_expr):
        return _normalize_datetime(self._text(node, xpath_expr))

    def _map_publisher(self, node):
        agents = node.xpath("dct:publisher/foaf:Agent", namespaces=DCAT_NS)
        if not agents:
            return json.dumps({"name": {lang: "" for lang in CKAN_LANGS}, "url": ""})
        agent = agents[0]
        url = agent.get(RDF_ABOUT_ATTR) or ""
        name_dict = _filter_ckan_langs(_xml_lang_dict(agent, "foaf:name"))
        return json.dumps({"name": name_dict, "url": url})

    def _map_contact_points(self, node):
        contacts = []
        for org in node.xpath(
            "dcat:contactPoint/vcard:Organization", namespaces=DCAT_NS
        ):
            fn_vals = org.xpath("vcard:fn/text()", namespaces=DCAT_NS)
            name = fn_vals[0].strip() if fn_vals else ""
            email_elems = org.xpath("vcard:hasEmail", namespaces=DCAT_NS)
            email = ""
            if email_elems:
                email_uri = _rdf_resource(email_elems[0])
                email = email_uri.replace("mailto:", "")
            contacts.append({"name": name, "email": email})
        return contacts

    def _map_keywords(self, node):
        keywords = {lang: [] for lang in CKAN_LANGS}
        for kw_elem in node.xpath("dcat:keyword", namespaces=DCAT_NS):
            from ckan.lib.munge import munge_tag

            lang = kw_elem.get(XML_LANG, "")
            text = (kw_elem.text or "").strip()
            if lang in CKAN_LANGS and text and text != "opendata.swiss":
                keywords[lang].append(munge_tag(text))
        return keywords

    def _map_groups(self, node):
        """
        Map EU authority data themes (e.g. REGI, ENVI) to opendata.swiss
        CKAN group names (lower-cased last URI segment).
        """
        groups = set()
        for theme_elem in node.xpath("dcat:theme", namespaces=DCAT_NS):
            uri = _rdf_resource(theme_elem)
            code = _uri_last_segment(uri).lower()
            if code:
                groups.add(code)
        return [{"name": group_code} for group_code in sorted(groups)]

    def _map_dataset_languages(self, node):
        langs = []
        for lang_elem in node.xpath("dct:language", namespaces=DCAT_NS):
            short = _eu_lang_to_short(_rdf_resource(lang_elem))
            if short and short in CKAN_LANGS and short not in langs:
                langs.append(short)
        return langs

    def _map_accrual_periodicity(self, node):
        elems = node.xpath("dct:accrualPeriodicity", namespaces=DCAT_NS)
        return _rdf_resource(elems[0]) if elems else ""

    def _map_temporals(self, node):
        temporals = []
        for period in node.xpath("dct:temporal/dct:PeriodOfTime", namespaces=DCAT_NS):
            start_vals = period.xpath("dcat:startDate/text()", namespaces=DCAT_NS)
            end_vals = period.xpath("dcat:endDate/text()", namespaces=DCAT_NS)
            if start_vals:
                start = _normalize_datetime(start_vals[0])
                end = _normalize_datetime(end_vals[0]) if end_vals else start
                temporals.append({"start_date": start, "end_date": end})
        return temporals

    def _map_qualified_relations(self, node):
        """
        Map ``dcat:qualifiedRelation/dcat:Relationship`` elements.
        Falls back to an empty list if the property is absent (common case).
        """
        qualified = []
        for relationship in node.xpath(
            "dcat:qualifiedRelation/dcat:Relationship", namespaces=DCAT_NS
        ):
            uri_elems = relationship.xpath("dct:relation", namespaces=DCAT_NS)
            if uri_elems:
                uri = _rdf_resource(uri_elems[0])
                if uri:
                    qualified.append(
                        {
                            "relation": uri,
                            "had_role": "http://www.iana.org/assignments/relation/related",
                        }
                    )
        return qualified

    def _map_conforms_to(self, node):
        return [
            _rdf_resource(elem)
            for elem in node.xpath("dct:conformsTo", namespaces=DCAT_NS)
            if _rdf_resource(elem)
        ]

    def _map_landing_page(self, node):
        elems = node.xpath("dcat:landingPage", namespaces=DCAT_NS)
        return _rdf_resource(elems[0]) if elems else ""

    def _map_relations(self, node):
        """
        Map ``dct:relation/rdf:Description`` elements to
        ``{"url": ..., "label": {de: ..., fr: ..., en: ..., it: ...}}``.

        geocat.ch already includes the geocat permalink as a dct:relation,
        so no separate permalink injection is needed here.
        """
        relations = []
        for relation_desc in node.xpath(
            "dct:relation/rdf:Description", namespaces=DCAT_NS
        ):
            url = relation_desc.get(RDF_ABOUT_ATTR) or ""
            if not url:
                continue
            labels_raw = _xml_lang_dict(relation_desc, "rdfs:label")
            labels = _filter_ckan_langs(labels_raw)
            # Fill missing CKAN languages with the first available value
            fallback = next(iter(labels_raw.values()), "") if labels_raw else ""
            for lang in CKAN_LANGS:
                if not labels.get(lang):
                    labels[lang] = fallback
            relations.append({"url": url, "label": labels})
        return relations

    # ------------------------------------------------------------------
    # Private helpers – distribution level
    # ------------------------------------------------------------------

    def _map_distributions(self, node):
        resources = []
        for dist in node.xpath(
            "dcat:distribution/dcat:Distribution", namespaces=DCAT_NS
        ):
            resource = self._map_single_distribution(dist)
            if resource:
                resources.append(resource)
        return resources

    def _map_single_distribution(self, dist):
        resource = {}

        # access URL (mandatory in DCAT-AP-CH)
        access_elems = dist.xpath("dcat:accessURL", namespaces=DCAT_NS)
        resource["url"] = _rdf_resource(access_elems[0]) if access_elems else ""

        # download URL (optional – present only for downloadable distributions)
        dl_elems = dist.xpath("dcat:downloadURL", namespaces=DCAT_NS)
        if dl_elems:
            dl_url = _rdf_resource(dl_elems[0])
            if dl_url:
                resource["download_url"] = dl_url

        # multilingual title (may be absent)
        title_dict = _filter_ckan_langs(_xml_lang_dict(dist, "dct:title"))
        resource["title"] = (
            title_dict if any(title_dict.values()) else _filter_ckan_langs({})
        )

        # multilingual description
        resource["description"] = _filter_ckan_langs(
            _xml_lang_dict(dist, "dct:description")
        )

        # format (EU file-type URI, passed through as-is)
        fmt_elems = dist.xpath("dct:format", namespaces=DCAT_NS)
        resource["format"] = _rdf_resource(fmt_elems[0]) if fmt_elems else ""

        # media type (IANA URI, passed through as-is)
        mt_elems = dist.xpath("dcat:mediaType", namespaces=DCAT_NS)
        resource["media_type"] = _rdf_resource(mt_elems[0]) if mt_elems else ""

        # rights / license
        lic_elems = dist.xpath("dct:license", namespaces=DCAT_NS)
        if lic_elems:
            rights = _rdf_resource(lic_elems[0])
        else:
            rs_elems = dist.xpath("dct:rights/dct:RightsStatement", namespaces=DCAT_NS)
            rights = _rdf_resource(rs_elems[0]) if rs_elems else self.default_rights
        resource["rights"] = rights
        resource["license"] = rights

        # dates
        resource["issued"] = _normalize_datetime(self._dist_text(dist, "dct:issued"))
        resource["modified"] = _normalize_datetime(
            self._dist_text(dist, "dct:modified")
        )

        # languages
        resource["language"] = [
            _eu_lang_to_short(_rdf_resource(lang_elem))
            for lang_elem in dist.xpath("dct:language", namespaces=DCAT_NS)
            if _eu_lang_to_short(_rdf_resource(lang_elem))
        ]

        return resource

    def _dist_text(self, node, xpath_expr):
        """Return first text value from an XPath on a distribution node."""
        vals = node.xpath(f"{xpath_expr}/text()", namespaces=DCAT_NS)
        return vals[0].strip() if vals else ""
