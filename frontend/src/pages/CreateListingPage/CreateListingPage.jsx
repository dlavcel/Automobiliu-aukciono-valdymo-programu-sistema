import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  BACKEND_BASE,
  MIN_IMAGE_WIDTH,
  MIN_IMAGE_HEIGHT,
  MAX_ANALYSIS_IMAGES,
  auctionTypeOptions,
  saleTypeOptions,
  fuelTypeOptions,
  driveTypeOptions,
  transmissionOptions,
  damageOptions,
  initialForm,
} from "./constants";
import {
  createListing,
  uploadListingImage,
  submitListing,
  predictListingPrice,
  analyzeListingImage,
} from "./api";
import {
  buildPayload,
  readImageDimensions,
  getPriceInsight,
  formatSeverity,
  getMaxKnownSeverity,
} from "./listingHelpers";
import ImageAnalysisModal from "./components/ImageAnalysisModal";
import PredictionChoiceModal from "./components/PredictionChoiceModal";
import styles from "./CreateListingPage.styles";

export default function CreateListingPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [createdListing, setCreatedListing] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [analyzingImageId, setAnalyzingImageId] = useState(null);
  const [batchAnalyzing, setBatchAnalyzing] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [wantedPrice, setWantedPrice] = useState("");
  const [showPredictChoice, setShowPredictChoice] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionModeLabel, setPredictionModeLabel] = useState("");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const [imageAnalysis, setImageAnalysis] = useState(null);
  const [batchAnalysisResults, setBatchAnalysisResults] = useState([]);
  const [batchSeveritySummary, setBatchSeveritySummary] = useState(null);

  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from(
      { length: currentYear - 1899 },
      (_, index) => currentYear - index
    );
  }, []);

  const predictedPrice =
    predictionResult?.predicted_price ?? createdListing?.predicted_price ?? null;

  const priceInsight = useMemo(() => {
    return getPriceInsight(predictedPrice, wantedPrice);
  }, [predictedPrice, wantedPrice]);

  const markDirty = () => {
    setHasUnsavedChanges(true);
    setPredictionResult(null);
    setUploadedImages([]);
    setImageAnalysis(null);
    setBatchAnalysisResults([]);
    setBatchSeveritySummary(null);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    markDirty();

    setForm((prev) => ({
      ...prev,
      [name]: value,
      ...(name === "sale_type" && value !== "reserve_price"
        ? { reserve_price: "" }
        : {}),
    }));
  };

  const handleRemoveSelectedImage = (indexToRemove) => {
  const urlToRemove = previewUrls[indexToRemove];
  if (urlToRemove) {
    URL.revokeObjectURL(urlToRemove);
  }

  setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  setPreviewUrls((prev) => prev.filter((_, index) => index !== indexToRemove));

  setUploadedImages([]);
  setImageAnalysis(null);
  setBatchAnalysisResults([]);
  setBatchSeveritySummary(null);
  setPredictionResult(null);
  setHasUnsavedChanges(true);
};

  const handleFilesChange = async (event) => {
    const selectedFiles = Array.from(event.target.files || []);

    previewUrls.forEach((url) => URL.revokeObjectURL(url));

    if (selectedFiles.length === 0) {
      setFiles([]);
      setPreviewUrls([]);
      markDirty();
      return;
    }

    try {
      const validFiles = [];
      const validPreviewUrls = [];
      const invalidFiles = [];

      for (const file of selectedFiles) {
        const { width, height, url } = await readImageDimensions(file);

        if (width >= MIN_IMAGE_WIDTH && height >= MIN_IMAGE_HEIGHT) {
          validFiles.push(file);
          validPreviewUrls.push(url);
        } else {
          invalidFiles.push(
            `${file.name} (${width}x${height}) - per maža raiška, reikia bent ${MIN_IMAGE_WIDTH}x${MIN_IMAGE_HEIGHT}`
          );
          URL.revokeObjectURL(url);
        }
      }

      setFiles(validFiles);
      setPreviewUrls(validPreviewUrls);
      markDirty();

      setError(invalidFiles.length > 0 ? invalidFiles.join("\n") : "");
    } catch (err) {
      setError(err.message || "Nepavyko patikrinti nuotraukų");
      setFiles([]);
      setPreviewUrls([]);
    }
  };

  const validateBaseFields = () => {
    if (!form.make.trim()) return "Įveskite markę";
    if (!form.model.trim()) return "Įveskite modelį";
    if (!form.year) return "Pasirinkite metus";
    if (!form.description.trim()) return "Įveskite aprašymą";
    if (!form.location.trim()) return "Įveskite lokaciją";
    if (form.sale_type === "reserve_price" && !form.reserve_price) {
      return "Reikia rezervinės kainos";
    }

    if (form.engine_volume && Number(form.engine_volume) > 10) {
      return "Variklio tūris negali būti didesnis nei 10.0";
    }

    if (form.cylinders && Number(form.cylinders) > 16) {
      return "Cilindrų skaičius negali būti didesnis nei 16";
    }

    return "";
  };

  const validateBeforeCreate = () => {
    const baseError = validateBaseFields();
    if (baseError) return baseError;
    if (files.length === 0) return "Reikia bent 1 tinkamos HD nuotraukos";
    return "";
  };

  const uploadImages = async (listingId) => {
    const uploaded = [];

    for (const file of files) {
      const uploadedImage = await uploadListingImage(listingId, file);
      uploaded.push(uploadedImage);
    }

    setUploadedImages(uploaded);
    return uploaded;
  };

  const createDraftListing = async ({ requireImages = false } = {}) => {
    const baseError = validateBaseFields();
    if (baseError) {
      setError(baseError);
      return null;
    }

    if (requireImages && files.length === 0) {
      setError("Reikia bent 1 tinkamos HD nuotraukos");
      return null;
    }

    const payload = buildPayload(form);

    const listing = await createListing(payload);

    let uploaded = [];
    if (files.length > 0) {
      uploaded = await uploadImages(listing.id);
    }

    const listingWithImages = {
      ...listing,
      images: uploaded,
    };

    setCreatedListing(listingWithImages);
    setUploadedImages(uploaded);
    setHasUnsavedChanges(false);

    return listingWithImages;
  };

  const ensureListingExistsForPrediction = async (useCv) => {
    if (createdListing?.id && !hasUnsavedChanges) return createdListing;
    return await createDraftListing({ requireImages: useCv });
  };


  const handleCreateAndSubmit = async (event) => {
  event.preventDefault();

  const validationError = validateBeforeCreate();
  if (validationError) {
    setError(validationError);
    return;
  }

  try {
    setSubmitting(true);
    setError("");
    setSuccess("");

    const listing = await createDraftListing({ requireImages: true });
    if (!listing) return;

    await submitListing(listing.id);

    setSuccess("Lotas sukurtas ir išsiųstas adminui peržiūrai");
    navigate("/user");
  } catch (err) {
    setError(err.response?.data?.detail || err.message || "Klaida");
  } finally {
    setSubmitting(false);
  }
};

  const handlePredictClick = async () => {
    setError("");
    setSuccess("");

    const baseError = validateBaseFields();
    if (baseError) {
      setError(baseError);
      return;
    }

    setShowPredictChoice(true);
  };

  const runPrediction = async (useCv) => {
    try {
      setPredicting(true);
      setError("");
      setSuccess("");
      setShowPredictChoice(false);

      const listing = await ensureListingExistsForPrediction(useCv);
      if (!listing?.id) return;

      const prediction = await predictListingPrice(listing.id, useCv);

      setPredictionResult(prediction);
      setPredictionModeLabel(
        useCv ? "Prognozė su nuotraukų analize" : "Greita prognozė be nuotraukų analizės"
      );
      setSuccess(
        useCv
          ? "Kainos prognozė su nuotraukų analize sėkmingai atlikta."
          : "Greita kainos prognozė sėkmingai atlikta."
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Nepavyko prognozuoti kainos"
      );
    } finally {
      setPredicting(false);
    }
  };

  const handlePrepareImagesForAnalysis = async () => {
    try {
      setSavingDraft(true);
      setError("");
      setSuccess("");
      setBatchAnalysisResults([]);
      setBatchSeveritySummary(null);

      const validationError = validateBeforeCreate();
      if (validationError) {
        setError(validationError);
        return;
      }

      const listing = await createDraftListing({ requireImages: true });
      if (!listing) return;

      setSuccess(
        "Nuotraukos paruoštos DI analizei. Pasirinkite nuotrauką arba įvertinkite visas."
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Nepavyko paruošti nuotraukų DI analizei"
      );
    } finally {
      setSavingDraft(false);
    }
  };

  const handleAnalyzeUploadedImage = async (imageId) => {
    if (!createdListing?.id) {
      setError("Pirma paruoškite nuotraukas DI analizei.");
      return;
    }

    try {
      setAnalyzingImageId(imageId);
      setError("");
      setImageAnalysis(null);

      const analysis = await analyzeListingImage(createdListing.id, imageId);

      setImageAnalysis({
        ...analysis,
        annotatedUrl: `${BACKEND_BASE}${analysis.annotated_image_url}`,
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Nepavyko analizuoti nuotraukos"
      );
    } finally {
      setAnalyzingImageId(null);
    }
  };

  const handleAnalyzeAllUploadedImages = async () => {
    if (!createdListing?.id) {
      setError("Pirma paruoškite nuotraukas DI analizei.");
      return;
    }

    if (uploadedImages.length === 0) {
      setError("Nėra įkeltų nuotraukų DI analizei.");
      return;
    }

    const imagesToAnalyze = uploadedImages.slice(0, MAX_ANALYSIS_IMAGES);

    try {
      setBatchAnalyzing(true);
      setError("");
      setBatchAnalysisResults([]);
      setBatchSeveritySummary(null);

      const results = [];

      for (const image of imagesToAnalyze) {
        const analysis = await analyzeListingImage(createdListing.id, image.id);

        results.push({
          ...analysis,
          image_id: image.id,
          original_image_url: image.image_url,
          annotatedUrl: `${BACKEND_BASE}${analysis.annotated_image_url}`,
        });
      }

      const primaryMax = getMaxKnownSeverity(
        results.map((result) => result.primary_severity)
      );

      const secondaryMax = getMaxKnownSeverity(
        results.map((result) => result.secondary_severity)
      );

      setBatchAnalysisResults(results);
      setBatchSeveritySummary({
        primary_severity: primaryMax,
        secondary_severity: secondaryMax,
        analyzed_count: results.length,
      });

      setSuccess(`Išanalizuota ${results.length} nuotraukų.`);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Nepavyko išanalizuoti visų nuotraukų"
      );
    } finally {
      setBatchAnalyzing(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.headerRow}>
          <div>
            <h1 style={styles.title}>Sukurti lotą</h1>
            <p style={styles.subtitle}>
              Užpildykite informaciją, įkelkite nuotraukas, pasitikrinkite kainą
              ir pateikite skelbimą peržiūrai.
            </p>
          </div>

          <button
            style={styles.secondaryBtn}
            onClick={() => navigate(-1)}
            type="button"
          >
            Grįžti
          </button>
        </div>

        <form onSubmit={handleCreateAndSubmit} style={styles.form}>
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Pagrindinė informacija</h2>

            <div style={styles.grid}>
              <Input label="Markė" name="make" value={form.make} onChange={handleChange} required />
              <Input label="Modelis" name="model" value={form.model} onChange={handleChange} required />

              <Select label="Metai" name="year" value={form.year} onChange={handleChange} required>
                <option value="">Pasirinkite metus</option>
                {yearOptions.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </Select>

              <Select label="Aukciono tipas" name="auction_type" value={form.auction_type} onChange={handleChange}>
                {auctionTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>

              <Select label="Pardavimo tipas" name="sale_type" value={form.sale_type} onChange={handleChange}>
                {saleTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>

              {form.sale_type === "reserve_price" && (
                <Input label="Rezervinė kaina" name="reserve_price" type="number" min="1" step="0.01" value={form.reserve_price} onChange={handleChange} required />
              )}

              <Input label="VIN" name="vin" value={form.vin} onChange={handleChange} maxLength={17} />
              <Input label="Rida" name="mileage" type="number" min="0" value={form.mileage} onChange={handleChange} />
              <Input label="Kėbulo tipas" name="body_type" value={form.body_type} onChange={handleChange} />
              <Input label="Spalva" name="color" value={form.color} onChange={handleChange} />
              <Input label="Lokacija" name="location" value={form.location} onChange={handleChange} required />
            </div>
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Techniniai duomenys</h2>

            <div style={styles.grid}>
              <Select label="Kuras" name="fuel_type" value={form.fuel_type} onChange={handleChange}>
                <option value="">Pasirinkite</option>
                {fuelTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>

              <Input label="Variklio tūris" name="engine_volume" type="number" min="0" max="10" step="0.1" value={form.engine_volume} onChange={handleChange} />
              <Input label="Cilindrai" name="cylinders" type="number" min="0" max="16" value={form.cylinders} onChange={handleChange} />

              <Select label="Varantieji ratai" name="drive_type" value={form.drive_type} onChange={handleChange}>
                <option value="">Pasirinkite</option>
                {driveTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>

              <Select label="Pavarų dėžė" name="transmission" value={form.transmission} onChange={handleChange}>
                <option value="">Pasirinkite</option>
                {transmissionOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>
            </div>
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Pažeidimai ir aprašymas</h2>

            <div style={styles.grid}>
              <Select label="Pagrindinis pažeidimas" name="primary_damage" value={form.primary_damage} onChange={handleChange}>
                <option value="">Pasirinkite</option>
                {damageOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>

              <Select label="Antrinis pažeidimas" name="secondary_damage" value={form.secondary_damage} onChange={handleChange}>
                <option value="">Pasirinkite</option>
                {damageOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </Select>
            </div>

            <label style={styles.label}>
              <span style={styles.labelText}>Aprašymas</span>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={6}
                required
                style={styles.textarea}
                placeholder="Aprašykite automobilio būklę, komplektaciją, defektus ir kitą svarbią informaciją"
              />
            </label>
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Nuotraukos</h2>

            <label style={styles.uploadBox}>
              <input type="file" accept="image/*" multiple onChange={handleFilesChange} style={{ display: "none" }} />
              <span>Paspauskite arba pasirinkite nuotraukas čia</span>
              <small>
                Reikalinga bent viena nuotrauka, mažiausiai {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}px
              </small>
            </label>

            {previewUrls.length > 0 && (
  <div style={styles.previewGrid}>
    {previewUrls.map((src, index) => (
      <div key={`${src}-${index}`} style={styles.previewCard}>
        <img
          src={src}
          alt={`Preview ${index + 1}`}
          style={styles.previewImage}
        />

        <button
          type="button"
          style={styles.removeImageBtn}
          onClick={() => handleRemoveSelectedImage(index)}
          disabled={savingDraft || submitting || predicting || batchAnalyzing}
        >
          X
        </button>
      </div>
    ))}
  </div>
)}
            <div style={styles.actionsLeft}>
              <button
                type="button"
                style={styles.secondaryBtn}
                onClick={handlePrepareImagesForAnalysis}
                disabled={savingDraft || submitting || predicting || batchAnalyzing || files.length === 0}
              >
                {savingDraft ? "Ruošiama..." : "Paruošti nuotraukas DI analizei"}
              </button>
            </div>

            {uploadedImages.length > 0 && (
              <>
                <h3 style={styles.subTitle}>Įkeltos nuotraukos DI analizei</h3>

                <div style={styles.actionsLeft}>
                  <button
                    type="button"
                    style={styles.predictBtn}
                    onClick={handleAnalyzeAllUploadedImages}
                    disabled={batchAnalyzing || uploadedImages.length === 0 || submitting || predicting || savingDraft}
                  >
                    {batchAnalyzing
                      ? "Analizuojamos nuotraukos..."
                      : `Įvertinti visas nuotraukas (${Math.min(uploadedImages.length, MAX_ANALYSIS_IMAGES)}/${MAX_ANALYSIS_IMAGES})`}
                  </button>
                </div>

                <div style={styles.uploadedGrid}>
                  {uploadedImages.map((image) => (
                    <button
                      key={image.id}
                      type="button"
                      style={styles.imageAnalyzeBtn}
                      onClick={() => handleAnalyzeUploadedImage(image.id)}
                      disabled={analyzingImageId === image.id || batchAnalyzing}
                    >
                      <img src={`${BACKEND_BASE}${image.image_url}`} alt="Įkelta nuotrauka" style={styles.previewImage} />
                      <span>
                        {analyzingImageId === image.id ? "Analizuojama..." : "Įvertinti nuotrauką"}
                      </span>
                    </button>
                  ))}
                </div>

                {batchSeveritySummary && (
                  <div style={styles.batchSummaryBox}>
                    <h3 style={styles.subTitle}>Bendra nuotraukų analizė</h3>

                    <div>
                      <strong>Išanalizuota nuotraukų:</strong>{" "}
                      {batchSeveritySummary.analyzed_count}
                    </div>

                    <div>
                      <strong>Pirminio pažeidimo sunkumas:</strong>{" "}
                      {formatSeverity(batchSeveritySummary.primary_severity)}
                    </div>

                    <div>
                      <strong>Antrinio pažeidimo sunkumas:</strong>{" "}
                      {formatSeverity(batchSeveritySummary.secondary_severity)}
                    </div>
                  </div>
                )}

                {batchAnalysisResults.length > 0 && (
                  <div style={styles.batchResultGrid}>
                    {batchAnalysisResults.map((result) => (
                      <div key={result.image_id} style={styles.batchResultCard}>
                        <img
                          src={result.annotatedUrl}
                          alt="Analizuota nuotrauka"
                          style={styles.previewImage}
                          onClick={() => setImageAnalysis(result)}
                        />

                        <div style={styles.helperText}>
                          Pirminis: {formatSeverity(result.primary_severity)}
                          <br />
                          Antrinis: {formatSeverity(result.secondary_severity)}
                          <br />
                          Aptikta: {result.detections?.length || 0}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Kainos prognozė</h2>

            <div style={styles.actionsLeft}>
              <button type="button" style={styles.predictBtn} onClick={handlePredictClick} disabled={predicting || submitting || savingDraft || batchAnalyzing}>
                {predicting ? "Prognozuojama..." : "Prognozuoti kainą"}
              </button>
            </div>

            <div style={styles.helperText}>
              Pirmiausia užpildykite automobilio informaciją. Tada galite
              pasirinkti greitą prognozę arba tikslesnę prognozę su nuotraukų DI
              analize.
            </div>

            {predictionModeLabel && (
              <div style={styles.infoBox}>
                Paskutinė prognozė: {predictionModeLabel}
              </div>
            )}

            {hasUnsavedChanges && createdListing?.id && (
              <div style={styles.warningBox}>
                Po paskutinių pakeitimų prognozė gali būti pasenusi.
                Perskaičiuokite ją iš naujo.
              </div>
            )}

            <div style={styles.grid}>
              <label style={styles.label}>
                <span style={styles.labelText}>Prognozuojama kaina</span>
                <input value={predictedPrice ? `${predictedPrice}` : ""} readOnly style={{ ...styles.input, background: "#f9fafb" }} placeholder="Dar nepaskaičiuota" />
              </label>

              <label style={styles.label}>
                <span style={styles.labelText}>Norima pardavimo kaina (€)</span>
                <input type="number" min="0" step="0.01" value={wantedPrice} onChange={(e) => setWantedPrice(e.target.value)} style={styles.input} placeholder="Pvz. 12500" />
              </label>
            </div>

            {priceInsight && (
              <div
                style={{
                  ...styles.priceInsightBox,
                  ...(priceInsight.status === "high"
                    ? styles.priceHigh
                    : priceInsight.status === "low"
                    ? styles.priceLow
                    : styles.priceOk),
                }}
              >
                <strong>{priceInsight.message}</strong>
                <div>Skirtumas eurais: {priceInsight.diff.toFixed(2)} €</div>
                <div>
                  Skirtumas procentais: {priceInsight.percent >= 0 ? "+" : ""}
                  {priceInsight.percent.toFixed(1)}%
                </div>
              </div>
            )}
          </section>

          {createdListing?.id && (
            <div style={styles.infoBox}>
              Sukurtas lotas ID: {createdListing.id}
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              {error.split("\n").map((line, index) => (
                <div key={index}>{line}</div>
              ))}
            </div>
          )}

          {success && <div style={styles.successBox}>{success}</div>}

          <div style={styles.actions}>
            <button type="submit" style={styles.primaryBtn} disabled={submitting || predicting || savingDraft || batchAnalyzing}>
              {submitting ? "Kuriama..." : "Sukurti ir pateikti"}
            </button>
          </div>
        </form>
      </div>

      <PredictionChoiceModal
        open={showPredictChoice}
        onClose={() => setShowPredictChoice(false)}
        onRunPrediction={runPrediction}
      />

      <ImageAnalysisModal
        imageAnalysis={imageAnalysis}
        onClose={() => setImageAnalysis(null)}
      />
    </div>
  );
}

function Input({ label, ...props }) {
  return (
    <label style={styles.label}>
      <span style={styles.labelText}>{label}</span>
      <input {...props} style={styles.input} />
    </label>
  );
}

function Select({ label, children, ...props }) {
  return (
    <label style={styles.label}>
      <span style={styles.labelText}>{label}</span>
      <select {...props} style={styles.input}>
        {children}
      </select>
    </label>
  );
}
