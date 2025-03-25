import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget, \
    QPushButton, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox, QFileDialog
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QPointF


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Создание графической сцены и представления
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)

        # Создание компонентов интерфейса
        self.add_vertex_button = QPushButton('Добавить вершину')
        self.add_edge_button = QPushButton('Добавить ребро')
        self.delete_edge_button = QPushButton('Удалить ребро')
        self.find_distances_button = QPushButton('Найти кратчайшие расстояния')
        self.clean_button = QPushButton('Очистить')

        # Создание вершин графа и рёбер
        self.vertices = {}
        self.edges = []
        self.count = 0

        # Подключение событий
        self.add_vertex_button.clicked.connect(self.add_vertex)
        self.add_edge_button.clicked.connect(self.show_add_edge_dialog)
        self.delete_edge_button.clicked.connect(self.delete_edge)
        self.find_distances_button.clicked.connect(self.find_shortest_distances)
        self.clean_button.clicked.connect(self.clean)
        self.scene.mouseDoubleClickEvent = self.reload_vertex

        # Настройка интерфейса
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.add_vertex_button)
        layout.addWidget(self.add_edge_button)
        layout.addWidget(self.delete_edge_button)
        layout.addWidget(self.find_distances_button)
        layout.addWidget(self.clean_button)
        self.setLayout(layout)

    def add_vertex(self):
        # Отображение диалогового окна для ввода названия вершины
        name, ok = QInputDialog.getText(self, 'Добавление вершины', 'Введите название вершины:')
        if ok:
            # Создание элемента вершины
            vertex_item = self.scene.addEllipse(0, 0, 10, 10, QPen(Qt.black), Qt.white)
            vertex_item.setFlag(vertex_item.ItemIsMovable)
            vertex_item.setPos(QPointF(30, 30) * len(self.vertices))

            # Создание текстового элемента для надписи рядом с вершиной
            text_item = self.scene.addText(name)
            text_item.setPos(vertex_item.pos() + QPointF(15, -5))

            # Добавление вершины и соответствующего текста в словарь
            self.vertices[name] = [vertex_item, text_item]

    def clean(self):
        self.scene.clear()
        self.vertices = {}
        self.edges = []

    def reload_vertex(self, event):
        if self.vertices:
            for x in self.vertices.values():
                x[1].setPos(x[0].pos() + QPointF(15, -5))

        if self.edges:
            for i in range(len(self.edges)):
                self.scene.removeItem(self.edges[i][2])

            # Перерисовываем все рёбра и надписи с учётом новых координат
            self.update_edges_and_labels()

    def update_edges_and_labels(self):
        # Обновление рёбер и надписей, если вершины перемещены
        for edge in self.edges:
            start_vertex_pos = self.vertices[edge[0]][0].pos()
            end_vertex_pos = self.vertices[edge[1]][0].pos()
            edge[2].setLine(start_vertex_pos.x() + 5, start_vertex_pos.y() + 5, end_vertex_pos.x() + 5, end_vertex_pos.y() + 5)
            edge[3].setPos((start_vertex_pos + end_vertex_pos) / 2)

    def show_add_edge_dialog(self):
        dialog = AddEdgeDialog(self, self.vertices.keys())
        if dialog.exec_() == QDialog.Accepted:
            start_vertex = dialog.start_vertex
            end_vertex = dialog.end_vertex
            weight = dialog.weight

            # Нахождение позиций вершин
            start_pos = self.vertices[start_vertex][0].pos()
            end_pos = self.vertices[end_vertex][0].pos()

            # Создание элемента ребра
            edge = self.scene.addLine(start_pos.x() + 5, start_pos.y() + 5, end_pos.x() + 5, end_pos.y() + 5,
                                      QPen(Qt.black))

            # Добавление текстового элемента для отображения информации о ребре
            edge_text = f'{weight}'
            text_item = self.scene.addText(edge_text)
            text_item.setPos((start_pos + end_pos) / 2)

            self.edges.append([start_vertex, end_vertex, edge, text_item, weight])

    def delete_edge(self):
        # Открытие диалогового окна для удаления рёбер
        items = [f'{edge[0]} -> {edge[1]}' for edge in self.edges]
        if not items:
            QMessageBox.information(self, 'Ошибка', 'В графе нет рёбер для удаления')
            return

        edge_to_delete, ok = QInputDialog.getItem(self, 'Удаление ребра', 'Выберите ребро для удаления:', items, editable=False)
        if ok:
            # Находим соответствующее ребро по названию
            edge_index = items.index(edge_to_delete)
            edge = self.edges[edge_index]
            self.scene.removeItem(edge[2])  # Удаляем линию ребра
            self.scene.removeItem(edge[3])  # Удаляем текстовое описание рёбра
            self.edges.pop(edge_index)  # Удаляем ребро из списка

    def find_shortest_distances(self):
        N = len(self.vertices)
        adjacency_matrix = [[float("inf") for x in range(N)] for y in range(N)]

        # Заполнение матрицы смежности значениями
        for i in range(N):
            for j in range(N):
                if i == j:
                    adjacency_matrix[i][j] = 0

        arr = {key: value for value, key in enumerate(self.vertices.keys())}
        for edges in self.edges:
            i, j = arr[edges[0]], arr[edges[1]]
            adjacency_matrix[i][j] = edges[4]
            adjacency_matrix[j][i] = edges[4]

        # Выполнение алгоритма Флойда-Уоршелла
        for k in range(N):
            for i in range(N):
                for j in range(N):
                    adjacency_matrix[i][j] = min(adjacency_matrix[i][j],
                                                 adjacency_matrix[i][k] + adjacency_matrix[k][j])

        # Открываем диалог с таблицей расстояний
        distance_table = DistanceTableWidget(self.vertices.keys(), adjacency_matrix)
        distance_table.exec_()


