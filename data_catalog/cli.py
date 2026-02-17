# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for the data catalog.

Designed for developer usage -- no API server required. All commands
operate against the local DuckDB catalog database.

CUSTOMIZE: Add domain-specific commands for your use case.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from data_catalog.db.connection import get_db
from data_catalog.db.repositories import AssetRepository, RelationshipRepository

console = Console()


@click.group()
def cli():
    """Data Catalog CLI -- query metadata without an API."""
    pass


# ------------------------------------------------------------------
# Search & Browse
# ------------------------------------------------------------------


@cli.command()
@click.argument("search_term")
@click.option("--limit", "-l", default=10, help="Max results")
def search(search_term: str, limit: int):
    """Search for assets by name or description.

    Example::

        catalog-cli search patient
        catalog-cli search "dbo" --limit 20
    """
    with get_db() as db:
        repo = AssetRepository(db)
        assets = repo.find_all(limit=500)

        matching = [
            a for a in assets
            if search_term.lower() in a.qualified_name.lower()
            or (a.description and search_term.lower() in a.description.lower())
        ]

        if not matching:
            console.print(f"[yellow]No assets matching '{search_term}'[/yellow]")
            return

        table = Table(title=f"Search: '{search_term}'")
        table.add_column("Qualified Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Rows", justify="right")
        table.add_column("Description", style="dim")

        for asset in matching[:limit]:
            rows = asset.statistics.get("row_count", 0) if asset.statistics else 0
            desc = (asset.description or "")[:50]
            table.add_row(asset.qualified_name, asset.asset_type, f"{rows:,}", desc)

        console.print(table)
        console.print(f"\n[dim]{len(matching[:limit])} of {len(matching)} results[/dim]")


@cli.command()
@click.argument("qualified_name")
def describe(qualified_name: str):
    """Show detailed information about an asset.

    Example::

        catalog-cli describe "[dbo].[Customers]"
    """
    with get_db() as db:
        repo = AssetRepository(db)
        asset = repo.find_by_qualified_name(qualified_name)

        if not asset:
            console.print(f"[red]Asset not found: {qualified_name}[/red]")
            return

        console.print(f"\n[bold cyan]{asset.qualified_name}[/bold cyan]")
        console.print(f"[dim]{asset.description or 'No description'}[/dim]\n")

        info = Table.grid(padding=(0, 2))
        info.add_column(style="bold")
        info.add_column()
        info.add_row("Type:", asset.asset_type)
        info.add_row("Source:", asset.source_system)
        if asset.statistics:
            info.add_row("Rows:", f"{asset.statistics.get('row_count', 0):,}")
        console.print(info)

        if asset.schema_metadata and "columns" in asset.schema_metadata:
            console.print("\n[bold]Columns:[/bold]")
            col_table = Table()
            col_table.add_column("Name", style="cyan")
            col_table.add_column("Type", style="green")
            for col in asset.schema_metadata["columns"]:
                col_table.add_row(
                    col["name"],
                    col.get("data_type", col.get("type", "unknown")),
                )
            console.print(col_table)


@cli.command("list-assets")
@click.option("--schema", "-s", help="Schema pattern filter")
@click.option("--limit", "-l", default=100, help="Max results")
def list_assets(schema: str | None, limit: int):
    """List all assets in the catalog.

    Example::

        catalog-cli list-assets
        catalog-cli list-assets --schema "dbo%"
    """
    with get_db() as db:
        repo = AssetRepository(db)
        if schema:
            assets = repo.find_by_schema_pattern(schema)
        else:
            assets = repo.find_all(limit=limit)

        if not assets:
            console.print("[yellow]No assets found[/yellow]")
            return

        table = Table(title="Catalog Assets")
        table.add_column("Qualified Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Rows", justify="right")

        for asset in assets[:limit]:
            rows = f"{asset.statistics.get('row_count', 0):,}" if asset.statistics else ""
            table.add_row(asset.qualified_name, asset.asset_type, rows)

        console.print(table)
        console.print(f"\n[dim]Total: {len(assets)} assets[/dim]")


