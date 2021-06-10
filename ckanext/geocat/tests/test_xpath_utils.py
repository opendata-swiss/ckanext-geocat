"""Tests for xpath utils """
from ckanext.geocat.utils import xpath_utils
import os
import unittest
from lxml import etree

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


class TestXpathUtils(unittest.TestCase):
    def setUp(self):
        xmlfile = os.path.join(__location__, 'fixtures', 'geocat-testdata.xml')
        tree = etree.parse(xmlfile)
        self.root = tree.getroot()

    def test_xpath_get_single_sub_node_for_node_and_path(self):
        path_identifier = './/gmd:fileIdentifier/gco:CharacterString/text()'
        data_identifier = '3143e92b-51fa-40ab-bcc0-fa389807e879'
        value = xpath_utils.xpath_get_single_sub_node_for_node_and_path(path=path_identifier, node=self.root)
        self.assertEqual(value, data_identifier)