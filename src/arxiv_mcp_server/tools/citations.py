"""Citation management functionality for the arXiv MCP server."""

import arxiv
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import mcp.types as types
from ..config import Settings

logger = logging.getLogger("arxiv-mcp-server")
settings = Settings()

# Define citation formats
CITATION_FORMATS = ["apa", "mla", "chicago", "harvard", "ieee", "bibtex"]


citation_tool = types.Tool(
    name="format_citation",
    description="Format a citation for an arXiv paper in various academic styles",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper to cite"
            },
            "format": {
                "type": "string",
                "description": "Citation format to use",
                "enum": CITATION_FORMATS,
                "default": "apa"
            }
        },
        "required": ["paper_id"]
    }
)


def format_authors(authors: List[str], format_type: str) -> str:
    """Format author names according to citation style."""
    if not authors:
        return ""
    
    if format_type == "apa":
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]}"
        else:
            return f"{authors[0]} et al."
    
    elif format_type == "mla":
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]}, and {authors[1]}"
        else:
            return f"{authors[0]} et al."
    
    elif format_type == "chicago":
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        elif len(authors) <= 7:
            # Chicago style lists up to 7 authors
            return ", ".join(authors[:-1]) + ", and " + authors[-1]
        else:
            return f"{authors[0]} et al."
    
    elif format_type == "harvard":
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        elif len(authors) == 3:
            return f"{authors[0]}, {authors[1]} and {authors[2]}"
        else:
            return f"{authors[0]} et al."
    
    elif format_type == "ieee":
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            # IEEE lists all authors
            return ", ".join(authors[:-1]) + ", and " + authors[-1]
    
    # Default case
    return ", ".join(authors)


def generate_citation(paper: arxiv.Result, format_type: str) -> str:
    """Generate citation string for a paper in the specified format."""
    # Extract common metadata
    title = paper.title
    authors = [author.name for author in paper.authors]
    year = paper.published.year
    month = paper.published.strftime("%B")
    url = paper.entry_id
    arxiv_id = paper.get_short_id()
    
    # Format authors based on citation style
    formatted_authors = format_authors(authors, format_type)
    
    if format_type == "apa":
        return f"{formatted_authors} ({year}). {title}. arXiv preprint arXiv:{arxiv_id}. {url}"
    
    elif format_type == "mla":
        return f"{formatted_authors}. \"{title}.\" arXiv, {month} {year}, {url}."
    
    elif format_type == "chicago":
        return f"{formatted_authors}. \"{title}.\" arXiv preprint arXiv:{arxiv_id} ({year}). {url}."
    
    elif format_type == "harvard":
        return f"{formatted_authors}, {year}. {title}. arXiv:{arxiv_id}. Available at: {url} [Accessed {datetime.now().strftime('%d %B %Y')}]."
    
    elif format_type == "ieee":
        return f"{formatted_authors}, \"{title},\" arXiv:{arxiv_id}, {year}."
    
    elif format_type == "bibtex":
        # Create BibTeX entry
        first_author_last = authors[0].split()[-1] if authors else "Unknown"
        bibtex = f"@article{{{first_author_last.lower()}{year},\n"
        bibtex += f"  author = {{{' and '.join(authors)}}},\n"
        bibtex += f"  title = {{{title}}},\n"
        bibtex += f"  journal = {{arXiv preprint arXiv:{arxiv_id}}},\n"
        bibtex += f"  year = {{{year}}},\n"
        bibtex += f"  url = {{{url}}}\n"
        bibtex += "}"
        return bibtex
    
    # If format is not recognized, return a default format
    return f"{formatted_authors}. {title}. arXiv:{arxiv_id}, {year}. {url}"


async def handle_citation(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle citation formatting requests."""
    try:
        paper_id = arguments["paper_id"]
        format_type = arguments.get("format", "apa").lower()
        
        # Validate format type
        if format_type not in CITATION_FORMATS:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"Unsupported citation format: {format_type}. Supported formats: {', '.join(CITATION_FORMATS)}"
                })
            )]
        
        # Fetch paper metadata
        client = arxiv.Client()
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        
        # Generate citation
        citation = generate_citation(paper, format_type)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "paper_id": paper_id,
                "format": format_type,
                "citation": citation
            })
        )]
        
    except StopIteration:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Paper {paper_id} not found on arXiv"
            })
        )]
    except Exception as e:
        logger.error(f"Citation error: {str(e)}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "status": "error",
                "message": f"Error: {str(e)}"
            })
        )]