@cli.command()
@click.argument("qualified_name")
def relationships(qualified_name: str):
    """Show FK relationships for an asset.

    Example::

        catalog-cli relationships "[dbo].[Orders]"
    """
    with get_db() as db:
        asset_repo = AssetRepository(db)
        rel_repo = RelationshipRepository(db)

        asset = asset_repo.find_by_qualified_name(qualified_name)
        if not asset:
            console.print(f"[red]Asset not found: {qualified_name}[/red]")
            return

        rels = rel_repo.find_by_asset(asset.id)
        if not rels:
            console.print(f"[yellow]No relationships for {qualified_name}[/yellow]")
            return

        table = Table(title=f"Relationships: {qualified_name}")
        table.add_column("Type", style="cyan")
        table.add_column("References")
        table.add_column("Columns")
        table.add_column("Validated", justify="center")

        for rel in rels:
            if rel.parent_asset_id == asset.id:
                other = asset_repo.find_by_id(rel.referenced_asset_id)
                direction = "->"
            else:
                other = asset_repo.find_by_id(rel.parent_asset_id)
                direction = "<-"

            ref_name = other.qualified_name if other else "Unknown"
            cols = ", ".join(
                f"{m['parent']}->{m['referenced']}"
                for m in rel.column_mappings[:2]
            )
            if len(rel.column_mappings) > 2:
                cols += f" (+{len(rel.column_mappings) - 2})"

            validated = "Y" if rel.is_validated else "N"
            table.add_row(rel.relationship_type, f"{direction} {ref_name}", cols, validated)

        console.print(table)


# ------------------------------------------------------------------
# Discovery Commands
# ------------------------------------------------------------------


@cli.command("discover-grain")
@click.argument("asset", required=False)
@click.option("--schema", "-s", help="Schema pattern")
@click.option("--all", "-a", "discover_all", is_flag=True, help="All assets")
def discover_grain_cmd(asset: str | None, schema: str | None, discover_all: bool):
    """Discover primary key (grain) for assets.

    Requires a source database connection.

    Example::

        catalog-cli discover-grain "[dbo].[Orders]"
        catalog-cli discover-grain --schema "dbo"
    """
    # CUSTOMIZE: Replace with your source database connection logic.
    console.print(
        "[yellow]Source database connection required. "
        "Customize _get_source_cursor() in cli.py.[/yellow]"
    )


@cli.command("discover-fk")
@click.argument("asset", required=False)
@click.option("--schema", "-s", help="Schema pattern")
def discover_fk_cmd(asset: str | None, schema: str | None):
    """Discover foreign key relationships.

    Requires a source database connection for validation.

    Example::

        catalog-cli discover-fk "[dbo].[Orders]"
    """
    console.print(
        "[yellow]Source database connection required. "
        "Customize _get_source_cursor() in cli.py.[/yellow]"
    )


# ------------------------------------------------------------------
# RAG Search
# ------------------------------------------------------------------


@cli.command("rag-search")
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Results to return")
@click.option("--expand/--no-expand", default=True, help="Graph expansion")
def rag_search_cmd(query: str, top_k: int, expand: bool):
    """Semantic search across catalog metadata.

    Uses Hamming pre-filter + cosine rerank for fast retrieval.

    Example::

        catalog-cli rag-search "patient diagnosis codes"
        catalog-cli rag-search "billing transactions" --top-k 20
    """
    from data_catalog.services.rag_search import RAGSearchService

    with get_db() as db:
        service = RAGSearchService(db)
        results = service.search(query, top_k=top_k, expand_graph=expand)

        if not results:
            console.print(f"[yellow]No results for: {query}[/yellow]")
            return

        table = Table(title=f"RAG Search: '{query}'")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Asset", style="cyan")
        table.add_column("Column", style="green")
        table.add_column("Score", justify="right")
        table.add_column("Description", style="dim")

        for i, r in enumerate(results, 1):
            score = f"{r.get('score', 0):.3f}"
            desc = (r.get("description", "") or "")[:40]
            table.add_row(
                str(i),
                r.get("qualified_name", ""),
                r.get("column_name", ""),
                score,
                desc,
            )

        console.print(table)


# ------------------------------------------------------------------
# Coverage & Stats
# ------------------------------------------------------------------


@cli.command()
@click.option("--by", "group_by", default="schema",
              type=click.Choice(["schema", "schema-table"]))
