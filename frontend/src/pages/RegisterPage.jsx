import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8001/api/v1";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    phone: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");

      await axios.post(`${API_BASE_URL}/auth/register`, form);

      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Nepavyko užsiregistruoti");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <form onSubmit={handleRegister} style={styles.form}>
        <h2>Registracija</h2>

        <input
          name="first_name"
          placeholder="Vardas"
          value={form.first_name}
          onChange={handleChange}
          style={styles.input}
        />

        <input
          name="last_name"
          placeholder="Pavardė"
          value={form.last_name}
          onChange={handleChange}
          style={styles.input}
        />

        <input
          name="phone"
          placeholder="Telefonas"
          value={form.phone}
          onChange={handleChange}
          style={styles.input}
        />

        <input
          name="email"
          type="email"
          placeholder="El. paštas"
          value={form.email}
          onChange={handleChange}
          style={styles.input}
          required
        />

        <input
          name="password"
          type="password"
          placeholder="Slaptažodis"
          value={form.password}
          onChange={handleChange}
          style={styles.input}
          minLength={8}
          required
        />

        {error && <div style={styles.error}>{error}</div>}

        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Registruojama..." : "Registruotis"}
        </button>

        <button
          type="button"
          style={styles.secondaryButton}
          onClick={() => navigate("/login")}
        >
          Jau turi paskyrą? Prisijunk
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
    width: "340px",
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