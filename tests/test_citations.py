"""Tests for citation management functionality."""

import pytest
import json
from unittest.mock import MagicMock, patch
from src.arxiv_mcp_server.tools.citations import handle_citation, generate_citation


# Mock data
class MockAuthor:
    def __init__(self, name):
        self.name = name

@pytest.fixture
def mock_arxiv_paper():
    mock_paper = MagicMock()
    mock_paper.title = "Understanding Deep Learning Requires Rethinking Generalization"
    mock_paper.authors = [
        MockAuthor("Zhang, Chiyuan"),
        MockAuthor("Bengio, Samy"),
        MockAuthor("Hardt, Moritz"),
        MockAuthor("Recht, Benjamin"),
        MockAuthor("Vinyals, Oriol")
    ]
    mock_paper.entry_id = "http://arxiv.org/abs/1611.03530v2"
    mock_paper.get_short_id.return_value = "1611.03530"
    
    # Mock the published date
    import datetime
    mock_paper.published = datetime.datetime(2017, 2, 15)
    
    return mock_paper


@pytest.mark.asyncio
@patch('arxiv.Client')
async def test_handle_citation_apa_format(mock_client, mock_arxiv_paper):
    # Configure mock
    mock_instance = mock_client.return_value
    mock_instance.results.return_value = iter([mock_arxiv_paper])
    
    # Test APA format
    result = await handle_citation({"paper_id": "1611.03530", "format": "apa"})
    
    # Check response format
    assert len(result) == 1
    assert result[0].type == "text"
    
    # Parse the JSON response
    response = json.loads(result[0].text)
    assert response["status"] == "success"
    assert response["paper_id"] == "1611.03530"
    assert response["format"] == "apa"
    assert "citation" in response
    
    # Verify citation format (APA style)
    assert "Zhang, Chiyuan et al. (2017)" in response["citation"]
    assert "Understanding Deep Learning Requires Rethinking Generalization" in response["citation"]
    assert "arXiv:1611.03530" in response["citation"]


@pytest.mark.asyncio
@patch('arxiv.Client')
async def test_handle_citation_bibtex_format(mock_client, mock_arxiv_paper):
    # Configure mock
    mock_instance = mock_client.return_value
    mock_instance.results.return_value = iter([mock_arxiv_paper])
    
    # Test BibTeX format
    result = await handle_citation({"paper_id": "1611.03530", "format": "bibtex"})
    
    # Parse the JSON response
    response = json.loads(result[0].text)
    assert response["status"] == "success"
    
    # Verify BibTeX format
    assert "@article{" in response["citation"]
    assert "author = {Zhang, Chiyuan and Bengio, Samy and Hardt, Moritz and Recht, Benjamin and Vinyals, Oriol}" in response["citation"]
    assert "title = {Understanding Deep Learning Requires Rethinking Generalization}" in response["citation"]
    assert "year = {2017}" in response["citation"]


@pytest.mark.asyncio
@patch('arxiv.Client')
async def test_handle_citation_invalid_format(mock_client, mock_arxiv_paper):
    # Configure mock
    mock_instance = mock_client.return_value
    mock_instance.results.return_value = iter([mock_arxiv_paper])
    
    # Test invalid format
    result = await handle_citation({"paper_id": "1611.03530", "format": "invalid_format"})
    
    # Parse the JSON response
    response = json.loads(result[0].text)
    assert response["status"] == "error"
    assert "Unsupported citation format" in response["message"]


@pytest.mark.asyncio
@patch('arxiv.Client')
async def test_handle_citation_paper_not_found(mock_client):
    # Configure mock to simulate paper not found
    mock_instance = mock_client.return_value
    mock_instance.results.return_value = iter([])  # Empty iterator
    
    # Test paper not found
    result = await handle_citation({"paper_id": "non_existent_id"})
    
    # Parse the JSON response
    response = json.loads(result[0].text)
    assert response["status"] == "error"
    assert "not found on arXiv" in response["message"]


def test_generate_citation_formats(mock_arxiv_paper):
    """Test that all citation formats are generated correctly."""
    formats = ["apa", "mla", "chicago", "harvard", "ieee", "bibtex"]
    
    for format_type in formats:
        citation = generate_citation(mock_arxiv_paper, format_type)
        assert citation  # Citation should not be empty
        
        # Basic checks for each format
        if format_type == "apa":
            assert "(2017)" in citation
        elif format_type == "mla":
            assert "arXiv," in citation
        elif format_type == "chicago":
            assert "arXiv preprint" in citation
        elif format_type == "harvard":
            assert "2017." in citation
        elif format_type == "ieee":
            assert "\"Understanding Deep Learning Requires Rethinking Generalization,\"" in citation
        elif format_type == "bibtex":
            assert "@article{" in citation
            assert "author =" in citation
            assert "title =" in citation
