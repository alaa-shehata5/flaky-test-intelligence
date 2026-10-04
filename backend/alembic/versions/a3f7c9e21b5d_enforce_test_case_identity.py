"""enforce test case logical identity

Revision ID: a3f7c9e21b5d
Revises: 51064ed56cbe
Create Date: 2026-10-04

Adds a uniqueness guard so the same logical test (project, classname,
test name) cannot be stored under two different unique keys.
"""

from __future__ import annotations

from alembic import op


revision: str = "a3f7c9e21b5d"
down_revision: str | None = "51064ed56cbe"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # Batch mode: SQLite cannot ALTER-add constraints, so it transparently
    # uses a copy-and-move strategy there; PostgreSQL applies plain ALTER.
    with op.batch_alter_table("test_cases") as batch_op:
        batch_op.create_unique_constraint(
            "uq_test_cases_project_identity",
            ["project_id", "classname", "test_name"],
        )


def downgrade() -> None:
    with op.batch_alter_table("test_cases") as batch_op:
        batch_op.drop_constraint("uq_test_cases_project_identity", type_="unique")
