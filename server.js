// server.js
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const { Pool } = require("pg");

const app = express();
const PORT = process.env.PORT || 10000;

// Clave de administrador (debe coincidir con la variable en Render)
const ADMIN_KEY = process.env.ADMIN_KEY;

// Configuración general
app.use(cors());
app.use(express.json());

// Configuración de multer para subir imágenes
const storage = multer.diskStorage({
  destination: "uploads/",
  filename: (req, file, cb) => {
    cb(null, "foto.jpg"); // Siempre se sobrescribe la misma foto
  },
});
const upload = multer({ storage });

// Servir la carpeta "uploads" como estático (para ver la foto)
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

// Ruta de prueba para confirmar que el servidor corre
app.get("/test", (req, res) => {
  res.send("Test OK");
});

// Conexión a PostgreSQL (Neon, en tu caso)
// Asegúrate de tener DATABASE_URL definido en Render, con ?sslmode=require
const pool = new Pool({
  connectionString: process.env.DATABASE_URL, 
  ssl: { rejectUnauthorized: false },
});

// Rutas públicas

// GET /entradas: Devuelve las últimas 5 entradas
app.get("/entradas", async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM entradas ORDER BY fecha DESC LIMIT 5");
    res.json(result.rows);
  } catch (err) {
    // Log detallado en los logs de Render
    console.log("Error en /entradas:", err);
    res.status(500).json({ error: err.message });
  }
});

// GET /todas: Devuelve todas las entradas
app.get("/todas", async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM entradas ORDER BY fecha DESC");
    res.json(result.rows);
  } catch (err) {
    console.log("Error en /todas:", err);
    res.status(500).json({ error: err.message });
  }
});

// GET /buscar: Busca entradas por palabra clave en el contenido
app.get("/buscar", async (req, res) => {
  const palabra = req.query.q;
  try {
    const result = await pool.query(
      "SELECT * FROM entradas WHERE contenido ILIKE $1 ORDER BY fecha DESC",
      [`%${palabra}%`]
    );
    res.json(result.rows);
  } catch (err) {
    console.log("Error en /buscar:", err);
    res.status(500).json({ error: err.message });
  }
});

// Middleware para rutas de administración (requiere x-admin-key)
app.use("/admin", (req, res, next) => {
  if (req.headers["x-admin-key"] !== ADMIN_KEY) {
    return res.status(403).json({ error: "Acceso denegado" });
  }
  next();
});

// POST /admin/nueva: Crea una nueva entrada
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
    console.log("Error en /admin/nueva:", err);
    res.status(500).json({ error: err.message });
  }
});

// DELETE /admin/borrar/:id: Elimina una entrada
app.delete("/admin/borrar/:id", async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query("DELETE FROM entradas WHERE id = $1", [id]);
    res.json({ mensaje: "Entrada eliminada" });
  } catch (err) {
    console.log("Error en /admin/borrar:", err);
    res.status(500).json({ error: err.message });
  }
});

// PUT /admin/modificar/:id: Actualiza una entrada
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
    console.log("Error en /admin/modificar:", err);
    res.status(500).json({ error: err.message });
  }
});

// POST /admin/subir-foto: Sube una imagen
app.post("/admin/subir-foto", upload.single("foto"), (req, res) => {
  res.json({ mensaje: "Foto subida con éxito", url: "/uploads/foto.jpg" });
});

// Iniciar el servidor
app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
  console.log("Base de datos conectada");
});
