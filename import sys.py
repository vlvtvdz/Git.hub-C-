import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QFont
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest

# Настройки API
api_id = 20200598
api_hash = '8965307d852ec92d2fc0f01a0ab38759'

# Инициализация клиента
client = TelegramClient('session_name', api_id, api_hash)

def convert_links_to_mentions(input_file, output_file):
    try:
        df = pd.read_csv(input_file)

        if 'links' not in df.columns:
            raise ValueError("Входной файл должен содержать колонку 'links'")

        df['mentions'] = df['links'].str.extract(r't\.me/([\w_]+)', expand=False)
        df['mentions'] = df['mentions'].apply(lambda x: f"@{x}" if pd.notna(x) else None)

        df['Title'] = ''
        df['Username'] = ''
        df['Members'] = ''
        df['About'] = ''
        df['DC_ID'] = ''
        df['Broadcast'] = ''
        df['Megagroup'] = ''
        df['Verified'] = ''

        df.to_csv(output_file, index=False)
    except Exception as e:
        raise ValueError(f"Ошибка при обработке файла: {e}")

def process_mentions(input_file, output_file):
    try:
        df = pd.read_csv(input_file)

        if 'mentions' not in df.columns:
            raise ValueError("Входной файл должен содержать колонку 'mentions'")

        batch_size = 60
        with client:
            for start in range(0, len(df), batch_size):
                end = start + batch_size
                batch = df.iloc[start:end]

                for index, row in batch.iterrows():
                    if pd.isna(row['mentions']):
                        continue

                    channel_username = row['mentions'].replace('@', '').strip()

                    try:
                        full_channel = client(GetFullChannelRequest(channel_username))
                        channel = full_channel.chats[0]
                        full_chat = full_channel.full_chat

                        df.at[index, 'Title'] = channel.title
                        df.at[index, 'Username'] = channel.username
                        df.at[index, 'Members'] = full_chat.participants_count
                        df.at[index, 'About'] = full_chat.about
                        df.at[index, 'DC_ID'] = channel.photo.dc_id if channel.photo else None
                        df.at[index, 'Broadcast'] = channel.broadcast
                        df.at[index, 'Megagroup'] = channel.megagroup
                        df.at[index, 'Verified'] = channel.verified
                    except Exception as e:
                        print(f"Ошибка для канала {channel_username}: {e}")

                df.to_csv(output_file, index=False)
    except Exception as e:
        raise ValueError(f"Ошибка при обработке файла: {e}")

class TelegramProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Telegram Processor')
        self.setGeometry(300, 300, 600, 400)

        font = QFont('Arial', 12)

        # Input file
        self.inputLabel = QLabel('Входной файл (links):', self)
        self.inputLabel.setFont(font)
        self.inputLabel.move(20, 20)

        self.inputLineEdit = QLineEdit(self)
        self.inputLineEdit.setFont(font)
        self.inputLineEdit.setGeometry(20, 50, 400, 30)

        self.inputButton = QPushButton('Выбрать...', self)
        self.inputButton.setFont(font)
        self.inputButton.setGeometry(440, 50, 120, 30)
        self.inputButton.clicked.connect(self.selectInputFile)

        # Output file
        self.outputLabel = QLabel('Выходной файл:', self)
        self.outputLabel.setFont(font)
        self.outputLabel.move(20, 100)

        self.outputLineEdit = QLineEdit(self)
        self.outputLineEdit.setFont(font)
        self.outputLineEdit.setGeometry(20, 130, 400, 30)

        self.outputButton = QPushButton('Сохранить как...', self)
        self.outputButton.setFont(font)
        self.outputButton.setGeometry(440, 130, 120, 30)
        self.outputButton.clicked.connect(self.selectOutputFile)

        # Convert button
        self.convertButton = QPushButton('1. Преобразовать ссылки в упоминания', self)
        self.convertButton.setFont(font)
        self.convertButton.setGeometry(20, 180, 540, 40)
        self.convertButton.clicked.connect(self.runConversion)

        # Process button
        self.processButton = QPushButton('2. Обработать упоминания', self)
        self.processButton.setFont(font)
        self.processButton.setGeometry(20, 240, 540, 40)
        self.processButton.clicked.connect(self.runProcessing)

        # Log area
        self.logArea = QTextEdit(self)
        self.logArea.setFont(font)
        self.logArea.setGeometry(20, 300, 540, 80)
        self.logArea.setReadOnly(True)

    def selectInputFile(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, 'Выберите CSV файл', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.inputLineEdit.setText(file)

    def selectOutputFile(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, 'Сохранить как', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.outputLineEdit.setText(file)

    def logMessage(self, message):
        self.logArea.append(message)

    def runConversion(self):
        input_file = self.inputLineEdit.text()
        output_file = self.outputLineEdit.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.critical(self, 'Ошибка', 'Укажите существующий входной файл.')
            return

        if not output_file:
            output_file = 'output.csv'
            self.outputLineEdit.setText(output_file)

        try:
            convert_links_to_mentions(input_file, output_file)
            self.logMessage('Успешно преобразовано.')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

    def runProcessing(self):
        input_file = self.inputLineEdit.text()
        output_file = self.outputLineEdit.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.critical(self, 'Ошибка', 'Укажите существующий входной файл.')
            return

        if not output_file:
            output_file = 'output.csv'
            self.outputLineEdit.setText(output_file)

        try:
            process_mentions(input_file, output_file)
            self.logMessage('Успешно обработано.')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = TelegramProcessorApp()
    mainWindow.show()
    sys.exit(app.exec_())
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QFont
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest

# Настройки API
api_id = 20200598
api_hash = '8965307d852ec92d2fc0f01a0ab38759'

# Инициализация клиента
client = TelegramClient('session_name', api_id, api_hash)

def convert_links_to_mentions(input_file, output_file):
    try:
        df = pd.read_csv(input_file)

        if 'links' not in df.columns:
            raise ValueError("Входной файл должен содержать колонку 'links'")

        df['mentions'] = df['links'].str.extract(r't\.me/([\w_]+)', expand=False)
        df['mentions'] = df['mentions'].apply(lambda x: f"@{x}" if pd.notna(x) else None)

        df['Title'] = ''
        df['Username'] = ''
        df['Members'] = ''
        df['About'] = ''
        df['DC_ID'] = ''
        df['Broadcast'] = ''
        df['Megagroup'] = ''
        df['Verified'] = ''

        df.to_csv(output_file, index=False)
    except Exception as e:
        raise ValueError(f"Ошибка при обработке файла: {e}")

def process_mentions(input_file, output_file):
    try:
        df = pd.read_csv(input_file)

        if 'mentions' not in df.columns:
            raise ValueError("Входной файл должен содержать колонку 'mentions'")

        batch_size = 60
        with client:
            for start in range(0, len(df), batch_size):
                end = start + batch_size
                batch = df.iloc[start:end]

                for index, row in batch.iterrows():
                    if pd.isna(row['mentions']):
                        continue

                    channel_username = row['mentions'].replace('@', '').strip()

                    try:
                        full_channel = client(GetFullChannelRequest(channel_username))
                        channel = full_channel.chats[0]
                        full_chat = full_channel.full_chat

                        df.at[index, 'Title'] = channel.title
                        df.at[index, 'Username'] = channel.username
                        df.at[index, 'Members'] = full_chat.participants_count
                        df.at[index, 'About'] = full_chat.about
                        df.at[index, 'DC_ID'] = channel.photo.dc_id if channel.photo else None
                        df.at[index, 'Broadcast'] = channel.broadcast
                        df.at[index, 'Megagroup'] = channel.megagroup
                        df.at[index, 'Verified'] = channel.verified
                    except Exception as e:
                        print(f"Ошибка для канала {channel_username}: {e}")

                df.to_csv(output_file, index=False)
    except Exception as e:
        raise ValueError(f"Ошибка при обработке файла: {e}")

class TelegramProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Telegram Processor')
        self.setGeometry(300, 300, 600, 400)

        font = QFont('Arial', 12)

        # Input file
        self.inputLabel = QLabel('Входной файл (links):', self)
        self.inputLabel.setFont(font)
        self.inputLabel.move(20, 20)

        self.inputLineEdit = QLineEdit(self)
        self.inputLineEdit.setFont(font)
        self.inputLineEdit.setGeometry(20, 50, 400, 30)

        self.inputButton = QPushButton('Выбрать...', self)
        self.inputButton.setFont(font)
        self.inputButton.setGeometry(440, 50, 120, 30)
        self.inputButton.clicked.connect(self.selectInputFile)

        # Output file
        self.outputLabel = QLabel('Выходной файл:', self)
        self.outputLabel.setFont(font)
        self.outputLabel.move(20, 100)

        self.outputLineEdit = QLineEdit(self)
        self.outputLineEdit.setFont(font)
        self.outputLineEdit.setGeometry(20, 130, 400, 30)

        self.outputButton = QPushButton('Сохранить как...', self)
        self.outputButton.setFont(font)
        self.outputButton.setGeometry(440, 130, 120, 30)
        self.outputButton.clicked.connect(self.selectOutputFile)

        # Convert button
        self.convertButton = QPushButton('1. Преобразовать ссылки в упоминания', self)
        self.convertButton.setFont(font)
        self.convertButton.setGeometry(20, 180, 540, 40)
        self.convertButton.clicked.connect(self.runConversion)

        # Process button
        self.processButton = QPushButton('2. Обработать упоминания', self)
        self.processButton.setFont(font)
        self.processButton.setGeometry(20, 240, 540, 40)
        self.processButton.clicked.connect(self.runProcessing)

        # Log area
        self.logArea = QTextEdit(self)
        self.logArea.setFont(font)
        self.logArea.setGeometry(20, 300, 540, 80)
        self.logArea.setReadOnly(True)

    def selectInputFile(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, 'Выберите CSV файл', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.inputLineEdit.setText(file)

    def selectOutputFile(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, 'Сохранить как', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.outputLineEdit.setText(file)

    def logMessage(self, message):
        self.logArea.append(message)

    def runConversion(self):
        input_file = self.inputLineEdit.text()
        output_file = self.outputLineEdit.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.critical(self, 'Ошибка', 'Укажите существующий входной файл.')
            return

        if not output_file:
            output_file = 'output.csv'
            self.outputLineEdit.setText(output_file)

        try:
            convert_links_to_mentions(input_file, output_file)
            self.logMessage('Успешно преобразовано.')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

    def runProcessing(self):
        input_file = self.inputLineEdit.text()
        output_file = self.outputLineEdit.text()

        if not input_file or not os.path.exists(input_file):
            QMessageBox.critical(self, 'Ошибка', 'Укажите существующий входной файл.')
            return

        if not output_file:
            output_file = 'output.csv'
            self.outputLineEdit.setText(output_file)

        try:
            process_mentions(input_file, output_file)
            self.logMessage('Успешно обработано.')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = TelegramProcessorApp()
    mainWindow.show()
    sys.exit(app.exec_())
