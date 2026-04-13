# SPDX-License-Identifier: GPL-3.0
"""Search mixin — global search handling."""


class SearchMixin:
    """Search behavior mixin for MainWindow."""

    def execute_global_search(self, query: str):
        self.switch_view("search")
        self._views["search"].execute_search(query)
