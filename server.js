// server.js
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const { Pool } = require("pg");

const app = express();
const PORT = process.env.PORT || 10000;

// Usa la variable de entorno, sin fallback para evitar confusiones
const ADMIN_KEY = process.env.ADMIN_KEY;

app.use(cors());
app.use(express.json());

// Configuración de multer para subir imágenes
const storage = multer.diskStorage({
  destination: "uploads/",
  filename: (req, file, cb) => {
    cb(null, "foto.jpg"); // Siempre se sobrescribe la foto
  },
});
const upload = multer({ storage });

// Servir archivos estáticos (imágenes)
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

// (Opcional) RUTA RAÍZ para ver que la API funciona
app.get("/", (req, res) => {
  res.send("Bienvenido a la API de Mi Diario");
});

// Conexión a Postgres (Supabase)
const pool = new Pool({
  connectionString: process.env.SUPABASE_CONNECTION_STRING,
  ssl: { rejectUnauthorized: false },
});

// Rutas públicas
app.get("/entradas", async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM entradas ORDER BY fecha DESC LIMIT 5");
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/todas", async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM entradas ORDER BY fecha DESC");
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/buscar", async (req, res) => {
  const palabra = req.query.q;
  try {
    const result = await pool.query(
      "SELECT * FROM entradas WHERE contenido ILIKE $1 ORDER BY fecha DESC",
      [`%${palabra}%`]
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Rutas de administración (todas empiezan con /admin)
app.use("/admin", (req, res, next) => {
  if (req.headers["x-admin-key"] !== ADMIN_KEY) {
    return res.status(403).json({ error: "Acceso denegado" });
  }
  next();
});

app.post("/admin/nueva", async (req, res) => {
  const { titulo, contenido } = req.body;
  if (!titulo || !contenido) {
    return res.status(400).json({ error: "Título y contenido son requeridos" });
  }
  try {
    const result = await pool.query(
      "INSERT INTO entradas (titulo, contenido) VALUES ($1, $2) RETURNING id, titulo, contenido",
      [titulo, contenido]
    );
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete("/admin/borrar/:id", async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query("DELETE FROM entradas WHERE id = $1", [id]);
    res.json({ mensaje: "Entrada eliminada" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.put("/admin/modificar/:id", async (req, res) => {
  const { id } = req.params;
  const { titulo, contenido } = req.body;
  if (!titulo || !contenido) {
    return res.status(400).json({ error: "Título y contenido son requeridos" });
  }
  try {
    await pool.query("UPDATE entradas SET titulo = $1, contenido = $2 WHERE id = $3", [titulo, contenido, id]);
    res.json({ mensaje: "Entrada modificada" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post("/admin/subir-foto", upload.single("foto"), (req, res) => {
  res.json({ mensaje: "Foto subida con éxito", url: "/uploads/foto.jpg" });
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
  console.log("Base de datos conectada");
});
