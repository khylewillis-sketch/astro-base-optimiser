from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QCheckBox, QGroupBox
)
from model.base_state import BaseState


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astro Empires Base Calculator (AE 1.5)")
        self.setMinimumWidth(900)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        # Left: Inputs
        self.input_panel = QVBoxLayout()
        layout.addLayout(self.input_panel, 1)

        # Right: Outputs
        self.output_panel = QVBoxLayout()
        layout.addLayout(self.output_panel, 1)

        self._build_inputs()
        self._build_outputs()

        self.recalculate()

    # --------------------------------------------------
    # INPUT PANEL
    # --------------------------------------------------
    def _build_inputs(self):
        self.input_panel.addWidget(QLabel("<b>Base Inputs</b>"))

        # Astro Type
        self.astro = QComboBox()
        self.astro.addItems([
            "Rocky", "Earthly", "Gaia", "Crystalline", "Metallic",
            "Oceanic", "Arid", "Glacial", "Toxic", "Volcanic"
        ])
        self.input_panel.addWidget(QLabel("Astro Type"))
        self.input_panel.addWidget(self.astro)

        # Moon?
        self.is_moon = QCheckBox("Moon")
        self.input_panel.addWidget(self.is_moon)

        # Position
        self.position = QSpinBox()
        self.position.setRange(1, 5)
        self.position.setValue(2)
        self.input_panel.addWidget(QLabel("Orbital Position"))
        self.input_panel.addWidget(self.position)

        # Tech Levels
        tech_box = QGroupBox("Tech Levels")
        tech_layout = QVBoxLayout(tech_box)

        self.tech_energy = self._spin("Energy", 38, tech_layout)
        self.tech_ai = self._spin("AI", 20, tech_layout)
        self.tech_cyber = self._spin("Cybernetics", 22, tech_layout)

        self.input_panel.addWidget(tech_box)

        # Structures (important ones)
        struct_box = QGroupBox("Structures")
        struct_layout = QVBoxLayout(struct_box)

        self.urb = self._spin("Urban Structures", 27, struct_layout)
        self.ob = self._spin("Orbital Base", 11, struct_layout)
        self.tf = self._spin("Terraform", 21, struct_layout)
        self.mlp = self._spin("MLP", 10, struct_layout)

        self.solar = self._spin("Solar Plants", 5, struct_layout)
        self.fusion = self._spin("Fusion Plants", 21, struct_layout)
        self.am = self._spin("Antimatter Plants", 12, struct_layout)
        self.op = self._spin("Orbital Plants", 4, struct_layout)

        self.mr = self._spin("Metal Refineries", 33, struct_layout)
        self.rf = self._spin("Robotic Factories", 28, struct_layout)
        self.nan = self._spin("Nanite Factories", 23, struct_layout)
        self.andr = self._spin("Android Factories", 21, struct_layout)

        self.input_panel.addWidget(struct_box)
        self.input_panel.addStretch()

    def _spin(self, label, default, layout):
        spin = QSpinBox()
        spin.setRange(0, 1000)
        spin.setValue(default)
        spin.valueChanged.connect(self.recalculate)
        layout.addWidget(QLabel(label))
        layout.addWidget(spin)
        return spin

    # --------------------------------------------------
    # OUTPUT PANEL
    # --------------------------------------------------
    def _build_outputs(self):
        self.output_panel.addWidget(QLabel("<b>Results</b>"))

        self.out_pop = QLabel()
        self.out_area = QLabel()
        self.out_energy = QLabel()
        self.out_prod = QLabel()
        self.out_con = QLabel()
        self.out_econ = QLabel()
        self.out_res = QLabel()

        for lbl in [
            self.out_pop, self.out_area, self.out_energy,
            self.out_prod, self.out_con, self.out_econ, self.out_res
        ]:
            self.output_panel.addWidget(lbl)

        self.output_panel.addStretch()

    # --------------------------------------------------
    # RE-CALCULATE
    # --------------------------------------------------
    def recalculate(self):
        tech = {
            "Energy": self.tech_energy.value(),
            "AI": self.tech_ai.value(),
            "Cybernetics": self.tech_cyber.value(),
        }

        structures = {
            "Urban Structures": self.urb.value(),
            "Orbital Base": self.ob.value(),
            "Terraform": self.tf.value(),
            "Multi-Level Platforms": self.mlp.value(),

            "Solar Plants": self.solar.value(),
            "Fusion Plants": self.fusion.value(),
            "Antimatter Plants": self.am.value(),
            "Orbital Plants": self.op.value(),

            "Metal Refineries": self.mr.value(),
            "Robotic Factories": self.rf.value(),
            "Nanite Factories": self.nan.value(),
            "Android Factories": self.andr.value(),
        }

        base = BaseState(
            astro_type=self.astro.currentText(),
            position=self.position.value(),
            tech_levels=tech,
            structure_levels=structures,
            is_moon=self.is_moon.isChecked()
        )

        results = base.compute_all()

        pop = results["population"]
        area = results["area"]
        energy = results["energy"]

        self.out_pop.setText(
            f"Population: {pop['required']} / {pop['capacity']} "
            f"(Surplus {pop['surplus']})"
        )

        self.out_area.setText(
            f"Area Remaining: {area['remaining']}"
        )

        self.out_energy.setText(
            f"Energy: {energy['consumed']} / {energy['produced']} "
            f"(+{energy['surplus']})"
        )

        self.out_prod.setText(f"Production: {results['production']:.1f}")
        self.out_con.setText(f"Construction: {results['construction']:.1f}")
        self.out_econ.setText(f"Economy: {results['economy']}")
        self.out_res.setText(f"Research: {results['research']:.1f}")