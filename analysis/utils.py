from pandas import DataFrame
from typing import List
import numpy as np

def escape_latex(text):
    return str(text).replace('_', r'\_')

def format_floats(num: float) -> str:
    """Format time with comma as decimal separator."""
    return f"{num:.3f}".replace('.', ',')

def prepare_value_for_latex(value) -> str:
    """Prepare different types of values for LaTeX output."""
    if isinstance(value, (float, np.floating)):
        return format_floats(value)
    return escape_latex(value)

# currently only supports basic tables
def df_to_table(df: DataFrame, table_name: str, table_label: str) -> str:
    latex_output: List[str] = []

    latex_output.append(r"\begin{table}[H]")
    latex_output.append(r"\centering")
    latex_output.append(r"\caption{" + table_name + "}")
    latex_output.append(r"\label{" + table_label + "}")
    latex_output.append(r"\begin{tabular}{|" + "|".join(["c"] * len(df.columns)) + r"|}")
    latex_output.append(r"\hline")
    latex_output.append(" & ".join([r"\textbf{"+x+"}" for x in list(df.columns.values)]) + r" \\")
    latex_output.append(r"\hline")
    for _, row in df.iterrows():
        latex_output.append(" & ".join([str(prepare_value_for_latex(item)) for item in row.values]) + r" \\ \hline")
    latex_output.append(r"\end{tabular}")
    latex_output.append(r"\end{table}")

    return '\n'.join(latex_output)
