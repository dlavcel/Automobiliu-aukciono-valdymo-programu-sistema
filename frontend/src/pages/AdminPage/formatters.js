export const formatMoney = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  return `${Number(value).toFixed(2)} €`;
};

export const formatSeverity = (value) => {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toFixed(1);
};

export const getStatusText = (status) => {
  const labels = {
    pending_review: "Peržiūroje",
    approved: "Patvirtintas",
    rejected: "Atmestas",
    draft: "Juodraštis",
  };

  return labels[status] || status || "-";
};
