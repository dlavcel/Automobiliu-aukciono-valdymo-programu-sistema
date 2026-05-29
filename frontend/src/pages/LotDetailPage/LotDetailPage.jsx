import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  BACKEND_BASE,
  WS_BASE_URL,
  analyzeListingImage,
  getAuction,
  getAuctionBids,
  placeEnglishBid,
  placeSealedBid,
} from "./auctionApi";
import BidForm from "./components/BidForm";
import ImageGalleryModal from "./components/ImageGalleryModal";
import {
  formatAuctionStatus,
  formatAuctionType,
  formatDamage,
  formatDriveType,
  formatFuelType,
  formatMoney,
  formatSaleType,
  formatSeverity,
  formatTransmission,
  formatValue,
} from "./formatters";
import "./LotDetailPage.css";

export default function LotDetailPage() {
  const { auctionId } = useParams();

  const [auction, setAuction] = useState(null);
  const [bids, setBids] = useState([]);
  const [selectedImage, setSelectedImage] = useState("");

  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [imageAnalysis, setImageAnalysis] = useState(null);
  const [analysisError, setAnalysisError] = useState("");
  const [analyzingImageId, setAnalyzingImageId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [bidAmount, setBidAmount] = useState("");
  const [bidLoading, setBidLoading] = useState(false);
  const [bidError, setBidError] = useState("");
  const [bidSuccess, setBidSuccess] = useState("");

  const [sealedBidAmount, setSealedBidAmount] = useState("");
  const [sealedBidLoading, setSealedBidLoading] = useState(false);
  const [sealedBidError, setSealedBidError] = useState("");
  const [sealedBidSuccess, setSealedBidSuccess] = useState("");

  const isEnglishAuction = auction?.auction_type === "english";
  const isSealedAuction = auction?.auction_type === "sealed_first_price";
  const isLiveAuction = auction?.status === "live";
  const isLoggedIn = !!localStorage.getItem("token");

  const currentPrice = Number(auction?.current_price || 0);
  const minIncrement = Number(auction?.min_increment || 1);
  const minimumBidWhole = Math.ceil(currentPrice + minIncrement);

  const loadAuction = async () => {
    const data = await getAuction(auctionId);
    setAuction(data);
    return data;
  };

  const loadBids = async () => {
    const data = await getAuctionBids(auctionId);
    setBids(data);
    return data;
  };

  useEffect(() => {
    let isMounted = true;

    async function loadPage() {
      try {
        setLoading(true);
        setError("");

        const auctionData = await getAuction(auctionId);
        if (!isMounted) return;

        setAuction(auctionData);

        if (auctionData?.auction_type === "english") {
          const bidsData = await getAuctionBids(auctionId);
          if (isMounted) setBids(bidsData);
        }
      } catch (err) {
        if (!isMounted) return;
        setError(err.response?.data?.detail || err.message || "Nepavyko užkrauti loto");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadPage();

    return () => {
      isMounted = false;
    };
  }, [auctionId]);

  useEffect(() => {
    if (!auctionId || !isEnglishAuction) return undefined;

    const ws = new WebSocket(`${WS_BASE_URL}/ws/auctions/${auctionId}`);

    ws.onerror = (wsError) => console.error("[WS DEBUG] error", wsError);

    ws.onmessage = async (message) => {
      try {
        const data = JSON.parse(message.data);
        if (data.event === "connected") return;

        if (data.event === "english_bid_placed") {
          setAuction((prev) =>
            prev
              ? {
                  ...prev,
                  current_price: data.current_price,
                  status: data.status || prev.status,
                }
              : prev
          );

          await Promise.all([loadAuction(), loadBids()]);
        }
      } catch (err) {
        console.error(err);
      }
    };

    return () => ws.close();
  }, [auctionId, isEnglishAuction]);

  const imageItems = useMemo(() => {
    const images = auction?.listing?.images || [];

    return images
      .map((img) => {
        const raw = img.image_url || img.url || "";
        if (!raw) return null;

        return {
          id: img.id,
          raw,
          url: raw.startsWith("http") ? raw : `${BACKEND_BASE}${raw}`,
        };
      })
      .filter(Boolean);
  }, [auction]);

  useEffect(() => {
    if (imageItems.length > 0) setSelectedImage(imageItems[0].url);
  }, [imageItems]);

  const resetGalleryAnalysis = () => {
    setImageAnalysis(null);
    setAnalysisError("");
  };

  const openGallery = (index) => {
    setGalleryIndex(index);
    resetGalleryAnalysis();
    setGalleryOpen(true);
  };

  const closeGallery = () => {
    setGalleryOpen(false);
    resetGalleryAnalysis();
    setAnalyzingImageId(null);
  };

  const goPrevImage = () => {
    resetGalleryAnalysis();
    setGalleryIndex((prev) => (prev === 0 ? imageItems.length - 1 : prev - 1));
  };

  const goNextImage = () => {
    resetGalleryAnalysis();
    setGalleryIndex((prev) => (prev === imageItems.length - 1 ? 0 : prev + 1));
  };

  const analyzeGalleryImage = async () => {
    const listingId = auction?.listing?.id;
    const image = imageItems[galleryIndex];

    if (!listingId || !image?.id) {
      setAnalysisError("Nepavyko nustatyti nuotraukos analizei.");
      return;
    }

    try {
      setAnalyzingImageId(image.id);
      resetGalleryAnalysis();

      const result = await analyzeListingImage(listingId, image.id);
      setImageAnalysis(result);
    } catch (err) {
      setAnalysisError(
        err.response?.data?.detail || err.message || "Nepavyko atlikti vaizdo analizės su DI"
      );
    } finally {
      setAnalyzingImageId(null);
    }
  };

  const validateEnglishBid = () => {
    const numericAmount = Number(bidAmount);

    if (!Number.isInteger(numericAmount)) return "Pasiūlymas turi būti sveikas skaičius";
    if (!numericAmount || numericAmount < minimumBidWhole) {
      return `Pasiūlymas turi būti bent ${formatMoney(minimumBidWhole)}`;
    }

    return "";
  };

  const handleBidSubmit = async (event) => {
    event.preventDefault();

    try {
      setBidLoading(true);
      setBidError("");
      setBidSuccess("");

      const validationError = validateEnglishBid();
      if (validationError) {
        setBidError(validationError);
        return;
      }

      const bid = await placeEnglishBid(auctionId, bidAmount);

      setBidAmount("");
      setBidSuccess("Pasiūlymas pateiktas");
      setAuction((prev) => (prev ? { ...prev, current_price: bid.amount } : prev));

      await Promise.all([loadAuction(), loadBids()]);
    } catch (err) {
      setBidError(err.response?.data?.detail || err.message || "Nepavyko pateikti pasiūlymo");
    } finally {
      setBidLoading(false);
    }
  };

  const validateSealedBid = () => {
    const numericAmount = Number(sealedBidAmount);

    if (!Number.isInteger(numericAmount)) return "Pasiūlymas turi būti sveikas skaičius";
    if (!numericAmount || numericAmount <= 0) return "Pasiūlymas turi būti didesnis už 0";

    return "";
  };

  const handleSealedBidSubmit = async (event) => {
    event.preventDefault();

    try {
      setSealedBidLoading(true);
      setSealedBidError("");
      setSealedBidSuccess("");

      const validationError = validateSealedBid();
      if (validationError) {
        setSealedBidError(validationError);
        return;
      }

      await placeSealedBid(auctionId, sealedBidAmount);

      setSealedBidAmount("");
      setSealedBidSuccess("Uždaras pasiūlymas pateiktas");
      await loadAuction();
    } catch (err) {
      setSealedBidError(
        err.response?.data?.detail || err.message || "Nepavyko pateikti uždaro pasiūlymo"
      );
    } finally {
      setSealedBidLoading(false);
    }
  };

  if (loading) return <div className="center">Kraunamas lotas...</div>;
  if (error) return <div className="center">{error}</div>;
  if (!auction) return <div className="center">Lotas nerastas</div>;

  const listing = auction.listing;
  const title = [listing?.make, listing?.model, listing?.year].filter(Boolean).join(" ");
  const galleryImage = imageItems[galleryIndex];
  const bidDisabled = !isLoggedIn || !isLiveAuction;

  return (
    <div className="lot-page">
      <div className="top-bar">
        <Link to="/" className="back-link">
          ← Grįžti į aukcionus
        </Link>
      </div>

      <div className="lot-layout">
        <ListingGallery
          title={title}
          imageItems={imageItems}
          selectedImage={selectedImage}
          onSelectImage={setSelectedImage}
          onOpenGallery={openGallery}
        />

        <div className="sidebar">
          <h1 className="title">{title || "Lotas"}</h1>

          <AuctionSummary auction={auction} listing={listing} isSealedAuction={isSealedAuction} />

          {isEnglishAuction && (
            <>
              <BidAvailabilityWarnings isLoggedIn={isLoggedIn} isLiveAuction={isLiveAuction} />
              <BidForm
                title="Pateikti pasiūlymą"
                amount={bidAmount}
                onAmountChange={setBidAmount}
                onSubmit={handleBidSubmit}
                loading={bidLoading}
                error={bidError}
                success={bidSuccess}
                disabled={bidDisabled}
                min={minimumBidWhole}
                placeholder={`Min. ${minimumBidWhole}`}
                submitLabel="Pateikti pasiūlymą"
                loadingLabel="Siunčiama..."
                showMinimum
              />
            </>
          )}

          {isSealedAuction && (
            <>
              <BidAvailabilityWarnings isLoggedIn={isLoggedIn} isLiveAuction={isLiveAuction} />
              <BidForm
                title="Pateikti uždarą pasiūlymą"
                description="Uždarame aukcione kiti dalyviai nemato tavo pasiūlymo. Iki aukciono pabaigos gali pateikti arba pakeisti savo pasiūlymą."
                amount={sealedBidAmount}
                onAmountChange={setSealedBidAmount}
                onSubmit={handleSealedBidSubmit}
                loading={sealedBidLoading}
                error={sealedBidError}
                success={sealedBidSuccess}
                disabled={bidDisabled}
                min={1}
                placeholder="Įveskite pasiūlymą"
                submitLabel="Pateikti uždarą pasiūlymą"
                loadingLabel="Siunčiama..."
              />
            </>
          )}

          {isEnglishAuction && <BidHistory bids={bids} />}

          <VehicleInfo listing={listing} />

          <div className="section">
            <h3 className="section-title">Aprašymas</h3>
            <p className="description">{listing?.description || "Aprašymo nėra"}</p>
          </div>
        </div>
      </div>

      {galleryOpen && galleryImage && (
        <ImageGalleryModal
          imageItems={imageItems}
          galleryIndex={galleryIndex}
          galleryImage={galleryImage}
          imageAnalysis={imageAnalysis}
          analysisError={analysisError}
          analyzingImageId={analyzingImageId}
          onClose={closeGallery}
          onPrev={goPrevImage}
          onNext={goNextImage}
          onAnalyze={analyzeGalleryImage}
        />
      )}
    </div>
  );
}

function ListingGallery({ title, imageItems, selectedImage, onSelectImage, onOpenGallery }) {
  const selectedIndex = imageItems.findIndex((img) => img.url === selectedImage);

  return (
    <div>
      <div className="main-image-wrap">
        <img
          src={selectedImage || "https://via.placeholder.com/1000x650?text=No+Image"}
          alt={title || "Lotas"}
          className="main-image"
          onClick={() => selectedIndex >= 0 && onOpenGallery(selectedIndex)}
        />

        {imageItems.length > 0 && (
          <button
            type="button"
            className="open-gallery-btn"
            onClick={() => onOpenGallery(selectedIndex >= 0 ? selectedIndex : 0)}
          >
            Atidaryti galeriją
          </button>
        )}
      </div>

      {imageItems.length > 1 && (
        <div className="thumb-row">
          {imageItems.map((img, index) => (
            <button
              key={img.id || img.url}
              onClick={() => onSelectImage(img.url)}
              className={`thumb-button ${selectedImage === img.url ? "thumb-button-active" : ""}`}
              type="button"
            >
              <img src={img.url} alt={`thumb-${index}`} className="thumb" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function AuctionSummary({ auction, listing, isSealedAuction }) {
  return (
    <div className="info-box">
      {!isSealedAuction && (
        <div className="price-box">
          <span className="price-label">Dabartinė kaina</span>
          <strong className="price">{formatMoney(auction.current_price)}</strong>
        </div>
      )}

      <InfoRow label="Prognozuota kaina" value={formatMoney(listing?.predicted_price)} />
      <InfoRow label="Pirminio pažeidimo sunkumas" value={formatSeverity(listing?.primary_damage_severity)} />
      <InfoRow label="Antrinio pažeidimo sunkumas" value={formatSeverity(listing?.secondary_damage_severity)} />
      <InfoRow label="Statusas" value={formatAuctionStatus(auction.status)} />
      <InfoRow label="Aukciono tipas" value={formatAuctionType(auction.auction_type)} />
      <InfoRow label="Pardavimo tipas" value={formatSaleType(auction.sale_type)} />
      <InfoRow label="Pradžia" value={auction.starts_at ? new Date(auction.starts_at).toLocaleString() : "-"} />
      <InfoRow label="Pabaiga" value={auction.ends_at ? new Date(auction.ends_at).toLocaleString() : "-"} />
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <strong>{label}</strong>
      <span>{value}</span>
    </div>
  );
}

function BidAvailabilityWarnings({ isLoggedIn, isLiveAuction }) {
  if (isLoggedIn && isLiveAuction) return null;

  return (
    <div className="section section-compact">
      {!isLoggedIn && <p className="warning">Norint pateikti pasiūlymą, reikia prisijungti.</p>}
      {!isLiveAuction && <p className="warning">Pasiūlymus galima teikti tik vykstančiame aukcione.</p>}
    </div>
  );
}

function BidHistory({ bids }) {
  return (
    <div className="section">
      <h3 className="section-title">Pasiūlymų istorija</h3>

      {bids.length === 0 ? (
        <p className="description">Pasiūlymų dar nėra.</p>
      ) : (
        <div className="bid-list">
          {bids.slice(0, 5).map((bid) => (
            <div key={bid.id} className="bid-item">
              <strong>{formatMoney(bid.amount)}</strong>
              <span>{bid.created_at ? new Date(bid.created_at).toLocaleString() : "-"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function VehicleInfo({ listing }) {
  const specs = [
    ["Markė", formatValue(listing?.make)],
    ["Modelis", formatValue(listing?.model)],
    ["Metai", formatValue(listing?.year)],
    ["Rida", formatValue(listing?.mileage)],
    ["Kuras", formatFuelType(listing?.fuel_type)],
    ["Pavarų dėžė", formatTransmission(listing?.transmission)],
    ["Varantieji ratai", formatDriveType(listing?.drive_type)],
    ["Spalva", formatValue(listing?.color)],
    ["Kėbulo tipas", formatValue(listing?.body_type)],
    ["Lokacija", formatValue(listing?.location)],
    ["Pirminis pažeidimas", formatDamage(listing?.primary_damage)],
    ["Pirminio pažeidimo sunkumas", formatSeverity(listing?.primary_damage_severity)],
    ["Antrinis pažeidimas", formatDamage(listing?.secondary_damage)],
    ["Antrinio pažeidimo sunkumas", formatSeverity(listing?.secondary_damage_severity)],
    ["Prognozuota kaina", formatMoney(listing?.predicted_price)],
  ];

  return (
    <div className="section">
      <h3 className="section-title">Transporto priemonės informacija</h3>

      <div className="spec-grid">
        {specs.map(([label, value]) => (
          <div key={label} className="spec-item">
            <span className="spec-label">{label}</span>
            <span>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
