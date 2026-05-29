import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8001/api/v1";

export default function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");

      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password,
      });

      const token = res.data.access_token;
      localStorage.setItem("token", token);

      const meRes = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (meRes.data.is_admin) {
        navigate("/admin");
      } else {
        navigate("/user");
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Nepavyko prisijungti");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <form onSubmit={handleLogin} style={styles.form}>
        <h2>Prisijungimas</h2>

        <input
          type="email"
          placeholder="El. paštas"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={styles.input}
          required
        />

        <input
          type="password"
          placeholder="Slaptažodis"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
          required
        />

        {error && <div style={styles.error}>{error}</div>}

        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Jungiamasi..." : "Prisijungti"}
        </button>

        <button
          type="button"
          style={styles.secondaryButton}
          onClick={() => navigate("/register")}
        >
          Neturi paskyros? Registruokis
        </button>
      </form>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    fontFamily: "Arial",
  },
  form: {
    width: "320px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  input: {
    height: "40px",
    padding: "0 10px",
    borderRadius: "6px",
    border: "1px solid #ccc",
  },
  button: {
    height: "40px",
    borderRadius: "6px",
    border: "none",
    background: "#111",
    color: "#fff",
    cursor: "pointer",
  },
  secondaryButton: {
    height: "40px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    background: "#fff",
    color: "#111",
    cursor: "pointer",
  },
  error: {
    color: "red",
    fontSize: "14px",
  },
};