import styles from "../CreateListingPage.styles";
import { formatSeverity } from "../listingHelpers";

function getDetectionLabel(det) {
  return det.label ?? det.class ?? "Nežinoma klasė";
}

function getDetectionConfidence(det) {
  return det.confidence ?? det.conf ?? 0;
}

function getDetectionSource(det) {
  return det.source ?? det.damage_source ?? "-";
}

export default function ImageAnalysisModal({ imageAnalysis, onClose }) {
  if (!imageAnalysis) return null;

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.analysisModal} onClick={(event) => event.stopPropagation()}>
        <h3 style={styles.modalTitle}>Nuotraukos analizė</h3>

        <img
          src={imageAnalysis.annotatedUrl}
          alt="Analizuota nuotrauka"
          style={styles.annotatedImage}
        />

        <div style={styles.analysisInfo}>
          <div>
            <strong>Pirminio pažeidimo sunkumas:</strong>{" "}
            {formatSeverity(imageAnalysis.primary_severity)}
          </div>
          <div>
            <strong>Antrinio pažeidimo sunkumas:</strong>{" "}
            {formatSeverity(imageAnalysis.secondary_severity)}
          </div>
        </div>

        {imageAnalysis.detections?.length > 0 ? (
          <div style={styles.detectionList}>
            <strong>Aptikti objektai:</strong>

            {imageAnalysis.detections.map((det, index) => (
              <div key={index} style={styles.detectionItem}>
                {getDetectionLabel(det)} — confidence:{" "}
                {Number(getDetectionConfidence(det)).toFixed(2)} — {getDetectionSource(det)}
              </div>
            ))}
          </div>
        ) : (
          <div style={styles.warningBox}>
            Šioje nuotraukoje DI neaptiko pažymimų pažeidimų.
          </div>
        )}

        <button type="button" style={styles.secondaryBtn} onClick={onClose}>
          Uždaryti
        </button>
      </div>
    </div>
  );
}
