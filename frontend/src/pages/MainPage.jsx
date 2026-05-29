import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_BASE = "http://127.0.0.1:8001";
const API_BASE_URL = "http://127.0.0.1:8001/api/v1";

const formatAuctionType = (type) => {
  switch (type) {
    case "english":
      return "Kylantis aukcionas";
    case "dutch":
      return "Mažėjantis aukcionas";
    case "sealed_first_price":
      return "Uždaro pasiūlymo aukcionas";
    default:
      return type || "-";
  }
};

const normalizeEnum = (value) => {
  if (value === null || value === undefined || value === "") return "";
  return String(value).toUpperCase().replace(/\s+/g, "_").replace(/&/g, "AND");
};

const formatAuctionStatus = (status) => {
  switch (normalizeEnum(status)) {
    case "SCHEDULED":
      return "Suplanuotas";
    case "LIVE":
      return "Vyksta";
    case "ENDED":
      return "Baigėsi";
    case "CANCELLED":
      return "Atšauktas";
    default:
      return status || "-";
  }
};

const formatDamage = (damage) => {
  switch (normalizeEnum(damage?.value || damage)) {
    case "NORMAL_WEAR":
      return "Natūralus nusidėvėjimas";
    case "MINOR_DENT_SCRATCHES":
      return "Smulkūs įlenkimai / įbrėžimai";
    case "FRONT_END":
    case "FRONT":
      return "Priekis";
    case "REAR_END":
    case "REAR":
      return "Galas";
    case "SIDE":
      return "Šonas";
    case "FRONT_AND_REAR":
    case "FRONT_&_REAR":
    case "FRONT_AND_REAR":
      return "Priekis ir galas";
    case "ELECTRICAL":
      return "Elektrinė dalis";
    case "MECHANICAL":
      return "Mechaninė dalis";
    case "WATER_FLOOD":
      return "Vandens / potvynio žala";
    case "BURN":
      return "Degimo žala";
    case "HAIL":
      return "Krušos žala";
    case "VANDALISM":
      return "Vandalizmas";
    case "ROLLOVER":
      return "Apsivertimas";
    case "ALL_OVER":
      return "Pažeidimai visur";
    case "UNDERCARRIAGE":
      return "Dugnas";
    default:
      return damage || "-";
  }
};

const formatSeverity = (value) => {
  if (value == null) return "-";
  if (Number(value) === -1) return "Non-visual / nerasta";
  return value;
};

const formatPrice = (value) => {
  if (value == null) return "-";
  return `${value} €`;
};

