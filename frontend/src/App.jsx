import { Routes, Route } from "react-router-dom";
import MainPage from "./pages/MainPage";
import LoginPage from "./pages/LoginPage";
import LotDetailPage from "./pages/LotDetailPage/LotDetailPage.jsx";
import CreateListingPage from "./pages/CreateListingPage/CreateListingPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import AdminPage from "./pages/AdminPage/AdminPage.jsx";
import UserPage from "./pages/UserPage/UserPage.jsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/lots/:auctionId" element={<LotDetailPage />} />
        <Route path="/create-listing" element={<CreateListingPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/user" element={<UserPage />} />
        <Route path="/listings/:listingId/edit" element={<CreateListingPage />} />
    </Routes>
  );
}

export default App;