
from datetime import datetime
from PySide6.QtCore import Qt, QTimer ,QPointF ,QThread, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QTextEdit, QProgressBar, QMessageBox,
    QComboBox
)
from database.repository import SupabaseRepository
from investigation.engine import InvestigationEngine

import networkx as nx

from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from graph.builder import BitcoinGraphBuilder


class NetworkGraph(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.Antialiasing)

        self.setStyleSheet("""
            QGraphicsView {
                background: #07111f;
                border: 1px solid #20344d;
                border-radius: 8px;
            }
        """)

        self.setMinimumHeight(420)

        self.graph = None

        self.show_empty_state()

    def show_empty_state(self):

        self.scene.clear()

        text = self.scene.addText(
            "WAITING FOR LIVE INVESTIGATION GRAPH"
        )

        text.setDefaultTextColor(
            QColor("#6f8299")
        )

        text.setPos(
            120,
            180
        )

    def set_graph(self, graph, root_tx=None):

        self.graph = graph
        self.root_tx = root_tx  

        self.scene.clear()

        if graph is None:
            self.show_empty_state()
            return

        if graph.number_of_nodes() == 0:
            self.show_empty_state()
            return

        self.render_graph()

    def render_graph(self):

        graph = self.graph

        if graph is None or graph.number_of_nodes() == 0:
            self.show_empty_state()
            return

        # ---------------------------------------------------------
        # 1. Find the root transaction
        # ---------------------------------------------------------

        root = None

        if self.root_tx:

            for node, data in graph.nodes(data=True):

                tx_hash = data.get("tx_hash")

                if tx_hash == self.root_tx:
                    root = node
                    break

                if str(node) == str(self.root_tx):
                    root = node
                    break

        # Fallback: first transaction node
        if root is None:

            for node, data in graph.nodes(data=True):

                if data.get("node_type") == "transaction":
                    root = node
                    break

        # ---------------------------------------------------------
        # 2. Calculate directed distance from root
        # ---------------------------------------------------------

        if root is not None:

            try:

                distances = nx.single_source_shortest_path_length(
                    graph.to_undirected(),
                    root
                )

            except Exception:

                distances = {
                    node: 0
                    for node in graph.nodes()
                }

        else:

            distances = {
                node: 0
                for node in graph.nodes()
            }

        # ---------------------------------------------------------
        # 3. Group nodes into horizontal layers
        # ---------------------------------------------------------

        layers = {}

        for node in graph.nodes():

            depth = distances.get(node, 0)

            layers.setdefault(
                depth,
                []
            ).append(node)

        # ---------------------------------------------------------
        # 4. Scene dimensions
        # ---------------------------------------------------------

        layer_width = 230
        row_height = 90

        max_layer_size = max(
            len(nodes)
            for nodes in layers.values()
        )

        scene_width = (
            max(layers.keys()) + 1
        ) * layer_width + 150

        scene_height = (
            max_layer_size * row_height
        ) + 120

        self.scene.setSceneRect(
            0,
            0,
            scene_width,
            scene_height
        )

        # ---------------------------------------------------------
        # 5. Calculate clean positions
        # ---------------------------------------------------------

        positions = {}

        for depth, nodes in sorted(
            layers.items()
        ):

            count = len(nodes)

            total_height = count * row_height

            start_y = (
                scene_height - total_height
            ) / 2

            x = (
                100
                + depth * layer_width
            )

            for index, node in enumerate(nodes):

                y = (
                    start_y
                    + index * row_height
                    + row_height / 2
                )

                positions[node] = QPointF(
                    x,
                    y
                )

        # ---------------------------------------------------------
        # 6. Draw directed edges
        # ---------------------------------------------------------

        for source, target, data in graph.edges(
            data=True
        ):

            if source not in positions:
                continue

            if target not in positions:
                continue

            p1 = positions[source]
            p2 = positions[target]

            # Direction line
            pen = QPen(
                QColor("#45647f")
            )

            pen.setWidth(2)

            self.scene.addLine(
                p1.x(),
                p1.y(),
                p2.x(),
                p2.y(),
                pen
            )

            # -----------------------------------------------------
            # Arrow head
            # -----------------------------------------------------

            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()

            length = (
                dx * dx + dy * dy
            ) ** 0.5

            if length > 0:

                ux = dx / length
                uy = dy / length

                arrow_size = 9

                # Stop arrow slightly before node
                end_x = (
                    p2.x()
                    - ux * 20
                )

                end_y = (
                    p2.y()
                    - uy * 20
                )

                left_x = (
                    end_x
                    - ux * arrow_size
                    + uy * arrow_size * 0.6
                )

                left_y = (
                    end_y
                    - uy * arrow_size
                    - ux * arrow_size * 0.6
                )

                right_x = (
                    end_x
                    - ux * arrow_size
                    - uy * arrow_size * 0.6
                )

                right_y = (
                    end_y
                    - uy * arrow_size
                    + ux * arrow_size * 0.6
                )

                polygon = QPolygonF([
                    QPointF(end_x, end_y),
                    QPointF(left_x, left_y),
                    QPointF(right_x, right_y)
                ])

                arrow = self.scene.addPolygon(
                    polygon,
                    QPen(QColor("#6d91ad")),
                    QBrush(QColor("#6d91ad"))
                )

        # ---------------------------------------------------------
        # 7. Draw nodes
        # ---------------------------------------------------------

        for node, data in graph.nodes(
            data=True
        ):

            position = positions[node]

            node_type = data.get(
                "node_type",
                "unknown"
            )

            # -----------------------------------------------------
            # Transaction node
            # -----------------------------------------------------

            if node_type == "transaction":

                radius = 25

                brush = QBrush(
                    QColor("#1479ff")
                )

                border = QPen(
                    QColor("#8cc8ff")
                )

                tx_hash = str(
                    data.get(
                        "tx_hash",
                        node
                    )
                )

                short_hash = (
                    tx_hash[:8]
                    + "..."
                    + tx_hash[-6:]
                )

                label = (
                    "TRANSACTION\n"
                    + short_hash
                )

            # -----------------------------------------------------
            # Address node
            # -----------------------------------------------------

            else:

                radius = 19

                brush = QBrush(
                    QColor("#18b878")
                )

                border = QPen(
                    QColor("#8df0c5")
                )

                address = str(
                    data.get(
                        "address",
                        node
                    )
                )

                if len(address) > 18:

                    short_address = (
                        address[:10]
                        + "..."
                        + address[-6:]
                    )

                else:

                    short_address = address

                label = (
                    "WALLET\n"
                    + short_address
                )

            # -----------------------------------------------------
            # Node circle
            # -----------------------------------------------------

            ellipse = self.scene.addEllipse(
                position.x() - radius,
                position.y() - radius,
                radius * 2,
                radius * 2,
                border,
                brush
            )

            # -----------------------------------------------------
            # Root transaction highlight
            # -----------------------------------------------------

            if node == root:

                root_pen = QPen(
                    QColor("#ffffff")
                )

                root_pen.setWidth(3)

                ellipse.setPen(
                    root_pen
                )

            # -----------------------------------------------------
            # Label
            # -----------------------------------------------------

            text = self.scene.addText(
                label
            )

            text.setDefaultTextColor(
                QColor("#dcecff")
            )

            text.setFont(
                QFont(
                    "Consolas",
                    8
                )
            )

            text.setPos(
                position.x() - 55,
                position.y() + radius + 5
            )

            # -----------------------------------------------------
            # Tooltip with full data
            # -----------------------------------------------------

            if node_type == "transaction":

                tooltip = str(
                    data.get(
                        "tx_hash",
                        node
                    )
                )

            else:

                tooltip = str(
                    data.get(
                        "address",
                        node
                    )
                )

            ellipse.setToolTip(
                tooltip
            )

            text.setToolTip(
                tooltip
            )

        # ---------------------------------------------------------
        # 8. Center graph in viewport
        # ---------------------------------------------------------

        self.fitInView(
            self.scene.sceneRect(),
            Qt.KeepAspectRatio
        )

