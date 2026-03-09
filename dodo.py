"""Run or update the project with PyDoit."""

import glob
import shutil
import subprocess
import sys
from os import environ
from pathlib import Path

from doit.action import CmdAction

sys.path.insert(1, "./src/")

from settings import config

DOIT_CONFIG = {
    "backend": "sqlite3",
    "dep_file": "./.doit-db.sqlite",
    "default_tasks": ["full_run"],
}

DATA_DIR = Path(config("DATA_DIR"))
MANUAL_DATA_DIR = Path(config("MANUAL_DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))

environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"


# fmt: off
def jupyter_execute_notebook(notebook_path):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --log-level WARN --inplace {notebook_path}"
def jupyter_to_html(notebook_path, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --log-level WARN --output-dir={output_dir} {notebook_path}"
def jupyter_to_md(notebook_path, output_dir=OUTPUT_DIR):
    return f"jupytext --to markdown --log-level WARN --output-dir={output_dir} {notebook_path}"
def jupyter_clear_output(notebook_path):
    return f"jupyter nbconvert --log-level WARN --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace {notebook_path}"
def jupytext_to_notebook(pyfile_path, notebook_path):
    return f"jupytext --to notebook --output {notebook_path} {pyfile_path}"
# fmt: on


def copy_file(origin_path, destination_path, mkdir=True):
    """Create a Python action for copying a file."""

    def _copy_file():
        origin = Path(origin_path)
        dest = Path(destination_path)
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, dest)

    return _copy_file


def mv_file(from_path, to_path):
    """Move a file to a destination path (cross-platform)."""

    def _mv_file():
        src = Path(from_path)
        dst = Path(to_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    return _mv_file


def touch_file(path):
    """Create a Python action that touches a stamp file."""

    def _touch_file():
        stamp = Path(path)
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()

    return _touch_file


def _latexmk_engine_flag():
    """Choose the best available LaTeX engine for latexmk."""
    if shutil.which("xelatex"):
        return "-xelatex"
    if shutil.which("lualatex"):
        return "-lualatex"
    if shutil.which("pdflatex"):
        return "-pdf"
    return None


def run_latexmk(tex_file, clean=False):
    """Create a Python action that runs latexmk with an available engine."""

    def _run_latexmk():
        if not shutil.which("latexmk"):
            raise RuntimeError(
                "latexmk not found in PATH. Install TeX Live (or MacTeX) with latexmk."
            )

        engine_flag = _latexmk_engine_flag()
        if engine_flag is None:
            raise RuntimeError(
                "No TeX engine found (xelatex/lualatex/pdflatex). "
                "Install TeX Live. On Ubuntu/WSL: "
                "`sudo apt-get install texlive-xetex texlive-latex-extra`."
            )

        cmd = ["latexmk", engine_flag, "-halt-on-error"]
        if clean:
            cmd.append("-c")
        cmd.extend(["-cd", tex_file])
        subprocess.run(cmd, check=True)

    return _run_latexmk


notebook_tasks = {
    "treasury_spot_futures_tour_ipynb": {
        "path": "./src/treasury_spot_futures_tour_ipynb.py",
        "file_dep": [],
        "targets": [],
    },
}

MANUAL_INPUTS = [
    MANUAL_DATA_DIR / "bloomberg.parquet",
    MANUAL_DATA_DIR / "TFZ_IRR.parquet",
]

STAGED_INPUTS = [
    DATA_DIR / "bloomberg.parquet",
    DATA_DIR / "TFZ_IRR.parquet",
]

SPREAD_OUTPUTS = [
    DATA_DIR / "implied_repo_first_deferred.parquet",
    DATA_DIR / "holding_period_days.parquet",
    DATA_DIR / "arbitrage_spreads.parquet",
]

PLOT_OUTPUTS = [
    OUTPUT_DIR / "treasury_futures_prices.html",
    OUTPUT_DIR / "example_plot.png",
]

TABLE_OUTPUTS = [
    OUTPUT_DIR / "example_table.tex",
    OUTPUT_DIR / "pandas_to_latex_simple_table1.tex",
]


def task_config():
    """Create data and output directories."""
    return {
        "actions": ["ipython ./src/settings.py"],
        "targets": [DATA_DIR, OUTPUT_DIR],
        "file_dep": ["./src/settings.py"],
    }


def task_stage_manual_data():
    """Copy version-controlled input data from data_manual to DATA_DIR."""
    return {
        "actions": [
            copy_file(MANUAL_DATA_DIR / "bloomberg.parquet", DATA_DIR / "bloomberg.parquet"),
            copy_file(MANUAL_DATA_DIR / "TFZ_IRR.parquet", DATA_DIR / "TFZ_IRR.parquet"),
        ],
        "file_dep": MANUAL_INPUTS,
        "targets": STAGED_INPUTS,
        "task_dep": ["config"],
        "clean": True,
    }


def task_pull_live_data():
    """Optional: refresh source data from Bloomberg/WRDS."""
    bloomberg_stamp = DATA_DIR / ".stamp_pull_live_bloomberg"
    wrds_stamp = DATA_DIR / ".stamp_pull_live_crsp"
    yield {
        "name": "bloomberg",
        "actions": [
            "ipython ./src/pull_bloomberg.py",
            touch_file(bloomberg_stamp),
        ],
        "file_dep": ["./src/pull_bloomberg.py", "./src/settings.py"],
        "targets": [bloomberg_stamp],
        "task_dep": ["config"],
        "uptodate": [False],
        "clean": True,
    }
    yield {
        "name": "crsp_wrds",
        "actions": [
            "ipython ./src/pull_CRSP.py",
            touch_file(wrds_stamp),
        ],
        "file_dep": ["./src/pull_CRSP.py", "./src/settings.py"],
        "targets": [wrds_stamp],
        "task_dep": ["config"],
        "uptodate": [False],
        "clean": True,
    }


def task_calc_spreads():
    """Compute implied repo and arbitrage spread outputs."""
    return {
        "actions": [
            "python ./src/calc_spread.py --MANUAL_DATA_DIR=./_data",
        ],
        "file_dep": [
            "./src/calc_spread.py",
            "./src/settings.py",
            *STAGED_INPUTS,
        ],
        "targets": SPREAD_OUTPUTS,
        "task_dep": ["stage_manual_data"],
        "clean": True,
    }


def task_example_plot():
    """Generate chartbook HTML chart and report-ready PNG figure."""
    return {
        "actions": [
            "ipython ./src/example_plot.py",
        ],
        "file_dep": [
            "./src/example_plot.py",
            DATA_DIR / "bloomberg.parquet",
        ],
        "targets": PLOT_OUTPUTS,
        "task_dep": ["stage_manual_data"],
        "clean": True,
    }


def task_summary_stats():
    """Generate LaTeX tables used by reports."""
    return {
        "actions": [
            "ipython ./src/example_table.py",
            "ipython ./src/pandas_to_latex_demo.py",
        ],
        "file_dep": [
            "./src/example_table.py",
            "./src/pandas_to_latex_demo.py",
            DATA_DIR / "arbitrage_spreads.parquet",
        ],
        "targets": TABLE_OUTPUTS,
        "task_dep": ["calc_spreads"],
        "clean": True,
    }


# fmt: off
def task_run_notebooks():
    """Convert notebook scripts, execute, and export to HTML."""
    for notebook in notebook_tasks.keys():
        pyfile_path = Path(notebook_tasks[notebook]["path"])
        notebook_path = pyfile_path.with_suffix(".ipynb")
        yield {
            "name": notebook,
            "actions": [
                jupytext_to_notebook(pyfile_path, notebook_path),
                jupyter_execute_notebook(notebook_path),
                jupyter_to_html(notebook_path),
                mv_file(notebook_path, OUTPUT_DIR / f"{notebook}.ipynb"),
            ],
            "file_dep": [
                pyfile_path,
                *notebook_tasks[notebook]["file_dep"],
            ],
            "targets": [
                OUTPUT_DIR / f"{notebook}.html",
                OUTPUT_DIR / f"{notebook}.ipynb",
                *notebook_tasks[notebook]["targets"],
            ],
            "task_dep": ["config"],
            "clean": True,
        }
# fmt: on


def task_compile_latex_docs():
    """Compile the LaTeX documents to PDFs."""
    file_dep = [
        "./reports/report_example.tex",
        "./reports/my_article_header.sty",
        "./reports/slides_example.tex",
        "./reports/my_beamer_header.sty",
        "./reports/my_common_header.sty",
        "./reports/report_simple_example.tex",
        "./reports/slides_simple_example.tex",
        OUTPUT_DIR / "example_plot.png",
        OUTPUT_DIR / "example_table.tex",
        OUTPUT_DIR / "pandas_to_latex_simple_table1.tex",
    ]
    targets = [
        "./reports/report_example.pdf",
        "./reports/slides_example.pdf",
        "./reports/report_simple_example.pdf",
        "./reports/slides_simple_example.pdf",
    ]

    return {
        "actions": [
            run_latexmk("./reports/report_example.tex"),
            run_latexmk("./reports/report_example.tex", clean=True),
            run_latexmk("./reports/slides_example.tex"),
            run_latexmk("./reports/slides_example.tex", clean=True),
            run_latexmk("./reports/report_simple_example.tex"),
            run_latexmk("./reports/report_simple_example.tex", clean=True),
            run_latexmk("./reports/slides_simple_example.tex"),
            run_latexmk("./reports/slides_simple_example.tex", clean=True),
        ],
        "targets": targets,
        "file_dep": file_dep,
        "task_dep": ["summary_stats", "example_plot"],
        "clean": True,
    }


def task_build_chartbook_site():
    """Build the chartbook documentation site."""
    notebook_scripts = [
        Path(notebook_tasks[notebook]["path"]) for notebook in notebook_tasks.keys()
    ]
    return {
        "actions": ["chartbook build -f"],
        "targets": ["./docs/index.html"],
        "file_dep": [
            "./README.md",
            "./chartbook.toml",
            DATA_DIR / "bloomberg.parquet",
            OUTPUT_DIR / "treasury_futures_prices.html",
            *notebook_scripts,
        ],
        "task_dep": ["run_notebooks", "example_plot"],
        "clean": True,
    }


def task_run_tests():
    """Run pytest and write a JUnit report."""
    return {
        "actions": [
            CmdAction(
                f"pytest ./src/ --junitxml={OUTPUT_DIR / 'test_results.xml'} -v",
                shell=True,
            ),
        ],
        "file_dep": glob.glob("./src/*.py"),
        "targets": [OUTPUT_DIR / "test_results.xml"],
        "task_dep": ["config"],
        "clean": True,
        "verbosity": 2,
    }


def task_full_run():
    """Run the full local pipeline from staged inputs to final artifacts."""
    return {
        "actions": [],
        "task_dep": [
            "compile_latex_docs",
            "build_chartbook_site",
        ],
    }
