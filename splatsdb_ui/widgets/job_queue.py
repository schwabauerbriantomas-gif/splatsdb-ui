# SPDX-License-Identifier: GPL-3.0
"""Job queue panel — background operation progress."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QFrame,
)
from PySide6.QtCore import Qt


class JobItem(QFrame):
    """A single job in the queue."""

    def __init__(self, job_id: str, description: str):
        super().__init__()
        self.job_id = job_id
        self._build_ui(description)

        self.setStyleSheet("""
            JobItem {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)

    def _build_ui(self, description: str):
        layout = QHBoxLayout(self)

        layout.addWidget(QLabel(f"⏳ {description}"))

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(200)
        self.progress.setFixedHeight(12)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Running...")
        self.status_label.setStyleSheet("color: #f9e2af; font-size: 11px;")
        layout.addWidget(self.status_label)


class JobQueuePanel(QWidget):
    """Bottom panel showing running background jobs."""

    def __init__(self):
        super().__init__()
        self._jobs: dict[str, JobItem] = {}
        self._build_ui()

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)

        header = QHBoxLayout()
        header.addWidget(QLabel("Jobs"))
        header.addStretch()
        self.count_label = QLabel("0 active")
        self.count_label.setStyleSheet("color: #585b70; font-size: 11px;")
        header.addWidget(self.count_label)
        self._layout.addLayout(header)

        self._jobs_layout = QVBoxLayout()
        self._layout.addLayout(self._jobs_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
            }
        """)

    def add_job(self, job_id: str, description: str):
        item = JobItem(job_id, description)
        self._jobs[job_id] = item
        self._jobs_layout.addWidget(item)
        self.count_label.setText(f"{len(self._jobs)} active")

    def finish_job(self, job_id: str, success: bool):
        item = self._jobs.get(job_id)
        if item:
            if success:
                item.status_label.setText("✅ Done")
                item.status_label.setStyleSheet("color: #a6e3a1; font-size: 11px;")
            else:
                item.status_label.setText("❌ Failed")
                item.status_label.setStyleSheet("color: #f38ba8; font-size: 11px;")

    def update_job(self, job_id: str, progress: int):
        item = self._jobs.get(job_id)
        if item:
            item.progress.setValue(progress)
