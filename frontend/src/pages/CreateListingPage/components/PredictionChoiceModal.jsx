import styles from "../CreateListingPage.styles";

export default function PredictionChoiceModal({ open, onClose, onRunPrediction }) {
  if (!open) return null;

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modal} onClick={(event) => event.stopPropagation()}>
        <h3 style={styles.modalTitle}>Pasirinkite prognozės tipą</h3>
        <p style={styles.modalText}>
          Su nuotraukų analize prognozė bus tikslesnė, nes bus įvertintos
          nuotraukos ir pažeidimų mastas.
        </p>

        <div style={styles.modalActionsColumn}>
          <button type="button" style={styles.primaryBtn} onClick={() => onRunPrediction(true)}>
            Prognozuoti su nuotraukų analize
          </button>

          <button type="button" style={styles.secondaryBtn} onClick={() => onRunPrediction(false)}>
            Greita prognozė be analizės
          </button>

          <button type="button" style={styles.linkBtn} onClick={onClose}>
            Atšaukti
          </button>
        </div>
      </div>
    </div>
  );
}
