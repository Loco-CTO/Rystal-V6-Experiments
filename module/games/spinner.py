#  ------------------------------------------------------------
#  Copyright (c) 2024 Rystal-Team
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#  ------------------------------------------------------------

import secrets
from typing import Any, List


class Spinner:
    def __init__(self):
        """Initializes the Spinner with a list of emoji options."""
        self.options: List[str] = [
            "🟥",
            "🟧",
            "🟨",
            "🟩",
            "🟦",
            "🟪",
            "🟫",
            "❤️",
            "🧡",
            "💛",
            "💚",
            "💙",
            "💜",
            "🤎",
            "🔴",
            "🟠",
            "🟡",
            "🟢",
            "🔵",
            "🟣",
            "🟤",
            "🃏",
            "⚪",
            "⚫",
        ]

    def spin_wheel(self) -> List[str]:
        """
        Spins the wheel and returns a list of 4 random options.

        Returns:
            list: A list of 4 randomly chosen emoji options.
        """
        return [secrets.choice(self.options) for _ in range(4)]

    @staticmethod
    def is_winning(columns: List[str]) -> tuple[Any, bool, bool]:
        """
        Determines if the given columns result in a win.

        Args:
            columns (list): A list of 4 emoji options.

        Returns:
            bool: True if the columns result in a win, False otherwise.
        """
        if "🃏" in columns:
            return False, False, False

        col1, col2, col3, col4 = columns
        mega_score = False

        if col1 == col2 == col3 == col4:
            if col1 in ("⚪", "⚫"):
                mega_score = True
            return True, mega_score, False

        def is_wildcard(col: str) -> bool:
            """
            Checks if the given column is a wildcard.

            Args:
                col (str): An emoji option.

            Returns:
                bool: True if the column is a wildcard, False otherwise.
            """
            return col in ["⚪", "⚫"]

        def check_wildcard_combinations(c1: str, c2: str, c3: str, c4: str) -> bool:
            """
            Checks if the columns result in a win considering wildcard combinations.

            Args:
                c1 (str): First column.
                c2 (str): Second column.
                c3 (str): Third column.
                c4 (str): Fourth column.

            Returns:
                bool: True if the columns result in a win considering wildcard combinations, False otherwise.
            """
            if {"⚫", "⚪"}.issubset({c1, c2, c3, c4}):
                return False

            return (
                (c1 == c2 == c3 and is_wildcard(c4))
                or (c1 == c2 == c4 and is_wildcard(c3))
                or (c1 == c3 == c4 and is_wildcard(c2))
                or (c2 == c3 == c4 and is_wildcard(c1))
                or (is_wildcard(c1) and is_wildcard(c2) and c1 == c2 and c3 == c4)
                or (is_wildcard(c1) and is_wildcard(c3) and c1 == c3 and c2 == c4)
                or (is_wildcard(c1) and is_wildcard(c4) and c1 == c4 and c2 == c3)
                or (is_wildcard(c2) and is_wildcard(c3) and c2 == c3 and c1 == c4)
                or (is_wildcard(c2) and is_wildcard(c4) and c2 == c4 and c1 == c3)
                or (is_wildcard(c3) and is_wildcard(c4) and c3 == c4 and c1 == c2)
            )

        return (
            check_wildcard_combinations(col1, col2, col3, col4),
            mega_score,
            check_wildcard_combinations(col1, col2, col3, col4),
        )

    def play(self) -> tuple[Any, list[str], bool, bool]:
        """
        Spins the wheel and checks if the result is a winning combination.

        Returns:
            tuple: A tuple containing a boolean indicating if it's a win and the list of columns.
        """
        columns = self.spin_wheel()
        won, mega_score, deficient_score = self.is_winning(columns)
        return won, columns, mega_score, deficient_score

    def run_simulation(self, num_spins: int, print_results: bool = False) -> float:
        """
        Runs a simulation of the spinner for a given number of spins.

        Args:
            num_spins (int): The number of spins to simulate.
            print_results (bool): If True, prints the results of each win and the overall statistics.

        Returns:
            float: The winning percentage of the simulation.
        """
        wins = 0
        mega_scores = 0
        deficient_scores = 0
        for _ in range(num_spins):
            win, columns, mega_score, deficient_score = self.play()
            if win:
                wins += 1
                if print_results:
                    print(", ".join(columns))
                if mega_score:
                    mega_scores += 1
                if deficient_score:
                    deficient_scores += 1

        winning_percentage = (wins / num_spins) * 100
        if print_results:
            print(f"Number of spins: {num_spins}")
            print(f"Number of wins: {wins}")
            print(f"Number of mega scores: {mega_scores}")
            print(f"Number of deficient scores: {deficient_scores}")
            print(f"Winning percentage: {winning_percentage:.2f}%")
            print(
                "Mega score rate: {:.2f}%".format((mega_scores / wins) * 100)
                if mega_scores != 0
                else "No mega scores"
            )
            print(
                "deficient score rate: {:.2f}%".format((deficient_scores / wins) * 100)
                if deficient_scores != 0
                else "No deficient scores"
            )
            print(
                "Winning percentage after deficient scores: {:.2f}%".format(
                    (wins - deficient_scores) / num_spins * 100
                )
            )
        return winning_percentage


if __name__ == "__main__":
    spinner = Spinner()
    spinner.run_simulation(10000, print_results=True)
