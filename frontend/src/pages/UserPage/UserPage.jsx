import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  approveAuction,
  getUserPageData,
  rejectAuction,
} from "./userApi.js";
import {
  ListingCard,
  PendingApprovalCard,
  WonLotCard,
} from "./components/UserCards";
import "./UserPage.css";

export default function UserPage() {
  const navigate = useNavigate();

  const [listings, setListings] = useState([]);
  const [wonLots, setWonLots] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const setUserPageData = ({ listings, wonLots, pendingApprovals }) => {
    setListings(listings);
    setWonLots(wonLots);
    setPendingApprovals(pendingApprovals);
  };

  const reloadUserPageData = async () => {
    const data = await getUserPageData();
    setUserPageData(data);
  };

  useEffect(() => {
    let isMounted = true;

    const loadUserPage = async () => {
      try {
        setLoading(true);
        setError("");
        setSuccess("");

        const data = await getUserPageData();
        if (isMounted) setUserPageData(data);
      } catch (err) {
        if (!isMounted) return;
        setError(
          err.response?.data?.detail ||
            err.message ||
            "Nepavyko užkrauti vartotojo puslapio"
        );
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadUserPage();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSellerDecision = async (auctionId, action) => {
    try {
      setActionLoadingId(auctionId);
      setError("");
      setSuccess("");

      if (action === "approve") {
        await approveAuction(auctionId);
        setSuccess("Pardavimas patvirtintas");
      } else {
        await rejectAuction(auctionId);
        setSuccess("Pardavimas atmestas");
      }

      await reloadUserPageData();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          (action === "approve"
            ? "Nepavyko patvirtinti pardavimo"
            : "Nepavyko atmesti pardavimo")
      );
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading) {
    return <div className="user-page__center">Kraunama...</div>;
  }

  return (
    <div className="user-page">
      <header className="user-page__header">
        <div>
          <h1 className="user-page__title">Vartotojo puslapis</h1>
          <p className="user-page__subtitle">
            Čia gali matyti savo lotus, laimėtus automobilius ir pardavėjo patvirtinimus
          </p>
        </div>

        <div className="user-page__header-actions">
          <button className="btn btn--secondary" onClick={() => navigate("/")}>← Pagrindinis</button>
          <button className="btn btn--primary" onClick={() => navigate("/create-listing")}>Sukurti lotą</button>
        </div>
      </header>

      {error && <div className="alert alert--error">{error}</div>}
      {success && <div className="alert alert--success">{success}</div>}

      <UserSection title="Laukia pardavėjo patvirtinimo" emptyText="Šiuo metu nėra aukcionų, laukiančių patvirtinimo" items={pendingApprovals}>
        {pendingApprovals.map((auction) => (
          <PendingApprovalCard
            key={auction.id}
            auction={auction}
            navigate={navigate}
            loading={actionLoadingId === auction.id}
            onApprove={() => handleSellerDecision(auction.id, "approve")}
            onReject={() => handleSellerDecision(auction.id, "reject")}
          />
        ))}
      </UserSection>

      <UserSection title="Laimėti automobiliai" emptyText="Laimėtų automobilių dar nėra" items={wonLots}>
        {wonLots.map((auction) => (
          <WonLotCard key={auction.id} auction={auction} navigate={navigate} />
        ))}
      </UserSection>

      <UserSection title="Mano lotai" emptyText="Lotų dar nėra" items={listings}>
        {listings.map((listing) => (
          <ListingCard key={listing.id} listing={listing} navigate={navigate} />
        ))}
      </UserSection>
    </div>
  );
}

function UserSection({ title, emptyText, items, children }) {
  return (
    <section className="user-section">
      <h2 className="user-section__title">{title}</h2>

      {items.length === 0 ? (
        <p className="user-section__empty">{emptyText}</p>
      ) : (
        <div className="user-section__grid">{children}</div>
      )}
    </section>
  );
}
