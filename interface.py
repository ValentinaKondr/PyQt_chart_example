import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QApplication, QLabel, QPlainTextEdit,
                             QGridLayout, QMessageBox, QGroupBox, QVBoxLayout, QSpinBox,)
from PyQt5.QtChart import QChart, QLineSeries, QScatterSeries, QChartView, QValueAxis
from PyQt5.QtGui import QColor, QTextCursor
from PyQt5.QtCore import *
import random
import numpy as np
import warnings


class DataGenerator:
    def __init__(self, sim_time_ms, quadratic_coef=0.03):
        self.__fin_simulation_time = sim_time_ms / 1000  # ms -> seconds
        self.__quad = quadratic_coef
        self.__time_segments = np.linspace(0, self.__fin_simulation_time, 100)

    def get_values(self, count):
        if count > 100:
            warnings.warn("DataGenerator's counter should be less than 101")    # due to QLineSeries overflow
            count = 100

        quad = self.__quad
        for i in range(count):
            y_value1 = (1800 + (-80 + 160 * random.random()) / 5) * self.__time_segments[i] + random.random()

            quad *= 1.022
            value = (1800 + (-80 + 160 * random.random()) / 5) * self.__time_segments[i]
            y_value2 = value - value * quad
            yield self.__time_segments[i], y_value1, y_value2


