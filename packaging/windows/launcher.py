"""Entry point used by the frozen Windows distribution."""

from anatomia_app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
