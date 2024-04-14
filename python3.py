import sys
import json
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox, QTabWidget, QCalendarWidget, QFileDialog, QDialog
from PyQt5.QtCore import QDate, QTimer
import pyttsx3
import openai
from datetime import datetime, timedelta

class AIChatAssistant(QDialog):
    def __init__(self, project_description, response):
        super().__init__()
        self.setWindowTitle("AI Chat Assistant")
        self.setGeometry(800, 800, 800, 800)

        layout = QVBoxLayout()

        self.display_text_edit = QTextEdit()
        self.input_text_edit = QLineEdit()
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_input)

        layout.addWidget(self.display_text_edit)
        layout.addWidget(self.input_text_edit)
        layout.addWidget(send_button)

        self.setLayout(layout)

        self.assistant_responses = [project_description]
        self.assistant_responses.append(response)
        self.update_display()

    def update_display(self):
        self.display_text_edit.clear()
        self.display_text_edit.setPlainText('\n'.join(self.assistant_responses))

    def send_input(self):
        user_input = self.input_text_edit.text()
        if user_input:
            self.assistant_responses.append("User: " + user_input)
            response = self.get_ai_response(user_input)
            self.assistant_responses.append("AI: " + response)
            self.update_display()
            self.input_text_edit.clear()


    def get_ai_response(self, input_text):
        openai.api_key = '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'
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=input_text,
            max_tokens=1024
        )
        return response.choices[0].text.strip()

class ProjectDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.project_timers = {}
        self.project_chats = {}
        self.project_responses = {}
        self.load_projects()
        self.engine = pyttsx3.init()

    def init_ui(self):
        self.setWindowTitle("Project Management Dashboard")
        self.setGeometry(200, 200, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        project_name_label = QLabel("Project Name:")
        self.project_name_edit = QLineEdit()
        layout.addWidget(project_name_label)
        layout.addWidget(self.project_name_edit)

        description_label = QLabel("Description:")
        self.description_edit = QTextEdit()
        layout.addWidget(description_label)
        layout.addWidget(self.description_edit)

        start_date_label = QLabel("Start Date:")
        self.start_date_edit = QCalendarWidget()
        layout.addWidget(start_date_label)
        layout.addWidget(self.start_date_edit)

        end_date_label = QLabel("End Date:")
        self.end_date_edit = QCalendarWidget()
        layout.addWidget(end_date_label)
        layout.addWidget(self.end_date_edit)

        add_button = QPushButton("Add Project")
        add_button.clicked.connect(self.add_project)
        layout.addWidget(add_button)

        delete_button = QPushButton("Delete Project")
        delete_button.clicked.connect(self.delete_project)
        layout.addWidget(delete_button)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.show()

    def load_projects(self):
        try:
            with open('projects.json', 'r') as file:
                data = json.load(file)
                for project in data:
                    project_tab = QWidget()
                    tab_layout = QVBoxLayout()
                    project_tab.setLayout(tab_layout)

                    project_name_label = QLabel(f'Project Name: {project.get("project_name", "")}')
                    tab_layout.addWidget(project_name_label)

                    description_label = QLabel(f'Description: {project.get("description", "")}')
                    tab_layout.addWidget(description_label)

                    start_date_label = QLabel(f'Start Date: {project.get("start_date", "")}')
                    tab_layout.addWidget(start_date_label)

                    end_date_label = QLabel(f'End Date: {project.get("end_date", "")}')
                    tab_layout.addWidget(end_date_label)

                    chat_text_edit = QTextEdit()
                    tab_layout.addWidget(chat_text_edit)
                    self.project_chats[project["id"]] = chat_text_edit

                    end_datetime = datetime.strptime(project.get("end_date", ""), "%Y-%m-%d")
                    remaining_time_label = QLabel("Time left: 00:00:00")
                    tab_layout.addWidget(remaining_time_label)
                    self.setup_timer(project.get("id", ""), end_datetime, remaining_time_label)

                    self.tab_widget.addTab(project_tab, f'Project {project.get("id", "")}')

        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def setup_timer(self, project_id, end_datetime, timer_label):
        def update_time():
            remaining_time = end_datetime - datetime.now()
            if remaining_time.total_seconds() <= 0:
                timer.stop()
                remaining_time = timedelta(seconds=0)

            hours = remaining_time.days * 24 + remaining_time.seconds // 3600
            minutes = (remaining_time.seconds // 60) % 60
            seconds = remaining_time.seconds % 60

            timer_label.setText(f'Time left: {hours:02}:{minutes:02}:{seconds:02}')

        timer = QTimer()
        timer.timeout.connect(update_time)
        timer.start(1000)
        self.project_timers[project_id] = timer

    def add_project(self):
        project_name = self.project_name_edit.text()
        description = self.description_edit.toPlainText()
        start_date = self.start_date_edit.selectedDate().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.selectedDate().toString("yyyy-MM-dd")

        if not all([project_name, description, start_date, end_date]):
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        try:
            with open('projects.json', 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        except FileNotFoundError:
            data = []

        project_id = len(data) + 1

        new_project = {
            "id": project_id,
            "project_name": project_name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date
        }

        data.append(new_project)

        with open('projects.json', 'w') as file:
            json.dump(data, file, indent=4)

        self.tab_widget.clear()
        self.load_projects()

        # Create a new file with the project name
        project_folder = f"{os.getcwd()}/{project_name}"
        os.makedirs(project_folder, exist_ok=True)
        with open(f"{project_folder}/{project_name}.txt", "w") as project_file:
            project_file.write(description)

        # Display the AI Chat Assistant dialog with project description
        assistant_response = "Welcome to the project chat!"
        self.project_responses[project_id] = {"assistant_response": assistant_response}
        ai_dialog = AIChatAssistant(description, assistant_response)
        ai_dialog.exec_()

        self.project_name_edit.clear()
        self.description_edit.clear()
        self.start_date_edit.setSelectedDate(QDate.currentDate())
        self.end_date_edit.setSelectedDate(QDate.currentDate())

    def delete_project(self):
        selected_index = self.tab_widget.currentIndex()

        if selected_index in self.project_timers:
            self.project_timers[selected_index].stop()
            del self.project_timers[selected_index]

        try:
            with open('projects.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []

        if selected_index < len(data):
            del data[selected_index]

            with open('projects.json', 'w') as file:
                json.dump(data, file, indent=4)

        self.tab_widget.clear()
        self.load_projects()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = ProjectDashboard()
    sys.exit(app.exec_())