class Interface(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Interface, self).__init__()
        self.__dataGenerator = None
        self.__wid = QWidget(self)
        self.setCentralWidget(self.__wid)
        self.__layout = QGridLayout()
        self.__layout.setSpacing(5)
        self.__axisx = QValueAxis()
        self.__axisx.setRange(0.0, 100.0)
        self.__axisy = QValueAxis()
        self.__values = list()
        self.__counter = 0
        self.__data_iterator = None
        self.time_ms = 0
        self.timer = QTimer(self)
        self.timerInterval = 1000
        self.timer.setInterval(self.timerInterval)
        self.timer.timeout.connect(self.run_simulation)
        self.initUI()

    def init_values(self):
        self.__counter = 0
        self.__data_iterator = self.__dataGenerator.get_values(100)
        self.time_ms = 0

    def on_tick(self):
        try:
            values = next(self.__data_iterator)
            self.__values.append(values)
        except StopIteration:
            self.timer.stop()

        self.__writeLog()
        self.__drawParetoChart()
        self.__drawComparisonChart()

    def __setWindowProperties(self, parent):
        self.setWindowTitle("Title")
        self.setGeometry(100, 60, 1000, 600)

    def __createOptimisationChartGroupBox(self):
        groupBox = QGroupBox("Множество Парето")
        layout = QGridLayout()
        layout.setSpacing(0)

        self.__pareto_chart = QChart()
        self.__pareto_chart_series = []
        view = QChartView(self.__pareto_chart)
        layout.addWidget(view)
        groupBox.setLayout(layout)
        return groupBox

    def __createButtonsGroupBox(self):
        groupBox = QGroupBox("Кнопки")
        layout = QGridLayout()
        layout.setSpacing(5)
        self.__btn_start = QPushButton("Запуск", self)
        self.__btn_stop = QPushButton("Остановка", self)
        layout.addWidget(self.__btn_start, 1, 1, 1, 3)
        layout.addWidget(self.__btn_stop, 1, 4, 1, 3)
        groupBox.setLayout(layout)
        return groupBox

    def __createQueryParametersGroupBox(self):
        groupBox = QGroupBox("Параметры запросов")
        layout = QGridLayout()
        layout.setSpacing(5)
        label_query_count = QLabel("Количество запросов: ")
        self.spinbox_query_count = QSpinBox()
        self.spinbox_query_count.setRange(100, 1000)
        self.spinbox_query_count.setSingleStep(100)
        label_update_frequency = QLabel("Частота обновления (мсек): ")
        self.spinbox_update_frequency = QSpinBox()
        self.spinbox_update_frequency.setRange(100, 300)
        self.spinbox_update_frequency.setSingleStep(100)
        layout.addWidget(label_query_count, 1, 1, 1, 1)
        layout.addWidget(self.spinbox_query_count, 1, 2, 1, 3)
        layout.addWidget(label_update_frequency, 2, 1, 1, 1)
        layout.addWidget(self.spinbox_update_frequency, 2, 2, 1, 3)
        groupBox.setLayout(layout)
        return groupBox

    def __createLogGroupBox(self):
        groupBox = QGroupBox("Замеры времени")
        self.__plainTextEdit_time_logs = QPlainTextEdit("")
        vbox = QVBoxLayout()
        vbox.addWidget(self.__plainTextEdit_time_logs)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)
        return groupBox

    def __createComparisonChartGroupBox(self):
        groupBox = QGroupBox("Сравнительный график")
        layout = QGridLayout()
        layout.setSpacing(0)
        self.__comparison_chart = QChart()
        self.__comparison_chart_series = []
        self.__comparison_view = QChartView(self.__comparison_chart)
        layout.addWidget(self.__comparison_view)
        groupBox.setLayout(layout)
        return groupBox

    def __start_btn_clicked(self):
        self.__drawParetoChart()
        self.interval = int(self.spinbox_query_count.value())
        self.timerInterval = int(self.spinbox_update_frequency.value())
        self.__dataGenerator = DataGenerator(self.timerInterval * 10)
        self.init_values()
        self.timer.start(self.timerInterval)

    def run_simulation(self):
        self.time_ms += self.timerInterval
        self.on_tick()

    def __stop_btn_clicked(self):
        self.timer.stop()

    def __drawParetoChart(self):
        def make_noise(value, noise_size):
            return value + (noise_size/-2 + noise_size * random.random())

        self.__pareto_chart.removeAllSeries()

        series1 = QScatterSeries()
        series1.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        series1.setMarkerSize(5)
        series1.append(make_noise(23, 2), make_noise(25, 2))
        series1.setBrush(QColor(Qt.red))
        self.__pareto_chart.addSeries(series1)
        self.__axisy.setRange(0.0, 100.0)

        series3 = QScatterSeries()
        series3.setName("Точка утопии")
        series3.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        series3.setMarkerSize(10)
        series3.append(make_noise(2, 0.5), make_noise(23, 2))
        self.__pareto_chart.addSeries(series3)

        series2 = QScatterSeries()
        series2.setName("Оптимальный")
        series2.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        series2.setMarkerSize(7)
        series2.append(make_noise(2, 0.5), make_noise(45, 4))
        self.__pareto_chart.addSeries(series2)

        self.__pareto_chart.setAxisX(self.__axisx, series1)
        self.__pareto_chart.setAxisY(self.__axisy, series1)
        self.__pareto_chart.setAxisX(self.__axisx, series2)
        self.__pareto_chart.setAxisY(self.__axisy, series2)
        self.__pareto_chart.setAxisX(self.__axisx, series3)
        self.__pareto_chart.setAxisY(self.__axisy, series3)

    def __writeLog(self):
        self.__counter += 1
        self.__plainTextEdit_time_logs.moveCursor(QTextCursor.End)
        time_string = ("[%d:%d]" % (self.time_ms / 1000, self.time_ms % 1000 / 100))
        try:
            optimal = self.__values[-1][2] - self.__values[-2][2]
            other = self.__values[-1][1] - self.__values[-2][1]
        except IndexError:
            optimal = 0
            other = 0
        for i in range(self.__counter):
            self.__plainTextEdit_time_logs.insertPlainText(
                '{0} {1:20} {2:1.4} \n'.format(time_string, 'Оптимальный:', float(optimal)))
            self.__plainTextEdit_time_logs.insertPlainText(
                '{0} {1:20} {2:1.4} \n'.format(time_string, 'Другой:', float(other)))
        self.__plainTextEdit_time_logs.moveCursor(QTextCursor.End)

    def __drawComparisonChart(self):
        self.__comparison_chart.removeAllSeries()
        series1 = QLineSeries(self)
        series2 = QLineSeries(self)
        series1.setName("Оптимальный")
        series2.setName("Другой")
        [(series1.append(i[0], i[1]), series2.append(i[0], i[2])) for i in self.__values]
        self.__comparison_chart.addSeries(series1)
        self.__comparison_chart.addSeries(series2)

        self.__comparison_chart.createDefaultAxes()

    def initUI(self):
        self.__layout.addWidget(self.__createOptimisationChartGroupBox(), 1, 1, 8, 5)
        self.__layout.addWidget(self.__createLogGroupBox(), 9, 1, 2, 5)
        self.__layout.addWidget(self.__createButtonsGroupBox(), 1, 6, 1, 5)
        self.__layout.addWidget(self.__createQueryParametersGroupBox(), 2, 6, 2, 5)
        self.__layout.addWidget(self.__createComparisonChartGroupBox(), 4, 6, 7, 5)
        self.__wid.setLayout(self.__layout)
        self.__btn_start.clicked.connect(self.__start_btn_clicked)
        self.__btn_stop.clicked.connect(self.__stop_btn_clicked)
        self.__setWindowProperties(self)
        self.show()

    def closeEvent(self, event):  # событие закрытия окна
        reply = QMessageBox.question(self, 'Выход',
                                     "Вы уверены, что хотите выйти?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def showWarning(self, message):
        q = QMessageBox()
        q.setIcon(QMessageBox.Warning)
        q.setText(message)
        q.setWindowTitle("Ошибка")
        q.setStandardButtons(QMessageBox.Ok);
        q.exec_()



def main():
    app = QApplication(sys.argv)
    ex = Interface()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

