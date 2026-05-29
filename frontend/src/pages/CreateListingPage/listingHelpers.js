export function buildGeneratedTitle(form) {
  return [form.make.trim(), form.model.trim(), form.year]
    .filter(Boolean)
    .join(" ");
}

export function buildPayload(form) {
  return {
    title: buildGeneratedTitle(form),
    make: form.make.trim(),
    model: form.model.trim(),
    year: Number(form.year),
    auction_type: form.auction_type,
    sale_type: form.sale_type,
    reserve_price:
      form.sale_type === "reserve_price" && form.reserve_price
        ? Number(form.reserve_price)
        : null,
    vin: form.vin.trim() || null,
    mileage: form.mileage ? Number(form.mileage) : null,
    fuel_type: form.fuel_type || null,
    engine_volume: form.engine_volume ? Number(form.engine_volume) : null,
    cylinders: form.cylinders ? Number(form.cylinders) : null,
    drive_type: form.drive_type || null,
    transmission: form.transmission || null,
    body_type: form.body_type.trim() || null,
    color: form.color.trim() || null,
    primary_damage: form.primary_damage || null,
    secondary_damage: form.secondary_damage || null,
    description: form.description.trim() || null,
    location: form.location.trim() || null,
  };
}

export function readImageDimensions(file) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      resolve({
        width: img.width,
        height: img.height,
        url: objectUrl,
      });
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error(`Nepavyko nuskaityti paveikslėlio: ${file.name}`));
    };

    img.src = objectUrl;
  });
}

export function getPriceInsight(predictedPrice, wantedPrice) {
  const predicted = Number(predictedPrice);
  const wanted = Number(wantedPrice);

  if (!predicted || !wanted || predicted <= 0) return null;

  const diff = wanted - predicted;
  const percent = (diff / predicted) * 100;
  const absPercent = Math.abs(percent);

  if (absPercent <= 10) {
    return {
      status: "ok",
      diff,
      percent,
      message: `Norima kaina yra arti prognozuojamos rinkos kainos (${
        percent >= 0 ? "+" : ""
      }${percent.toFixed(1)}%).`,
    };
  }

  if (percent > 10) {
    return {
      status: "high",
      diff,
      percent,
      message: `Norima kaina yra per didelė (${percent.toFixed(
        1
      )}% virš prognozuojamos kainos).`,
    };
  }

  return {
    status: "low",
    diff,
    percent,
    message: `Norima kaina yra per maža (${Math.abs(percent).toFixed(
      1
    )}% žemiau prognozuojamos kainos).`,
  };
}

export function formatSeverity(value) {
  if (value === null || value === undefined) return "Nežinoma";
  if (Number(value) === -1) return "Nežinoma";
  return Number(value).toFixed(1);
}

export function getMaxKnownSeverity(values) {
  const known = values
    .map((value) => Number(value))
    .filter((value) => !Number.isNaN(value) && value !== -1);

  if (known.length === 0) return -1;
  return Math.max(...known);
}

