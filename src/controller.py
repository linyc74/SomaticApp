from typing import List
from fabric import Connection
from .io import IO
from .view import View
from .model import BuildSubmissionCommands, COMPUTE_ROOT_DIR, COMPUTE_BASH_PROFILE


class Controller:

    io: IO
    view: View

    def __init__(self, io: IO, view: View):
        self.io = io
        self.view = view
        self.__connect_buttons_to_actions()
        self.view.show()

    def __connect_buttons_to_actions(self):
        for button in self.view.buttons:
            action_method = getattr(self, f'action_{button.key}', None)
            if action_method is not None:
                button.qbutton.clicked.connect(action_method)

    def action_load_parameters(self):
        ActionLoadParameters(self).exec()

    def action_save_parameters(self):
        ActionSaveParameters(self).exec()

    def action_submit_jobs(self):
        ActionSubmitJobs(self).exec()


class Action:

    io: IO
    view: View

    def __init__(self, controller: Controller):
        self.io = controller.io
        self.view = controller.view


class ActionLoadParameters(Action):

    def exec(self):
        file = self.view.file_dialog_open()
        if file == '':
            return

        try:
            parameters = self.io.read(file=file)
            self.view.set_parameters(parameters=parameters)
        except Exception as e:
            self.view.message_box_error(msg=str(e))


class ActionSaveParameters(Action):

    def exec(self):
        file = self.view.file_dialog_save()
        if file == '':
            return

        try:
            parameters = self.view.get_parameters()
            self.io.write(file=file, parameters=parameters)
        except Exception as e:
            self.view.message_box_error(msg=str(e))


class ActionSubmitJobs(Action):

    run_table: str
    ssh_password: str

    connection: Connection
    env_cmd: str
    submission_commands: List[str]

    def exec(self):

        self.run_table = self.view.file_dialog_open()
        if self.run_table == '':
            return

        self.ssh_password = self.view.password_dialog()
        if self.ssh_password == '':
            return

        if not self.view.message_box_yes_no(msg='Are you sure you want to submit?'):
            return

        self.set_connection()
        self.build_submission_commands()

        success = True
        for command in self.submission_commands:
            try:
                self.submit_one(command)
            except Exception as e:
                self.view.message_box_error(msg=str(e))
                success = False
                break

        if success:
            self.view.message_box_info(msg=f'All {len(self.submission_commands)} job(s) submitted!')

        self.connection.close()

    def set_connection(self):
        p = self.view.get_parameters()
        self.connection = Connection(
            host=p['Compute Public IP'],
            user=p['Compute User'],
            port=p['Compute Port'],
            connect_kwargs={'password': self.ssh_password}
        )

    def build_submission_commands(self):
        self.submission_commands = BuildSubmissionCommands().main(
            run_table=self.run_table,
            parameters=self.view.get_parameters()
        )

    def submit_one(self, command: str):
        with self.connection.cd(COMPUTE_ROOT_DIR):
            with self.connection.prefix(f'source {COMPUTE_BASH_PROFILE}'):
                self.connection.run(command, echo=True)  # echo=True for printing out the command
