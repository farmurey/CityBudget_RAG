import click
import json
from pathlib import Path
from main import CityBudgetRAG
from src.config import Config

@click.group()
def cli():
    """City Budget RAG CLI"""
    pass

@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--city', default='Unknown', help='City name')
@click.option('--year', default='Unknown', help='Fiscal year')
def ingest(pdf_path, city, year):
    """Ingest a PDF document"""
    config = Config()
    rag = CityBudgetRAG(config)
    
    metadata = {
        "file_name": Path(pdf_path).name,
        "city_name": city,
        "fiscal_year": year
    }
    
    result = rag.ingest_document(pdf_path, metadata)
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.argument('question')
def query(question):
    """Query the system"""
    config = Config()
    rag = CityBudgetRAG(config)
    
    result = rag.query(question)
    click.echo(f"\nAnswer: {result['answer']}\n")
    click.echo("Sources:")
    for source in result['sources']:
        click.echo(f"  - Page {source['page']}: {source['document']}")

if __name__ == '__main__':
    cli()