function AuctionCard({ auction }) {
  const navigate = useNavigate();

  const rawImage =
    auction.listing?.images?.[0]?.image_url ||
    auction.listing?.images?.[0]?.url ||
    "";

  const imageUrl = rawImage
    ? rawImage.startsWith("http")
      ? rawImage
      : `${BACKEND_BASE}${rawImage}`
    : "https://via.placeholder.com/400x250?text=No+Image";

  const title = [
    auction.listing?.make,
    auction.listing?.model,
    auction.listing?.year,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      style={styles.card}
      onClick={() => navigate(`/lots/${auction.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          navigate(`/lots/${auction.id}`);
        }
      }}
    >
      <img
        src={imageUrl}
        alt={title || "Aukcionas"}
        style={styles.image}
        onError={(e) => {
          e.currentTarget.src =
            "https://via.placeholder.com/400x250?text=No+Image";
        }}
      />

      <div style={styles.cardBody}>
        <h3 style={styles.title}>{title || "Aukcionas"}</h3>

        <div style={styles.row}>
          <strong>Statusas:</strong>
          <span>{formatAuctionStatus(auction.status)}</span>
        </div>

        <div style={styles.row}>
          <strong>Aukciono tipas:</strong>
          <span>{formatAuctionType(auction.auction_type)}</span>
        </div>

        <div style={styles.row}>
          <strong>Pirminis pažeidimas:</strong>
          <span>{formatDamage(auction.listing?.primary_damage)}</span>
        </div>

        <div style={styles.row}>
          <strong>Pirminis pažeidimo lygis:</strong>
          <span>
            {formatSeverity(auction.listing?.primary_damage_severity)}
          </span>
        </div>

        <div style={styles.row}>
          <strong>Prognozuojama kaina:</strong>
          <span>{formatPrice(auction.listing?.predicted_price)}</span>
        </div>

        <div style={styles.row}>
          <strong>Pradžia:</strong>
          <span>
            {auction.starts_at
              ? new Date(auction.starts_at).toLocaleString()
              : "-"}
          </span>
        </div>

        <div style={styles.row}>
          <strong>Pabaiga:</strong>
          <span>
            {auction.ends_at
              ? new Date(auction.ends_at).toLocaleString()
              : "-"}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function MainPage() {
  const navigate = useNavigate();

  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const fetchAuctions = async (silent = false) => {
      try {
        if (!silent) setLoading(true);
        setError("");

        const [liveRes, scheduledRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/auctions?status=live`),
          axios.get(`${API_BASE_URL}/auctions?status=scheduled`),
        ]);

        if (!isMounted) return;

        setAuctions([...(liveRes.data || []), ...(scheduledRes.data || [])]);
      } catch (err) {
        if (!isMounted) return;

        setError(
          err.response?.data?.detail ||
            err.message ||
            "Nepavyko užkrauti aukcionų"
        );
      } finally {
        if (isMounted && !silent) setLoading(false);
      }
    };

    fetchAuctions(false);

    const intervalId = setInterval(() => {
      fetchAuctions(true);
    }, 5000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const visibleAuctions = useMemo(() => {
    return auctions.filter((auction) => {
      const status = auction?.status?.toLowerCase();
      return (
        auction &&
        auction.listing &&
        status !== "ended" &&
        status !== "cancelled"
      );
    });
  }, [auctions]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
    navigate("/");
  };

  if (loading) {
    return <div style={styles.center}>Kraunami aukcionai...</div>;
  }

  if (error) {
    return <div style={styles.center}>{error}</div>;
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={styles.headerRow}>
          <div>
            <h1 style={styles.pageTitle}>Visi aukcionai</h1>
            <p style={styles.subtitle}>
              Rodomi tik aktyvūs ir suplanuoti patvirtinti aukcionai
            </p>
          </div>

          {/* 👉 ČIA pridėtas mygtukas */}
          <div style={{ display: "flex", gap: "10px" }}>
            {isLoggedIn && (
              <button style={styles.createBtn} onClick={() => navigate("/user")}>
                Mano kabinetas
              </button>
            )}

            {isLoggedIn ? (
              <button onClick={handleLogout} style={styles.logoutBtn}>
                Atsijungti
              </button>
            ) : (
              <button
                onClick={() => navigate("/login")}
                style={styles.loginBtn}
              >
                Prisijungti
              </button>
            )}
          </div>
        </div>
      </div>

      {visibleAuctions.length === 0 ? (
        <div style={styles.empty}>Šiuo metu aukcionų nėra</div>
      ) : (
        <div style={styles.grid}>
          {visibleAuctions.map((auction) => (
            <AuctionCard key={auction.id} auction={auction} />
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: {
    padding: "32px",
    maxWidth: "1280px",
    margin: "0 auto",
    fontFamily: "Arial, sans-serif",
  },
  header: {
    marginBottom: "24px",
  },
  headerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "16px",
  },
  pageTitle: {
    margin: 0,
    fontSize: "32px",
  },
  subtitle: {
    color: "#666",
    marginTop: "8px",
  },

  createBtn: {
    height: "42px",
    padding: "0 18px",
    borderRadius: "10px",
    border: "none",
    background: "#2563eb",
    color: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },

  loginBtn: {
    height: "42px",
    padding: "0 18px",
    borderRadius: "10px",
    border: "1px solid #111",
    background: "#111",
    color: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },
  logoutBtn: {
    height: "42px",
    padding: "0 18px",
    borderRadius: "10px",
    border: "1px solid #d0d0d0",
    background: "#fff",
    color: "#111",
    cursor: "pointer",
    fontWeight: 600,
  },
  center: {
    padding: "40px",
    textAlign: "center",
    fontSize: "18px",
  },
  empty: {
    padding: "40px",
    textAlign: "center",
    background: "#f5f5f5",
    borderRadius: "12px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: "20px",
  },
  card: {
    border: "1px solid #e5e5e5",
    borderRadius: "16px",
    overflow: "hidden",
    background: "#fff",
    boxShadow: "0 4px 16px rgba(0,0,0,0.06)",
    cursor: "pointer",
  },
  image: {
    width: "100%",
    height: "220px",
    objectFit: "cover",
  },
  cardBody: {
    padding: "16px",
  },
  title: {
    marginTop: 0,
    marginBottom: "12px",
  },
  row: {
    marginBottom: "8px",
    display: "flex",
    justifyContent: "space-between",
  },
};