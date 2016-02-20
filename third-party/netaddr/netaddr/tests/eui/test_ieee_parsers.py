import os
import sys

import pytest

from netaddr.eui.ieee import OUIIndexParser, IABIndexParser, FileIndexer


SAMPLE_DIR = os.path.dirname(__file__)

@pytest.mark.skipif(sys.version_info > (3,), reason="requires python 2.x")
def test_oui_parser_py2():
    from cStringIO import StringIO
    outfile = StringIO()
    with open(os.path.join(SAMPLE_DIR, 'sample_oui.txt')) as infile:
        iab_parser = OUIIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '51966,1,138\n'


@pytest.mark.skipif(sys.version_info > (3,), reason="requires python 2.x")
def test_iab_parser_py2():
    from cStringIO import StringIO
    outfile = StringIO()
    with open(os.path.join(SAMPLE_DIR, 'sample_iab.txt')) as infile:
        iab_parser = IABIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '84683452,1,181\n'


@pytest.mark.skipif(sys.version_info < (3,), reason="requires python 3.x")
def test_oui_parser_py3():
    from io import StringIO
    outfile = StringIO()
    with open(os.path.join(SAMPLE_DIR, 'sample_oui.txt')) as infile:
        iab_parser = OUIIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '51966,1,138\n'


@pytest.mark.skipif(sys.version_info < (3,), reason="requires python 3.x")
def test_iab_parser_py3():
    from io import StringIO
    outfile = StringIO()
    with open(os.path.join(SAMPLE_DIR, 'sample_iab.txt')) as infile:
        iab_parser = IABIndexParser(infile)
        iab_parser.attach(FileIndexer(outfile))
        iab_parser.parse()
    assert outfile.getvalue() == '84683452,1,181\n'