class AddEdgeDialog(QDialog):
    def __init__(self, parent, vertices):
        super().__init__(parent)

        self.setWindowTitle('Добавление ребра')

        # Создание элементов формы
        self.start_vertex_combo = QComboBox(self)
        self.start_vertex_combo.addItems(vertices)

        self.end_vertex_combo = QComboBox(self)
        self.end_vertex_combo.addItems(vertices)

        self.weight_input = QLineEdit(self)

        # Настройка формы
        layout = QFormLayout(self)
        layout.addRow('Откуда:', self.start_vertex_combo)
        layout.addRow('Куда:', self.end_vertex_combo)
        layout.addRow('Вес:', self.weight_input)

        # Кнопки
        self.button_box = QPushButton('Добавить ребро', self)
        self.button_box.clicked.connect(self.accept)
        layout.addRow(self.button_box)

    def accept(self):
        start_vertex = self.start_vertex_combo.currentText()
        end_vertex = self.end_vertex_combo.currentText()
        weight = self.weight_input.text()

        # Проверка корректности ввода
        if not weight.isdigit():
            QMessageBox.warning(self, 'Ошибка', 'Вес должен быть числом!')
            return

        self.start_vertex = start_vertex
        self.end_vertex = end_vertex
        self.weight = int(weight)
        super().accept()


class DistanceTableWidget(QDialog):
    def __init__(self, keys, adjacency_matrix):
        super().__init__()

        self.setWindowTitle('Кратчайшие расстояния')

        # Создание виджета таблицы для вывода расстояний
        self.table_widget = QTableWidget(self)

        # Вывод кратчайших расстояний в таблицу
        self.display_distances_in_table(keys, adjacency_matrix)

        # Кнопка для сохранения таблицы в файл
        self.save_button = QPushButton('Сохранить в файл', self)
        self.save_button.clicked.connect(self.save_to_file)

        # Настройка интерфейса
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_widget)
        layout.addWidget(self.save_button)

    def display_distances_in_table(self, keys, adjacency_matrix):
        self.table_widget.setColumnCount(len(keys))
        self.table_widget.setRowCount(len(keys))
        self.table_widget.setHorizontalHeaderLabels(keys)
        self.table_widget.setVerticalHeaderLabels(keys)

        for i, start_vertex in enumerate(keys):
            for j, end_vertex in enumerate(keys):
                if adjacency_matrix[i][j] != None:
                    self.table_widget.setItem(i, j, QTableWidgetItem(str(int(adjacency_matrix[i][j]))))

    def save_to_file(self):
        # Открытие диалогового окна для выбора пути сохранения файла
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить таблицу в файл", "", "Text Files (*.txt);;All Files (*)", options=options)

        if file_name:
            with open(file_name, 'w') as file:
                for i in range(self.table_widget.rowCount()):
                    row = []
                    for j in range(self.table_widget.columnCount()):
                        row.append(self.table_widget.item(i, j).text())
                    file.write("\t".join(row) + "\n")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = GraphWidget()
    window.setCentralWidget(widget)
    window.setGeometry(300, 300, 800, 600)
    window.show()
    sys.exit(app.exec_())
