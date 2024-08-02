"""main file."""

from condition_analysis_web.gui import run_gui, sign_in


def main() -> None:
    """Process Main function."""
    sign_in(run_gui)


if __name__ == "__main__":
    main()
