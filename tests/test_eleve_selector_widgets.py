import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from views.eleve_selector_widgets import EleveSearchPanel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _row(id_eleve, matricule, nom):
    return {
        "id_eleve": id_eleve,
        "matricule_national": "",
        "matricule": matricule,
        "nom": nom,
        "prenoms": "Test",
        "sexe": 1,
        "famille_label": "Parent",
        "inscrit": False,
        "classe_libelle": "",
    }


def test_rechargement_invalide_selection_si_eleve_disparait(qapp):
    panel = EleveSearchPanel()
    selected = []
    deselected = []
    panel.eleveSelected.connect(selected.append)
    panel.eleveDeselected.connect(lambda: deselected.append(True))

    panel._afficher([_row(1, "26-001", "ANCIEN")])
    panel.table.selectRow(0)
    assert panel.selected_id_eleve() == 1

    panel._afficher([_row(2, "26-002", "NOUVEAU")])

    assert panel.selected_id_eleve() is None
    assert deselected
    assert panel.btn_modifier.isEnabled() is False


def test_rechargement_conserve_selection_du_meme_eleve(qapp):
    panel = EleveSearchPanel()
    selected = []
    panel.eleveSelected.connect(selected.append)

    panel._afficher([_row(3, "26-003", "MEME")])
    panel.table.selectRow(0)
    selected.clear()

    panel._afficher([_row(3, "26-003", "MEME MODIFIE")])

    assert panel.selected_id_eleve() == 3
    assert selected == [3]
    assert panel.btn_modifier.isEnabled() is True
