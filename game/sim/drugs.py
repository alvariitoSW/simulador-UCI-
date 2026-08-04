"""Metadatos de fármacos usados en los distintos casos (para mostrar en la UI)."""

DRUGS = {
    "norepinefrina": {
        "label": "Noradrenalina",
        "unit": "mcg/kg/min",
        "min": 0.0, "max": 1.0, "step": 0.01,
        "info": "Vasopresor de primera línea en shock séptico. Objetivo: TAM >= 65 mmHg.",
    },
    "fluidos": {
        "label": "Bolo de cristaloides (500 ml)",
        "unit": "ml",
        "info": "Reanimación con líquidos. Cuidado con la sobrecarga (edema pulmonar) en dosis excesivas.",
    },
    "antibiotico": {
        "label": "Antibiótico de amplio espectro",
        "unit": "",
        "info": "Debe administrarse cuanto antes tras reconocer sepsis (idealmente <1h).",
    },
    "propofol": {
        "label": "Propofol",
        "unit": "mcg/kg/min",
        "min": 0.0, "max": 80.0, "step": 2.0,
        "info": "Sedante de acción rápida. Dosis alta -> hipotensión y sedación profunda.",
    },
    "fentanilo": {
        "label": "Fentanilo",
        "unit": "mcg/h",
        "min": 0.0, "max": 200.0, "step": 5.0,
        "info": "Analgésico opioide. Complementa la sedación; en exceso deprime el centro respiratorio.",
    },
    "epinefrina": {
        "label": "Epinefrina 1 mg IV",
        "unit": "mg",
        "info": "En paro cardiaco: 1 mg IV cada 3-5 minutos según protocolo ACLS.",
    },
}
