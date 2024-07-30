"""main file."""

from condition_analysis_web.gui import run_gui, sign_up


def main() -> None:
    """Process Main function."""
    sign_up(run_gui)


if __name__ == "__main__":
    main()
