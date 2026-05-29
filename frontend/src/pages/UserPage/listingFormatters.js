export function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (Number.isNaN(number)) return `${value} €`;
  return `${number.toFixed(2)} €`;
}

export function formatAuctionStatus(status) {
  switch (status) {
    case "scheduled":
      return "Suplanuotas";
    case "live":
      return "Vyksta";
    case "ended":
      return "Baigėsi";
    case "cancelled":
      return "Atšauktas";
    default:
      return status || "-";
  }
}

export function formatSaleResultStatus(status) {
  switch (status) {
    case "pending":
      return "Laukiama";
    case "sold":
      return "Parduotas";
    case "reserve_not_met":
      return "Rezervas nepasiektas";
    case "awaiting_seller_approval":
      return "Laukia pardavėjo patvirtinimo";
    case "rejected_by_seller":
      return "Neparduotas";
    default:
      return status || "-";
  }
}

export function getListingDisplayStatus(listing) {
  const auction = listing.auction;

  if (listing.status === "rejected") {
    return { text: "Atmestas", color: "#dc2626" };
  }

  if (auction) {
    if (auction.sale_result_status === "sold") {
      return { text: "Parduotas", color: "#16a34a" };
    }

    if (auction.sale_result_status === "rejected_by_seller") {
      return { text: "Neparduotas", color: "#dc2626" };
    }

    if (auction.sale_result_status === "reserve_not_met") {
      return { text: "Rezervas nepasiektas", color: "#dc2626" };
    }

    if (auction.sale_result_status === "awaiting_seller_approval") {
      return { text: "Laukia patvirtinimo", color: "#f59e0b" };
    }

    if (auction.status === "live") {
      return { text: "Aukcionas vyksta", color: "#2563eb" };
    }

    if (auction.status === "scheduled") {
      return { text: "Aukcionas suplanuotas", color: "#7c3aed" };
    }

    if (auction.status === "cancelled") {
      return { text: "Aukcionas atšauktas", color: "#6b7280" };
    }

    if (auction.status === "ended") {
      return { text: "Aukcionas baigėsi", color: "#6b7280" };
    }
  }

  switch (listing.status) {
    case "pending_review":
      return { text: "Peržiūroje", color: "#f59e0b" };
    case "approved":
      return { text: "Patvirtintas", color: "#16a34a" };
    case "draft":
      return { text: "Juodraštis", color: "#6b7280" };
    default:
      return { text: listing.status || "-", color: "#111827" };
  }
}
