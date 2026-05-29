import {
  formatSeverity,
  getDetectionConfidence,
  getDetectionLabel,
  getDetectionSource,
} from "../formatters";

export default function ImageGalleryModal({
  imageItems,
  galleryIndex,
  galleryImage,
  imageAnalysis,
  analysisError,
  analyzingImageId,
  onClose,
  onPrev,
  onNext,
  onAnalyze,
}) {
  return (
    <div className="gallery-overlay" onClick={onClose}>
      <div className="gallery-modal" onClick={(e) => e.stopPropagation()}>
        <div className="gallery-header">
          <div>
            <h3 className="gallery-title">Nuotraukų galerija</h3>
            <p className="gallery-counter">
              {galleryIndex + 1} / {imageItems.length}
            </p>
          </div>

          <button type="button" className="close-btn" onClick={onClose}>
            Uždaryti
          </button>
        </div>

        <div className="gallery-content">
          {imageItems.length > 1 && (
            <button type="button" className="nav-btn" onClick={onPrev}>
              ‹
            </button>
          )}

          <img
            src={imageAnalysis?.annotatedUrl || galleryImage.url}
            alt="Galerijos nuotrauka"
            className="gallery-image"
          />

          {imageItems.length > 1 && (
            <button type="button" className="nav-btn" onClick={onNext}>
              ›
            </button>
          )}
        </div>

        <div className="gallery-actions">
          <button
            type="button"
            className="ai-btn"
            onClick={onAnalyze}
            disabled={analyzingImageId === galleryImage.id}
          >
            {analyzingImageId === galleryImage.id
              ? "Analizuojama..."
              : "Vaizdo analizė su DI"}
          </button>
        </div>

        {analysisError && <div className="gallery-error">{analysisError}</div>}

        {imageAnalysis && <ImageAnalysisResult imageAnalysis={imageAnalysis} />}
      </div>
    </div>
  );
}

function ImageAnalysisResult({ imageAnalysis }) {
  return (
    <div className="analysis-box">
      <h3 className="section-title">Nuotraukos analizė</h3>

      <div className="analysis-info">
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
        <div className="detection-list">
          <strong>Aptikti objektai:</strong>

          {imageAnalysis.detections.map((det, index) => (
            <div key={index} className="detection-item">
              {getDetectionLabel(det)} — confidence: {Number(getDetectionConfidence(det)).toFixed(2)} — {getDetectionSource(det)}
            </div>
          ))}
        </div>
      ) : (
        <div className="warning-box">Šioje nuotraukoje DI neaptiko pažeidimų.</div>
      )}
    </div>
  );
}