class MetricCard(QFrame):
    def __init__(self, title, value="0", accent="#36c5f0"):
        super().__init__()
        self.setObjectName("MetricCard")
        self.accent = accent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.title = QLabel(title.upper())
        self.title.setObjectName("MetricTitle")
        self.value = QLabel(str(value))
        self.value.setObjectName("MetricValue")
        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))

class InvestigationWorker(QThread):

    finished = Signal(object)
    progress = Signal(object)
    error = Signal(str)

    def __init__(self, engine, network, tx_hash):
        super().__init__()

        self.engine = engine
        self.network = network
        self.tx_hash = tx_hash

    def run(self):
        try:
            result = self.engine.investigate(
                network=self.network,
                tx_hash=self.tx_hash,
                save_evidence=True,
                on_update=self.progress.emit,
            )

            self.finished.emit(result)

        except Exception as exc:
            self.error.emit(str(exc))

class ForensicsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo = SupabaseRepository()
        self.investigation_engine = InvestigationEngine(max_transactions=20, max_depth=2)
        self.current_investigation = None
        self.investigation_worker = None
        self.active_tx = None
        self.setWindowTitle("VDA // BLOCKCHAIN FORENSICS HUD")
        self.resize(1500, 920)
        self.setMinimumSize(1180, 760)

        self.setup_style()
        self.build_ui()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)
        self.refresh_data()

    def setup_style(self):
        self.setStyleSheet("""
        QWidget {
            background: #05080d;
            color: #d7e3ef;
            font-family: Consolas, "Courier New";
        }
        QMainWindow { background: #05080d; }
        QFrame#TopBar, QFrame#Panel, QFrame#MetricCard {
            background: #09111a;
            border: 1px solid #1b3042;
            border-radius: 5px;
        }
        QFrame#MetricCard {
            border-left: 3px solid #36c5f0;
        }
        QLabel#Brand {
            color: #36c5f0;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 2px;
        }
        QLabel#Status {
            color: #54e38e;
            font-size: 11px;
            font-weight: 700;
        }
        QLabel#PanelTitle {
            color: #8faec7;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#MetricTitle {
            color: #637e94;
            font-size: 9px;
            font-weight: 700;
        }
        QLabel#MetricValue {
            color: #eaf6ff;
            font-size: 23px;
            font-weight: 700;
        }
        QPushButton {
            background: #0d1a26;
            color: #8fdcff;
            border: 1px solid #1e4862;
            border-radius: 3px;
            padding: 8px 12px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: #11283a;
            border-color: #36c5f0;
        }
        QPushButton#Investigate {
            color: #071017;
            background: #36c5f0;
            border: none;
        }
        QComboBox, QTextEdit {
            background: #070d14;
            border: 1px solid #1b3042;
            color: #cfe3f2;
            padding: 5px;
        }
        QTableWidget {
            background: #070d14;
            border: 1px solid #1b3042;
            gridline-color: #10202d;
            selection-background-color: #12364a;
        }
        QHeaderView::section {
            background: #0b1722;
            color: #63839b;
            border: none;
            padding: 7px;
            font-size: 9px;
            font-weight: 700;
        }
        QProgressBar {
            background: #070d14;
            border: 1px solid #1b3042;
            height: 8px;
        }
        QProgressBar::chunk { background: #ff4d67; }
        QSplitter::handle { background: #0c1721; }
        """)

    def panel(self, title):
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        label = QLabel(title.upper())
        label.setObjectName("PanelTitle")
        layout.addWidget(label)
        return frame, layout

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Header
        header = QFrame()
        header.setObjectName("TopBar")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(15, 9, 15, 9)

        brand = QLabel("VDA // FORENSICS COMMAND HUD")
        brand.setObjectName("Brand")
        hl.addWidget(brand)
        hl.addStretch()

        self.network = QComboBox()
        self.network.addItems(["ALL NETWORKS", "BITCOIN", "ETHEREUM"])
        hl.addWidget(self.network)

        self.clock = QLabel("--:--:--")
        self.clock.setStyleSheet("color:#8faec7;font-size:12px;")
        hl.addWidget(self.clock)

        self.status = QLabel("● SUPABASE LINK")
        self.status.setObjectName("Status")
        hl.addWidget(self.status)

        root.addWidget(header)

        # Metrics
        metrics = QGridLayout()
        metrics.setSpacing(8)
        self.m_cases = MetricCard("Active Cases")
        self.m_risk = MetricCard("High Risk Cases", accent="#ff4d67")
        self.m_flagged = MetricCard("Flagged Wallets")
        self.m_vasps = MetricCard("VASP Candidates")
        self.m_value = MetricCard("Value Tracked")
        for i, card in enumerate([self.m_cases, self.m_risk, self.m_flagged, self.m_vasps, self.m_value]):
            metrics.addWidget(card, 0, i)
        root.addLayout(metrics)

        # Main split
        split = QSplitter(Qt.Horizontal)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,0,0)

        graph_panel, gl = self.panel("TRANSACTION TOPOLOGY // LIVE")
        self.graph = NetworkGraph()
        gl.addWidget(self.graph)

        controls = QHBoxLayout()
        self.investigate = QPushButton("START BLOCKCHAIN INVESTIGATION")
        self.investigate.setObjectName("Investigate")
        self.investigate.clicked.connect(self.start_investigation)
        controls.addWidget(self.investigate)

        self.verify = QPushButton("VERIFY SELECTED WALLET")
        self.verify.clicked.connect(self.verify_selected)
        controls.addWidget(self.verify)
        controls.addStretch()
        gl.addLayout(controls)
        ll.addWidget(graph_panel, 1)

        event_panel, el = self.panel("LIVE TRANSACTION / CASE STREAM")
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["TIME", "NETWORK", "TX HASH", "SOURCE", "DESTINATION", "RISK", "FIAT"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        el.addWidget(self.table)
        ll.addWidget(event_panel, 1)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0,0,0,0)

        alert_panel, al = self.panel("THREAT ALERTS")
        self.alerts = QTextEdit()
        self.alerts.setReadOnly(True)
        al.addWidget(self.alerts)
        rl.addWidget(alert_panel, 1)

        intel_panel, il = self.panel("SELECTED CASE INTELLIGENCE")
        self.intel = QTextEdit()
        self.intel.setReadOnly(True)
        il.addWidget(self.intel)
        rl.addWidget(intel_panel, 1)

        risk_panel, rkl = self.panel("RISK SIGNAL")
        self.risk_bar = QProgressBar()
        self.risk_bar.setRange(0,100)
        self.risk_bar.setValue(0)
        rkl.addWidget(self.risk_bar)
        self.risk_label = QLabel("NO CASE SELECTED")
        self.risk_label.setStyleSheet("color:#637e94;font-size:10px;")
        rkl.addWidget(self.risk_label)
        rl.addWidget(risk_panel)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([1050, 360])
        root.addWidget(split, 1)

        # footer
        footer = QHBoxLayout()
        self.last_sync = QLabel("LAST SYNC: --")
        self.last_sync.setStyleSheet("color:#496477;font-size:9px;")
        footer.addWidget(self.last_sync)
        footer.addStretch()
        footer.addWidget(QLabel("GRAPH ENGINE: READY   |   ML ENGINE: STANDBY   |   CRAWLER: STANDBY"))
        root.addLayout(footer)

        self.table.itemSelectionChanged.connect(self.show_selected_case)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

    def update_clock(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def refresh_data(self):
        try:
            cases = self.repo.get_transaction_logs(100)
            flagged = self.repo.get_flagged_wallets(100)
            metrics = self.repo.get_portal_metrics()

            high_risk = sum(
                1 for c in cases
                if str(c.get("high_risk_flag", "")).lower() in ("true", "1", "yes")
            )

            self.m_cases.set_value(len(cases))
            self.m_risk.set_value(high_risk)
            self.m_flagged.set_value(len(flagged))
            self.m_vasps.set_value(metrics.get("vasps_count", 0) if metrics else 0)
            self.m_value.set_value(
                f"₹{metrics.get('total_value_tracked', 0):,.0f}" if metrics else "₹0"
            )

            self.populate_table(cases)
            self.build_alerts(cases)
            self.status.setText("● SUPABASE LINK // ONLINE")
            self.status.setStyleSheet("color:#54e38e;font-size:11px;font-weight:700;")
            self.last_sync.setText(
                "LAST SYNC: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        except Exception as exc:
            self.status.setText("● SUPABASE LINK // ERROR")
            self.status.setStyleSheet("color:#ff4d67;font-size:11px;font-weight:700;")
            self.last_sync.setText(f"SYNC ERROR: {exc}")

    def populate_table(self, cases):
        self.table.setRowCount(0)
        for case in cases:
            row = self.table.rowCount()
            self.table.insertRow(row)

            timestamp = str(case.get("timestamp") or case.get("created_at") or "")
            network = str(case.get("blockchain_network") or "-")
            tx = str(case.get("tx_hash") or "-")
            source = str(case.get("sender_wallet") or "-")
            dest = str(case.get("destination_wallet") or "-")
            risk = "HIGH" if str(case.get("high_risk_flag")).lower() in ("true","1","yes") else "NORMAL"
            fiat = str(case.get("fiat_value") or "0")

            values = [
                timestamp[:19], network, tx[:18], source[:16],
                dest[:16], risk, fiat
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.table.setItem(row, col, item)

            # Preserve complete values for actions; display values remain shortened.
            self.table.item(row, 2).setData(Qt.UserRole, tx)
            self.table.item(row, 3).setData(Qt.UserRole, source)
            self.table.item(row, 4).setData(Qt.UserRole, dest)

    def build_alerts(self, cases):
        alerts = []
        for case in cases:
            if str(case.get("high_risk_flag")).lower() in ("true", "1", "yes"):
                tx = str(case.get("tx_hash") or "UNKNOWN")
                alerts.append(f"[HIGH] suspicious transaction // {tx[:24]}")
        if not alerts:
            alerts.append("[INFO] no high-risk cases detected in current queue")
        self.alerts.setPlainText("\n".join(alerts[:30]))

    def show_selected_case(self):
        row = self.table.currentRow()
        if row < 0:
            return

        tx = self.table.item(row, 2).text()
        source = self.table.item(row, 3).text()
        dest = self.table.item(row, 4).text()
        risk = self.table.item(row, 5).text()
        network = self.table.item(row, 1).text()

        self.intel.setPlainText(
            f"NETWORK        : {network}\n"
            f"TRANSACTION    : {tx}\n"
            f"SOURCE         : {source}\n"
            f"DESTINATION    : {dest}\n"
            f"RISK CLASS     : {risk}\n\n"
            f"NEXT ACTIONS\n"
            f"  > crawl transaction history\n"
            f"  > construct address graph\n"
            f"  > calculate path risk\n"
            f"  > generate GraphSAGE embedding\n"
            f"  > correlate entity / VASP intelligence"
        )

        value = 90 if risk == "HIGH" else 25
        self.risk_bar.setValue(value)
        self.risk_label.setText(f"CURRENT RISK SIGNAL: {value}/100 // {risk}")

    def verify_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Wallet Verification", "Select a case first.")
            return
        dest = self.table.item(row, 4).text()
        result = self.repo.verify_wallet(dest)
        if result:
            QMessageBox.warning(
                self,
                "FLAGGED WALLET",
                f"Wallet is present in flagged_wallets.\nRisk: {result.get('risk_level')}"
            )
        else:
            QMessageBox.information(
                self,
                "Wallet Verification",
                "No exact match found in flagged_wallets."
            )
    def start_investigation(self):

        if (
            self.investigation_worker is not None
            and self.investigation_worker.isRunning()
        ):
            return

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Investigation",
                "Select a transaction first."
            )
            return

        tx_item = self.table.item(row, 2)

        network = self.table.item(
            row, 1
        ).text().strip().lower()

        tx = tx_item.data(
            Qt.UserRole
        ) or tx_item.text()

        if not tx or tx == "-":
            QMessageBox.warning(
                self,
                "Investigation",
                "Selected case has no transaction hash."
            )
            return

        self.intel.append(
            f"\n\n[ENGINE] Investigation started: "
            f"{tx[:18]}...\n"
            "[ENGINE] Blockchain crawler -> RUNNING"
        )

        self.investigate.setEnabled(False)

        self.active_tx = tx

        # Create worker
        self.investigation_worker = InvestigationWorker(
            self.investigation_engine,
            network,
            tx
        )

        # Live crawler updates
        self.investigation_worker.progress.connect(
            self.on_investigation_progress
        )

        # Investigation completed
        self.investigation_worker.finished.connect(
            self.on_investigation_finished
        )

        # Investigation failed
        self.investigation_worker.error.connect(
            self.on_investigation_error
        )

        # Start background investigation
        self.investigation_worker.start()

    def on_investigation_progress(self, crawl_result):
        """
        Called whenever the crawler discovers another transaction.
        """

        try:
            builder = BitcoinGraphBuilder()

            graph = builder.build(
                crawl_result
            )

            # Update HUD graph immediately
            self.graph.set_graph(
                graph,
                self.active_tx
            )

            nodes = graph.number_of_nodes()
            edges = graph.number_of_edges()

            self.risk_label.setText(
                f"LIVE GRAPH: {nodes} NODES / {edges} EDGES"
            )

            self.intel.append(
                f"\n[CRAWLER] "
                f"Live graph updated: "
                f"{nodes} nodes / {edges} edges"
            )

        except Exception as exc:
            self.intel.append(
                f"\n[HUD] Graph update error: {exc}"
            )

    def on_investigation_finished(self, result):

        self.current_investigation = result

        summary = result["summary"]

        evidence = result.get(
            "evidence",
            {}
        )

        # Final graph
        self.graph.set_graph(
            result["graph"],
            result["tx_hash"]
        )

        self.intel.append(
            "\n[ENGINE] Blockchain crawler -> COMPLETE"
            f"\n[ENGINE] Transactions: "
            f"{summary['transactions']}"
            f"\n[ENGINE] Addresses: "
            f"{summary['addresses']}"
            f"\n[ENGINE] Graph: "
            f"{summary['nodes']} nodes / "
            f"{summary['edges']} edges"
            f"\n[ENGINE] Evidence saved -> "
            f"{evidence.get('graph_graphml', 'N/A')}"
            "\n[ENGINE] GraphSAGE -> STANDBY"
            "\n[ENGINE] Entity intelligence -> STANDBY"
        )

        self.risk_label.setText(
            f"INVESTIGATION GRAPH: "
            f"{summary['nodes']} NODES / "
            f"{summary['edges']} EDGES"
        )

        self.investigate.setEnabled(True)

        self.investigation_worker.deleteLater()

    def on_investigation_error(self, message):

        self.intel.append(
            f"\n[ENGINE] INVESTIGATION ERROR: {message}"
        )

        QMessageBox.critical(
            self,
            "Investigation Error",
            message
        )

        self.investigate.setEnabled(True)

        if hasattr(self, "investigation_worker"):
            worker = self.investigation_worker
            self.investigation_worker = None
            worker.deleteLater()