def coverage(group_by: str):
    """Show pipeline coverage status.

    Example::

        catalog-cli coverage
        catalog-cli coverage --by schema-table
    """
    from data_catalog.db.models import (
        ColumnValueFrequency,
        ColumnVector,
        SearchIndexColumn,
    )

    with get_db() as db:
        repo = AssetRepository(db)
        assets = repo.find_all(limit=1000)

        if group_by == "schema":
            # Schema-level summary
            schemas: dict[str, dict] = {}
            for asset in assets:
                s = asset.table_schema
                if s not in schemas:
                    schemas[s] = {"assets": 0, "confirmed_pk": 0, "no_pk": 0}
                schemas[s]["assets"] += 1
                gs = (asset.schema_metadata or {}).get("grain_status")
                if gs == "confirmed":
                    schemas[s]["confirmed_pk"] += 1
                elif gs == "no_natural_pk":
                    schemas[s]["no_pk"] += 1

            table = Table(title="Coverage by Schema")
            table.add_column("Schema", style="cyan")
            table.add_column("Assets", justify="right")
            table.add_column("PK Confirmed", justify="right", style="green")
            table.add_column("No PK", justify="right", style="yellow")

            for schema, info in sorted(schemas.items()):
                table.add_row(
                    schema,
                    str(info["assets"]),
                    str(info["confirmed_pk"]),
                    str(info["no_pk"]),
                )

            console.print(table)
        else:
            # Per-asset detail
            table = Table(title="Coverage by Asset")
            table.add_column("Asset", style="cyan")
            table.add_column("PK Status", style="green")
            table.add_column("Columns", justify="right")

            for asset in assets:
                gs = (asset.schema_metadata or {}).get("grain_status", "unknown")
                cols = len((asset.schema_metadata or {}).get("columns", []))
                table.add_row(asset.qualified_name, gs, str(cols))

            console.print(table)


@cli.command()
def stats():
    """Show one-screen catalog summary.

    Example::

        catalog-cli stats
    """
    from data_catalog.db.models import ColumnVector, Relationship

    with get_db() as db:
        repo = AssetRepository(db)
        assets = repo.find_all(limit=10000)

        total = len(assets)
        confirmed = sum(
            1 for a in assets
            if (a.schema_metadata or {}).get("grain_status") == "confirmed"
        )
        no_pk = sum(
            1 for a in assets
            if (a.schema_metadata or {}).get("grain_status") == "no_natural_pk"
        )
        unknown = total - confirmed - no_pk

        rels = db.query(Relationship).count()
        validated = db.query(Relationship).filter(
            Relationship.is_validated == True  # noqa: E712
        ).count()

        vectors = db.query(ColumnVector).count()

        console.print("\n[bold]Data Catalog Summary[/bold]\n")
        console.print(f"  Assets:        {total}")
        console.print(f"  PK confirmed:  [green]{confirmed}[/green]")
        console.print(f"  No natural PK: [yellow]{no_pk}[/yellow]")
        if unknown:
            console.print(f"  Unknown:       [red]{unknown}[/red]")
        console.print(f"  Relationships: {rels} ({validated} validated)")
        console.print(f"  Vectors:       {vectors}")
        console.print()


# ------------------------------------------------------------------
# Graph Analysis
# ------------------------------------------------------------------


@cli.command("graph-analyze")
@click.option("--schema", "-s", help="Schema pattern filter")
@click.option("--output", "-o", "output_format", default="text",
              type=click.Choice(["text", "json"]))
def graph_analyze_cmd(schema: str | None, output_format: str):
    """Run graph analysis on FK relationships.

    Computes communities, PageRank, and clustering.

    Example::

        catalog-cli graph-analyze
        catalog-cli graph-analyze --output json
    """
    from data_catalog.services.graph_metrics import GraphMetricsService

    with get_db() as db:
        service = GraphMetricsService(db)
        results = service.analyze(schema_filter=schema)

        if output_format == "json":
            console.print(json.dumps(results, indent=2, default=str))
        else:
            console.print("\n[bold]Graph Analysis Results[/bold]\n")
            console.print(f"  Nodes: {results.get('nodes', 0)}")
            console.print(f"  Edges: {results.get('edges', 0)}")
            console.print(f"  Communities: {results.get('communities', 0)}")

            if "top_pagerank" in results:
                console.print("\n[bold]Top PageRank:[/bold]")
                for item in results["top_pagerank"][:10]:
                    console.print(
                        f"  {item['name']}: {item['score']:.4f}"
                    )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main():
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
